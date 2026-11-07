#!/usr/bin/env python3
"""Small, offline-testable safety/performance primitives for Fiction Studio.

The source and generated media stay private. Nothing here grants release
approval, pads an episode to a fixed duration, or substitutes a narrator.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import wave
import zipfile

VOICE_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
VOICE_INSTRUCTION = (
    "A warm, natural male audiobook narrator, calm suspense, clear and measured, "
    "no exaggerated acting."
)
VOICE_PROFILE = "audiobook_ryan_qwen_1p7b_approved_2026_11_06_v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for buf in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(buf)
    return digest.hexdigest()


def chunk_key(text: str, *, model=VOICE_MODEL, instruction=VOICE_INSTRUCTION, speaker="Ryan") -> str:
    """Cache identity includes all settings that affect voice, not only text."""
    data = json.dumps([model, instruction, speaker, "English", text], ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:24]


def validated_wav(path: Path, *, min_seconds=.25, sample_rate=24000) -> bool:
    """Valid audio cache must actually decode and carry spoken-length frames."""
    try:
        if not Path(path).is_file() or Path(path).stat().st_size < 4096:
            return False
        with wave.open(str(path), "rb") as audio:
            return (audio.getnchannels() == 1 and audio.getsampwidth() == 2
                    and audio.getframerate() == sample_rate
                    and audio.getnframes() >= sample_rate * min_seconds)
    except (EOFError, OSError, wave.Error):
        return False


def atomic_json(path: Path, data: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent,
                                     prefix=target.name + ".", suffix=".tmp", delete=False) as fh:
        tmp = Path(fh.name)
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, target)


def probe_media(path: Path) -> dict:
    """Return actual streams and format, never inferred from filename/extension."""
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=index,codec_type,codec_name,width,height,duration,sample_rate",
        "-of", "json", str(path)
    ], check=True, capture_output=True, text=True, timeout=80)
    return json.loads(result.stdout)


def validate_review_video(path: Path, *, expected_audio_seconds: float | None = None,
                          expected_hash: str | None = None,
                          min_width: int = 1920, min_height: int = 1080,
                          min_duration_seconds: float = 10.0) -> dict:
    """Check actual MP4, A/V streams, dimensions, duration, and optional SHA.

    A passing result is a *technical review*, not a listening/visual approval.
    No 25-minute quota or artificial silence is imposed.
    """
    path = Path(path)
    if not path.is_file() or path.stat().st_size < 100_000:
        raise ValueError("Actual video file is missing/too small")
    data = probe_media(path)
    streams = data.get("streams", [])
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError("Review MP4 must have exactly one video and one narration audio track")
    if videos[0].get("codec_name") not in ("h264", "hevc", "av1"):
        raise ValueError("Unrecognized or incompatible review video codec")
    if videos[0].get("width", 0) < min_width or videos[0].get("height", 0) < min_height:
        raise ValueError("Video resolution below approved Full HD review standard")
    duration = float(data.get("format", {}).get("duration") or 0)
    if not 1 <= min_duration_seconds <= 4 * 3600:
        raise ValueError("Invalid required minimum review duration")
    if not min_duration_seconds <= duration <= 4 * 3600:
        raise ValueError("Unrealistic or absent actual video duration")
    if expected_audio_seconds is not None and abs(duration - expected_audio_seconds) > 1.5:
        raise ValueError("Picture and approved narration durations differ by >1.5 seconds")
    file_hash = sha256(path)
    if expected_hash and file_hash != expected_hash:
        raise ValueError("MP4 SHA-256 differs from private Kaggle report")
    return {"status": "TECHNICAL_REVIEW_PASS", "sha256": file_hash,
            "duration_seconds": round(duration, 3), "width": videos[0]["width"],
            "height": videos[0]["height"], "size_bytes": path.stat().st_size,
            "narration_audio_track_present": True,
            "full_listening_review_completed": False,
            "visual_continuity_review_completed": False,
            "ready_for_youtube": False}


def validate_scene_ledger(scenes: list[dict], *, segment_count: int) -> None:
    """Images must cover all speech with no gaps or overlaps."""
    if segment_count < 1 or not scenes:
        raise ValueError("No speech segments or visual scenes")
    last = 0
    for i, scene in enumerate(scenes):
        start, end = scene.get("start_chunk"), scene.get("end_chunk")
        if not isinstance(start, int) or not isinstance(end, int) or isinstance(start, bool):
            raise ValueError(f"Scene {i} has invalid timeline indexes")
        if start != last or end <= start or end > segment_count:
            raise ValueError(f"Scene {i} has missing/overlapping audio coverage")
        if not scene.get("scene_key"):
            raise ValueError(f"Scene {i} has no stable scene key for caching")
        if not (scene.get("approved_visual_file") or scene.get("visual_approved")):
            raise ValueError(f"Scene {i} has no approved source-linked visual")
        last = end
    if last != segment_count:
        raise ValueError("Some narration chunks are not illustrated")


def efficient_checkpoint(source_dir: Path, out: Path, *, source_sha256: str, voice_profile=VOICE_PROFILE) -> dict:
    """Atomic restorable checkpoint; already-compressed A/V/images use ZIP_STORED.

    A checkpoint is a **private** production output; never attach it to a
    public issue/PR or upload it as a public GitHub Actions artifact.
    """
    if not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
        raise ValueError("Source SHA-256 required for a reusable checkpoint")
    source_dir, out = Path(source_dir), Path(out)
    items = sorted(f for f in source_dir.rglob("*") if f.is_file() and f != out)
    if not items:
        raise ValueError("Cannot checkpoint empty output directory")
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": 1, "source_sha256": source_sha256,
                "voice_profile": voice_profile,
                "files": {str(f.relative_to(source_dir)): sha256(f) for f in items}}
    with tempfile.NamedTemporaryFile(dir=out.parent, suffix=".zip", delete=False) as fh:
        temp = Path(fh.name)
    try:
        with zipfile.ZipFile(temp, "w") as archive:
            for file in items:
                compression = (zipfile.ZIP_STORED if file.suffix.lower() in
                               {".mp4", ".m4a", ".mp3", ".png", ".jpg", ".jpeg", ".webp", ".zip"}
                               else zipfile.ZIP_DEFLATED)
                archive.write(file, str(file.relative_to(source_dir)), compress_type=compression)
            archive.writestr("__checkpoint_manifest.json", json.dumps(manifest, sort_keys=True))
        os.replace(temp, out)
    finally:
        temp.unlink(missing_ok=True)
    return {"files": len(items), "bytes": out.stat().st_size, "source_sha256": source_sha256}


def inspect_checkpoint(path: Path, *, source_sha256: str, voice_profile=VOICE_PROFILE) -> dict:
    with zipfile.ZipFile(path) as z:
        m = json.loads(z.read("__checkpoint_manifest.json"))
        if m.get("source_sha256") != source_sha256 or m.get("voice_profile") != voice_profile:
            raise ValueError("Checkpoint does not belong to this manuscript/voice")
        names = set(z.namelist()) - {"__checkpoint_manifest.json"}
        if names != set(m.get("files", {})):
            raise ValueError("Checkpoint manifest does not match files")
        for name, digest in m["files"].items():
            p = Path(name)
            if p.is_absolute() or ".." in p.parts or "\\" in name:
                raise ValueError("Unsafe checkpoint filename")
            if hashlib.sha256(z.read(name)).hexdigest() != digest:
                raise ValueError("Checkpoint file checksum mismatch")
    return m