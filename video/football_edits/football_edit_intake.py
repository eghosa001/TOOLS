#!/usr/bin/env python3
"""Edit-first football Short intake. A project manifest is not a video and gives no rights clearance."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
from datetime import date
from urllib.parse import urlparse
from football_video_score_gate import check as score_gate

STYLES=("moment_story","player_edit","rivalry_edit","comeback_edit","goal_story","skill_sequence","match_story")
RIGHTS=("licensed","owned","written_permission","cc_by","cc_by_sa","cc0","public_domain","documented_exception_review","pending")
def fail(msg):raise ValueError(msg)
def https(u):
    if not isinstance(u,str):return False
    p=urlparse(u)
    return p.scheme=="https" and bool(p.netloc)
def new(args):
    if args.style not in STYLES:fail("unknown edit style")
    if not args.subject.strip():fail("must name a real player, team or match")
    m={
      "schema_version":1,"content_mode":"narrated_football_edit","status":"UNVERIFIED_DRAFT",
      "subject":args.subject,"theme":args.theme,"style":args.style,
      "format":args.format,"duration_target_seconds":args.duration,
      "goal":"Create a compelling real-footage-first edit with a factual story and a payoff",
      "source_research_date":date.today().isoformat(),
      "story": {"hook":"","narrative_progression":"","payoff":"","verified_story_claims":[]},
      "creative_contribution":{"editing_concept":"","manual_selection_rationale":"","original_narration_or_commentary":"","original_visual_treatment":"","original_audio_contribution":""},
      "audio":{"speaker":"Ryan","provider":"Qwen3-TTS","pitch_preserving":True,"tempo":1.35,"narration_used":True,"music_license_verified":False},
      "shots":[],"captions_checked":False,"no_generated_football_visuals":True,"no_auto_publish":True,
      "editorial_review":{"exact_clip_provenance_verified":False,"goals_complete_and_correctly_identified":False,
        "final_video_watched_with_sound":False,"spoken_names_checked":False,
        "rights_reviewed":False,"six_part_scorecard":None}
    }
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(m,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("UNVERIFIED_FOOTBALL_EDIT_MANIFEST",str(p))
def validate(m,phase="plan",video=None):
    errors=[]
    if m.get("schema_version")!=1 or m.get("content_mode")!="narrated_football_edit":errors.append("incorrect edit-first manifest schema")
    if m.get("style") not in STYLES:errors.append("unknown edit style")
    if m.get("format") not in ("short","long"):errors.append("format must be short or long")
    if not str(m.get("subject","")).strip():errors.append("named actual subject missing")
    story=m.get("story") or {}
    for k in ("hook","narrative_progression","payoff"):
        if len(str(story.get(k,"")).strip())<12:errors.append("missing real-story "+k)
    contribution=m.get("creative_contribution") or {}
    if not any(len(str(v).strip())>=20 for v in contribution.values()):errors.append("original creative contribution is not documented")
    if m.get("no_generated_football_visuals") is not True:errors.append("no AI sports visuals allowed")
    if m.get("no_auto_publish") is not True:errors.append("must not auto-publish")
    shots=m.get("shots",[])
    if not isinstance(shots,list) or len(shots)<3:errors.append("at least three manually chosen real footage shots needed")
    else:
        for i,s in enumerate(shots):
            if not isinstance(s,dict):errors.append(f"shot {i}: invalid");continue
            if not https(s.get("source_url")):errors.append(f"shot {i}: verified source url required")
            if not s.get("recorded_event_or_athlete"):errors.append(f"shot {i}: actual recorded event or athlete missing")
            if not s.get("action_description"):errors.append(f"shot {i}: exact on-screen action must be described")
            if s.get("asset_kind")!="actual_football_video":errors.append(f"shot {i}: real film required, not a generated photo or diagram")
            if s.get("rights_status") not in RIGHTS:errors.append(f"shot {i}: rights status unassessed")
            start,end=s.get("source_in_seconds"),s.get("source_out_seconds")
            if type(start) not in (float,int) or type(end) not in (float,int) or not 0<=start<end:errors.append(f"shot {i}: invalid in/out")
            if phase=="release":
                if s.get("rights_status")=="pending":errors.append(f"shot {i}: source rights still pending")
                if not s.get("original_rightsholder_verified"):errors.append(f"shot {i}: owner not verified")
                if not s.get("action_verified_by_watching"):errors.append(f"shot {i}: action not watched")
                if not s.get("reason_for_use"):errors.append(f"shot {i}: creative purpose missing")
    if phase=="release":
        review=m.get("editorial_review") or {}
        for k in ("exact_clip_provenance_verified","goals_complete_and_correctly_identified","final_video_watched_with_sound","spoken_names_checked","rights_reviewed"):
            if review.get(k) is not True:errors.append("human review missing: "+k)
        if m.get("captions_checked") is not True:errors.append("captions not checked")
        if (m.get("audio") or {}).get("music_license_verified") is not True:errors.append("music/sound rights not cleared")
        score=review.get("six_part_scorecard")
        if not isinstance(score,dict):errors.append("six-part editorial video scorecard missing")
        else:
            result=score_gate(score,video,True)
            if result["status"]!="PASS":errors.extend(result["reasons"])
    return {"status":"HOLD" if errors else ("EDITORIAL_RELEASE_READY_NOT_LEGAL_GUARANTEE" if phase=="release" else "PLAN_READY_FOR_HUMAN_FOOTAGE_REVIEW"),"issues":errors,
            "content_mode":"narrated_football_edit","user_publish_request_needed":True}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="command",required=True)
    n=sub.add_parser("new")
    n.add_argument("--subject",required=True);n.add_argument("--theme",default="")
    n.add_argument("--style",choices=STYLES,default="moment_story")
    n.add_argument("--format",choices=["short","long"],default="short")
    n.add_argument("--duration",type=float,default=30.)
    n.add_argument("--output",required=True)
    c=sub.add_parser("check");c.add_argument("--manifest",required=True)
    c.add_argument("--phase",choices=["plan","release"],default="plan")
    c.add_argument("--video")
    args=ap.parse_args()
    if args.command=="new":new(args);return
    r=validate(json.loads(Path(args.manifest).read_text(encoding="utf-8")),args.phase,args.video)
    print(json.dumps(r,indent=2,ensure_ascii=False))
    if r["status"]=="HOLD":sys.exit(2)
if __name__=="__main__":main()
