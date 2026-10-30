#!/usr/bin/env python3
"""Canon-aware editorial/technical planner for The Ninefold Tide pilot.

This is a READ-ONLY decision-support layer, not a video generator or an
autonomous artistic approver. Story, asset, voice and final-cut approval must
remain with the human director.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "config.json"
SHOTS = ROOT / "pilot_shots.json"
ASSETS = ROOT / "asset_register.json"
SCHEMA_VERSION = 1

# The purpose/motion rules below are derived from the source-of-truth Drive
# bible, cast bible, continuity and director's shot handoff as at 2026-10-30.
# They deliberately do not rewrite the approved script or invent new scenes.
BEATS = {
    "ep101_001": ("geography", "Kito pride; establish ferry hazard", "Separate fixed rooftop, moving sluice deck and approaching ferry"),
    "ep101_002": ("acting", "Kito: delighted bravado", "Spool has finite cable and an operable mechanism"),
    "ep101_003": ("acting", "Naya: skeptical, sharply attentive", "Naya remains on service walkway"),
    "ep101_004": ("acting", "Kito: false confidence and recoil anticipation", "Hand position precedes mechanical launch"),
    "ep101_005": ("contact", "Kito launches; shoulder recoils", "Finite hook path; cable must originate from roof spool and remain connected"),
    "ep101_006": ("contact", "Physical mishap takes hold", "Hook MISSES bow ring and CATCHES outer rail; tension develops in stages"),
    "ep101_007": ("impact", "Kito: joy becomes fear", "Spool pulls Kito forward with readable ground friction, not weightless sliding"),
    "ep101_008": ("impact", "Iri: controlled urgency", "Iri catches coat and uses anchored stanchion for leverage, not superhuman strength"),
    "ep101_009": ("detail", "Kito: fear and helpless reach", "Hand cannot reach lever until release action occurs in shot 011"),
    "ep101_010": ("acting", "Naya: anger to deliberate problem-solving", "Release instruction identifies LEFT side under red notch"),
    "ep101_011": ("contact", "Iri slips and recovers", "Slack remains caught; hook and rope cannot teleport or vanish"),
    "ep101_012": ("geography", "Naya/Iri/Kito: shared controlled response", "Thin spool cord is a MESSENGER only; ferry needs heavy bow hawser later"),
}
MECHANICAL = {"ep101_001", "ep101_005", "ep101_006", "ep101_008", "ep101_011", "ep101_012"}
CHARACTERS = {"naya", "kito", "iri"}

def read(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def digest(source) -> str:
    return hashlib.sha256(json.dumps(source, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

def immutable_shot(shot: dict) -> dict:
    return {key: shot.get(key) for key in (
        "id", "start_frame", "end_frame", "description",
        "editorial_reason", "dialogue", "asset_ids"
    )}

def validate(config, shots, assets) -> list[str]:
    errors = []
    source = config.get("source_of_truth", {})
    for name in ("series_bible_v2", "continuity", "cast_design_bible", "episode_101_v2", "pilot_handoff"):
        if not str(source.get(name, "")).startswith("https://docs.google.com/document/d/"):
            errors.append("Missing canon reference: " + name)
    fps = config.get("target", {}).get("fps")
    total = config.get("target", {}).get("frames")
    if fps != 24 or total != 720 or shots.get("fps") != fps or shots.get("total_frames") != total:
        errors.append("Pilot frame rate/frame budget differs from the manually authored 24fps, 720-frame canon")
    rows = shots.get("shots")
    if not isinstance(rows, list) or len(rows) != 12:
        return errors + ["Must use exactly twelve director-authored pilot shots"]
    registered = {x.get("id") for x in assets.get("assets", [])}
    cursor = 0
    seen = set()
    for index, shot in enumerate(rows, 1):
        sid = shot.get("id")
        if sid != f"ep101_{index:03d}" or sid in seen or sid not in BEATS:
            errors.append(f"Unexpected/missing director shot at position {index}: {sid!r}")
        seen.add(sid)
        a, b = shot.get("start_frame"), shot.get("end_frame")
        if not isinstance(a, int) or not isinstance(b, int) or a != cursor or b <= a:
            errors.append(f"{sid}: gap, overlap or invalid shot frame bounds")
        if isinstance(b, int):
            cursor = b
        if not shot.get("description") or not shot.get("editorial_reason"):
            errors.append(f"{sid}: missing director intent")
        if not isinstance(shot.get("asset_ids"), list) or not shot["asset_ids"]:
            errors.append(f"{sid}: missing deliberately selected asset IDs")
        else:
            errors.extend(f"{sid}: unknown asset {asset}" for asset in shot["asset_ids"] if asset not in registered)
        if shot.get("editor_approved") and not shot.get("cut_approved_by"):
            errors.append(f"{sid}: editorial approval lacks named approver")
    if cursor != total:
        errors.append(f"Final shot must end at frame {total}, not {cursor}")
    return errors

def get_external(result: dict, sid: str, name: str):
    record = result.get("shots", {}).get(sid, {})
    return record.get(name) if isinstance(record, dict) else None

def observations(sid: str, scene, frames) -> list[dict]:
    issues = []
    def add(severity, code, detail, next_action):
        issues.append({"severity": severity, "code": code,
                       "evidence": detail, "recommended_action": next_action})
    if isinstance(scene, dict):
        if scene.get("has_camera") is False:
            add("blocker", "missing-camera", "Blender report shows no active camera",
                "Create or explicitly assign the director's approved 3D layout camera")
        if scene.get("fps") not in (None, 24):
            add("blocker", "fps", "Blender scene fps is not 24",
                "Correct scene frame rate, then recheck manually authored frame timing")
        if scene.get("missing_external_files"):
            add("blocker", "unresolved-media", scene["missing_external_files"],
                "Relink verified originals; do not replace with guessed textures or stock")
        if scene.get("camera") and scene.get("has_camera"):
            if scene.get("resolution_x", 0) < 1920 or scene.get("resolution_y", 0) < 1080:
                add("advisory", "render-res", "Blender scene resolution below canonical 1080p",
                    "Use lower resolution for internal layout only; final source must conform to 1920x1080")
        if scene.get("poly_count", 0) > 2_000_000:
            add("advisory", "geometry-cost", scene["poly_count"],
                "Use linked instances or lower-detail viewport proxies; keep approved final silhouettes")
        if scene.get("animated_object_count", 0) == 0 and sid in MECHANICAL:
            add("review", "motion-evidence", "No animated Blender object detected",
                "Confirm motion comes from the authored 2D shot or a separate approved mechanical cache")
    if isinstance(frames, dict):
        if frames.get("frame_count", 0) == 0:
            add("blocker", "no-frames", "Frame report detected no rendered PNGs",
                "Render the explicitly authored shot before considering visual approval")
        if frames.get("near_black_samples", 0) > 0:
            add("review", "near-black", frames["near_black_samples"],
                "Inspect intentional shadows and fades; rule out blank/underexposed frames")
        if frames.get("constant_sampled_sequence"):
            add("review", "constant-frames", "Sampled frames appear identical",
                "Review moving characters, depth and camera; held 2D drawings may be intentional")
    return issues

def plan(config, shots, assets, evidence=None) -> dict:
    errors = validate(config, shots, assets)
    evidence = evidence or {}
    rows = []
    registry = {x.get("id"): x for x in assets.get("assets", [])}
    for shot in shots.get("shots", []):
        sid = shot.get("id", "")
        if sid not in BEATS:
            continue
        typ, performance, mechanics = BEATS[sid]
        asset_ids = shot.get("asset_ids", [])
        missing_approvals = [
            x for x in asset_ids if x in registry
            and not (registry[x].get("approved_for_animation") is True and
                     registry[x].get("rights_confirmed") is True)
        ]
        scene = get_external(evidence, sid, "scene")
        frames = get_external(evidence, sid, "frames")
        technical_issues = observations(sid, scene, frames)
        needs_blender = sid in MECHANICAL
        tasks = [
            "Draw character acting and hand-contact keys in Krita/OpenToonz to match five-view model sheets",
            "Keep approved shot duration, narrative purpose and dialogue unchanged",
            "Use Blender for mechanical staging/depth/camera references only; preserve hand-drawn character finish",
            "Check continuity against adjacent shots and the director's handoff",
        ]
        if needs_blender:
            tasks.insert(0, "Block bridge/ferry/rope mechanical geography in Blender before hand-drawn contact keys")
        if shot.get("dialogue"):
            tasks.append("Align approved WAV phonemes and breaths; correct eyes/brows/cheeks independently of mouth cues")
        if typ in ("impact", "contact"):
            tasks.append("Review anticipation, contact frame, load path and recoil with actual animated frames")
        if missing_approvals:
            tasks.append("Resolve reference rights and art approval for: " + ", ".join(missing_approvals))
        rows.append({
            "id": sid, "frames": [shot["start_frame"], shot["end_frame"]],
            "beat_type": typ, "acting_target": performance,
            "canonical_physics": mechanics,
            "technique": {
                "character_performance": "hand_drawn_2d_priority",
                "blender": "mechanical_layout_and_camera_guides" if needs_blender else "optional_perspective_reference",
                "reuse": "approved_master_character_sheets_and_motion_keys",
            },
            "asset_ids": asset_ids, "unapproved_assets": missing_approvals,
            "scene_evidence": "present" if isinstance(scene, dict) else "not_provided",
            "frame_evidence": "present" if isinstance(frames, dict) else "not_provided",
            "issues": technical_issues, "recommended_tasks": tasks,
            "human_review_required": True,
            "ready_for_release": False,
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "name": "The Ninefold Tide — evidence-grounded, non-autonomous director worklist",
        "canon_sources": config.get("source_of_truth", {}),
        "canon_snapshot_status": "working design canon; assets/scripts/voices are not automatically approved",
        "immutable_timeline_sha256": digest([immutable_shot(s) for s in shots.get("shots", [])]),
        "review_evidence_sha256": digest(evidence),
        "errors": errors, "shots": rows,
        "technical_issue_count": sum(len(x["issues"]) for x in rows),
        "artistic_review_completed": False, "publication_authorized": False,
        "limits": [
            "Technical heuristics cannot assess character acting, originality, taste or age appearance",
            "No auto-selected footage, rewriting, final render acceptance, sound approval or publishing",
            "New motion keys and camera designs need editor review against Google Drive canon",
        ],
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence", type=Path,
                   help="Optional JSON mapping shot IDs to Blender scene reports and frame inspection reports")
    p.add_argument("--output", type=Path, help="Optional JSON report path")
    p.add_argument("--strict", action="store_true", help="Exit non-zero on structural canon errors")
    args = p.parse_args()
    evidence = read(args.evidence) if args.evidence else None
    result = plan(read(CANON), read(SHOTS), read(ASSETS), evidence)
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)
    if args.strict and result["errors"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
