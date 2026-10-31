#!/usr/bin/env python3
"""Offline E101 pilot handoff check: timing, exact dialogue and planned Foley.

This is a planning-integrity check. It NEVER approves creative performance, sources
audio, renders frames or authorizes publication. No internet/GPU/paid credits.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHOTS = "pilot_shots.json"
VOICE_LINES = "audio/pilot_voice_lines.json"
TIMING = "audio/pilot_34s_proposed_timing.json"
CUES = "audio/pilot_soundscape_34s_plan.json"


def _load(root: Path, path: str) -> dict:
    data = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(path + ": expected JSON object")
    return data


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def check(root: Path = ROOT) -> dict:
    original = _load(root, SHOTS)
    voices = _load(root, VOICE_LINES)
    timing = _load(root, TIMING)
    cue_sheet = _load(root, CUES)

    _require(original["fps"] == timing["fps"] == cue_sheet["fps"] == 24, "24fps mismatch")
    _require(original["total_frames"] == timing["original_duration_frames"] == 720, "historical pilot length changed")
    _require(timing["total_frames"] == cue_sheet["total_frames"] == 816, "34-second frame count mismatch")
    _require(timing["total_seconds"] == 34, "34-second duration mismatch")
    _require(timing["approval_status"] == "PREVIEW_TIMING_ONLY_NOT_ANIMATIC_LOCK", "timing incorrectly promoted")
    _require(cue_sheet["cue_status"] == "PLANNED_NOT_RECORDED", "unverified cues promoted")
    _require(cue_sheet["mix_state"] == "NOT_MIXED_OR_APPROVED", "unverified mix promoted")
    _require(cue_sheet["rights_state"] == "ALL_SFX_UNSOURCED", "unverified rights promoted")
    _require(cue_sheet["source_locked_for_existing_audio"].endswith(
        "/1f3ACxh4rUrafPbcZV8KJSzTbM4x5nIwVuGtVfd1xRd8/edit"),
        "original v2 script reference changed: recorded WAVs must remain tied to v2")

    original_shots = original["shots"]
    retimed = timing["shots"]
    _require(len(original_shots) == len(retimed) == 12, "expected exactly 12 shots")
    _require({s["id"] for s in original_shots} == {s["shot_id"] for s in retimed}, "shot IDs mismatch")
    expected_extensions = {"ep101_003": 36, "ep101_004": 24, "ep101_007": 36}
    boundaries: dict[str, tuple[int, int]] = {}
    cursor = 0
    for old, new in zip(original_shots, retimed):
        sid = old["id"]
        _require(sid == new["shot_id"], "shot order changed: " + sid)
        _require(old["shot_status"] == "planned" and old["editor_approved"] is False, "unapproved shot promoted: " + sid)
        _require(new["added_frames"] == expected_extensions.get(sid, 0), "unreviewed frame extension: " + sid)
        _require(new["duration_frames"] == old["end_frame"] - old["start_frame"] + new["added_frames"],
                 "retimed duration inconsistent: " + sid)
        _require(new["start_frame"] == cursor, "gap or overlap before " + sid)
        _require(new["end_frame"] == cursor + new["duration_frames"], "end-frame mismatch: " + sid)
        boundaries[sid] = (new["start_frame"], new["end_frame"])
        cursor = new["end_frame"]
    _require(cursor == 816, "timeline must end exactly at frame 816")

    all_voice_ids = {v["line_id"] for v in voices["dialogue_lines"]}
    _require(len(all_voice_ids) == len(voices["dialogue_lines"]), "duplicate voice ID")
    timing_voice_ids = {v["line_id"] for v in timing["selected_audio_fit"]}
    _require(all_voice_ids == timing_voice_ids, "timeline/voice lineup mismatch")
    by_shot = {s["id"]: s for s in original_shots}
    for line in voices["dialogue_lines"]:
        expected = line["speaker"].title() + ": " + line["canonical_text"]
        _require(by_shot[line["shot_id"]]["dialogue"] == expected,
                 "voice script drift in " + line["line_id"])
        _require(line["approved"] is False, "voice line incorrectly human-approved: " + line["line_id"])
    for audio in timing["selected_audio_fit"]:
        start, end = boundaries[audio["line_id"]]
        begin = float(audio["audio_start_seconds"])
        finish = begin + float(audio["duration_seconds"])
        _require(begin >= start / 24 - .005 and finish <= end / 24 + .025,
                 "voice clip overruns its planned shot: " + audio["line_id"])
        _require(bool(SHA256.fullmatch(audio["source_wav_sha256"])), "invalid WAV fingerprint")

    cues = cue_sheet["cues"]
    _require(len(cues) == 12 and len({c["id"] for c in cues}) == 12, "expect 12 distinct SFX cue plans")
    _require({c["shot_id"] for c in cues} == set(boundaries), "cues must cover all 12 shots")
    for cue in cues:
        start, end = boundaries[cue["shot_id"]]
        _require(start <= cue["start_frame"] < cue["end_frame"] <= end,
                 "sound cue violates picture timeline: " + cue["id"])
        _require(cue["stem"] in {"ambience", "foley", "mechanics", "water"},
                 "unknown sound stem: " + cue["id"])
        _require(isinstance(cue["description"], str) and len(cue["description"]) >= 40,
                 "missing actionable sound direction: " + cue["id"])
        _require(cue["asset_path"] is None and cue["source_rights_verified"] is False
                 and cue["technically_verified"] is False and cue["human_review_approved"] is False,
                 "unrecorded / unlicensed effect incorrectly marked approved: " + cue["id"])
    return {
        "status": "PLAN_INTEGRITY_PASS_NOT_PRODUCTION_APPROVAL",
        "frames": cursor,
        "duration_seconds": 34,
        "shots": len(retimed),
        "dialogue_clips": len(timing_voice_ids),
        "unrecorded_sound_cues": len(cues),
        "episode_ready": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(check(), indent=2))
    except (ValueError, KeyError, TypeError) as exc:
        raise SystemExit("E101_PILOT_PLAN_FAIL: " + str(exc)) from exc
