#!/usr/bin/env python3
"""Validate the source-paced 3D history film plans.

This is a STRUCTURAL storyboard gate, not an automatic artistic approval.
Machine checks cannot establish that the narration matches the footage.
Release requires independent per-shot human visual checks.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from story_quality_gate import check_story

REQUIRED = {
    "id", "start_seconds", "end_seconds", "spoken", "caption",
    "scene_key", "camera", "required_visible_action", "must_show",
    "foley_cue", "proof_required", "human_visual_approved",
}
PROOF_FRAMES = {"first_frame", "midpoint", "end_frame"}

def verify(path: Path, strict_release: bool = False,
           proofs: Path | None = None, clips: Path | None = None) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    story_report = check_story(data, require_editor_approval=strict_release, filename=path.name)
    assert data["type"] == "historical_3d_short_storyboard", path
    assert data["seconds"] == 64
    assert (data["width"], data["height"], data["fps"]) == (1080, 1920, 30)
    shots = data["shots"]
    assert len(shots) == 12, f"{path}: expected 12 independently directed shots"
    assert data["narration"]["engine"] == "Qwen3-TTS"
    assert data["narration"]["one_independent_take_per_shot"] is True
    assert data["narration"]["never_compress_six_chapters_to_twenty_five_seconds"] is True
    assert len(data["history_sources"]) >= 2
    assert data.get("publication_approved") is False or strict_release, (
        "Publication must not be auto-approved by a storyboard-only change"
    )
    cursor = 0
    names, scenes, cameras, spoken_words = set(), set(), set(), 0
    for i, shot in enumerate(shots, 1):
        missing = REQUIRED.difference(shot)
        assert not missing, f"{path}: shot {i} lacks {sorted(missing)}"
        name = shot["id"]
        assert name not in names, f"duplicate shot id: {name}"
        assert shot["scene_key"] not in scenes, f"duplicate scene key: {shot['scene_key']}"
        names.add(name); scenes.add(shot["scene_key"]); cameras.add(shot["camera"])
        assert shot["start_seconds"] == cursor, (name, "gap or overlap", cursor)
        duration = shot["end_seconds"] - cursor
        assert duration in (5, 6), (name, "shot duration", duration)
        cursor = shot["end_seconds"]
        words = len(re.findall(r"\b[\w’'-]+\b", shot["spoken"]))
        spoken_words += words
        assert 8 <= words <= 22, (name, "narration beats must be individually paced", words)
        assert len(shot["must_show"]) >= 3, (name, "specific set props required")
        assert len(shot["required_visible_action"]) >= 68, (name, "describe actual visible event")
        assert shot["caption"] and shot["foley_cue"]
        assert set(shot["proof_required"]) == PROOF_FRAMES
        assert isinstance(shot["human_visual_approved"], bool)
        if clips is not None:
            clip = clips / f"{name}.mp4"
            assert clip.is_file(), f"Missing independently rendered clip {clip}"
            probe = subprocess.check_output([
                "ffprobe","-v","error","-show_entries","format=duration",
                "-of","default=noprint_wrappers=1:nokey=1",str(clip)], text=True)
            actual = float(probe.strip())
            assert abs(actual - duration) <= 0.2, (name, "clip not shot-timed", actual, duration)
        if proofs is not None:
            for stage in ("first_frame", "midpoint", "end_frame"):
                image = proofs / name / (stage + ".jpg")
                assert image.is_file() and image.stat().st_size > 1000, (
                    "No evidence frame; requires art review", str(image))
        if strict_release:
            assert shot["human_visual_approved"], f"{name}: explicit human approval missing"
    assert cursor == data["seconds"], f"Missing timeline at {cursor}s"
    assert 120 <= spoken_words <= 172, (path, "unexpected total narration", spoken_words)
    assert len(cameras) >= 7, "Too few varied camera compositions"
    for pack in data["asset_candidates"]:
        assert pack["license"] == "CC0-1.0", f"Must independently verify commercial rights for {pack}"
        assert pack["url"].startswith("https://"), pack
    if strict_release:
        assert data["publication_approved"] is True, "User must approve publication"
        assert clips is not None and proofs is not None, "All shot files and evidence frames required"
    return {"file": str(path), "shots":len(shots), "seconds":cursor,
            "words":spoken_words, "visual_scenes":len(scenes),
            "story_first_status":story_report["status"],
            "status":"approved" if strict_release else "storyboard-only, NOT render-approved"}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("storyboards", nargs="+", type=Path)
    p.add_argument("--strict-release", action="store_true")
    p.add_argument("--proofs", type=Path)
    p.add_argument("--clips", type=Path)
    args = p.parse_args()
    for f in args.storyboards:
        print(json.dumps(verify(f,args.strict_release,args.proofs,args.clips),sort_keys=True))
