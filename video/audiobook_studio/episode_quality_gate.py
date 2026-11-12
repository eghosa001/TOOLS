#!/usr/bin/env python3
"""Fail-closed per-member scorecards for preproduction and predelivery.

Private scorecards must never be committed to GitHub. This validates signed
evidence fields and hashes, NOT whether a human actually watched the video.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

ROLES = {
 "story_editor": {
  "preproduction": ("approved_canon_and_script", "complete_source_anchored_scene_plan"),
  "predelivery": ("story_fidelity", "scene_accuracy")},
 "visual_director": {
  "preproduction": ("approved_character_style_references", "proven_scene_artwork_method"),
  "predelivery": ("character_identity_continuity","visual_style_consistency",
                  "background_world_accuracy","composition_readability","color_lighting_quality")},
 "narration_lead": {
  "preproduction": ("locked_narration_text_and_voice",),
  "predelivery": ("narration_quality",)},
 "sound_engineer": {
  "preproduction": ("music_first_rights_and_workflow_ready",),
  "predelivery": ("audio_mix_quality",)},
 "video_editor": {
  "preproduction": ("timing_and_repository_render_pipeline_ready",),
  "predelivery": ("timing_pacing","technical_video_quality")},
 "release_qa": {
  "preproduction": ("qa_and_verified_drive_delivery_workflow_ready",),
  "predelivery": ("thumbnail_packaging_quality","repository_compliance",
                  "google_drive_delivery_readiness","final_review_confidence")},
}
HARD_GATES = {
 "preproduction": (
  "approved_canon_loaded", "source_anchored_scene_plan_ready",
  "approved_character_references_ready", "music_first_and_rights_ready",
  "voice_and_video_pipeline_verified", "drive_delivery_method_verified",
  "no_known_production_blockers"),
 "predelivery": (
  "approved_script_fidelity","complete_source_coverage","story_image_match",
  "character_continuity","full_color_verified","narration_quality_verified",
  "music_and_audio_verified","scene_timing_verified",
  "full_encoded_video_human_reviewed","full_audio_human_listened",
  "technical_video_verified","rights_verified","thumbnail_and_naming_verified",
  "repository_checks_passed","actual_mp4_uploaded_and_verified_in_google_drive",
  "no_unresolved_delivery_blockers"),
}

def need(value, error):
    if not value:
        raise ValueError(error)

def filled(value):
    return isinstance(value,str) and bool(value.strip())

def timestamp(value, label):
    need(filled(value), "SCORECARD_TIMESTAMP_REQUIRED: "+label)
    need(value.endswith("Z") or bool(re.search(r"[+-]\d\d:\d\d$",value)),
         "SCORECARD_TIMEZONE_REQUIRED: "+label)
    try:
        return datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as e:
        raise ValueError("SCORECARD_INVALID_TIMESTAMP: "+label) from e

def validate_scorecard(packet, phase="preproduction", final_mp4=None):
    need(phase in HARD_GATES, "SCORECARD_BAD_PHASE")
    need(isinstance(packet,dict) and packet.get("schema_version")==1,
         "SCORECARD_SCHEMA_REQUIRED")
    for k in ("series_id","episode_id"):
        need(filled(packet.get(k)), "SCORECARD_EPISODE_ID_REQUIRED: "+k)
    need(bool(re.fullmatch("[0-9a-f]{64}",str(packet.get("source_sha256","")))),
         "SCORECARD_SOURCE_HASH_REQUIRED")
    roster=packet.get("team_roster")
    need(isinstance(roster,list) and roster, "SCORECARD_TEAM_ROSTER_REQUIRED")
    assigned={r:set() for r in ROLES}
    people=set()
    member_names={}
    for member in roster:
        need(isinstance(member,dict), "SCORECARD_INVALID_TEAM_MEMBER")
        mid=member.get("member_id")
        need(filled(mid) and mid not in people, "SCORECARD_DUPLICATE_OR_MISSING_MEMBER")
        people.add(mid)
        need(filled(member.get("name")), "SCORECARD_TEAM_NAME_REQUIRED")
        member_names[mid]=member["name"]
        roles=member.get("roles")
        need(isinstance(roles,list) and roles and len(set(roles))==len(roles) and
             set(roles)<=set(ROLES), "SCORECARD_INVALID_ASSIGNED_ROLES")
        for role in roles:assigned[role].add(mid)
    need(all(assigned.values()), "SCORECARD_ALL_SIX_ROLES_REQUIRED")
    stage=packet.get(phase)
    need(isinstance(stage,dict), "SCORECARD_STAGE_REQUIRED: "+phase)
    checked=timestamp(stage.get("checked_at"),phase)
    gates=stage.get("hard_gates")
    need(isinstance(gates,dict) and set(gates)==set(HARD_GATES[phase]),
         "SCORECARD_ALL_HARD_GATES_REQUIRED: "+phase)
    for key in HARD_GATES[phase]:
        need(gates[key] is True, "SCORECARD_HARD_GATE_FAILED: "+phase+"/"+key)
    need(stage.get("unresolved_blockers")==[],
         "SCORECARD_UNRESOLVED_BLOCKERS: "+phase)
    cards=stage.get("team_scorecards")
    need(isinstance(cards,dict) and set(cards)==set(ROLES),
         "SCORECARD_ALL_TEAM_REVIEWS_REQUIRED: "+phase)
    count=0
    lowest=10.0
    for role,people_in_role in assigned.items():
        entries=cards[role]
        need(isinstance(entries,list) and entries,
             "SCORECARD_ROLE_REVIEW_MISSING: "+role)
        ids=[e.get("member_id") for e in entries if isinstance(e,dict)]
        need(len(ids)==len(entries) and len(ids)==len(set(ids)) and
             set(ids)==people_in_role,
             "SCORECARD_MISSING_TEAM_MEMBER_REVIEW: "+role)
        expected=set(ROLES[role][phase])
        for entry in entries:
            who=role+"/"+entry["member_id"]
            need(entry.get("reviewer")==member_names[entry["member_id"]],
                 "SCORECARD_REVIEWER_ROSTER_IDENTITY_MISMATCH: "+who)
            need(entry.get("approved") is True and filled(entry.get("reviewer")) and
                 filled(entry.get("signed_review_reference")),
                 "SCORECARD_SIGNED_REVIEW_REQUIRED: "+who)
            need(timestamp(entry.get("reviewed_at"),who)<=checked,
                 "SCORECARD_REVIEW_DATE_INVALID: "+who)
            scores=entry.get("scores")
            need(isinstance(scores,dict) and set(scores)==expected,
                 "SCORECARD_ALL_ASSIGNED_CATEGORIES_REQUIRED: "+who)
            for category in sorted(expected):
                item=scores[category]
                need(isinstance(item,dict), "SCORECARD_CATEGORY_MISSING: "+who)
                value=item.get("score")
                need(type(value) in (int,float) and 8<=value<=10,
                     "SCORE_BELOW_8_OR_INVALID: "+who+"/"+category)
                need(filled(item.get("evidence")) and len(item["evidence"].strip())>=12,
                     "SCORECARD_SPECIFIC_EVIDENCE_REQUIRED: "+who+"/"+category)
                count+=1
                lowest=min(lowest,value)
    if phase=="predelivery":
        prior=packet.get("preproduction")
        need(isinstance(prior,dict),"SCORECARD_PREPRODUCTION_HISTORY_MISSING")
        begin=timestamp(stage.get("production_started_at"),"production_started_at")
        need(timestamp(prior.get("checked_at"),"preproduction")<=begin<=checked,
             "SCORECARD_PREFLIGHT_MUST_PRECEDE_PRODUCTION")
        validate_scorecard(packet,"preproduction")
        sha=stage.get("final_mp4_sha256")
        need(bool(re.fullmatch("[0-9a-f]{64}",str(sha))),
             "SCORECARD_FINAL_MP4_HASH_REQUIRED")
        media=stage.get("drive_file_id")
        need(filled(media) and bool(re.fullmatch("[A-Za-z0-9_-]{10,200}",media)),
             "SCORECARD_DRIVE_FILE_ID_REQUIRED")
        need(stage.get("drive_file_url") in (
            "https://drive.google.com/file/d/"+media+"/view",
            "https://drive.google.com/file/d/"+media+"/view?usp=drivesdk"),
            "SCORECARD_DRIVE_VIDEO_URL_REQUIRED")
        size=stage.get("drive_file_size_bytes")
        need(type(size) is int and size>=1024,
             "SCORECARD_DRIVE_FILE_SIZE_REQUIRED")
        need(filled(stage.get("drive_verification_reference")) and
             filled(stage.get("final_encoded_video_review_reference")),
             "SCORECARD_DRIVE_AND_FULL_VIDEO_REVIEW_EVIDENCE_REQUIRED")
        if final_mp4 is not None:
            path=Path(final_mp4)
            need(path.is_file() and path.suffix.lower()==".mp4",
                 "SCORECARD_LOCAL_FINAL_MP4_MISSING")
            need(path.stat().st_size==size,
                 "SCORECARD_DRIVE_FILE_SIZE_MISMATCH")
            need(hashlib.sha256(path.read_bytes()).hexdigest()==sha,
                 "SCORECARD_FINAL_MP4_SHA_MISMATCH")
    return {"status":"SCORECARD_8_PLUS_PASS","phase":phase,
            "episode_id":packet["episode_id"],"category_scores_checked":count,
            "lowest_score":lowest, "actual_mp4_hash_checked":final_mp4 is not None}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_scorecard",type=Path)
    p.add_argument("--phase",choices=tuple(HARD_GATES),default="preproduction")
    p.add_argument("--final-mp4",type=Path)
    a=p.parse_args()
    try:
        if a.phase=="predelivery" and a.final_mp4 is None:
            raise ValueError("SCORECARD_REAL_LOCAL_MP4_REQUIRED_BEFORE_DELIVERY")
        data=json.loads(a.private_scorecard.read_text(encoding="utf-8"))
        result=validate_scorecard(data,a.phase,final_mp4=a.final_mp4)
    except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError) as e:
        p.exit(2,"VIDEO_DELIVERY_OR_PRODUCTION_BLOCKED: "+str(e)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()

