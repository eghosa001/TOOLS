#!/usr/bin/env python3
"""Offline source-to-still QA for private illustrated audiobook episodes.

Checks the exact narration-to-image manifest, hashes and editorial attestations.
It CANNOT determine image semantics from pixels; an editor must inspect images.
Private text, pictures and reports are never committed to this public repo.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

BEAT_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{1,63}$")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return digest(Path(path).read_bytes())


def normalized(text: str) -> str:
    # Whitespace-only normalization; punctuation, spelling and every word remain locked.
    return " ".join(text.lstrip("\ufeff").split())


def check_episode(source_path: Path, beats_path: Path, *, require_images=True,
                  require_pixel_review=True) -> dict:
    source_path, beats_path = Path(source_path), Path(beats_path)
    source = source_path.read_text(encoding="utf-8-sig")
    data = json.loads(beats_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise ValueError("Private beat manifest schema 1 required")
    if not data.get("story_id") or not data.get("episode_id"):
        raise ValueError("Story ID and episode ID required")
    beats = data.get("beats")
    if not isinstance(beats, list) or not beats:
        raise ValueError("An ordered nonempty beat list is required")
    if normalized(" ".join(x.get("text", "") for x in beats)) != normalized(source):
        raise ValueError("Narrated beats DO NOT reproduce the approved script verbatim and in order")
    if data.get("source_sha256") != file_digest(source_path):
        raise ValueError("Private script SHA-256 does not match beat manifest")
    narrator = data.get("narrator", {})
    if narrator.get("engine") != "kokoro" or narrator.get("voice") != "am_michael":
        raise ValueError("Audiobook default is approved male Kokoro Michael")
    speed = narrator.get("speed", 0)
    if not isinstance(speed, (int, float)) or not (0.85 <= speed <= 1.35):
        raise ValueError("Invalid synthesis speed; 1.25 is the working audition default")
    if float(narrator.get("post_atempo", 1.0)) != 1.0:
        raise ValueError("Do not multiply synthesis speed by a second speed-up stage")
    ids = set()
    frame_fingerprints = set()
    total_words = 0
    for index, beat in enumerate(beats):
        bid = beat.get("id")
        if not isinstance(bid, str) or not BEAT_ID.fullmatch(bid) or bid in ids:
            raise ValueError(f"Beat {index}: missing/duplicate/unsafe ID")
        ids.add(bid)
        t = beat.get("text", "")
        if not isinstance(t, str) or not normalized(t):
            raise ValueError(f"Beat {bid}: no spoken excerpt")
        total_words += len(t.split())
        vis = beat.get("visual", {})
        if not isinstance(vis, dict):
            raise ValueError(f"Beat {bid}: missing visual contract")
        if not isinstance(vis.get("must_show"), list) or not vis["must_show"]:
            raise ValueError(f"Beat {bid}: list the observed action/object/place")
        if not isinstance(vis.get("must_not_show"), list) or not vis["must_not_show"]:
            raise ValueError(f"Beat {bid}: define disallowed contradictions")
        if not isinstance(vis.get("setting"), str) or not vis["setting"].strip():
            raise ValueError(f"Beat {bid}: missing geographical setting")
        if vis.get("period") not in ("present", "memory", "other"):
            raise ValueError(f"Beat {bid}: distinguish present from flashback")
        if not isinstance(vis.get("character_references"), list):
            raise ValueError(f"Beat {bid}: supply character-reference IDs or []")
        # Story/lore-specific semantics belong in this beat's PRIVATE visual
        # must_show/must_not_show and reviewer judgement, never hardcoded here.
        # A universal validator cannot infer the correct state of any named
        # artifact, realm, person or period from story prose automatically.
        # Prevent repeated filler frames hidden behind different scene descriptions.
        if require_images:
            image = beat.get("image")
            if not image or Path(image).is_absolute() or ".." in Path(image).parts:
                raise ValueError(f"Beat {bid}: use an existing private relative image path")
            image_path = (beats_path.parent / image).resolve()
            if not image_path.is_file() or image_path.stat().st_size < 10_000:
                raise ValueError(f"Beat {bid}: original still image is missing")
            fingerprint = file_digest(image_path)
            if fingerprint != beat.get("image_sha256"):
                raise ValueError(f"Beat {bid}: displayed image does not match reviewed SHA-256")
            if fingerprint in frame_fingerprints:
                raise ValueError(f"Beat {bid}: repeated image where distinct narrated beat needs artwork")
            frame_fingerprints.add(fingerprint)
            if image_path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                raise ValueError(f"Beat {bid}: artwork must be a still image")
        if require_pixel_review:
            review = beat.get("pixel_review", {})
            required = ("inspected_actual_image", "exact_speech_match",
                        "period_and_world_state_correct", "character_and_props_consistent",
                        "rights_recorded", "no_bad_text_or_duplicates")
            if not all(review.get(k) is True for k in required):
                raise ValueError(f"Beat {bid}: human/editor pixel-source review is incomplete")
            if not str(review.get("reviewer", "")).strip():
                raise ValueError(f"Beat {bid}: name the reviewer, don't self-certify automatically")
            if review.get("image_sha256") != beat.get("image_sha256"):
                raise ValueError(f"Beat {bid}: review is stale after image change")
    return {
        "status": "SOURCE_AND_REVIEW_LEDGER_PASS",
        "story_id": data["story_id"],
        "episode_id": data["episode_id"],
        "source_sha256": data["source_sha256"],
        "total_beats": len(beats),
        "word_count_including_headings": total_words,
        "review_status": "PIXEL_EDITOR_ATTESTED" if require_pixel_review else "NOT_APPROVED",
        "note": "This test cannot substitute for watching/listening to the final MP4",
    }
