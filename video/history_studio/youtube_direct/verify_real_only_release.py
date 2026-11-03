#!/usr/bin/env python3
"""Pre-upload release gate: Facts Uncovered may only upload rights-cleared real visuals.

Both independent editorial manifests must describe the same complete, timed
picture track. The reviewed final MP4 hash must match exactly. This validates
the recorded evidence; it cannot independently prove copyright ownership or
detect undisclosed AI within a falsely annotated source. Human review required.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HISTORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE = load_module("real_source_policy", HISTORY_ROOT / "source_first_policy.py")
MOTION = load_module("real_motion_gate", HISTORY_ROOT / "video_motion_gate.py")


def sha256(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def verify(video: Path, source_manifest: dict, motion_manifest: dict,
           thumbnail: Path | None = None) -> dict:
    errors: list[str] = []
    if not video.is_file() or video.suffix.lower() != ".mp4":
        return {"status": "FAIL", "errors": ["Missing actual MP4 master"]}
    digest = sha256(video)
    try:
        source_result = SOURCE.validate(source_manifest, phase="plan")
        motion_result = MOTION.validate(motion_manifest)
    except (ValueError, TypeError, KeyError) as exc:
        return {"status": "FAIL", "errors": [f"Invalid source evidence: {exc}"]}
    errors += [f"Source: {error}" for error in source_result["errors"]]
    errors += [f"Motion: {error}" for error in motion_result["errors"]]

    src_shots, mov_shots = source_manifest["shots"], motion_manifest["shots"]
    if len(src_shots) != len(mov_shots):
        errors.append("The source and motion shot ledgers have differing shot counts")
    else:
        for i, (left, right) in enumerate(zip(src_shots, mov_shots), 1):
            try:
                same = (left["id"] == right["id"] and
                        abs(float(left["start_seconds"]) - float(right["start_seconds"])) < .06 and
                        abs(float(left["end_seconds"]) - float(right["end_seconds"])) < .06)
            except (TypeError, ValueError, KeyError):
                same = False
            if not same:
                errors.append(f"Shot {i}: source/motion evidence mismatch")
    for name, manifest in (("source", source_manifest), ("motion", motion_manifest)):
        if manifest.get("master_sha256", "").lower() != digest:
            errors.append(f"{name}: reviewed master SHA-256 does not match supplied MP4")

    review = source_manifest.get("final_editorial_review", {})
    if not isinstance(review, dict) or (
        review.get("approved_for_facts_uncovered") is not True
        or not str(review.get("reviewer", "")).strip()
        or review.get("reviewed_mp4_sha256", "").lower() != digest
        or not str(review.get("visual_and_audio_review_notes", "")).strip()
    ):
        errors.append("Missing individual human editorial approval tied to final MP4 hash")

    if thumbnail:
        info = source_manifest.get("thumbnail", {})
        if not isinstance(info, dict) or not thumbnail.is_file():
            errors.append("Missing verified real-photo thumbnail metadata or file")
        else:
            if info.get("real_photo_verified") is not True:
                errors.append("Thumbnail must be a verified real photo or scan")
            if info.get("commercial_rights_verified") is not True:
                errors.append("Thumbnail commercial-use rights not verified")
            if info.get("synthetic_media") is True:
                errors.append("Synthetic or AI-generated thumbnail forbidden")
            if info.get("sha256", "").lower() != sha256(thumbnail):
                errors.append("Thumbnail SHA-256 does not match approved source")
            if not MOTION.valid_url(info.get("source_page_url")) or not MOTION.valid_url(info.get("license_evidence_url")):
                errors.append("Thumbnail requires actual source and licence evidence URLs")
    return {"status": "FAIL" if errors else "PASS", "errors": errors,
            "master_sha256": digest, "actual_motion_share": motion_result["motion_share"],
            "total_shots": len(src_shots)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--motion-manifest", required=True, type=Path)
    parser.add_argument("--thumbnail", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    for file in (args.source_manifest, args.motion_manifest):
        if not file.is_file():
            raise SystemExit(f"Missing mandatory rights-and-origin evidence: {file}")
    outcome = verify(
        args.video,
        json.loads(args.source_manifest.read_text(encoding="utf-8")),
        json.loads(args.motion_manifest.read_text(encoding="utf-8")),
        args.thumbnail,
    )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome, indent=2))
    return 0 if outcome["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
