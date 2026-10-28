#!/usr/bin/env python3
"""Fuse the *existing* manually directed Titanic cut list, voice timing, and
actual downloaded image metadata into a source-first EDITORIAL WORKLIST.

Does NOT select footage, create a video, re-time voice, approve images or
replace old assets. Every unreviewed shot is marked PENDING. No fake signoff.
"""
from pathlib import Path
import json, csv, hashlib, math
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OUT=HERE/"timed_review";OUT.mkdir(parents=True,exist_ok=True)
def load(name):return json.loads((HERE/name).read_text())
def main():
    original=json.loads((ROOT/"MANUAL_SCENE_LEDGER_DRAFT.json").read_text())["scenes"]
    timing=json.loads((HERE/"TIMED_SHOTS_REVIEW.json").read_text())
    researched=load("MANUALLY_RESEARCHED_AUTHENTIC_SCENE_CANDIDATES.json")
    images=json.loads((HERE/"TITANIC_EXACT_SOURCE_INTAKE_REPORT.json").read_text())
    assert len(original)==302 and len(timing["scenes"])==302
    exact={r["scene_id"]:r for r in timing["scenes"]}
    candidates={x["id"]:x for x in researched["archive_candidates"]}
    downloaded={x["id"]:x for x in images["source_specific_metadata"]}
    decisions={x["shot_id"]:x for x in researched["shot_editor_decisions"]}
    output=[];categories={}
    for legacy in original:
        sid=legacy["scene_id"];record=exact[sid]
        assert record["chapter"]==legacy["chapter"]
        chosen=decisions.get(sid)
        candidate=candidates.get(chosen["source_id"]) if chosen else None
        intake=downloaded.get(chosen["source_id"]) if chosen else None
        media_available=bool(intake and intake.get("file"))
        no_mismatch=bool(chosen and not chosen["decision_state"].startswith("REJECTED"))
        if chosen and not no_mismatch:
            category="REJECTED_NARRATION_MISMATCH"
        elif candidate and candidate["kind"]=="DOCUMENTARY_DIAGRAM":
            category="DIAGRAM_EXCEPTION_REQUIRES_EDITOR_AND_TWO_SEARCHES"
        elif candidate and not media_available:
            category="RESEARCHED_REAL_SOURCE_MISSING"
        elif candidate:
            category="DOWNLOADED_REAL_SOURCE_AWAITING_VISUAL_LICENSE_APPROVAL"
        elif legacy["asset_type"]=="archive":
            category="LEGACY_ARCHIVAL_IMAGE_REQUIRES_EXACT_SOURCE_AND_HASH_CHECK"
        else:category="NO_SOURCE_FIRST_IMAGE_SELECTED_YET"
        categories[category]=categories.get(category,0)+1
        row={
          "scene_id":sid,"chapter":legacy["chapter"],
          "start_seconds":record["start_seconds"],"end_seconds":record["end_seconds"],
          "narration_full_paragraph":legacy["narration_paragraph"],
          "narration_cue":legacy.get("narration_cue",""),
          "old_asset_id":legacy["asset_id"],"old_visual_type":legacy["asset_type"],
          "source_first_status":category,
          "new_source_id":candidate["id"] if candidate else None,
          "exact_file_page_url":candidate["url"] if candidate else None,
          "source_description":candidate["specific"] if candidate else None,
          "documented_editor_reason":chosen["editorial_reason"] if chosen else None,
          "retrieved_candidate_name":intake.get("file") if intake else None,
          "retrieved_image_sha256":intake.get("sha256") if intake else None,
          "source_metadata_rights":intake.get("actual_metadata_rights") if intake else None,
          "source_media_resolution":([intake["width"],intake["height"]] if intake and intake.get("file") else None),
          "source_photo_identity_visually_checked":False,
          "commercial_license_final_editor_confirmed":False,
          "individual_editor_release_signoff":False,
          "actual_master_continuous_av_reviewed":False,
          "release_status":"BLOCKED"}
        if row["end_seconds"]<=row["start_seconds"]:raise ValueError("Bad timeline "+sid)
        output.append(row)
    assert len(output)==302
    if any(x["release_status"]!="BLOCKED" for x in output):raise ValueError("Unreviewed shot was approved")
    total=timing["runtime_seconds"]
    assert 5100<total<5400
    data={"source_first_compliance":"FAIL","narration_preserved":True,
          "old_private_youtube_video":"Vcc-5ay6ELI",
          "editorial_shots":output,"downloaded_real_source_approved_count":0,
          "downloaded_real_source_candidates":[x["id"] for x in images["source_specific_metadata"] if x["file"]],
          "shot_status_count":categories,"voice_seconds":total,
          "manual_source_review_complete":False,"visual_approval_complete":False,
          "render_permitted":False,"public_upload_permitted":False}
    (OUT/"titanic_302_audio_locked_unapproved_visual_choices.json").write_text(json.dumps(data,indent=2))
    with (OUT/"titanic_302_audio_locked_review.csv").open("w",newline="",encoding="utf8") as f:
        fields=["scene_id","chapter","start_seconds","end_seconds","old_asset_id",
               "old_visual_type","source_first_status","new_source_id",
               "exact_file_page_url","retrieved_image_sha256","source_media_resolution",
               "commercial_license_final_editor_confirmed","release_status"]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for row in output:w.writerow({k:row[k] for k in fields})
    (OUT/"FAIL_CLOSED_SUMMARY.json").write_text(json.dumps({
        "shot_count":302,"voice_runtime_sec":total,"candidate_status":categories,
        "compliant":False,"automated_graphic_substitution_allowed":False,
        "next_step":"Research, download and verify subject-matched real photographs; individually approve each shot and each necessary exception; do not render or upload before final source-first gate passes"
    },indent=2))
    print("TITANIC_REAL_MEDIA_EDITORIAL_WORKLIST_EXACTLY_AUDIO_TIMED",len(output),json.dumps(categories),flush=True)
if __name__=="__main__":main()
