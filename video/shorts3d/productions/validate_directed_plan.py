#!/usr/bin/env python3
"""No claim of 3D production readiness without asset, action and reference proof.

Validates the hand-directed 1904 Marathon / Operation Mincemeat shot map.
Structural checks can pass; strict preproduction/release fail until real asset
provenance, 3-5s lookdev and independent frame/audio approvals exist.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIRECTOR = BASE / "1904-marathon-operation-mincemeat-directed-plan.json"
REFERENCE_HASHES = {
    "51817fefcea61887cebbaa3bc38edb69275055a6494951350fa93e3e011765fc",
    "b4e9c6abff483a222936637badca7eb5f068dbb5dab745889ac5036a6bf4360b",
}
REQUIRED = ("set", "action_blocking", "camera_direction", "synchronized_foley",
            "required_unique_prop_or_rig", "visible_action", "narration")
SCENE_KEYS = {"marathon": "st-louis-1904-marathon-64s.json",
              "mincemeat": "operation-mincemeat-64s.json"}


def check(path: Path = DIRECTOR, strict: bool = False):
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    def require(condition, message):
        if not condition:
            errors.append(message)

    require(set(x.get("sha256") for x in data["reference_originals"]) == REFERENCE_HASHES,
            "Reference video hashes changed")
    require(data["quality_gate"]["min_editor_score_each_dimension"] >= 8.5,
            "Reference threshold must remain >=8.5 in EVERY category")
    require(len(data["films"]) == 2, "Both original history stories required")
    require({f["slug"] for f in data["films"]} == set(SCENE_KEYS), "Wrong target stories")
    for film in data["films"]:
        slug = film["slug"]
        script = path.parents[1] / "storyboards" / SCENE_KEYS[slug]
        require(script.is_file(), f"{slug}: actual storyboard missing")
        if not script.is_file():
            continue
        board = json.loads(script.read_text(encoding="utf-8"))
        require(len(board["shots"]) == 12, f"{slug}: 12 authored shots required")
        require(len(film["shot_directives"]) == 12, f"{slug}: directed events missing")
        require(film["seconds"] == 64 and film["fps"] == 30, f"{slug}: 64s 30fps needed")
        require(film["renderer"] == "Godot 4.7.2" and film["audio"].startswith("Qwen3-TTS"),
                f"{slug}: unauthorized renderer/voice substitution")
        require(film["render_authorized"] is False or strict,
                f"{slug}: never self-authorize from structural checker")
        for count, (shot, source) in enumerate(zip(film["shot_directives"], board["shots"]), 1):
            prefix = f"{slug} shot {count}"
            require(shot["id"] == source["id"], f"{prefix}: mismatched shot ID")
            require(shot["seconds"] == [source["start_seconds"], source["end_seconds"]],
                    f"{prefix}: timecodes mismatch narration")
            require(shot["narration"] == source["spoken"],
                    f"{prefix}: lines different from Qwen text")
            require(shot["visible_action"] == source["required_visible_action"],
                    f"{prefix}: narrated action missing or replaced")
            require(all(isinstance(shot.get(k), str) and len(shot[k]) >= 8 for k in REQUIRED),
                    f"{prefix}: incomplete visual/foley/art direction")
            require(shot.get("needs_on_screen") == source.get("must_show"),
                    f"{prefix}: factual prop list changed without source update")
            if strict:
                for flag in ("prop_verified_and_downloaded", "first_middle_last_frame_approved",
                             "shot_edit_approved"):
                    require(shot.get(flag) is True, f"{prefix}: {flag} missing")
        if strict:
            require(film.get("render_authorized") is True,
                    f"{slug}: explicit independent preproduction approval missing")
            require(board["story_editorial_approval"]["human_story_approved"] is True,
                    f"{slug}: human story editorial approval missing")
            require(board["render_authorized"] is True, f"{slug}: storyboard render authorization missing")
    if strict:
        require(data.get("reference_lookdev_evidence_file"),
                "Actual 3-5s film reference review missing")
        require(data.get("asset_checksums_and_license_manifest"),
                "Asset download hashes and licensing missing")
    return errors


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="Block production until scene assets + sample + reviews really exist")
    args = ap.parse_args()
    faults = check(strict=args.strict)
    if faults:
        for fault in faults:
            print("BLOCKED:", fault)
        raise SystemExit(1)
    print("STRUCTURAL_DIRECTION_ONLY_NOT_RENDER_OR_RELEASE_APPROVAL"
          if not args.strict else "PREPRODUCTION_EVIDENCE_VERIFIED")
