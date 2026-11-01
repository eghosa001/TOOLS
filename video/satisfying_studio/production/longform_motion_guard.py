"""Hard stop against padding a short ASMR take into a long-form master.

This is a picture-edit preflight, not audio parity, rights or human review approval.
Run before rendering and again with the exact final picture manifest.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path


class NoStretchError(ValueError):
    pass


def _unique_seconds(ranges):
    result = 0.0
    for group in ranges.values():
        end = -1.0
        for start, stop in sorted(group):
            result += max(0.0, stop - max(start, end))
            end = max(stop, end)
    return result


def validate(manifest, *, project_dir=None, verify_files=True, sample=False):
    """Require 1x real-time takes, real source durations and meaningful new footage.

    Every clip: source_path, source_sha256, source_duration_seconds, in_seconds,
    out_seconds, playback_speed=1, license, approved=true.
    Repeats cannot be adjacent or less than 150 seconds apart.
    At least 35% of a ten-minute timeline must be non-repeated original time;
    the stricter studio audiovisual approval rules still apply.
    """
    target = float(manifest.get("target_seconds", 600))
    shots = manifest.get("clips", [])
    if not math.isfinite(target) or target <= 0 or not shots:
        raise NoStretchError("Invalid target or no verified moving source clips")
    elapsed = 0.0
    appearances = defaultdict(list)
    unique_ranges = defaultdict(list)
    for number, clip in enumerate(shots, 1):
        label = f"shot {number}"
        for key in ("source_path", "source_sha256", "license"):
            if not clip.get(key):
                raise NoStretchError(f"{label}: missing {key}")
        if clip.get("approved") is not True:
            raise NoStretchError(f"{label}: unapproved source")
        if abs(float(clip.get("playback_speed", 1.0)) - 1.0) > 0.0001:
            raise NoStretchError(f"{label}: NO STRETCHING: playback must be exactly 1x")
        if any(clip.get(key) for key in ("reverse", "freeze", "loop", "interpolate")):
            raise NoStretchError(f"{label}: freeze/reverse/loop/interpolation forbidden")
        sha = str(clip["source_sha256"]).lower()
        if len(sha) != 64 or any(x not in "0123456789abcdef" for x in sha):
            raise NoStretchError(f"{label}: real SHA256 required")
        dur = float(clip["source_duration_seconds"])
        start = float(clip.get("in_seconds", 0))
        stop = float(clip.get("out_seconds", dur))
        if not all(map(math.isfinite, (dur, start, stop))) or dur <= 0 or start < 0 or stop <= start or stop > dur + 0.05:
            raise NoStretchError(f"{label}: fabricated duration/invalid source trim")
        if verify_files:
            if project_dir is None:
                raise NoStretchError("project_dir needed to verify source bytes")
            root = Path(project_dir).resolve()
            path = (root / clip["source_path"]).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise NoStretchError(f"{label}: source file absent/outside source directory")
            with path.open("rb") as f:
                actual_sha = hashlib.file_digest(f, "sha256").hexdigest()
            if sha != actual_sha:
                raise NoStretchError(f"{label}: source SHA256 mismatch")
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nokey=1:noprint_wrappers=1", str(path)],
                text=True, capture_output=True, check=True)
            if abs(float(probe.stdout.strip()) - dur) > 0.1:
                raise NoStretchError(f"{label}: declared duration differs from file")
        prior = appearances[sha]
        if prior and elapsed - prior[-1][1] < 150:
            raise NoStretchError(f"{label}: repeated footage too soon (<150s)")
        if len(prior) >= 3:
            raise NoStretchError(f"{label}: same source used more than three times")
        prior.append((elapsed, elapsed + stop - start))
        unique_ranges[sha].append((start, stop))
        elapsed += stop - start
    new_seconds = _unique_seconds(unique_ranges)
    if not sample and new_seconds < 0.35 * target:
        raise NoStretchError(
            f"Only {new_seconds:.1f}s distinct footage for {target:.1f}s: "
            f"obtain at least {0.35 * target:.1f}s real/new footage; do not pad")
    if not sample and abs(target - elapsed) > 0.5:
        raise NoStretchError(
            f"Picture totals {elapsed:.2f}s not {target:.2f}s; no frozen ending or slowdown")
    return {
        "picture_seconds": round(elapsed, 3),
        "distinct_source_seconds": round(new_seconds, 3),
        "unique_sources": len(unique_ranges),
        "publication_approved": False,
        "note": "Metadata preflight ONLY. Full per-scene sound parity and owner sign-off are separate."
    }


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("manifest", type=Path)
    p.add_argument("--sample", action="store_true")
    args = p.parse_args()
    data = json.loads(args.manifest.read_text())
    print(json.dumps(validate(data, project_dir=args.manifest.parent, sample=args.sample), indent=2))


if __name__ == "__main__":
    main()
