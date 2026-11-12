#!/usr/bin/env python3
"""Highest-priority, fail-closed voice-to-image review for Mythveil audiobooks.

Every shot must match the actual spoken excerpt, remain in time, and preserve
cast/prop continuity. An average score, story score, hashes, automated model
labels or a valid MP4 cannot override one bad shot. This checks submitted
PRIVATE review evidence, not the truth of an asserted human inspection.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import re

ASPECTS = (
    "spoken_word_fidelity",
    "image_matches_spoken_event",
    "narration_image_timing",
    "character_and_prop_continuity",
)
HEX = re.compile(r"[0-9a-f]{64}\Z")


def _require(ok, reason):
    if not ok:
        raise ValueError("VOICE_IMAGE_PRIORITY_BLOCKED: " + reason)


def _hash(value):
    return isinstance(value, str) and bool(HEX.fullmatch(value))


def _filled(value, minimum=1):
    return isinstance(value, str) and len(value.strip()) >= minimum


def _utc(value):
    _require(_filled(value), "signed review timestamp missing")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        _require(stamp.utcoffset() is not None, "review timestamp needs timezone")
        return stamp
    except (ValueError, AttributeError):
        raise ValueError("VOICE_IMAGE_PRIORITY_BLOCKED: invalid review timestamp")


def validate_voice_image_priority(report, *, source_sha256, final_mp4_sha256,
                                  checked_at, named_reviewers):
    """Validate every actual scene in its spoken order; never use an average.

    Report belongs in the signed private episode packet. A named human must
    have watched the entire final MP4 while listening to its actual soundtrack.
    Individual scene evidence is not replaceable with a one-line assertion.
    """
    _require(isinstance(report, dict), "scene-level voice/image review missing")
    _require(report.get("source_sha256") == source_sha256 and _hash(source_sha256),
             "review source differs from locked narration")
    _require(report.get("final_mp4_sha256") == final_mp4_sha256
             and _hash(final_mp4_sha256), "review not bound to final MP4")
    _require(_hash(report.get("narration_audio_sha256")),
             "narration audio SHA-256 missing")
    _require(_filled(report.get("reviewer")) and report["reviewer"] in named_reviewers,
             "a named assigned reviewer is required")
    _require(_filled(report.get("signed_review_reference"), 12),
             "signed review evidence missing")
    _require(_utc(report.get("reviewed_at")) <= _utc(checked_at),
             "review must be completed before predelivery")
    for field in ("watched_entire_final_mp4", "listened_entire_final_audio",
                  "spoken_script_checked", "images_checked_at_actual_timestamps",
                  "phone_and_headphones_checked"):
        _require(report.get(field) is True, "full review not complete: " + field)
    scenes = report.get("scenes")
    _require(isinstance(scenes, list) and scenes,
             "scene-by-scene evidence required; an overall score is insufficient")
    duration = report.get("final_mp4_duration_ms")
    _require(type(duration) is int and duration >= 1000,
             "actual final-video duration missing")
    _require(report.get("scene_count") == len(scenes),
             "scene count does not match complete review")
    joined = []
    previous_end = 0
    previous_image = None
    minimum = 10.0
    for number, item in enumerate(scenes, start=1):
        _require(isinstance(item, dict) and item.get("scene_number") == number,
                 f"scene {number}: missing, duplicate or out of order")
        begin, end = item.get("start_ms"), item.get("end_ms")
        _require(type(begin) is int and type(end) is int and 0 <= begin < end,
                 f"scene {number}: invalid actual narration timing")
        _require(abs(begin - previous_end) <= 250,
                 f"scene {number}: visual/audio timing gap or overlap")
        _require(end <= duration + 250,
                 f"scene {number}: shot extends beyond final video")
        previous_end = end
        spoken = item.get("source_excerpt")
        _require(_filled(spoken, 1), f"scene {number}: spoken excerpt missing")
        _require(item.get("source_excerpt_sha256")
                 == hashlib.sha256(spoken.encode("utf-8")).hexdigest(),
                 f"scene {number}: spoken excerpt/hash mismatch")
        joined.append(spoken)
        frame_sha = item.get("image_sha256")
        _require(_hash(frame_sha), f"scene {number}: reviewed image SHA missing")
        _require(frame_sha != previous_image,
                 f"scene {number}: repeated adjacent illustration")
        previous_image = frame_sha
        for field in ("actual_image_pixels_inspected", "spoken_audio_listened",
                      "no_early_visual_spoiler", "no_unrelated_filler"):
            _require(item.get(field) is True,
                     f"scene {number}: missing actual review for {field}")
        _require(_filled(item.get("specific_evidence"), 30),
                 f"scene {number}: insufficient event-specific evidence")
        scores = item.get("scores")
        _require(isinstance(scores, dict) and set(scores) == set(ASPECTS),
                 f"scene {number}: all four voice/image scores required")
        for aspect in ASPECTS:
            rating = scores[aspect]
            _require(type(rating) in (int, float) and 8 <= rating <= 10,
                     f"scene {number}: {aspect} below 8/10")
            minimum = min(minimum, rating)
    _require(abs(previous_end - duration) <= 500,
             "reviewed scenes do not cover full final-video duration")
    _require(hashlib.sha256("".join(joined).encode("utf-8")).hexdigest()
             == source_sha256,
             "spoken excerpts do not exactly reconstruct approved source")
    return {"status": "VOICE_IMAGE_PRIMARY_GATE_PASS",
            "scenes_checked": len(scenes), "lowest_scene_score": minimum,
            "human_review_evidence_asserted": True,
            "human_review_independently_authenticated": False}
