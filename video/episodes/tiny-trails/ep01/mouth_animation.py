#!/usr/bin/env python3
"""Strict timing bridge: Rhubarb phoneme cues to existing ORIGINAL rig jaw.

Provides better speech segmentation than loudness-only movement, but does NOT
create new mouth shapes, alter source characters or claim full 3D visemes.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from prepare_rhubarb_cues import check_cues, duration, sha256

# Approximate a single real native jaw axis, NOT nine sculpted phonetic shapes.
# Closing on "A" and "X" and distinguishing rounded/open vowels is deliberate.
JAW_OPENNESS = {"A": 0.0, "B": .12, "C": .52, "D": 1.0, "E": .38,
                "F": .28, "G": .16, "H": .65, "X": 0.0}


def verify_manifest(audio_dir, story, required=True):
    path = Path(audio_dir) / "mouth-cues.json"
    if not path.is_file():
        if required:
            raise FileNotFoundError("Required Rhubarb sound-timed mouth cues missing")
        return None
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (manifest.get("schema_version") != 1 or
        manifest.get("title") != story["title"] or
        len(manifest.get("lines", [])) != len(story["dialogue"]) or
        manifest.get("original_story_sha256") != sha256(Path(__file__).resolve().parent / "story.json")):
        raise ValueError("Rhubarb mouth cues do not match unchanged episode story")
    result = {}
    for actual, row in zip(story["dialogue"], manifest["lines"]):
        wav = Path(audio_dir) / ("line_%03d.wav" % actual["id"])
        if (row.get("id") != actual["id"] or row.get("speaker") != actual["speaker"] or
            row.get("story_start") != actual["start"] or
            row.get("story_end") != actual["end"] or
            row.get("text_sha256") != hashlib.sha256(actual["text"].encode("utf-8")).hexdigest() or
            row.get("wav_sha256") != sha256(wav)):
            raise ValueError("Original spoken line changed since lip sync extraction")
        check_cues(row["cues"], duration(wav))
        result[actual["id"]] = row
    return result


def jaw_samples_for_line(line, row, fps=24):
    """Return one bounded, smoothed control amplitude per timeline frame."""
    start = round(line["start"] * fps) + 1
    end = round(line["end"] * fps) + 1
    events = row["cues"]
    values = []
    k = 0
    smoothed = 0.0
    for f in range(start, end + 1):
        at = (f - start) / fps
        while k + 1 < len(events) and events[k]["end"] <= at:
            k += 1
        if at < events[k]["start"] or at >= events[k]["end"]:
            opening = 0.0
        else:
            opening = JAW_OPENNESS[events[k]["value"]]
        # Low-pass prevents harsh single-frame pops at 12 unique fps.
        smoothed = .52 * opening + .48 * smoothed
        values.append(smoothed)
    return start, end, values
