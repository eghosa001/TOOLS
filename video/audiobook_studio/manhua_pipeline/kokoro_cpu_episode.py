#!/usr/bin/env python3
"""Kokoro Michael CPU-only narration + strict scene-aligned MP4 workflow.

Input sources and artworks are PRIVATE, never committed in the public TOOLS repo.
Narration and all images are divided at the exact same meaningful text beats;
no approximate word-proportional visual duration and no combined speed-ups.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import wave

from video.audiobook_studio.manhua_pipeline.scene_locked_quality import (
    check_episode, file_digest,
)

RATE = 24000
GAP_S = 0.14
DEFAULT_ENGINE_VERSION = "kokoro-0.9.4"
VOICE = "am_michael"


def valid_wav(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 4096:
        return False
    try:
        with wave.open(str(path), "rb") as w:
            return (w.getnchannels() == 1 and w.getsampwidth() == 2
                    and w.getframerate() == RATE and w.getnframes() > 2000)
    except (wave.Error, OSError, EOFError):
        return False


def cache_id(text: str, speed: float) -> str:
    data = json.dumps([DEFAULT_ENGINE_VERSION, "a", VOICE, float(speed),
                       text], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:24]


def generate_wav(text: str, path: Path, *, speed: float, pipeline) -> None:
    import numpy as np
    frames = []
    for result in pipeline(text, voice=VOICE, speed=speed):
        audio = result.audio if hasattr(result, "audio") else result[2]
        if hasattr(audio, "detach"):
            audio = audio.detach().cpu().numpy()
        samples = np.asarray(audio, dtype=np.float32).reshape(-1)
        if not samples.size or not np.isfinite(samples).all():
            raise RuntimeError("Kokoro generated invalid speech")
        frames.append(samples)
    if not frames:
        raise RuntimeError("Kokoro did not generate any speech")
    data = np.concatenate(frames)
    data = np.concatenate((data, np.zeros(round(GAP_S * RATE), dtype=np.float32)))
    pcm = (np.clip(data, -1.0, 1.0) * 32767).astype("<i2").tobytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp.wav")
    with wave.open(str(temp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm)
    os.replace(temp, path)
    if not valid_wav(path):
        raise RuntimeError("Kokoro output WAV failed verification")


def concat_wavs(parts: list[Path], output: Path) -> list[float]:
    """Concatenate real decoded PCM frames; return precise measured scene seconds."""
    durations = []
    with wave.open(str(output), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        for path in parts:
            if not valid_wav(path):
                raise ValueError("Missing, truncated or invalid narrator WAV: " + str(path))
            with wave.open(str(path), "rb") as source:
                frames = source.getnframes()
                durations.append(frames / RATE)
                out.writeframes(source.readframes(frames))
    return durations


def synthesize(source: Path, beats_path: Path, root: Path) -> tuple[Path, list[float]]:
    check_episode(source, beats_path, require_images=False, require_pixel_review=False)
    data = json.loads(beats_path.read_text(encoding="utf-8"))
    beats = data["beats"]
    speed = float(data["narrator"]["speed"])
    work = root / "kokoro_cache"
    work.mkdir(parents=True, exist_ok=True)
    wavs = []
    pipeline = None
    for beat in beats:
        key = cache_id(beat["text"], speed)
        path = work / (beat["id"] + "_" + key + ".wav")
        if not valid_wav(path):
            if pipeline is None:
                from kokoro import KPipeline
                pipeline = KPipeline(lang_code="a", device="cpu")
            generate_wav(beat["text"], path, speed=speed, pipeline=pipeline)
        wavs.append(path)
    joined = root / "narration_pcm.wav"
    seconds = concat_wavs(wavs, joined)
    return joined, seconds


def ffmpeg_master(source: Path, output: Path) -> None:
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(source), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "192k", str(output)
    ], check=True, timeout=600)


def write_scene_timeline(beats: list[dict], beats_path: Path,
                         seconds: list[float], out: Path) -> Path:
    if len(seconds) != len(beats):
        raise ValueError("Narration chunk count does not match visual beat count")
    timeline = []
    for beat, dur in zip(beats, seconds):
        picture = (beats_path.parent / beat["image"]).resolve()
        timeline.append({
            "image": str(picture),
            "seconds": round(dur, 6),
            "image_sha256": file_digest(picture),
            "source_sha256": hashlib.sha256(beat["text"].encode("utf-8")).hexdigest(),
            "scene_key": beat["id"],
        })
    path = out / "PRIVATE_SCENE_TIMELINE.json"
    path.write_text(json.dumps(timeline, indent=2, ensure_ascii=False) + "\n")
    return path


def cached_scene_seconds(beats: list[dict], timeline_path: Path) -> list[float]:
    """Reuse measured beat timing only when it still covers this exact spoken script."""
    if not timeline_path.is_file():
        raise ValueError(
            "Cannot reuse narration without the matching prior scene timeline; "
            "run once in narrate mode or restore PRIVATE_SCENE_TIMELINE.json."
        )
    rows = json.loads(timeline_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or len(rows) != len(beats):
        raise ValueError("Cached narration timeline does not match the beat count")
    seconds = []
    for beat, row in zip(beats, rows):
        expected = hashlib.sha256(beat["text"].encode("utf-8")).hexdigest()
        if not isinstance(row, dict) or row.get("source_sha256") != expected:
            raise ValueError("Cached narration timeline does not match the exact spoken beats")
        value = row.get("seconds")
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError("Cached narration timeline has invalid measured timing")
        seconds.append(float(value))
    return seconds


def run(source: Path, beats_path: Path, out: Path, mode: str,
        approved_audio: Path | None = None) -> dict:
    check = check_episode(source, beats_path,
                          require_images=(mode == "render"),
                          require_pixel_review=(mode == "render"))
    if mode == "check":
        return check
    out.mkdir(parents=True, exist_ok=True)
    data = json.loads(beats_path.read_text(encoding="utf-8"))
    if approved_audio is not None:
        if mode != "render":
            raise ValueError("--approved-audio is supported only with --mode render")
        audio = approved_audio.expanduser().resolve(strict=True)
        seconds = cached_scene_seconds(
            data["beats"], out / "PRIVATE_SCENE_TIMELINE.json")
        audio_reused = True
    else:
        joined, seconds = synthesize(source, beats_path, out)
        audio = out / "narration.m4a"
        ffmpeg_master(joined, audio)
        audio_reused = False
    report = {**check, "narrator": VOICE, "synthesis_speed": float(
        data["narrator"]["speed"]),
        "speech_beats": len(seconds), "measured_scene_seconds": seconds,
        "audio_file": audio.name, "audio_sha256": file_digest(audio),
        "audio_reused": audio_reused,
        "audio_full_listen_approved": False, "publish_approved": False}
    if mode == "render":
        from video.audiobook_studio.manhua_pipeline.assemble_existing import (
            assemble,
        )
        import argparse as _argparse
        timeline = write_scene_timeline(data["beats"], beats_path, seconds, out)
        video = out / "EPISODE_PRIVATE_REVIEW.mp4"
        assembly = assemble(_argparse.Namespace(
            audio=str(audio), image=None, timeline=str(timeline), thumbnail=None,
            visual_qa_report=None, require_visual_qa=False,
            output=str(video), motion="none", preset="ultrafast", force=False))
        report.update(video_file=video.name,
                      video_sha256=file_digest(video),
                      measured_duration_seconds=assembly["duration_seconds"],
                      assembly_seconds=assembly.get("assembly_seconds"),
                      assembly_cache_hit=assembly.get("cache_hit", False),
                      editorial_visual_ledger=check["review_status"],
                      technical_video_review=assembly["technical_review"])
    (out / "PRIVATE_EPISODE_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path,
                        help="PRIVATE verbatim approved episode UTF-8 text")
    parser.add_argument("--beats", required=True, type=Path,
                        help="PRIVATE ordered source-locked visual manifest JSON")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--mode", choices=("check", "narrate", "render"),
                        default="check")
    parser.add_argument(
        "--approved-audio", type=Path,
        help=("Reuse an existing approved narration during render; requires the "
              "matching prior PRIVATE_SCENE_TIMELINE.json in --out. Skips TTS and mastering.")
    )
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.beats, args.out, args.mode,
                         approved_audio=args.approved_audio),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
