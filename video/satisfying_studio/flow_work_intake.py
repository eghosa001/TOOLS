#!/usr/bin/env python3
"""Conservative intake check for Work/Flow clips and existing ASMR sources.

NOT a release gate or permission to publish. Studio quality_gate.py remains
mandatory against the exact fully reviewed master.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

CHANNEL_ID = "UC9PFLzcnIYHVGy_svH86jyw"
CHANNEL_TITLE = "Surreal ASMR"
SOURCE_TYPES = {"FLOW_GENERATED", "OWNED_ORIGINAL", "LICENSED_STOCK", "REFERENCE_ONLY"}
HEX = re.compile(r"^[0-9a-f]{64}$")
ALIAS = re.compile(r"^account_[1-9][0-9]*$")
MEDIA_EXT = {".mp4", ".mov", ".mkv", ".webm"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe_media(path: Path) -> dict:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,avg_frame_rate,codec_name",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True, timeout=30,
    )
    data = json.loads(p.stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not video:
        raise ValueError("Video stream missing")
    duration = float(data.get("format", {}).get("duration", 0))
    if duration <= 0:
        raise ValueError("Media duration missing or invalid")
    if int(video.get("width", 0)) < 1 or int(video.get("height", 0)) < 1:
        raise ValueError("Invalid dimensions")
    return {
        "duration_s": round(duration, 3), "width": int(video["width"]),
        "height": int(video["height"]), "fps": video.get("avg_frame_rate"),
        "video_codec": video.get("codec_name"), "audio_present": bool(audio),
    }


def audit_manifest(manifest_path: Path) -> dict:
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("Expected schema_version 1")
    channel = manifest.get("channel", {})
    if channel != {"title": CHANNEL_TITLE, "id": CHANNEL_ID}:
        raise ValueError("Channel must be immutable canonical Surreal ASMR identity")
    clips = manifest.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError("At least one clip is required")
    if len(clips) > 100:
        raise ValueError("Batch exceeds maximum of 100 clips")
    results = []
    seen_hashes = set()
    for i, item in enumerate(clips):
        label = f"clip[{i}]"
        try:
            source_type = item["source_type"]
            if source_type not in SOURCE_TYPES:
                raise ValueError("Unknown source_type")
            if source_type == "FLOW_GENERATED" and not ALIAS.fullmatch(item.get("account_alias", "")):
                raise ValueError("Flow generation requires account_alias account_1, account_2, etc")
            if any(k in item for k in ("email", "password", "access_token", "refresh_token", "cookie")):
                raise ValueError("Credentials and account emails prohibited in intake manifest")
            rel = Path(item["path"])
            if rel.is_absolute() or ".." in rel.parts or rel.suffix.lower() not in MEDIA_EXT:
                raise ValueError("Only relative media paths without traversal are permitted")
            file = (manifest_path.parent / rel).resolve()
            if not file.is_relative_to(manifest_path.parent):
                raise ValueError("Media escapes manifest directory")
            if not file.is_file() or file.stat().st_size == 0:
                raise ValueError("Media file missing/empty")
            expected_hash = item.get("sha256", "")
            if not isinstance(expected_hash, str) or not HEX.fullmatch(expected_hash):
                raise ValueError("Valid SHA256 required")
            actual_hash = sha256_file(file)
            if expected_hash != actual_hash:
                raise ValueError("Source SHA256 mismatch")
            if actual_hash in seen_hashes:
                raise ValueError("Duplicate source media in this batch")
            seen_hashes.add(actual_hash)
            media = probe_media(file)
            rights = item.get("rights", {})
            rights_status = rights.get("status")
            rights_evidence = rights.get("evidence_url", "")
            if rights_status not in ("VERIFIED", "PENDING", "REFERENCE_ONLY"):
                raise ValueError("Rights status must be VERIFIED, PENDING, or REFERENCE_ONLY")
            if rights_status == "VERIFIED" and not (
                isinstance(rights_evidence, str) and rights_evidence.startswith("https://")
            ):
                raise ValueError("Verified rights require a source/terms evidence HTTPS URL")
            if source_type == "REFERENCE_ONLY" and rights_status == "VERIFIED":
                raise ValueError("REFERENCE_ONLY cannot have verified commercial reuse")
            status = "EDITORIAL_REVIEW_REQUIRED" if rights_status == "VERIFIED" else "HOLD_RIGHTS"
            results.append({
                "path": str(rel), "sha256": actual_hash, "source_type": source_type,
                "rights_status": rights_status, "status": status,
                "media": media, "audio_repair_review_needed": not media["audio_present"],
            })
        except (KeyError, ValueError, OSError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            results.append({
                "path": item.get("path", "(missing)") if isinstance(item, dict) else "(invalid)",
                "status": "REJECTED_INTAKE", "reason": str(e), "label": label,
            })
    return {
        "schema_version": 1, "channel": channel,
        "counts": {
            "total": len(results),
            "rejected": sum(r["status"] == "REJECTED_INTAKE" for r in results),
            "hold_rights": sum(r["status"] == "HOLD_RIGHTS" for r in results),
            "editorial_review": sum(r["status"] == "EDITORIAL_REVIEW_REQUIRED" for r in results),
        },
        "results": results,
        "release_authorization": (
            "NONE. Run existing quality_gate.py release on exact master; "
            "obtain owner approval before upload."
        ),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    result = audit_manifest(args.manifest)
    payload = json.dumps(result, indent=2) + "\n"
    print(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    if result["counts"]["rejected"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
