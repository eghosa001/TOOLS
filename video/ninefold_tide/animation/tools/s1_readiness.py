#!/usr/bin/env python3
"""Canon-linked S1 character/world preflight. No renders, downloads or approvals.

Reads Drive-linked public *metadata only*; original art stays private. The
preflight accepts correctly marked incomplete assets but fails if artists,
model sheets or environment stages are promoted without supporting evidence.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHARACTERS = "animation/canon/characters/s1_model_readiness.json"
WORLD = "animation/canon/environments/s1_world_continuity.json"
CAST = "audio/cast.json"
CAM = "animation/shots/E101/CAM03B/brief/shot.json"
LEAD_HEIGHTS = {"naya": 164, "kito": 145, "iri": 172}
REQUIRED_OBJECTS = {
    "fixed_harbour_quay", "fixed_roof", "service_stair",
    "safety_stanchion", "mooring_cleat", "school_ferry", "swing_bridge",
    "thin_messenger_spool", "heavy_hawser", "iri_safety_line",
}
REQUIRED_STATES = {
    "naya_reading_disc": ("confiscated_by_supervisor_ren", "E101"),
    "kito_full_glider": ("destroyed", "E104"),
    "belen_hand": ("seriously_injured", "E106"),
    "iri_evidence_token": ("restricted", "E107"),
    "tovan_toolbag": ("lost_irretrievably", "E109"),
    "iri_badge": ("surrendered", "E111"),
    "unique_allocation_order": ("lost_irretrievably", "E112"),
    "central_gate": ("remains_sealed", "E112"),
}


def read(root: Path, rel: str) -> dict:
    d = json.loads((root / rel).read_text(encoding="utf-8"))
    if not isinstance(d, dict):
        raise ValueError("JSON root not an object: " + rel)
    return d


def check(cond: bool, message: str):
    if not cond:
        raise ValueError(message)


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(root: Path = ROOT) -> dict:
    cast, art, world, cam = (read(root, r) for r in (CAST, CHARACTERS, WORLD, CAM))
    check(cast["character_count"] == art["roster_size"] == 20,
          "20-character canon mismatch")
    actual = {row["id"]: row for row in cast["characters"]}
    check(len(actual) == 20, "duplicate or missing voice cast")
    recorded = {row["id"]: row for row in art["regular_cast"]}
    check(len(recorded) == 20 and set(recorded) == set(actual),
          "art roster does not match voice/canon roster")
    check(art["schema_version"] == world["schema_version"] == 1,
          "unsupported manifest revision")
    for key in ("character_bible", "art_index"):
        check(art.get(key, "").startswith("https://docs.google.com/document/d/"),
              "Drive canon link missing: " + key)
    for role, row in recorded.items():
        source = actual[role]
        check(row["name"] == source["name"] and row["age"] == source["age"],
              "cast identity or age drift: " + role)
        if row["model_sheet_approved"]:
            check(nonempty(row["model_source"]) and nonempty(row["reviewer"]),
                  "unsubstantiated approved cast model: " + role)
        else:
            check(row["art_status"] in {"CONCEPT_OR_UNREVIEWED", "IN_PROGRESS"},
                  "unapproved cast row incorrectly promoted: " + role)
    required_views = art["required_model_views"]
    required_expr = art["required_expressions"]
    check(required_views == ["front", "three_quarter_front", "profile",
                            "three_quarter_rear", "rear"], "five-view naming changed")
    check(len(required_expr) == 8 and len(set(required_expr)) == 8,
          "eight distinct expression slots needed")
    leads = {r["id"]: r for r in art["priority_leads"]}
    check(set(leads) == set(LEAD_HEIGHTS), "pilot lead lineup mismatch")
    for name, lead in leads.items():
        check(lead["height_cm"] == LEAD_HEIGHTS[name], "lead height drift: " + name)
        check(set(lead["view_sources"]) == set(required_views),
              "missing turnaround view slots: " + name)
        check(set(lead["expression_sources"]) == set(required_expr),
              "missing expression slots: " + name)
        check(len(lead["continuity"]) >= 3 and len(lead["acting"]) >= 3,
              "acting or costume continuity missing: " + name)
        if lead["human_art_approved"]:
            needed = list(lead["view_sources"].values()) + list(lead["expression_sources"].values())
            needed += [lead[k] for k in ("hand_sheet_source", "viseme_sheet_source",
                                         "walk_cycle_source", "run_cycle_source",
                                         "editable_layer_source", "reviewer")]
            check(all(nonempty(x) for x in needed),
                  "hero design falsely art-approved: " + name)
            check(recorded[name]["model_sheet_approved"],
                  "approved hero must also have regular-model approval: " + name)
    objs = {obj["id"]: obj for obj in world["physical_objects"]}
    check(set(objs) == REQUIRED_OBJECTS, "pilot physical set items missing or altered")
    for label in ("fixed_harbour_quay", "fixed_roof", "service_stair",
                  "safety_stanchion", "mooring_cleat"):
        check(objs[label]["mobility"] == "fixed", "immovable item moved: " + label)
    for label in ("school_ferry", "swing_bridge"):
        check(objs[label]["mobility"] == "moving", "moving object locked incorrectly: " + label)
    for label in ("thin_messenger_spool", "heavy_hawser", "iri_safety_line"):
        check(objs[label]["mobility"] == "portable", "three ropes conflated: " + label)
    check(world["camera_reference"]["scene_id"] == "E101/CAM03B",
          "camera scene identity mismatch")
    c = world["camera_reference"]
    src = cam["camera_lock"]
    for a, b in (("camera_position_m", "position_m"), ("camera_look_at_m", "look_at_m"),
                 ("naya_root_m", "naya_root_m"), ("hand_target_m", "hand_target_m"),
                 ("focal_length_mm", "focal_length_mm")):
        check(c[a] == src[b], "CAM03B world-space camera/contact drift: " + a)
    episodes = {r["episode"]: r for r in world["episode_geography"]}
    check(set(episodes) == {"E101", "E104", "E106", "E108", "E109", "E110", "E111", "E112"},
          "missing critical staging reference")
    for key, val in episodes.items():
        check(nonempty(val["location"]) and nonempty(val["mechanical_test"]),
              "empty world physics note: " + key)
    states = {s["asset"]: s for s in world["cross_episode_state"]}
    check(set(states) == set(REQUIRED_STATES), "cross-episode prop states incomplete")
    for name, (event, episode) in REQUIRED_STATES.items():
        check(states[name]["transition"] == event and states[name]["effective_from"] == episode,
              "prop state drift: " + name)
    # Having a planned file, a GLB, a programmatic frame or a synthetic WAV is
    # NOT proof of professional painted animation or live audio quality.
    artwork_ready = all(x["model_sheet_approved"] for x in art["regular_cast"]) and all(
        x["human_art_approved"] for x in art["priority_leads"])
    world_ready = all(x["artist_approved"] for x in world["physical_objects"]) and all(
        world["approval"].values()) and all(x["blocking_approved"] for x in world["episode_geography"])
    return {"result": "STRUCTURAL_CANON_PASS_NOT_CREATIVE_APPROVAL",
            "tracked_character_roles": len(recorded), "pilot_leads": len(leads),
            "pilot_physical_objects": len(objs), "critical_episode_stages": len(episodes),
            "tracked_prop_events": len(states), "artwork_ready": artwork_ready,
            "world_ready": world_ready, "full_production_ready": False}


if __name__ == "__main__":
    try:
        print(json.dumps(validate(), indent=2))
    except (ValueError, KeyError, TypeError) as exc:
        raise SystemExit("NINEFOLD_S1_CANON_FAIL: " + str(exc)) from exc
