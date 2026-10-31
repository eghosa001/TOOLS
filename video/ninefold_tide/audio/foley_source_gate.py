#!/usr/bin/env python3
"""E101 natural-Foley technical preflight, with rights and listening gate.

No audio is fabricated or downloaded. With no licensed WAVs on disk it fails
the *final-audio* gate by design; a successful plan check is not sound approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "pilot_soundscape_34s_plan.json"
STEMS = {"ambience", "foley", "mechanics", "water"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def wav_inspection(path: Path) -> dict:
    """Quantitative technical check. It cannot judge how convincing Foley sounds."""
    with wave.open(str(path), "rb") as wav:
        rate, channels, width, frames = wav.getframerate(), wav.getnchannels(), wav.getsampwidth(), wav.getnframes()
        if wav.getcomptype() != "NONE" or channels not in (1, 2) or width not in (2, 3):
            raise ValueError("Uncompressed 16- or 24-bit mono/stereo PCM WAV required")
        if rate != 48000 or frames < 1:
            raise ValueError("Foley source must be 48kHz, nonempty")
        raw = wav.readframes(frames)
    bps = 8 * width
    limit = 1 << (bps - 1)
    peak, clipped = 0, 0
    samples = 0
    for at in range(0, len(raw), width):
        value = int.from_bytes(raw[at:at + width], "little", signed=True)
        magnitude = abs(value)
        peak = max(peak, magnitude)
        clipped += int(magnitude >= limit - (64 if width == 2 else 16384))
        samples += 1
    if peak == 0:
        raise ValueError("Only digital silence found")
    ratio = clipped / max(samples, 1)
    if ratio >= 0.0001:
        raise ValueError("Potentially clipped / aggressively normalized audio")
    return {"duration_seconds": round(frames / rate, 4),
            "sample_rate": rate, "channels": channels, "bit_depth": bps,
            "peak_dbfs": round(20 * math.log10(peak / limit), 3),
            "clipped_ratio": round(ratio, 6), "sha256": digest(path)}


def plan_check(plan: dict) -> dict:
    if plan.get("fps") != 24 or plan.get("total_frames") != 816:
        raise ValueError("Pilot picture timeline changed")
    cues = plan.get("cues")
    if not isinstance(cues, list) or len(cues) != 12:
        raise ValueError("Expected 12 independent physical sound cues")
    ids = set()
    for cue in cues:
        if cue["id"] in ids or cue["stem"] not in STEMS:
            raise ValueError("Duplicate cue / invalid stem")
        ids.add(cue["id"])
        if not 0 <= cue["start_frame"] < cue["end_frame"] <= 816:
            raise ValueError("Cue lies outside picture")
    return {"status": "SOUND_PLAN_CHECKED_NOT_RECORDED", "planned_cues": len(cues),
            "natural_audio_approved": False}


def final_audio_check(plan: dict, workspace: Path) -> dict:
    plan_check(plan)
    results = []
    for cue in plan["cues"]:
        if not isinstance(cue.get("asset_path"), str) or not cue["asset_path"]:
            raise ValueError("Sound missing: " + cue["id"])
        rel = Path(cue["asset_path"])
        if rel.is_absolute() or ".." in rel.parts or "\\" in str(rel):
            raise ValueError("Unsafe sound file path: " + cue["id"])
        file = (workspace / rel).resolve()
        if not file.is_relative_to(workspace.resolve()) or not file.is_file():
            raise ValueError("Private sound file unavailable: " + cue["id"])
        # The cue must have artist-verified source rights; this is never set by code.
        rights = cue.get("rights") or {}
        if rights.get("basis") not in {"creator_recorded", "licensed_reusable"}:
            raise ValueError("Rights basis absent: " + cue["id"])
        if not all(isinstance(rights.get(k), str) and rights[k].strip() for k in ("creator", "proof_reference")):
            raise ValueError("Missing provenance/rights evidence: " + cue["id"])
        if not (cue.get("source_rights_verified") is True and
                cue.get("technically_verified") is True and
                cue.get("human_review_approved") is True and
                isinstance(cue.get("human_reviewer"), str) and len(cue["human_reviewer"].strip()) >= 3):
            raise ValueError("Human listening and rights review missing: " + cue["id"])
        evidence = wav_inspection(file)
        if cue.get("wav_sha256") != evidence["sha256"]:
            raise ValueError("Source WAV checksum mismatch: " + cue["id"])
        results.append({"id": cue["id"], **evidence})
    return {"status": "SOURCE_QA_PASSED_NOT_EPISODE_MIX_APPROVED",
            "inspected_cues": len(results), "source_clips": results,
            "episode_sound_mix_approved": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("plan", "sources"), default="plan")
    parser.add_argument("--plan", type=Path, default=PLAN)
    parser.add_argument("--workspace", type=Path, default=ROOT / "private_foley")
    args = parser.parse_args()
    try:
        src = json.loads(args.plan.read_text(encoding="utf8"))
        report = plan_check(src) if args.stage == "plan" else final_audio_check(src, args.workspace)
        print(json.dumps(report, indent=2))
    except (ValueError, KeyError, OSError, wave.Error) as exc:
        raise SystemExit("FOLEY_QA_BLOCKED: " + str(exc)) from exc
