#!/usr/bin/env python3
"""Derive timed Rhubarb mouth-shape cues from ORIGINAL Episode 1 voice WAVs.

Rhubarb is external, free software (MIT); install its official version
separately. This tool produces metadata only and never renders video,
changes dialogue, or fabricates native facial shape keys.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
import tempfile
import wave
from pathlib import Path

ALLOWED = set("ABCDEFGHX")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def duration(path):
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / wav.getframerate()


def check_cues(cues, seconds):
    if not isinstance(cues, list) or not cues:
        raise ValueError("Rhubarb produced no mouth shapes")
    expected = 0.0
    for index, cue in enumerate(cues):
        if cue.get("value") not in ALLOWED:
            raise ValueError("Unknown mouth shape at index " + str(index))
        start = cue.get("start")
        end = cue.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            raise ValueError("Invalid cue time type")
        if not all(math.isfinite(v) for v in (start, end)):
            raise ValueError("Nonfinite mouth cue")
        if start < 0 or end <= start or start > expected + 0.04 or start < expected - 0.04:
            raise ValueError("Gap, overlapping or reversed mouth cues")
        if end > seconds + 0.07:
            raise ValueError("Mouth shapes extend past actual voice WAV")
        expected = end
    if abs(expected - seconds) > 0.08:
        raise ValueError("Rhubarb cues do not cover voice recording")
    if not any(cue["value"] not in ("A", "X") for cue in cues):
        raise ValueError("No phonetic cues detected; actual speech needs review")
    return len(cues)


def prepare(story_path, audio_dir, rhubarb_exe, output):
    story_path, audio_dir, output = Path(story_path), Path(audio_dir), Path(output)
    source_story = story_path.read_bytes()
    story = json.loads(source_story)
    if story.get("title") != "The Leaf That Wouldn't Stay" or len(story.get("dialogue", [])) != 15:
        raise ValueError("Refusing to process incorrect pilot or rewritten episode")
    rhubarb_exe = Path(rhubarb_exe).resolve()
    if not rhubarb_exe.is_file():
        raise FileNotFoundError("Rhubarb binary missing")
    version = subprocess.check_output([str(rhubarb_exe), "--version"], text=True, timeout=20).strip()
    if "1.14.0" not in version:
        raise RuntimeError("Pin expected official Rhubarb 1.14.0, got " + version)
    lines = []
    for line in story["dialogue"]:
        wav = audio_dir / ("line_%03d.wav" % line["id"])
        if not wav.is_file():
            raise FileNotFoundError("Original Piper WAV missing: " + str(wav))
        seconds = duration(wav)
        if seconds <= 0.06 or seconds > (line["end"] - line["start"] - 0.12):
            raise ValueError("Original WAV violates fixed story line timing")
        with tempfile.TemporaryDirectory(prefix="rhubarb_ep01_") as temp:
            transcript = Path(temp) / "dialog.txt"
            transcript.write_text(line["text"] + "\n", encoding="utf-8")
            cues_path = Path(temp) / "cues.json"
            subprocess.run([str(rhubarb_exe), "-q", "-r", "pocketSphinx",
                            "-f", "json", "--extendedShapes", "GHX",
                            "-d", str(transcript), "-o", str(cues_path), str(wav)],
                           check=True, timeout=90, capture_output=True, text=True)
            generated = json.loads(cues_path.read_text(encoding="utf-8"))
            cues = generated.get("mouthCues")
            count = check_cues(cues, seconds)
        lines.append({"id": line["id"], "speaker": line["speaker"],
                      "text_sha256": hashlib.sha256(line["text"].encode("utf-8")).hexdigest(),
                      "wav_sha256": sha256(wav),
                      "wav_seconds": round(seconds, 6),
                      "story_start": line["start"], "story_end": line["end"],
                      "cue_count": count, "cues": cues})
    result = {"schema_version": 1, "title": story["title"],
              "original_story_sha256": hashlib.sha256(source_story).hexdigest(),
              "generator": "DanielSWolf/rhubarb-lip-sync", "generator_version": version,
              "native_viseme_deformation_verified": False,
              "full_facial_performance_verified": False,
              "video_rendered": False, "lines": lines}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("EP01_REAL_RHUBARB_AUDIO_TIMED_MOUTH_SHAPES",
          len(lines), "original_WAVs", sum(x["cue_count"] for x in lines),
          "shape_events", "NOT_full_facial_lipsync")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--story", type=Path, default=Path(__file__).resolve().parent / "story.json")
    p.add_argument("--audio-dir", type=Path, required=True)
    p.add_argument("--rhubarb", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    prepare(a.story, a.audio_dir, a.rhubarb, a.output)


if __name__ == "__main__":
    main()
