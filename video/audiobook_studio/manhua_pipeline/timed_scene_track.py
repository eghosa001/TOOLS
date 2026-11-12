#!/usr/bin/env python3
"""Reliably encode source-timed, 24 fps illustrated scene tracks.

ffconcat image duration metadata + fps can silently drop/hold entire source
events on some FFmpeg builds. Encoding each still into a CFR shot and joining
those shots by stream copy preserves each narrated beat and permits hash caching.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
import hashlib
import json
import os
import subprocess

from PIL import Image, ImageOps

VERSION = "scene_cfr24_v1"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(2**20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(args: list[str], timeout: int = 600) -> None:
    subprocess.run(args, check=True, timeout=timeout, capture_output=True)


def build_timed_scene_track(
    scenes: list[tuple[Path, float]], destination: Path, *,
    preset: str = "ultrafast", motion: str = "none",
) -> dict:
    """Create cached CFR video, exact cumulative frame boundaries, no narration."""
    if preset not in ("ultrafast", "superfast", "veryfast", "fast"):
        raise ValueError("Unsupported scene encoding preset")
    if motion not in ("none", "subtle") or not scenes:
        raise ValueError("Invalid scene motion or empty timeline")
    destination = Path(destination).resolve()
    cache = destination.parent / ("." + destination.stem + ".scene_cache")
    cache.mkdir(parents=True, exist_ok=True)
    elapsed = 0.0
    previous = 0
    jobs = []
    vf = ("scale=1920:1080:force_original_aspect_ratio=decrease,"
          "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p")
    if motion == "subtle":
        vf = ("scale=1920:1080:force_original_aspect_ratio=increase,"
              "crop=1920:1080,zoompan=z='min(zoom+0.00008,1.06)':d=1:"
              "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
              "s=1920x1080:fps=24,format=yuv420p")
    for i, (image, seconds) in enumerate(scenes):
        elapsed += seconds
        end = round(elapsed * 24)
        frames = end - previous
        previous = end
        if frames < 1:
            raise ValueError("SCENE_FRAME_BOUNDARY_FAILED")
        image = Path(image).resolve(strict=True)
        fingerprint = hashlib.sha256(
            f"{VERSION}:{_sha(image)}:{frames}:{preset}:{motion}".encode()).hexdigest()
        stem = f"{i+1:04d}_{fingerprint[:16]}"
        jobs.append((image, cache/(stem + ".mp4"), frames))
    def encode(job: tuple[Path, Path, int]) -> tuple[Path, bool]:
        image, part, frames = job
        if part.exists() and part.stat().st_size > 5000:
            return part, True
        tmp = part.with_name(part.stem + ".temporary.mp4")
        try:
            _run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
                  "-y", "-loop", "1", "-framerate", "24", "-i", str(image),
                  "-vf", vf, "-frames:v", str(frames), "-an",
                  "-c:v", "libx264", "-preset", preset, "-crf", "21",
                  "-r", "24", "-movflags", "+faststart", str(tmp)],
                 timeout=max(180, int(frames / 2)))
            tmp.replace(part)
        finally:
            tmp.unlink(missing_ok=True)
        return part, False
    # Keep output ordering independent of worker completion ordering.
    with ThreadPoolExecutor(max_workers=min(3, os.cpu_count() or 1)) as workers:
        results = list(workers.map(encode, jobs))
    listing = cache/"cfr_segments.ffconcat"
    paths = [p for p, _ in results]
    if any("'" in str(path) or "\n" in str(path) for path in paths):
        raise ValueError("Unsafe scene cache paths")
    listing.write_text("ffconcat version 1.0\n"
                       + "".join(f"file '{part}'\n" for part in paths))
    destination.parent.mkdir(parents=True, exist_ok=True)
    pending = destination.with_name(destination.stem + ".partial.mp4")
    _run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
          "-y", "-safe", "0", "-f", "concat", "-i", str(listing),
          "-map", "0:v:0", "-c", "copy", "-movflags", "+faststart",
          str(pending)])
    info = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=nb_frames,r_frame_rate,duration",
         "-of", "json", str(pending)], timeout=40))
    stream = info["streams"][0]
    if (int(stream.get("nb_frames", -1)) != previous
            or stream.get("r_frame_rate") != "24/1"
            or abs(float(stream.get("duration", 0)) - elapsed) > .15):
        pending.unlink(missing_ok=True)
        raise ValueError("SCENE_CFR_TIMING_FAILED: exact 24fps frame count")
    pending.replace(destination)
    return {"video": str(destination), "scene_count": len(jobs), "frames": previous,
            "duration_seconds": previous / 24,
            "cache_hits": sum(bool(hit) for _, hit in results)}


def verify_rendered_scene_frames(
    video: Path, scenes: list[tuple[Path, float]], *,
    maximum_mean_error: float = 20.0
) -> dict:
    """Inspect a real decoded midpoint frame for every story-timed scene.

    This proves the correct image is visible when narration expects it; it
    does NOT substitute for creative/editorial story-event or full listening QA.
    """
    position = 0.0
    errors = []
    for index, (image, seconds) in enumerate(scenes):
        midpoint = position + seconds / 2
        position += seconds
        frame = subprocess.check_output([
            "ffmpeg", "-hide_banner", "-nostdin", "-v", "error",
            "-ss", f"{midpoint:.3f}", "-i", str(video),
            "-frames:v", "1", "-vf", "scale=96:54",
            "-f", "image2pipe", "-vcodec", "mjpeg", "-"], timeout=55)
        with Image.open(BytesIO(frame)) as actual, Image.open(image) as source:
            visible = actual.convert("RGB").resize((96, 54), Image.Resampling.BILINEAR)
            expected = ImageOps.fit(source.convert("RGB"), (96, 54), Image.Resampling.BILINEAR)
        left, right = visible.tobytes(), expected.tobytes()
        mean = sum(abs(a-b) for a, b in zip(left, right)) / len(left)
        errors.append(round(mean, 3))
        if mean > maximum_mean_error:
            raise ValueError(
                f"ENCODED_SCENE_MISMATCH at scene {index+1}: "
                f"mean image error {mean:.2f}; voice/visual timing is wrong")
    return {"decoded_midpoint_frames_checked": len(errors),
            "worst_mean_rgb_error": max(errors), "all_scenes_timed_correctly": True,
            "human_visual_qa_completed": False}
