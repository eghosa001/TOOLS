#!/usr/bin/env python3
"""Per-shot reference craft controls for Universal Edit Studio (no AI assets).

Turns explicit human-authored source framing and dialogue captions into real
FFmpeg filters; never chooses shots, invents visuals, or grants reuse rights.
"""
from __future__ import annotations
import math
from pathlib import Path

PALETTE = {
    "white": "white", "amber": "0xFFC36B", "red": "0xFF6666",
    "pink": "0xFF5DCB", "cyan": "0x5CE6ED", "lime": "0xACF281",
    "yellow": "0xFFF078",
}
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def number(value, label, low, high):
    if type(value) not in (float, int) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{label} must be between {low} and {high}")
    return float(value)


def visual_filter(shot, w, h, source_w, source_h, fps, speed, default_fit, scratch, index):
    """Return one -vf filtergraph with editor-authored actions."""
    framing = shot.get("framing", {})
    if not isinstance(framing, dict):
        raise ValueError("framing must be a per-shot object")
    mode = framing.get("mode", default_fit)
    if mode not in ("contain", "cover", "soft_background"):
        raise ValueError("framing.mode must be contain, cover or soft_background")
    fx = number(framing.get("focus_x", 0.5), "focus_x", 0, 1)
    fy = number(framing.get("focus_y", 0.5), "focus_y", 0, 1)
    source_aspect = source_w / source_h
    out_aspect = w / h
    visible_fraction = min(source_aspect / out_aspect, out_aspect / source_aspect)
    if mode == "cover" and visible_fraction < 0.57 and framing.get("visually_verified") is not True:
        raise ValueError(
            "Aggressive cover crop discards too much source frame. "
            "Choose contain/soft_background, or explicitly verify subject-safe crop per shot."
        )
    base = f"setpts=(PTS-STARTPTS)/{speed:.5f}"
    if mode == "contain":
        chain = (f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,"
                 f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black")
        graph = f"{base},{chain}"
    elif mode == "cover":
        chain = (f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,"
                 f"crop={w}:{h}:(iw-ow)*{fx:.4f}:(ih-oh)*{fy:.4f}")
        graph = f"{base},{chain}"
    else:
        # Both layers are the SAME real source frame; foreground is never cropped.
        graph = (f"{base},split=2[back][front];"
                 f"[back]scale={w}:{h}:force_original_aspect_ratio=increase,"
                 f"crop={w}:{h},boxblur=luma_radius=16:luma_power=2[blur];"
                 f"[front]scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos[fg];"
                 f"[blur][fg]overlay=(W-w)/2:(H-h)/2")
    grade = shot.get("grade", {})
    if grade:
        if not isinstance(grade, dict):
            raise ValueError("grade must be an object")
        c = number(grade.get("contrast", 1), "contrast", .82, 1.18)
        s = number(grade.get("saturation", 1), "saturation", .65, 1.28)
        b = number(grade.get("brightness", 0), "brightness", -.07, .07)
        graph += f",eq=contrast={c:.3f}:saturation={s:.3f}:brightness={b:.3f}"
    graph += f",setsar=1,fps={fps},format=yuv420p"
    events = shot.get("caption_events", [])
    if not isinstance(events, list) or len(events) > 20:
        raise ValueError("Maximum 20 precisely timed caption events per shot")
    shot_duration = (shot["end_sec"] - shot["start_sec"]) / speed
    for j, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError("caption event must be an object")
        caption = event.get("text", "")
        if not isinstance(caption, str) or not 1 <= len(caption.strip()) <= 80 or "\n" in caption:
            raise ValueError("Caption must contain 1-80 characters on one line")
        a = number(event.get("at_sec"), "caption at_sec", 0, shot_duration)
        b = number(event.get("until_sec"), "caption until_sec", a + .01, shot_duration + .015)
        color = event.get("color", "white")
        if color not in PALETTE:
            raise ValueError("caption color must be an approved readable palette color")
        size = int(number(event.get("size", 54), "caption size", 24, 92))
        y = number(event.get("y_fraction", .71), "caption y_fraction", .18, .82)
        textfile = Path(scratch) / f"caption_{index:03d}_{j:02d}.txt"
        textfile.write_text(caption, encoding="utf-8")
        graph += (f",drawtext=fontfile={FONT}:textfile={textfile}:"
                  f"fontcolor={PALETTE[color]}:fontsize={size}:borderw=3:"
                  f"bordercolor=black@0.72:x=(w-text_w)/2:y=h*{y:.3f}:"
                  f"enable='between(t,{a:.3f},{b:.3f})'")
    return graph, {
        "framing": mode,
        "source_visible_fraction": round(visible_fraction if mode == "cover" else 1., 4),
        "caption_events": len(events),
        "grade_applied": bool(grade),
    }
