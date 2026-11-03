#!/usr/bin/env python3
"""Fail-closed motion-footage gate for Facts Uncovered historical documentaries.

An encoded MP4 is NOT proof of moving footage: still pictures rendered with
zoompan remain STILL_PHOTO. This gate checks the EDITOR'S PER-SHOT SOURCE LEDGER,
not merely the final container codec. Human footage review remains mandatory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

MOTION_KINDS = frozenset({
    "ARCHIVAL_EVENT_FILM", "PERIOD_CONTEXT_FILM",
    "LICENSED_REENACTMENT_FILM", "ORIGINAL_RECONSTRUCTION_FILM",
})
STILL_KINDS = frozenset({
    "STILL_PHOTO", "ARCHIVAL_DOCUMENT", "MAP", "DIAGRAM", "AI_STILL",
})


def valid_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    u = urlparse(value)
    return u.scheme == "https" and bool(u.netloc)


def validate(manifest: dict) -> dict:
    errors: list[str] = []
    shots = manifest.get("shots", [])
    if not isinstance(shots, list) or not shots:
        return {"status": "FAIL", "errors": ["Missing nonempty shots list"],
                "motion_share": 0, "motion_seconds": 0, "total_seconds": 0}
    threshold = manifest.get("min_motion_share", 0.65)
    if isinstance(threshold, bool) or not isinstance(threshold, (float, int)) or not 0 < threshold <= 1:
        errors.append("min_motion_share must be greater than zero and at most one")
        threshold = 0.65

    cursor = 0.0
    motion = 0.0
    seen = set()
    for index, shot in enumerate(shots, 1):
        if not isinstance(shot, dict):
            errors.append(f"Shot {index}: invalid shot record")
            continue
        ident = shot.get("id", f"shot-{index}")
        if ident in seen:
            errors.append(f"Duplicate shot id: {ident}")
        seen.add(ident)
        try:
            start, end = float(shot["start_seconds"]), float(shot["end_seconds"])
        except (ValueError, TypeError, KeyError):
            errors.append(f"{ident}: invalid timecodes")
            continue
        if not (0 <= start < end):
            errors.append(f"{ident}: invalid time interval")
            continue
        if abs(start - cursor) > 0.06:
            errors.append(f"{ident}: missing or overlapping coverage at {cursor:.2f}s")
        cursor = end
        kind = shot.get("visual_kind")
        if kind not in (MOTION_KINDS | STILL_KINDS):
            errors.append(f"{ident}: unknown visual_kind {kind!r}")
            continue
        if kind in MOTION_KINDS:
            if shot.get("motion_verified") is not True:
                errors.append(f"{ident}: moving frames not independently verified")
            if shot.get("commercial_rights_verified") is not True:
                errors.append(f"{ident}: video commercial/derivative rights not verified")
            if kind == "ORIGINAL_RECONSTRUCTION_FILM":
                if not shot.get("production_ref"):
                    errors.append(f"{ident}: original reconstruction needs production provenance")
            elif not valid_url(shot.get("source_page_url")):
                errors.append(f"{ident}: footage needs an exact HTTPS source page")
            if kind in {"PERIOD_CONTEXT_FILM", "LICENSED_REENACTMENT_FILM",
                        "ORIGINAL_RECONSTRUCTION_FILM"} and not shot.get("on_screen_disclosure"):
                errors.append(f"{ident}: contextual/recreated footage must be labelled")
            motion += end - start
    total = cursor
    expected = manifest.get("duration_seconds")
    if expected is not None:
        try:
            if abs(float(expected) - total) > 0.06:
                errors.append("Shot coverage does not match planned video duration")
        except (ValueError, TypeError):
            errors.append("Invalid planned video duration")
    share = motion / total if total else 0
    if share + 1e-9 < threshold:
        errors.append(
            f"Actual moving-footage coverage {share:.1%} below {threshold:.0%} minimum; "
            "Ken Burns photos, animated maps and slideshow clips do not count")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "motion_share": round(share, 4),
            "motion_seconds": round(motion, 2), "total_seconds": round(total, 2)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = validate(json.loads(args.manifest.read_text(encoding="utf-8")))
    result_json = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(result_json, encoding="utf-8")
    print(result_json, end="")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
