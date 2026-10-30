#!/usr/bin/env python3
"""Fail-closed director review record for FIRST FINISHED-LOOK Ninefold Tide proof.

This tool checks review provenance and the actual media fingerprint, not artistic
quality itself. A real director must watch and listen to the file.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pipeline

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "first_proof_review_template.json"


def assess(review: dict, master: Path | None) -> list[str]:
    errors: list[str] = []
    template = pipeline.read_json(TEMPLATE)
    if review.get("schema_version") != template.get("schema_version"):
        errors.append("Review schema version differs from template")
    director = review.get("director") or {}
    if director.get("final_approved") is not True:
        errors.append("Director has not personally approved the first proof")
    if not director.get("reviewer") or not director.get("approval_date"):
        errors.append("Named reviewer and approval date required")
    if review.get("status") != "APPROVED":
        errors.append("Review status is not APPROVED")
    for name in template["criteria"]:
        evidence = (review.get("criteria") or {}).get(name)
        if not isinstance(evidence, dict) or evidence.get("passed") is not True:
            errors.append(f"Not reviewed/passed: {name}")
        elif not evidence.get("evidence") or not evidence.get("notes"):
            errors.append(f"Missing human evidence and notes for: {name}")
    meta = review.get("master") or {}
    if not meta.get("inspected_on_date"):
        errors.append("Date of actual complete audiovisual review missing")
    if master is None or not master.is_file():
        errors.append("Missing real finished-look MP4: cannot certify a nonexistent video")
    else:
        if meta.get("sha256") != pipeline.checksum(master):
            errors.append("Master SHA-256 differs from the actual file reviewed")
        try:
            pipeline.verify(master)
        except (OSError, ValueError, KeyError) as exc:
            errors.append(f"Full-resolution media verification failed: {exc}")
    # This report deliberately does not claim that metadata alone establishes
    # premium quality or rights; the reviewers must actually inspect media.
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=ROOT / "workspace" / "07_review" / "ep101_first_proof.json")
    parser.add_argument("--master", type=Path)
    opts = parser.parse_args()
    try:
        record = pipeline.read_json(opts.review)
        errors = assess(record, opts.master)
    except (ValueError, OSError) as exc:
        errors = [str(exc)]
    print(json.dumps({
        "status": "REVIEW_RECORD_COMPLETE" if not errors else "BLOCKED",
        "errors": errors,
        "notice": "Artistic quality still depends on honest full picture-and-sound human review."
    }, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
