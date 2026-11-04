#!/usr/bin/env python3
"""Universal football video intake and fail-closed editorial preflight.

Creates an editable *unverified* plan, never footage. It cannot select shots,
verify copyright, or generate a video. An editor must research and fill it in.
Standard-library only; no network traffic. Defaults are from JSON, not V4 code.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

CONFIG = Path(__file__).with_name("football_video_defaults.json")
FORMATS = {"short", "long"}
ANALYSES = {"match_preview", "match_review", "classic_match", "player_comparison"}
CAMERA = {"match_action", "real_football_broll"}
PAIR = "player_matchup"
VALID_RIGHTS = {"licensed", "owned", "original_creator_permission", "documented_exception_review", "pending"}

class ProductionBlocked(ValueError):
    pass

def need(ok: bool, message: str):
    if not ok:
        raise ProductionBlocked(message)

def defaults():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    need(cfg.get("audio", {}).get("tempo") == 1.35, "Canonical 1.35 audio preference changed; review the policy.")
    need(cfg.get("delivery", {}).get("render_on_policy_change") is False, "Policy-only changes must never auto-render.")
    return cfg

def as_day(v, label):
    try:
        return date.fromisoformat(v)
    except (ValueError, TypeError):
        raise ProductionBlocked(f"{label} must be YYYY-MM-DD") from None

def https(url):
    return isinstance(url, str) and urlparse(url).scheme == "https" and bool(urlparse(url).hostname)

def new_plan(args):
    cfg = defaults()
    kind = args.analysis_type
    fmt = args.format
    need(kind in ANALYSES and fmt in FORMATS, "Unsupported format or analysis type")
    today = as_day(args.as_of, "--as-of")
    fixture = as_day(args.fixture_date, "--fixture-date") if args.fixture_date else None
    if kind != "player_comparison":
        need(fixture is not None, "A named match needs --fixture-date")
        need(args.team_a and args.team_b and args.team_a.casefold() != args.team_b.casefold(),
             "Two different verified team names required")
        if kind == "match_preview":
            need(fixture >= today, "This game is already in the past: use match_review or classic_match, not live preview")
        elif kind in {"match_review", "classic_match"}:
            need(fixture <= today, "The match has not happened: use match_preview")
    else:
        need(args.player_a and args.player_b and args.player_a.casefold() != args.player_b.casefold(),
             "Player comparison requires two distinct real player names")
    targets = [args.team_a,args.team_b] if kind != "player_comparison" else []
    players = [args.player_a,args.player_b] if kind == "player_comparison" else []
    title = args.title or (" vs ".join(players or targets) + (" | " + kind.replace("_", " ").title()))
    return {
      "schema_version":1, "pipeline":cfg["pipeline"],"status":"UNVERIFIED_NOT_READY",
      "format":fmt,"analysis_type":kind,"title":title,"as_of":today.isoformat(),
      "target":{"teams":targets,"players":players,
                "fixture_date":fixture.isoformat() if fixture else None,
                "fixture_time_and_timezone":None,"competition":None,
                "fixture_status":"unverified","result":None},
      "research":{"fixture_sources":[],"factual_claims":[],"latest_completed_matches":[],
                  "head_to_head":[],"searches_by_origin":[],"final_result_sources":[]},
      "audio":{"model":cfg["audio"]["model"],"speaker":cfg["audio"]["speaker"],
               "tempo":cfg["audio"]["tempo"],"pitch_preserving":True,
               "natural_names_reviewed":False,"separate_qwen_wav_per_shot":True,
               "loudness_target_lufs":cfg["audio"]["loudness"]["integrated_lufs"]},
      "sources":[],"shots":[],
      "editorial_review":{"every_shot_seen":False,"every_name_heard":False,
        "full_video_watched":False,"all_claims_matched":False,
        "match_result_verified":False,"all_goal_directions_verified":False,
        "every_source_rights_assessed":False,"approved":False,"human_reviewer":None,
        "quality_scores":{},"six_part_scorecard":None,"output_file":None,"drive_url":None},
      "do_not_auto_publish":True,"contains_ai_generated_images_or_video":False
    }

def validate(plan, phase="plan"):
    cfg = defaults()
    need(isinstance(plan,dict) and plan.get("schema_version")==1 and
         plan.get("pipeline")==cfg["pipeline"],"Wrong football project schema")
    fmt,kind = plan.get("format"),plan.get("analysis_type")
    need(fmt in FORMATS and kind in ANALYSES,"Unknown format or analysis type")
    target=plan.get("target",{})
    need(isinstance(target,dict),"Missing target")
    today=as_day(plan.get("as_of"),"as_of")
    d=as_day(target.get("fixture_date"),"fixture_date") if kind!="player_comparison" else None
    teams=target.get("teams",[])
    players=target.get("players",[])
    if kind!="player_comparison":
        need(isinstance(teams,list) and len(teams)==2 and all(isinstance(x,str) and x.strip() for x in teams),
             "Match must name two real teams")
        need(isinstance(target.get("competition"),str) and target["competition"].strip(),
             "Verified competition required")
        need(isinstance(target.get("fixture_time_and_timezone"),str) and
             target["fixture_time_and_timezone"].strip(),"Verified kickoff/timezone required")
        if kind=="match_preview":
            need(d>=today,"Cannot present a past game as a live future preview")
            need(target.get("fixture_status")=="verified_upcoming",
                 "Preview needs official upcoming-fixture confirmation; same-day final status must be checked")
        if kind in {"match_review","classic_match"}:
            need(d<=today,"A completed match must be in the past or today")
            need(target.get("fixture_status")=="verified_completed",
                 "Post-game review needs verified completed fixture and final whistle")
            need(isinstance(target.get("result"),str) and len(target["result"])>=3,
                 "Verified actual final result required")
    else:
        need(isinstance(players,list) and len(players)==2 and all(isinstance(x,str) and x.strip() for x in players),
             "Player comparison needs two real people")
    audio=plan.get("audio",{})
    need(audio.get("model")==cfg["audio"]["model"] and audio.get("speaker")=="Ryan",
         "Football voice must use the actual approved Qwen Ryan model")
    need(audio.get("tempo")==cfg["audio"]["tempo"] and audio.get("pitch_preserving") is True,
         "Tempo must be the default 1.35× with pitch preservation")
    need(audio.get("separate_qwen_wav_per_shot") is True,"Narration must be separately synced per shot")
    need(plan.get("contains_ai_generated_images_or_video") is False,
         "AI-generated football images and video prohibited")
    need(plan.get("do_not_auto_publish") is True,"Never publish directly from this pipeline")
    research=plan.get("research",{})
    if kind!="player_comparison":
        sources=research.get("fixture_sources",[])
        need(isinstance(sources,list) and len(sources)>=2 and all(https(u) for u in sources),
             "Two real independent/official fixture evidence links required")
    claims=research.get("factual_claims",[])
    need(isinstance(claims,list) and len(claims)>=2 and all(
        isinstance(c,dict) and isinstance(c.get("claim"),str) and len(c["claim"])>=8 and
        https(c.get("source_url")) for c in claims),
        "At least two independently sourced relevant football claims required")
    origins=research.get("searches_by_origin",[])
    need(isinstance(origins,list) and len({x.get("origin") for x in origins if isinstance(x,dict) and
         https(x.get("search_result_url"))})>=3,
         "Document actual searches in at least three distinct origin categories")
    if kind=="match_preview":
        latest=research.get("latest_completed_matches",[])
        need(isinstance(latest,list) and len(latest)>=2 and
             {x.get("team") for x in latest if isinstance(x,dict)}>=set(teams) and
             all(https(x.get("evidence_url")) and as_day(x.get("played_on"),"latest match date") < d
                 for x in latest if isinstance(x,dict)),
             "Both clubs' most recent completed games need verified opponents, dates and source links")
    if kind=="match_review":
        need(len(research.get("final_result_sources",[]))>=2 and
             all(https(u) for u in research["final_result_sources"]),
             "Post-match breakdown needs at least two final score / event sources")
    if kind=="classic_match":
        need(len(research.get("head_to_head",[]))>=1,
             "Historic context and original tournament date/source required")
    media=plan.get("sources",[])
    need(isinstance(media,list) and len(media)>0,"No verified real-media sources chosen yet")
    by_id={}
    for src in media:
        need(isinstance(src,dict) and isinstance(src.get("id"),str) and src["id"] and
             src["id"] not in by_id,"Duplicate/invalid media source ID")
        by_id[src["id"]]=src
        need(src.get("kind") in {"match_footage","real_football_broll","real_player_photo"},
             f"{src['id']}: media must be real")
        need(https(src.get("original_url")) and isinstance(src.get("rights_controller"),str)
             and len(src["rights_controller"].strip())>=3,
             f"{src['id']}: exact original source URL and true controller required")
        need(src.get("real_camera_verified") is True and src.get("synthetic") is False,
             f"{src['id']}: camera provenance must be reviewed, not AI or a still pan")
        need(src.get("rights_status") in VALID_RIGHTS,
             f"{src['id']}: actual rights status must be recorded")
        if src["kind"]=="match_footage":
            actual=src.get("actual_match",{})
            need(isinstance(actual,dict) and isinstance(actual.get("teams"),list) and
                 len(actual["teams"])==2 and isinstance(actual.get("date"),str) and
                 as_day(actual["date"],"source match date"),f"{src['id']}: exact filmed opponents and date required")
            filmed_day=as_day(actual["date"],"source match date")
            if kind=="match_preview":
                need(filmed_day<d,f"{src['id']}: footage cannot be from the future game being previewed")
                need(bool(set(actual["teams"]) & set(teams)),
                     f"{src['id']}: footage must depict one of the actual fixture teams")
            if kind=="player_comparison":
                need(bool(set(src.get("depicted_players",[])) & set(players)),
                     f"{src['id']}: player comparison action must actually show one of the named players")
        if src["kind"]=="real_player_photo":
            need(isinstance(src.get("depicted_players"),list) and
                 len(src.get("depicted_players"))==1 and src["depicted_players"][0],
                 f"{src['id']}: photo must identify its actual photographed footballer")
    shots=plan.get("shots",[])
    need(isinstance(shots,list) and shots,"Manual shot list is still empty")
    duration=0.0;move=0.0;action=0.0;matchups=0
    for i,shot in enumerate(shots):
        need(isinstance(shot,dict),f"Shot {i}: must be object")
        a,b=shot.get("start_sec"),shot.get("end_sec")
        need(isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float))
             and b>a and abs(a-duration)<.06,f"Shot {i}: non-contiguous/missing timing")
        duration=b
        need(shot.get("manual_choice") is True,f"Shot {i}: manual source choice required")
        need(shot.get("spoken_line") and shot.get("audio_file") and
             shot.get("full_audio_listened") is True,
             f"Shot {i}: real synced Qwen WAV and listened spoken line required")
        sid=shot.get("source_id")
        need(sid in by_id,f"Shot {i}: source not in reviewed source list")
        src=by_id[sid]
        need(shot.get("on_screen_source_credit") is True,
             f"Shot {i}: original match and owner must be credited on screen")
        need(shot.get("visual_matches_spoken_claim") is True,
             f"Shot {i}: observed footage must actually match the spoken sentence")
        focal=shot.get("focal_entities")
        need(isinstance(focal,list) and focal and
             all(isinstance(x,str) and x.strip() for x in focal),
             f"Shot {i}: identify real people/teams actually described")
        need(bool(set(focal)&(set(teams)|set(players))),
             f"Shot {i}: the scene must discuss the named fixture or compared players")
        if shot.get("visual_type") in {"match_action","real_football_broll"}:
            need(src["kind"] in {"match_footage","real_football_broll"},
                 f"Shot {i}: video source type mismatch")
            need(shot.get("source_in_sec") is not None and shot.get("source_out_sec") is not None
                 and shot["source_out_sec"]>shot["source_in_sec"],
                 f"Shot {i}: exact real-camera source timecodes required")
            move+=b-a
            if shot["visual_type"]=="match_action":
                need(src["kind"]=="match_footage",f"Shot {i}: actual match-action source needed")
                action+=b-a
        else:
            need(False,f"Shot {i}: photo/graphic must be over real relevant moving action, not a replacement slide")
        if i==0:
            need(shot["visual_type"]=="match_action" and
                 shot.get("first_frame_actual_football") is True,
                 "First rendered frame must be actual, relevant football action")
        if kind in {"match_review","classic_match"} and shot.get("role","target_match")=="target_match":
            actual=src.get("actual_match",{})
            need(set(actual.get("teams",[]))==set(teams) and actual.get("date")==str(d),
                 f"Shot {i}: match review cannot pass different game's action as the target fixture")
        if shot.get("claims_scoring_team"):
            need(shot.get("actual_scoring_team")==shot["claims_scoring_team"] and
                 shot.get("goal_setup_visible") is True and
                 shot.get("goal_finish_visible") is True,
                 f"Shot {i}: wrong scoring direction or goal cut before finish")
        pair=shot.get("player_matchup")
        if pair:
            matchups+=1
            need(isinstance(pair,list) and len(pair)==2 and
                 all(isinstance(q,dict) and q.get("name") and q.get("photo_source_id") in by_id and
                     by_id[q["photo_source_id"]]["kind"]=="real_player_photo" and
                     q["name"] in by_id[q["photo_source_id"]].get("depicted_players",[])
                     for q in pair),
                 f"Shot {i}: two actual identified source photographs required for matchup")
    if kind=="player_comparison":
        need(matchups>=1,"Player comparison must show two real portraits together")
    need(move/duration >= cfg["video"]["relevant_real_motion_share_min"] and
         action/duration >= cfg["video"]["relevant_actual_match_action_share_min"],
         "Video lacks sufficient relevant real motion or actual match action")
    if fmt=="short":
        need(duration <= cfg["formats"]["short"]["target_duration_seconds"][1] or
             plan.get("explicit_longer_short_requested") is True,
             "Default Short must stay <=59.8s; longer Shorts need explicit request and copyright review")
    else:
        need(duration>=180,"Detailed long-form must be substantially more developed than a Short")
    if phase=="release":
        reviewer=plan.get("editorial_review",{})
        for key in ("every_shot_seen","every_name_heard","full_video_watched",
                    "all_claims_matched","all_goal_directions_verified","every_source_rights_assessed",
                    "approved"):
            need(reviewer.get(key) is True,f"Human final quality review not complete: {key}")
        need(isinstance(reviewer.get("human_reviewer"),str) and
             len(reviewer["human_reviewer"].strip())>=3,
             "Real human editor sign-off missing")
        need(audio.get("natural_names_reviewed") is True,
             "Name pronunciation and natural prosody have not been listened to")
        need(all(x.get("rights_status") in {"licensed","owned","original_creator_permission","documented_exception_review"}
                 for x in media),"Unassessed rights are not publication-ready")
        need(reviewer.get("output_file") and Path(reviewer["output_file"]).is_file(),
             "Completed verified MP4 required before release")
        scores=reviewer.get("quality_scores",{})
        for k in ("footage","factual_accuracy","voice","shot_sync","mobile_legibility"):
            need(isinstance(scores.get(k),(int,float)) and scores[k]>=8.5,
                 f"User-approved 8.5/10 editorial quality standard not met for {k}")
        # Additional 4 Nov 2026 user mandate: six evidence-backed ratings,
        # all of them with hard floors; scorecard tied to the EXACT final MP4.
        # This does not reduce the five existing 8.5/10 minimums above.
        from football_video_score_gate import check as check_six_part_score
        scorecard=reviewer.get("six_part_scorecard")
        need(isinstance(scorecard,dict),
             "Mandatory six-part 0–10 video rating not supplied")
        report=check_six_part_score(scorecard,reviewer["output_file"],release=True)
        need(report["status"]=="PASS",
             "Mandatory 8/10 six-part football video score failed: "
             + "; ".join(report["reasons"]))
    return {"status":"EDITORIAL_"+phase.upper()+"_GATE_PASSED_NOT_COPYRIGHT_CLEARANCE",
            "format":fmt,"analysis_type":kind,"duration_sec":round(duration,2),
            "real_motion_share":round(move/duration,4),
            "match_action_share":round(action/duration,4),
            "voice_tempo":audio["tempo"],"human_rights_review_needed":True,
            "never_auto_publish":True}

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    sub=cli.add_subparsers(dest="cmd",required=True)
    new=sub.add_parser("new",help="Create unverified plan only; NEVER render")
    new.add_argument("--format",choices=sorted(FORMATS),default="short")
    new.add_argument("--analysis-type",choices=sorted(ANALYSES),default="match_preview")
    new.add_argument("--team-a")
    new.add_argument("--team-b")
    new.add_argument("--player-a")
    new.add_argument("--player-b")
    new.add_argument("--fixture-date")
    new.add_argument("--title")
    new.add_argument("--output",type=Path,required=True)
    new.add_argument("--as-of",default=datetime.now(ZoneInfo("Africa/Lagos")).date().isoformat())
    ck=sub.add_parser("check",help="Fail-closed real media and speech edit QA")
    ck.add_argument("--phase",choices=["plan","release"],default="plan")
    ck.add_argument("--manifest",type=Path,required=True)
    try:
        args=cli.parse_args()
        if args.cmd=="new":
            data=new_plan(args)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            need(not args.output.exists(),"Target manifest exists; never overwrite researched work")
            args.output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            print(json.dumps({"status":"UNVERIFIED_PLAN_CREATED_NOT_RENDERED",
                  "file":str(args.output),"tempo":data["audio"]["tempo"],
                  "format":data["format"],"analysis_type":data["analysis_type"]}))
        else:
            print(json.dumps(validate(json.loads(args.manifest.read_text(encoding="utf-8")),args.phase),indent=2))
        return 0
    except (ProductionBlocked,ValueError,KeyError,OSError) as exc:
        print("FOOTBALL_VIDEO_QUALITY_GATE_BLOCKED:",exc,file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
