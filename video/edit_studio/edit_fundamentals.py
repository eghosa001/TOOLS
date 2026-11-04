#!/usr/bin/env python3
"""Fail-closed craft gate: is this a designed cinematic edit, not a mini-trailer?
Documents creative intent. This cannot substitute for watching/listening to a real export.
"""
from __future__ import annotations
from pathlib import Path

class EditIdentityError(ValueError):
    pass

def require(ok,reason):
    if not ok:raise EditIdentityError(reason)

def wording(x,n=4):
    return isinstance(x,str) and len(x.strip().split())>=n

def validate_edit_identity(manifest):
    if manifest.get("schema_version",0)<3:return {"status":"legacy_not_enforced"}
    c=manifest.get("edit_identity")
    require(isinstance(c,dict),"v3 must define edit_identity before cutting any footage")
    require(c.get("format") in {"character_edit","scene_edit","comedic_edit","comparative_edit"},
        "This is not a trailer, summary, historical documentary, highlights package or stock montage")
    for name,minimum in [
        ("single_creative_idea",9),("character_or_subject",2),("audience_emotion",5),
        ("before_state",5),("after_state",5),("why_change_matters",7),
        ("recognition_motif",5),("opening_frame_meaning",6),
        ("music_interpretation",8),("specific_last_frame",6)]:
        require(wording(c.get(name),minimum),f"edit_identity.{name}: describe actual meaning, not effects")
    require(c["before_state"].strip().lower()!=c["after_state"].strip().lower(),
        "Opening and closing cannot leave subject in the same narrative state")
    require(c.get("sources_and_references_separate") is True,
        "Uploaded reference edits are for studying craft ONLY, never source media")
    require(c.get("music_rights_verified") is True or c.get("music_rights_verified") is False,
        "Record music rights truthfully; rights verification is independent")
    require(c.get("text_not_substituting_story") is True,
        "Captions/labels cannot substitute for a character moment")
    moments=c.get("creative_timing")
    require(isinstance(moments,list) and len(moments)>=4,
        "At least hook, anticipation, actual visual flip and held reaction required")
    required={"hook","anticipation","visual_flip","reaction"}
    labels=[m.get("role") for m in moments if isinstance(m,dict)]
    require(required.issubset(set(labels)),"Missing hook, anticipation, visual_flip or reaction")
    prev=-1
    for m in moments:
        require(isinstance(m,dict) and m.get("role") in required|{"acceleration","counterpoint","payoff"},
            "Every moment must have a meaningful role")
        t=m.get("at_sec")
        require(type(t) in (int,float) and t>prev,"Creative timing must progress in output time")
        prev=t
        require(wording(m.get("what_viewer_newly_feels_or_learns"),6),
            "Every moment must change understanding, emotion or expectation")
        require(wording(m.get("sound_picture_sync"),5),
            "Timing must map a specific musical event to a specific visual event")
    require(moments[0]["role"]=="hook" and moments[0]["at_sec"]<=1.5,
        "A meaning-bearing first image, not a title screen, must hook immediately")
    require(labels.index("visual_flip")>labels.index("anticipation"),
        "The edit must EARN its visual turn through anticipation")
    require(labels.index("reaction")>labels.index("visual_flip"),
        "Protect the final physical or emotional reaction after visual climax")
    src=manifest.get("media_sources",[])
    if src:
        for s in src:
            require(s.get("media_role")=="independent_original_source",
                "Reference uploads and pre-edited fan edits cannot be treated as independent shot sources")
            path=Path(s.get("file","")).name.lower()
            require(not path.startswith("(1080p)") and not path.startswith("contact_(1080p)"),
                "The user's uploaded reference clips are NOT footage sources")
    # QA is the decisive gate, not self-generated numeric scores.
    return {"status":"concept_gate_passed_not_quality_approval","creative_moments":len(moments),
        "meaningful_visual_flip":True,"reaction_after_flip":True,
        "release_quality_proven":False}
