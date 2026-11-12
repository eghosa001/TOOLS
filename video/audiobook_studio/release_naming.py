#!/usr/bin/env python3
"""Offline, fail-closed episode identity and publishing-name validation.

Run: python video/audiobook_studio/release_naming.py manifest.json --release-packet PRIVATE_PACKET.json
See EPISODE_NAMING_STANDARD.md. Do not store private manuscripts in this repo.
This gate does not replace media, permissions, or ownership checks.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import unicodedata

MYTHVEIL_CHANNEL_ID = "UC9gPFT64nrou4TMSxu1NZKg"


def slug(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Canonical name is required")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.replace("’", "").replace("'", "")
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    if not value:
        raise ValueError("Canonical name must contain letters or numbers")
    return value


def canonical_identity(series: str, episode: int, title: str) -> dict[str, str]:
    if type(episode) is not int or not 1 <= episode <= 999:
        raise ValueError("Episode number must be a positive integer (1–999)")
    for field, value in (("series_title", series), ("episode_title", title)):
        if not isinstance(value, str) or not value or value.strip() != value:
            raise ValueError(f"{field} must be a nonempty canonical title without outer whitespace")
        if any(x in value for x in ("\n", "\r", "|")) or re.search(r"\s{2,}", value):
            raise ValueError(f"{field} contains forbidden separators/spacing")
    number = f"{episode:02d}"
    base = f"{slug(series)}_E{number}_{slug(title)}"
    return {
        "youtube_title": f"{series} | Episode {number}: {title} | Audiobook",
        "description_headline": f"{series} — Episode {number}: {title}",
        "thumbnail_series_title": series,
        "thumbnail_episode_number": f"EP {number}",
        "thumbnail_episode_title": title,
        "drive_episode_folder": f"{slug(series)}/E{number}_{slug(title)}/",
        "master_filename": base + "_MASTER_1080p.mp4",
        "thumbnail_filename": base + "_THUMBNAIL.jpg",
        "qa_filename": base + "_QA.json",
        "narration_filename_prefix": base + "_NARRATION_KokoroMichael.",
    }


def validate_manifest(data: dict) -> dict[str, str]:
    """Reject release metadata that differs from canonical, approved story identity."""
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object for the release manifest")
    required = ("series_title", "episode_number", "episode_title", "youtube_title",
                "description_headline", "thumbnail_series_title",
                "thumbnail_episode_number", "thumbnail_episode_title",
                "drive_episode_folder", "master_filename",
                "thumbnail_filename", "narration_filename", "qa_filename",
                "channel_id", "owner_public_release_approved")
    absent = [k for k in required if k not in data]
    if absent:
        raise ValueError("Required naming fields missing: " + ", ".join(absent))
    expected = canonical_identity(data["series_title"], data["episode_number"], data["episode_title"])
    for key, value in expected.items():
        if key == "narration_filename_prefix":
            name = data["narration_filename"]
            if not isinstance(name, str) or not name.startswith(value) or name.rsplit(".", 1)[-1].lower() not in {"wav", "mp3", "m4a", "flac"}:
                raise ValueError(f"narration_filename must use canonical prefix and actual audio extension: {value}...")
        elif data[key] != value:
            raise ValueError(f"{key} naming mismatch: expected {value!r}; got {data[key]!r}")
    if data["channel_id"] != MYTHVEIL_CHANNEL_ID:
        raise ValueError("Mythveil channel identity mismatch")
    if data["owner_public_release_approved"] is not True:
        raise ValueError("Public release blocked: explicit owner approval required")
    if data.get("already_published_video_id"):
        raise ValueError("Duplicate upload blocked: use existing YouTube video ID for updates")
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate canonical Mythveil audiobook episode names before upload")
    parser.add_argument("release_manifest", type=Path)
    parser.add_argument("--release-packet", type=Path, required=True,
                        help="PRIVATE evidence packet proving all 109 rules and five release holds")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.release_manifest.read_text(encoding="utf-8"))
        expected = validate_manifest(manifest)
        packet = json.loads(args.release_packet.read_text(encoding="utf-8"))
        if packet.get("release_manifest") != manifest:
            raise ValueError("RELEASE_PACKET_MANIFEST_MISMATCH")
        from mandatory_release_gate import validate_packet
        if validate_packet(packet) != expected["youtube_title"]:
            raise ValueError("RELEASE_PACKET_TITLE_MISMATCH")
    except (ValueError, OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
        parser.exit(2, f"PUBLICATION_BLOCKED: {exc}\n")
    print("EPISODE_NAMING_AND_ALL_RULES_PASS", expected["youtube_title"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
