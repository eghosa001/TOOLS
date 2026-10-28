#!/usr/bin/env python3
"""Manually directed editor for Facts Uncovered Great Pyramid.
Creative decisions live ONLY in a separately approved JSON shot map.
This renderer performs mechanical composition and refuses unapproved edits.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

SCENE_KINDS = {"ARCHIVAL", "ORIGINAL_DIAGRAM", "ARTISTIC_RECONSTRUCTION"}
MOVEMENTS = {"STATIC", "PUSH", "PAN_LEFT", "PAN_RIGHT"}
APPROVED = "APPROVED"


def run(*args):
    p = subprocess.run([str(x) for x in args], text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError("Command failed: " + " ".join(str(x) for x in args[:5])
                           + "\n" + p.stderr[-2500:])


def media_duration(path):
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True, capture_output=True, check=True
    )
    return float(p.stdout.strip())


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def resolved_asset(base, value):
    p = Path(value)
    if not p.is_absolute():
        p = base / p
    p = p.resolve()
    if not p.is_file():
        raise ValueError("Missing visual asset: " + str(p))
    return p


def validate(manifest, directory):
    """Fail closed on missing rights, timing, editorial approvals and assets."""
    if not isinstance(manifest, dict) or not manifest.get("shots"):
        raise ValueError("No manually authored shot map.")
    if manifest.get("manual_editor_approval") != APPROVED:
        raise ValueError("Documentary/Short not individually editor-approved.")
    if manifest.get("historical_accuracy_approval") != APPROVED:
        raise ValueError("Historical approval missing.")
    w, h, fps = (manifest.get("width"), manifest.get("height"), manifest.get("fps"))
    if (w, h) not in ((1920, 1080), (1080, 1920)) or fps != 24:
        raise ValueError("Expected 1080p widescreen or vertical at 24 fps.")
    wav = resolved_asset(directory, manifest["narration_wav"])
    length = media_duration(wav)
    cursor = 0.0
    shotids = set()
    for i, s in enumerate(manifest["shots"], 1):
        sid = s.get("id")
        if not sid or sid in shotids:
            raise ValueError("Unique shot ID required at position " + str(i))
        shotids.add(sid)
        if s.get("editorial_status") != APPROVED or s.get("rights_status") != APPROVED:
            raise ValueError("Unapproved editorial/rights shot " + str(sid))
        if s.get("historical_accuracy_status") != APPROVED:
            raise ValueError("Unapproved historical shot " + str(sid))
        if s.get("kind") not in SCENE_KINDS:
            raise ValueError("Invalid visual kind " + str(sid))
        if s.get("movement") not in MOVEMENTS:
            raise ValueError("Movement must be manually chosen " + str(sid))
        if s.get("transition", "CUT") != "CUT":
            raise ValueError("Only reviewed hard cuts supported; no silent transition substitution.")
        if not str(s.get("exact_narration", "")).strip():
            raise ValueError("Missing actual spoken passage for " + str(sid))
        start, end = float(s["start"]), float(s["end"])
        if abs(start - cursor) > 0.06 or end - start < 0.3:
            raise ValueError("Gap, overlap or invalid duration at " + str(sid))
        cursor = end
        asset = resolved_asset(directory, s["asset_file"])
        declared_hash = s.get("asset_sha256")
        if not declared_hash or sha256(asset) != declared_hash:
            raise ValueError("Missing or incorrect SHA256 for " + str(sid))
        if s["kind"] == "ARCHIVAL":
            if not s.get("source_url") or not s.get("licence") or not s.get("creator"):
                raise ValueError("Incomplete archival attribution for " + str(sid))
        else:
            if not str(s.get("visual_disclosure", "")).strip():
                raise ValueError("Reconstruction/diagram disclosure missing for " + str(sid))
        if s.get("framing") not in ("CONTAIN", "COVER"):
            raise ValueError("Framing must be selected per shot " + str(sid))
    if abs(cursor - length) > 0.20:
        raise ValueError("Approved timeline ends at %.3f, actual narration at %.3f" % (cursor, length))
    return wav, length


def prepare_frame(s, base, target, width, height):
    src = Image.open(resolved_asset(base, s["asset_file"])).convert("RGB")
    if s["framing"] == "COVER":
        canvas = ImageOps.fit(src, (width, height), method=Image.Resampling.LANCZOS)
    else:
        canvas = Image.new("RGB", (width, height), (11, 19, 28))
        fitted = ImageOps.contain(src, (width, height), method=Image.Resampling.LANCZOS)
        canvas.paste(fitted, ((width - fitted.width)//2, (height - fitted.height)//2))
    label = s.get("on_screen_label", "").strip()
    if s["kind"] != "ARCHIVAL":
        label = (s["visual_disclosure"] + "  |  " + label).strip(" |")
    if label:
        draw = ImageDraw.Draw(canvas, "RGBA")
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(font_path, 28 if width == 1920 else 29)
        max_len = 105 if width == 1920 else 44
        label = label[:max_len]
        bounds = draw.textbbox((0, 0), label, font=font)
        tw = bounds[2] - bounds[0]
        x = 35 if width == 1920 else 26
        y = 30 if height == 1080 else 180
        draw.rounded_rectangle((x-15, y-11, x+tw+18, y+46),
                               radius=8, fill=(9, 16, 26, 225))
        draw.text((x, y), label, font=font, fill=(246, 238, 222, 255))
    canvas.save(target, quality=96, subsampling=0)


def motion_filter(s, width, height, frames):
    z = s["movement"]
    if z == "STATIC":
        return "format=yuv420p"
    if z == "PUSH":
        expr = "z='min(zoom+0.00011,1.035)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
    elif z == "PAN_LEFT":
        expr = "z='1.035':x='(iw-iw/zoom)*(1-on/%d)':y='(ih-ih/zoom)/2'" % max(1, frames)
    else:
        expr = "z='1.035':x='(iw-iw/zoom)*(on/%d)':y='(ih-ih/zoom)/2'" % max(1, frames)
    return "zoompan=%s:d=1:s=%dx%d:fps=24,format=yuv420p" % (expr, width, height)


def render(manifest_path, output_path, workdir):
    manifest_path = Path(manifest_path).resolve()
    directory = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    narration, narration_length = validate(manifest, directory)
    workdir = Path(workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    width, height = manifest["width"], manifest["height"]
    clips = []
    for i, s in enumerate(manifest["shots"]):
        frame = workdir / ("approved_%04d.jpg" % i)
        clip = workdir / ("approved_%04d.mp4" % i)
        prepare_frame(s, directory, frame, width, height)
        duration = float(s["end"]) - float(s["start"])
        nframes = round(duration * 24)
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-loop", "1", "-framerate", "24", "-i", frame,
            "-frames:v", nframes,
            "-vf", motion_filter(s, width, height, nframes),
            "-c:v", "libx264", "-preset", "medium", "-crf", "17",
            "-pix_fmt", "yuv420p", "-an", clip)
        clips.append(clip)
    concat = workdir / "locked_clips.txt"
    concat.write_text("".join("file '%s'\n" % str(p) for p in clips), encoding="utf-8")
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-f", "concat", "-safe", "0", "-i", concat, "-i", narration,
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-t", str(narration_length), "-movflags", "+faststart", output_path)
    actual = media_duration(output_path)
    if abs(actual - narration_length) > 0.25:
        raise RuntimeError("Final runtime mismatch: %.3fs vs %.3fs" % (actual, narration_length))
    report = {
        "editorial_gate": "PASSED_SPECIFICATION_VALIDATION",
        "continuous_editorial_playback": "NOT_VERIFIED",
        "input_manifest": str(manifest_path),
        "output_file": str(output_path),
        "output_sha256": sha256(output_path),
        "actual_duration_seconds": actual,
        "approved_shot_count": len(clips),
        "human_release_approval": "NOT_VERIFIED",
    }
    output_path.with_suffix(".validation.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("shot_map", help="Individually approved timeline JSON")
    parser.add_argument("output", help="Output MP4")
    parser.add_argument("--workdir", default="manual_render_work")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    manifest_path = Path(args.shot_map).resolve()
    if args.validate_only:
        m = json.loads(manifest_path.read_text())
        wav, sec = validate(m, manifest_path.parent)
        print(json.dumps({"status": "VALID", "shots": len(m["shots"]),
                          "narration_seconds": sec, "source_audio": str(wav)}))
    else:
        render(manifest_path, args.output, args.workdir)


if __name__ == "__main__":
    main()
