#!/usr/bin/env python3
"""Deterministic, low-data, 2D frame renderer for approved Ninefold shot artwork.

This creates WORK-IN-PROGRESS PNG frames, never an approved master or a video.
There is deliberately no image-to-image AI, pose invention, frame morphing,
automatic voice selection, or release approval.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import shutil
from functools import lru_cache
from pathlib import Path
from time import perf_counter

from PIL import Image

MAX_FRAMES = 2400
MAX_PIXELS = 1920 * 1080 * 2


class FrameSpecError(ValueError):
    """Reject invalid schedules, absent painted artwork and unsafe paths."""


def asset_path(base: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise FrameSpecError("Every artwork file must be a nonempty relative path")
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise FrameSpecError(f"Missing or outside-of-artwork source: {relative}")
    if path.suffix.lower() != ".png":
        raise FrameSpecError(f"Artwork must be transparent/painted PNG: {relative}")
    return path


def keyframes(keys: list, frames: int, label: str) -> list:
    if not isinstance(keys, list) or not keys:
        raise FrameSpecError(f"{label} must have at least one key starting at frame 1")
    positions = [key.get("frame") for key in keys if isinstance(key, dict)]
    if len(positions) != len(keys) or positions[0] != 1:
        raise FrameSpecError(f"{label} must start on frame 1")
    if any(type(f) is not int or f < 1 or f > frames for f in positions):
        raise FrameSpecError(f"{label} contains an invalid frame number")
    if positions != sorted(set(positions)):
        raise FrameSpecError(f"{label} must have ascending, distinct frames")
    return keys


def finite(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FrameSpecError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise FrameSpecError(f"{label} must be finite")
    return result


def validate_spec(data: dict, base: Path) -> dict:
    if not isinstance(data, dict) or data.get("version") != 1:
        raise FrameSpecError("Expected a version 1 JSON object")
    shot = data.get("shot_id")
    if not isinstance(shot, str) or not shot or len(shot) > 100:
        raise FrameSpecError("shot_id must be a nonempty name")
    w, h, frames, fps = (data.get(n) for n in ("width", "height", "frames", "fps"))
    if any(type(x) is not int for x in (w, h, frames, fps)):
        raise FrameSpecError("width, height, frames and fps must be integers")
    if w < 1 or h < 1 or w * h > MAX_PIXELS or frames < 1 or frames > MAX_FRAMES or fps != 24:
        raise FrameSpecError("Use a bounded image size, <=2400 frames and 24 fps")
    camera = keyframes(data.get("camera", [{"frame": 1, "x": 0, "y": 0}]), frames, "camera")
    for key in camera:
        for attr in ("x", "y"):
            finite(key.get(attr, 0), f"camera {attr}")
    layers = data.get("layers")
    if not isinstance(layers, list) or len(layers) < 2:
        raise FrameSpecError("At least two expressly layered image assets are required")
    ids = []
    files = set()
    for layer in layers:
        if not isinstance(layer, dict):
            raise FrameSpecError("Each layer must be an object")
        lid = layer.get("id")
        if not isinstance(lid, str) or not lid:
            raise FrameSpecError("Each layer needs a stable ID")
        ids.append(lid)
        z = finite(layer.get("z", 0), f"{lid} z")
        parallax = finite(layer.get("parallax", 1), f"{lid} parallax")
        if not (0 <= parallax <= 1) or abs(z) > 100000:
            raise FrameSpecError(f"{lid}: invalid depth or z order")
        if not isinstance(layer.get("on_twos", False), bool):
            raise FrameSpecError(f"{lid}: on_twos must be boolean")
        if ("image" in layer) == ("drawings" in layer):
            raise FrameSpecError(f"{lid}: choose image OR timed drawings")
        drawings = (keyframes(layer["drawings"], frames, f"{lid} drawings")
                    if "drawings" in layer else [{"frame": 1, "image": layer["image"]}])
        for drawing in drawings:
            files.add(str(asset_path(base, drawing.get("image"))))
        motions = keyframes(layer.get("motion", [
            {"frame": 1, "x": layer.get("x", 0), "y": layer.get("y", 0), "scale": 1}
        ]), frames, f"{lid} motion")
        for motion in motions:
            for attr, default in (("x", 0), ("y", 0), ("scale", 1)):
                val = finite(motion.get(attr, default), f"{lid} {attr}")
                if attr == "scale" and not (0.05 <= val <= 8):
                    raise FrameSpecError(f"{lid}: scale outside safe limits")
    if len(set(ids)) != len(ids):
        raise FrameSpecError("Layer IDs must be unique")
    # Refuse blank transparent PNGs: technical evidence, NOT artistic approval.
    for name in sorted(files):
        try:
            with Image.open(name) as raw:
                if raw.format != "PNG" or raw.size[0] < 1 or raw.size[1] < 1:
                    raise FrameSpecError(f"Invalid PNG: {name}")
                if not raw.convert("RGBA").getbbox():
                    raise FrameSpecError(f"Empty artwork layer: {name}")
        except (OSError, ValueError) as exc:
            raise FrameSpecError(f"Unreadable artwork {name}: {exc}") from exc
    return {"source_files": sorted(files), "camera": camera,
            "layers": sorted(layers, key=lambda layer: layer.get("z", 0))}


def interpolate(keys: list, frame: int, attr: str, default: float) -> float:
    points = [row["frame"] for row in keys]
    idx = bisect.bisect_right(points, frame) - 1
    a = keys[max(0, idx)]
    if idx >= len(keys) - 1:
        return finite(a.get(attr, default), attr)
    b = keys[idx + 1]
    t = (frame - a["frame"]) / (b["frame"] - a["frame"])
    # Smooth camera/body positions but NEVER morph one drawing into another.
    t = t * t * (3 - 2 * t) if a.get("ease", "smooth") == "smooth" else t
    start = finite(a.get(attr, default), attr)
    end = finite(b.get(attr, default), attr)
    return start + (end - start) * t


def drawing_at(layer: dict, frame: int) -> str:
    drawings = layer.get("drawings")
    if drawings is None:
        return layer["image"]
    points = [row["frame"] for row in drawings]
    return drawings[bisect.bisect_right(points, frame) - 1]["image"]


def exposure(frame: int, on_twos: bool) -> int:
    return 1 + (frame - 1) // 2 * 2 if on_twos else frame


@lru_cache(maxsize=48)
def source_rgba(name: str) -> Image.Image:
    with Image.open(name) as src:
        return src.convert("RGBA")


@lru_cache(maxsize=64)
def scaled_rgba(name: str, width: int, height: int) -> Image.Image:
    im = source_rgba(name)
    if im.size == (width, height):
        return im
    return im.resize((width, height), Image.Resampling.LANCZOS)


def plan_frame(data: dict, valid: dict, base: Path, frame: int, render_scale: float):
    c = valid["camera"]
    camx = interpolate(c, frame, "x", 0)
    camy = interpolate(c, frame, "y", 0)
    plan = []
    for layer in valid["layers"]:
        sample = exposure(frame, layer.get("on_twos", False))
        drawing = str(asset_path(base, drawing_at(layer, sample)))
        motion = layer.get("motion", [
            {"frame": 1, "x": layer.get("x", 0), "y": layer.get("y", 0), "scale": 1}
        ])
        x = interpolate(motion, sample, "x", 0)
        y = interpolate(motion, sample, "y", 0)
        size = interpolate(motion, sample, "scale", 1)
        depth = layer.get("parallax", 1)
        destx = round((x - camx * depth) * render_scale)
        desty = round((y - camy * depth) * render_scale)
        w, h = source_rgba(drawing).size
        tw, th = max(1, round(w * size * render_scale)), max(1, round(h * size * render_scale))
        plan.append((drawing, destx, desty, tw, th))
    return tuple(plan)


def composite(canvas: Image.Image, image: Image.Image, x: int, y: int) -> None:
    # Handles moving foreground art beyond camera edges without exceptions.
    left, top = max(x, 0), max(y, 0)
    right, bottom = min(x + image.width, canvas.width), min(y + image.height, canvas.height)
    if left >= right or top >= bottom:
        return
    crop = image.crop((left - x, top - y, right - x, bottom - y))
    canvas.alpha_composite(crop, (left, top))


def fingerprint(data: dict, source_files: list[str]) -> str:
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8"))
    for name in source_files:
        digest.update(Path(name).name.encode("utf-8"))
        with open(name, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def render(spec_path: Path, out: Path, scale: float = 1.0,
           start: int = 1, end: int | None = None) -> dict:
    start_time = perf_counter()
    base = spec_path.resolve().parent
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    valid = validate_spec(data, base)
    if not (0.1 <= scale <= 1.0) or not math.isfinite(scale):
        raise FrameSpecError("Render scale must be between 0.1 and 1")
    last = data["frames"] if end is None else end
    if not (1 <= start <= last <= data["frames"]):
        raise FrameSpecError("Invalid frame range")
    width, height = max(1, round(data["width"] * scale)), max(1, round(data["height"] * scale))
    out.mkdir(parents=True, exist_ok=True)
    previous_plan = None
    previous_png = None
    copied = 0
    for frame in range(start, last + 1):
        path = out / f"frame_{frame:06d}.png"
        current = plan_frame(data, valid, base, frame, scale)
        if current == previous_plan and previous_png is not None:
            shutil.copyfile(previous_png, path)
            copied += 1
        else:
            canvas = Image.new("RGBA", (width, height))
            for image_name, x, y, tw, th in current:
                composite(canvas, scaled_rgba(image_name, tw, th), x, y)
            canvas.convert("RGB").save(path, format="PNG", compress_level=1)
        previous_plan, previous_png = current, path
    report = {
        "status": "technical_frames_only_NOT_DIRECTOR_APPROVED",
        "shot_id": data["shot_id"], "fps": data["fps"],
        "width": width, "height": height,
        "frame_range": [start, last], "rendered_frames": last - start + 1,
        "held_frames_reused_without_recompositing": copied,
        "input_sha256": fingerprint(data, valid["source_files"]),
        "elapsed_seconds": round(perf_counter() - start_time, 3),
        "explicit_art_files": len(valid["source_files"]),
        "artistic_approval": False, "release_authorized": False,
        "notes": [
            "Each frame preserves original drawn source; no morphing or invented key drawings.",
            "Held poses, layered parallax, camera and foreground occlusion are deterministic.",
            "Review acting, lip sync, hand contacts, character likeness and licensing manually.",
            "No audio, auto-montage, 3D render, video encoding, upload or publication performed."
        ],
    }
    report_file = out / f"technical_report_{start:06d}_{last:06d}.json"
    report_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path, help="Manually authored shot exposure sheet")
    parser.add_argument("--out", required=True, type=Path, help="Internal technical PNG frames directory")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="1 for full-res; 0.5 for quick technical layout only")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()
    try:
        print(json.dumps(render(args.spec, args.out, args.scale, args.start, args.end), indent=2))
    except (FrameSpecError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Frame stage blocked: {exc}\n")


if __name__ == "__main__":
    main()
