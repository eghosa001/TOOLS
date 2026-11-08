#!/usr/bin/env python3
"""Fail-closed FULL-COLOR, story-linked multi-panel audiobook production gate.

New productions must have colorized original art BEFORE assembly. Reusing one
page's independently cropped panels is supported; repeated source pages do not
imply repeated identical shots. Visual *meaning* cannot be inferred by this
technical gate: actual source-to-pixel inspection remains mandatory.
No private story material is stored in the repository.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from PIL import Image, UnidentifiedImageError

ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$")
HASH = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized(text: str) -> str:
    return " ".join(text.lstrip("\ufeff").split())


def full_color_check(image: Path) -> dict:
    """Examine real pixels, not an image prompt or a claimed 'colored' flag.

    A faint blue highlight on otherwise gray artwork is insufficient.
    This is a cheap automatic gate, NOT visual/story quality certification.
    """
    image = Path(image)
    try:
        with Image.open(image) as source:
            im = source.convert("RGB")
            w, h = im.size
            if w < 896 or h < 504:
                raise ValueError("FULL_COLOR_REQUIRED: image below production resolution")
            im.thumbnail((192, 108), Image.Resampling.BILINEAR)
            pixels = list(im.getdata())
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError("FULL_COLOR_REQUIRED: invalid artwork file") from exc
    meaningful = 0
    sat_sum = 0.0
    considered = 0
    for red, green, blue in pixels:
        highest, lowest = max(red, green, blue), min(red, green, blue)
        if highest <= 35:
            continue  # black ink is permitted in otherwise colorful artwork
        saturation = (highest - lowest) / highest
        considered += 1
        sat_sum += saturation
        if highest - lowest >= 14 and saturation >= 0.11:
            meaningful += 1
    fraction = meaningful / max(1, considered)
    avg_saturation = sat_sum / max(1, considered)
    if fraction < 0.08 or avg_saturation < 0.055:
        raise ValueError(
            f"FULL_COLOR_REQUIRED: grayscale or barely tinted artwork "
            f"(colored_fraction={fraction:.3f}, avg_saturation={avg_saturation:.3f})"
        )
    return {
        "width": w,
        "height": h,
        "colored_fraction": round(fraction, 4),
        "mean_saturation": round(avg_saturation, 4),
        "technical_full_color": True,
        "semantic_scene_accuracy_verified": False,
    }


def validate_color_panel_timeline(
    entries: list[dict], *, timeline_path: Path, source_text: Path | None,
    narration_seconds: float,
) -> dict:
    """Check strict art/source timing without imposing fake image-count quotas.

    Each entry needs an EXACT piece of the approved narration source, its
    digest, a real colored panel crop, the crop digest, and sheet/panel IDs.
    The full ordered excerpts must reproduce the complete approved source.
    Multiple non-adjacent beats may legitimately reuse a panel.
    """
    if not isinstance(entries, list) or not entries or source_text is None:
        raise ValueError("COLOR_PANEL_SOURCE_REQUIRED: timeline and approved source text")
    timeline_path = Path(timeline_path).resolve()
    source = Path(source_text).resolve(strict=True).read_text(encoding="utf-8-sig")
    if not normalized(source):
        raise ValueError("COLOR_PANEL_SOURCE_REQUIRED: source is empty")
    identities = set()
    source_parts = []
    pages = set()
    panels = set()
    scanned = {}
    previous_hash = None
    total = 0.0
    story_episode = None
    for index, beat in enumerate(entries):
        if not isinstance(beat, dict):
            raise ValueError(f"COLOR_PANEL_METADATA_REQUIRED: shot {index} is not an object")
        for key in ("story_id", "episode_id", "page_id", "panel_id"):
            if not ID.fullmatch(str(beat.get(key, ""))):
                raise ValueError(f"COLOR_PANEL_METADATA_REQUIRED: shot {index} missing {key}")
        identity = (beat["story_id"], beat["episode_id"])
        if story_episode is None:
            story_episode = identity
        elif story_episode != identity:
            raise ValueError("STORY_MIXING_FORBIDDEN: all shots must belong to one episode")
        passage = beat.get("source_excerpt")
        if not isinstance(passage, str) or not normalized(passage):
            raise ValueError(f"COLOR_PANEL_SOURCE_REQUIRED: missing spoken text in shot {index}")
        source_parts.append(passage)
        if beat.get("source_sha256") != hashlib.sha256(passage.encode("utf-8")).hexdigest():
            raise ValueError(f"COLOR_PANEL_SOURCE_HASH_FAILED: shot {index}")
        seconds = beat.get("seconds")
        if isinstance(seconds, bool) or not isinstance(seconds, (float, int)) or not 0.04 <= seconds <= 180:
            raise ValueError(f"COLOR_PANEL_DURATION_FAILED: shot {index}")
        total += seconds
        raw = beat.get("image")
        if not isinstance(raw, str) or not raw or ".." in Path(raw).parts:
            raise ValueError(f"COLOR_PANEL_PATH_FAILED: shot {index}")
        image = Path(raw)
        if not image.is_absolute():
            image = timeline_path.parent / image
        image = image.resolve(strict=True)
        if image.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            raise ValueError(f"FULL_COLOR_REQUIRED: not an illustration image in shot {index}")
        actual_hash = sha256(image)
        if not HASH.fullmatch(str(beat.get("image_sha256", ""))) or beat["image_sha256"] != actual_hash:
            raise ValueError(f"COLOR_PANEL_IMAGE_HASH_FAILED: shot {index}")
        if actual_hash == previous_hash:
            raise ValueError(f"DUPLICATE_ADJACENT_PANEL: shot {index}; merge the hold instead")
        previous_hash = actual_hash
        if actual_hash not in scanned:
            scanned[actual_hash] = full_color_check(image)
        pages.add(beat["page_id"])
        panels.add((beat["page_id"], beat["panel_id"], actual_hash))
        identities.add((identity, beat["page_id"], beat["panel_id"]))
    if normalized(" ".join(source_parts)) != normalized(source):
        raise ValueError("COLOR_PANEL_SOURCE_COVERAGE_FAILED: missing/duplicated/reordered words")
    if abs(total - narration_seconds) > 0.30:
        raise ValueError("COLOR_PANEL_AUDIO_SYNC_FAILED: timeline/audio duration mismatch")
    return {
        "status": "FULL_COLOR_PANEL_TIMELINE_PASS",
        "story_id": story_episode[0],
        "episode_id": story_episode[1],
        "shots": len(entries),
        "unique_source_pages": len(pages),
        "unique_panel_crops": len(panels),
        "distinct_images_checked": len(scanned),
        "duration_seconds": round(total, 4),
        "technical_color_gate_passed": True,
        "source_hash_and_coverage_passed": True,
        "semantics_verified_by_automation": False,
        "human_full_video_review_completed": False,
    }
