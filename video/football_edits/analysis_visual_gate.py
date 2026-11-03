#!/usr/bin/env python3
"""Fail-closed, source-first visual standard for football tactical previews/reviews.

This checks an editor-authored timeline; it does not select footage, certify
copyright status, detect AI visually, or replace human picture/sound review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

KINDS = {"match_footage", "other_real_football_footage", "player_photo", "editorial_graphic"}
FRAMES = {"match_action", "real_football_broll", "real_player_photo", "player_photo_versus",
          "tactical_diagram", "stat_card"}
RIGHTS = {"cc0", "public_domain", "cc_by", "cc_by_sa", "commercial_license",
          "written_permission", "pexels_license", "owned"}
MIN_REAL_MOVING_SHARE = 0.80
MIN_MATCH_ACTION_SHARE = 0.70
MAX_GENERIC_BROLL_SHARE = 0.10
MAX_GRAPHIC_SHARE = 0.20
MAX_PHOTO_SHARE = 0.20
MAX_NONMOVING_STREAK_SECONDS = 8.0
FRAME_KIND = {
    "match_action": {"match_footage"},
    "real_football_broll": {"other_real_football_footage", "match_footage"},
    "real_player_photo": {"player_photo"},
    "player_photo_versus": {"player_photo"},
    "tactical_diagram": {"editorial_graphic"},
    "stat_card": {"editorial_graphic"},
}
MOVING_FRAMES = {"match_action", "real_football_broll"}
GRAPHIC_FRAMES = {"tactical_diagram", "stat_card"}
PHOTO_FRAMES = {"real_player_photo", "player_photo_versus"}


class VisualGateError(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise VisualGateError(message)


def link(value):
    return isinstance(value, str) and urlparse(value).scheme == "https" and bool(urlparse(value).netloc)


def valid_day(value):
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_file(root, value):
    need(isinstance(value, str) and value.strip(), "Missing asset path")
    p = Path(value)
    need(not p.is_absolute() and ".." not in p.parts, "Asset path must be relative")
    absolute = (root / p).resolve()
    need(root == absolute or root in absolute.parents, "Asset escapes root")
    return absolute


def _canon(value):
    return " ".join(value.casefold().split()) if isinstance(value,str) else ""


def _entities(value, label, required=False):
    need(isinstance(value,list), f"{label}: list required")
    clean=[_canon(v) for v in value]
    need(all(clean) and len(clean)==len(set(clean)),f"{label}: names must be nonblank and unique")
    if required:
        need(bool(clean),f"{label}: at least one named entity required")
    return set(clean)


def validate_plan(plan):
    need(isinstance(plan, dict), "Manifest must be an object")
    need(plan.get("schema_version") == 1 and plan.get("pipeline") == "football_analysis_real_media",
         "Wrong football-analysis manifest/schema")
    need(plan.get("visual_policy") == "REAL_CAPTURED_MEDIA_NO_GENERATIVE_VISUALS",
         "Synthetic/AI visuals are prohibited (Qwen narration is permitted)")
    need(plan.get("format") in {"short", "long"}, "Specify short or long format")
    need(plan.get("analysis_type") in {"match_preview", "match_review", "classic_match",
                                        "player_comparison"}, "Invalid analysis type")
    need(isinstance(plan.get("title"), str) and len(plan["title"].strip()) >= 12, "Title missing")
    need(isinstance(plan.get("original_analysis"), str)
         and len(plan["original_analysis"].split()) >= 12, "Original sourced tactical thesis required")
    need(plan.get("automatic_shot_selection") is False, "Editor must manually choose every shot")
    need(plan.get("automatic_media_fallback") is False, "Missing source must stop; no fallback")
    # Every source and shot must demonstrably depict a named subject of THIS video,
    # not merely any available copyrighted or openly licensed football recording.
    target=plan.get("target",{})
    need(isinstance(target,dict),"Named video subject/fixture is required")
    match_analysis=plan["analysis_type"] in {"match_preview","match_review","classic_match"}
    target_teams=_entities(target.get("teams"),"target.teams",required=match_analysis)
    target_players=_entities(target.get("players"),"target.players",required=plan["analysis_type"]=="player_comparison")
    if match_analysis:
        need(len(target_teams)==2,"A named match analysis requires exactly two actual clubs/teams")
        need(valid_day(target.get("fixture_date")),"Verified fixture date is mandatory")
    if plan["analysis_type"]=="player_comparison":
        need(len(target_players)==2,"Player comparison requires two verified real player names")
    allowed_subjects=target_teams | target_players
    need(bool(allowed_subjects),"The video must identify its actual teams/players")
    sources = plan.get("sources")
    need(isinstance(sources, list) and sources, "Exact individual media sources required")
    ids = {}
    for src in sources:
        need(isinstance(src, dict), "Invalid source")
        sid, kind = src.get("id"), src.get("kind")
        need(isinstance(sid, str) and sid and sid not in ids, "Missing/duplicate source ID")
        need(kind in KINDS, f"{sid}: invalid visual source type; no generated imagery")
        ids[sid] = src
        filmed_teams=_entities(src.get("depicted_teams"),f"{sid}.depicted_teams")
        filmed_players=_entities(src.get("depicted_players"),f"{sid}.depicted_players")
        # No asset becomes relevant simply by being a free football video.
        if kind != "editorial_graphic":
            need(bool((filmed_teams | filmed_players) & allowed_subjects),
                 f"{sid}: unrelated video/photo: source depicts none of this video's named teams or players")
            if kind=="player_photo":
                need(bool(filmed_players & target_players),
                     f"{sid}: photographed player is not one of the players analysed")
        else:
            need(bool((filmed_teams | filmed_players) & allowed_subjects),
                 f"{sid}: tactical graphic is about a different match/player")
        need(isinstance(src.get("subject"), str) and len(src["subject"].strip()) >= 4,
             f"{sid}: actual depicted subject required")
        need(isinstance(src.get("editorial_reason"), str) and len(src["editorial_reason"].strip()) >= 12,
             f"{sid}: why is this real asset relevant?")
        need(isinstance(src.get("file"), str) and src["file"].strip()
             and not Path(src["file"]).is_absolute() and ".." not in Path(src["file"]).parts,
             f"{sid}: relative asset file required")
        need(re.fullmatch(r"[0-9a-f]{64}", src.get("sha256", "")) is not None,
             f"{sid}: source SHA256 required")
        need(src.get("is_ai_generated") is False and src.get("camera_capture") is (kind != "editorial_graphic"),
             f"{sid}: original real-camera provenance (or clearly original diagram) required")
        if kind == "editorial_graphic":
            need(src.get("created_by_editor") is True, f"{sid}: diagrams must be editor-authored")
            continue
        need(link(src.get("source_page")) and link(src.get("rights_evidence")),
             f"{sid}: exact source landing page and licence evidence required")
        need(src.get("rights_status") in RIGHTS, f"{sid}: unverified or restricted reuse rights")
        need(src.get("commercial_use") is True and src.get("derivatives_allowed") is True,
             f"{sid}: explicit commercial editing rights required")
        need(valid_day(src.get("rights_checked_on")), f"{sid}: dated rights review required")
        need(isinstance(src.get("creator"), str) and len(src["creator"].strip()) >= 3,
             f"{sid}: creator credit required")
        if src["rights_status"] in {"cc_by", "cc_by_sa", "commercial_license",
                                    "written_permission", "pexels_license"}:
            need(link(src.get("license_url")), f"{sid}: full licence/permission URL required")
        if src["rights_status"] == "cc_by_sa":
            need(isinstance(src.get("share_alike_plan"), str) and src["share_alike_plan"].strip(),
                 f"{sid}: ShareAlike obligation must be addressed")
        if kind in {"match_footage", "other_real_football_footage"}:
            need(src.get("genuine_moving_camera_footage") is True,
                 f"{sid}: video must actually contain real moving footage, not a pan over a still")
            need(src.get("original_recording_checked") is True,
                 f"{sid}: manual check of original moving frames required")
        if kind == "match_footage":
            recorded=_entities(src.get("recorded_match_teams"),f"{sid}.recorded_match_teams",required=True)
            need(len(recorded)==2,"Recorded football game must identify both actual opposing teams")
            need(filmed_teams == recorded,
                 f"{sid}: recorded-match teams must agree with depicted teams")
            if match_analysis:
                need(bool(recorded & target_teams),
                     f"{sid}: unrelated game: footage must show at least one actual team in the requested fixture")
                if plan["analysis_type"] in {"match_review","classic_match"}:
                    need(recorded==target_teams and src.get("recorded_match_date")==target["fixture_date"],
                         f"{sid}: review/classic-match footage must depict the exact requested match and date")
                elif plan["analysis_type"]=="match_preview":
                    need(src.get("recorded_match_date") < target["fixture_date"],
                         f"{sid}: preview may use only clearly labelled earlier matches, not future or same-day fabricated footage")
            else:
                need(bool(filmed_players & target_players),
                     f"{sid}: player comparison footage must actually show one of the compared players")
            need(isinstance(src.get("recorded_match"), str) and len(src["recorded_match"]) >= 8
                 and valid_day(src.get("recorded_match_date")),
                 f"{sid}: identify the actual historical game/date; do not imply current-match footage")

    shots = plan.get("shots")
    need(isinstance(shots, list) and shots, "Manual shot list required")
    cursor = 0.0
    seconds = {"moving": 0.0, "match": 0.0, "broll": 0.0, "photo": 0.0, "graphic": 0.0}
    streak = 0.0
    for i, shot in enumerate(shots, 1):
        need(isinstance(shot, dict), f"Shot {i}: invalid record")
        a,b,frame = shot.get("start_sec"), shot.get("end_sec"), shot.get("frame_type")
        need(isinstance(a, (int,float)) and not isinstance(a,bool)
             and isinstance(b, (int,float)) and not isinstance(b,bool)
             and 0 <= a < b and abs(a - cursor) <= 0.05,
             f"Shot {i}: missing/overlapping edit timeline or invalid time")
        cursor = b
        need(frame in FRAMES, f"Shot {i}: unsupported/synthetic visual kind")
        refs = shot.get("source_ids")
        focal=_entities(shot.get("focal_entities"),f"Shot {i}.focal_entities",required=True)
        need(focal <= allowed_subjects,
             f"Shot {i}: narration focus names unrelated clubs/players")
        need(isinstance(refs, list) and refs and len(set(refs)) == len(refs),
             f"Shot {i}: unique source IDs required")
        need(all(s in ids and ids[s]["kind"] in FRAME_KIND[frame] for s in refs),
             f"Shot {i}: medium mismatch, unknown source or synthetic imagery")
        need(isinstance(shot.get("spoken_line"), str) and len(shot["spoken_line"].strip()) >= 12,
             f"Shot {i}: align to a specific narration passage")
        need(isinstance(shot.get("editorial_reason"), str) and len(shot["editorial_reason"].strip()) >= 16,
             f"Shot {i}: explain why this shot, not a stock filler image")
        need(shot.get("manually_selected") is True, f"Shot {i}: editor must direct footage selection")
        length = b-a
        if frame in MOVING_FRAMES:
            src=ids[refs[0]]
            depicted=_entities(src["depicted_teams"],"depicted_teams") | _entities(src["depicted_players"],"depicted_players")
            need(bool(focal & depicted),
                 f"Shot {i}: football footage does not show the named team or player discussed")
            if frame=="real_football_broll":
                need(bool(_entities(src["depicted_teams"],"depicted_teams") & target_teams
                          or _entities(src["depicted_players"],"depicted_players") & target_players),
                     f"Shot {i}: generic/unrelated sports stock B-roll prohibited")
            need(len(refs) == 1, f"Shot {i}: moving footage must use one source")
            sa,sb = shot.get("source_in_sec"), shot.get("source_out_sec")
            need(isinstance(sa,(int,float)) and isinstance(sb,(int,float))
                 and not isinstance(sa,bool) and not isinstance(sb,bool)
                 and 0 <= sa < sb and 0.5 <= (sb-sa)/length <= 2.5,
                 f"Shot {i}: exact observed in/out timecodes required")
            need(shot.get("real_motion_verified") is True,
                 f"Shot {i}: inspect original camera footage rather than a still slideshow")
            seconds["moving"] += length
            seconds["match" if frame == "match_action" else "broll"] += length
            streak = 0.0
        elif frame in PHOTO_FRAMES:
            need(length <= 6.0, f"Shot {i}: photo shot is too long; use actual football motion")
            need(shot.get("photographs_unaltered_identity") is True,
                 f"Shot {i}: no AI face replacement, identity changing, or synthetic likeness")
            if frame == "player_photo_versus":
                actual_photographed=[
                    _entities(ids[sid]["depicted_players"],f"{sid}.depicted_players",required=True)
                    for sid in refs
                ]
                need(all(len(players)==1 for players in actual_photographed)
                     and actual_photographed[0].isdisjoint(actual_photographed[1]),
                     f"Shot {i}: photos must depict two distinct, correctly identified players")
                need({*actual_photographed[0],*actual_photographed[1]} == {
                      _canon(name) for name in shot.get("player_names",[])},
                     f"Shot {i}: versus labels must match the two genuine photographs")
                need(len(refs) == 2 and shot.get("face_each_other") is True,
                     f"Shot {i}: head-to-head requires two real player photos facing each other")
                need(len(shot.get("player_names", [])) == 2
                     and len(set(shot.get("player_names", []))) == 2,
                     f"Shot {i}: identify both photographed players")
            else:
                need(len(refs) == 1, f"Shot {i}: one approved photo source")
            seconds["photo"] += length
            streak += length
        else:
            need(length <= 8.0, f"Shot {i}: graphic is too long")
            need(len(refs) == 1, f"Shot {i}: one authored graphic file")
            need(shot.get("illustrative_not_match_recording") is True,
                 f"Shot {i}: diagrams must be disclosed, not mistaken for actual footage")
            seconds["graphic"] += length
            streak += length
        need(streak <= MAX_NONMOVING_STREAK_SECONDS + 0.001,
             f"Shot {i}: over eight seconds without real moving football footage")

    need(cursor >= 20, "Not enough analysed material for a complete video")
    need(seconds["moving"]/cursor >= MIN_REAL_MOVING_SHARE,
         f"Genuine moving football footage only {seconds['moving']/cursor:.1%}; require at least 80%")
    need(seconds["match"]/cursor >= MIN_MATCH_ACTION_SHARE,
         "At least 70% of the video must be genuine real match-action footage, not generic football stock")
    need(seconds["broll"]/cursor <= MAX_GENERIC_BROLL_SHARE,
         "Generic football B-roll cannot exceed 10% of runtime or masquerade as a specific match")
    need(seconds["photo"]/cursor <= MAX_PHOTO_SHARE,
         "Too many static photos; limit to 20% of runtime")
    need(seconds["graphic"]/cursor <= MAX_GRAPHIC_SHARE,
         "Too much diagram/stat-card runtime; limit to 20%")
    need(any(s["frame_type"] == "match_action" for s in shots),
         "A match analysis must actually include some rights-cleared real match action")
    if plan["analysis_type"] == "player_comparison":
        need(any(s["frame_type"] == "player_photo_versus" for s in shots),
             "Player comparisons need a genuine photograph-versus composition")
    return {"status":"PLAN_MEDIA_STANDARD_PASSED_NOT_PUBLICATION_APPROVED",
            "total_sec":round(cursor,3),"real_footage_share":round(seconds["moving"]/cursor,4),
            "match_action_share":round(seconds["match"]/cursor,4),
            "broll_share":round(seconds["broll"]/cursor,4),
            "photo_share":round(seconds["photo"]/cursor,4),
            "graphics_share":round(seconds["graphic"]/cursor,4),
            "review_and_rights_clearance":"required"}


def validate_release(manifest, root):
    report = validate_plan(manifest)
    root = Path(root).resolve()
    for src in manifest["sources"]:
        asset = safe_file(root, src["file"])
        need(asset.is_file() and digest(asset) == src["sha256"],
             f"{src['id']}: asset missing/changed since source rights review")
    name = manifest.get("output_file")
    output = safe_file(root, name)
    need(output.is_file() and output.suffix.lower() == ".mp4", "Actual reviewed MP4 missing")
    meta=json.loads(subprocess.check_output(
        ["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(output)],timeout=30))
    video=next((s for s in meta["streams"] if s.get("codec_type")=="video"),None)
    audio=next((s for s in meta["streams"] if s.get("codec_type")=="audio"),None)
    need(video and audio, "Video and audible narration required")
    need((video.get("width"),video.get("height")) in {(1080,1920),(1920,1080)},
         "Final cut must be full HD landscape or portrait")
    need(abs(float(meta["format"]["duration"])-report["total_sec"]) <= 0.75,
         "Actual export duration must match edited timeline")
    review=manifest.get("human_review",{})
    need(isinstance(review,dict) and review.get("approved") is True,
         "Human picture-and-sound review required before delivery/publication")
    need(isinstance(review.get("reviewer"),str) and len(review["reviewer"].strip()) >= 3
         and valid_day(review.get("reviewed_on")), "Human reviewer and actual review date required")
    for key in ("watched_complete_export", "listened_to_complete_export", "source_rights_rechecked",
                "footage_motion_checked", "every_shot_matches_narration",
                "no_synthetic_images_or_video", "versus_photos_authentic", "factual_accuracy_rechecked",
                "every_clip_is_about_the_named_fixture_or_player", "original_fixture_dates_verified"):
        need(review.get(key) is True, f"Human review incomplete: {key}")
    actual=digest(output)
    need(review.get("export_sha256")==actual, "Review must be signed against exact output file hash")
    report.update({"status":"TECHNICAL_RELEASE_EVIDENCE_PASSED_NOT_YOUTUBE_APPROVAL",
                   "output_sha256":actual})
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--phase",choices=["plan","release"],required=True)
    p.add_argument("--assets-root",type=Path,default=Path("."))
    opts=p.parse_args()
    try:
        manifest=json.loads(opts.manifest.read_text(encoding="utf-8"))
        report=validate_plan(manifest) if opts.phase=="plan" else validate_release(manifest,opts.assets_root)
    except (VisualGateError,ValueError,OSError,KeyError,subprocess.CalledProcessError) as e:
        print("FOOTBALL_REAL_MEDIA_GATE_BLOCKED:",e,file=sys.stderr)
        return 2
    print(json.dumps(report,indent=2))
    return 0


if __name__=="__main__":
    sys.exit(main())
