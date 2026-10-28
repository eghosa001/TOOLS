#!/usr/bin/env python3
"""Fail-closed editorial audit for the exact PRIVATE Titanic 2026 picture master.

No topic-to-video, media selection, image substitutions or rendering.
Never represent candidate/legacy assets as commercial-release approved.
Creates a complete shot-by-shot gap list with specific source research leads
handpicked in MANUALLY_RESEARCHED_AUTHENTIC_SCENE_CANDIDATES.json.
"""
from __future__ import annotations
import csv, importlib.util, json, math, pathlib
BASE=pathlib.Path(__file__).resolve().parent.parent
ROOT=pathlib.Path(__file__).resolve().parent
LEDGER=BASE/"MANUAL_SCENE_LEDGER_DRAFT.json"
RESEARCH=ROOT/"MANUALLY_RESEARCHED_AUTHENTIC_SCENE_CANDIDATES.json"
OUT=ROOT/"audit_output"
POLICY=BASE.parent.parent/"source_first_policy.py"

def load(p):
    return json.loads(p.read_text(encoding="utf8"))

def main():
    old=load(LEDGER)
    new=load(RESEARCH)
    shots=old["scenes"]
    proposals=new["shot_editor_decisions"]
    files={z["id"]:z for z in new["archive_candidates"]}
    assert len(shots)==302
    assert len({x["scene_id"] for x in shots})==302
    assert len({x["shot_id"] for x in proposals})==len(proposals)
    assert all(x["source_id"] in files for x in proposals)
    by_id={x["shot_id"]:x for x in proposals}
    rows=[]
    count={"LEGACY_GRAPHIC":0,"LEGACY_ARCHIVE_UNAPPROVED":0,"AUTHENTIC_SOURCE_PROPOSED":0,
           "PROPOSED_DIAGRAM_EXCEPTION":0,"REJECTED_MISMATCH":0}
    for shot in shots:
        sid=shot["scene_id"]
        proposed=by_id.get(sid)
        kind=shot["asset_type"]
        status="LEGACY_ARCHIVE_UNAPPROVED" if kind=="archive" else "LEGACY_GRAPHIC"
        source_url="";name="";ident="";reason=""
        if proposed:
            asset=files[proposed["source_id"]]
            source_url=asset["url"];name=asset["title"];ident=asset["id"]
            reason=proposed["editorial_reason"]
            if proposed["decision_state"].startswith("REJECTED"):
                status="REJECTED_MISMATCH"
            elif asset["kind"]=="DOCUMENTARY_DIAGRAM":
                status="PROPOSED_DIAGRAM_EXCEPTION"
            else:status="AUTHENTIC_SOURCE_PROPOSED"
        count[status]+=1
        editor_approved=shot.get("editor_approved") is True
        row={
            "chapter":shot["chapter"],"scene_id":sid,
            "narration_paragraph":shot.get("narration_paragraph",""),
            "narration_cue":shot.get("narration_cue",""),
            "old_asset_id":shot["asset_id"],"old_type":kind,
            "status":status,"proposed_source_id":ident,
            "source_title":name,"exact_landing_page":source_url,
            "editor_reason":reason,
            "spoken_quote_verified":False,
            "picture_identity_verified":False,
            "license_confirmed":False,
            "downloaded_file_sha256":None,
            "source_first_approved":False,
            "release_approved":False,
            "required_next_action":(
              "Reject narration/visual mismatch and search again" if status=="REJECTED_MISMATCH"
              else "Confirm separately justified diagram exception after TWO authentic searches" if status=="PROPOSED_DIAGRAM_EXCEPTION"
              else "Retrieve actual image, verify source identity and commercial licence + hash; then approve selected composition" if proposed
              else "Search subject-exact authentic commercially reusable image; record sources, or substantiate a diagram exception"
            )}
        rows.append(row)
    authentic_baseline=sum(x["asset_type"]=="archive" for x in shots)
    target=math.ceil(0.6*len(shots))
    # A candidate does not count toward compliance until its actual content and licence pass.
    evidence={
      "project":"Facts Uncovered Titanic 2026 Private review master",
      "film_duration_sec":5212.561687,
      "old_total_shots":len(shots),
      "legacy_archive_shots":authentic_baseline,
      "legacy_graphics":len(shots)-authentic_baseline,
      "baseline_fraction":round(authentic_baseline/len(shots),4),
      "default_authentic_requirement":0.6,
      "minimum_required_at_302_shots":target,
      "baseline_shortfall":max(0,target-authentic_baseline),
      "candidate_exact_asset_count":len(files),
      "personally_selected_shot_leads":len(proposals),
      "candidate_status_counts":count,
      "all_302_individual_editorial_approvals":False,
      "actual_source_first_release_gate":"FAIL",
      "full_continuous_AV_review":"NOT VERIFIED",
      "PRIVATE_youtube_video_id":"Vcc-5ay6ELI",
      "uploaded_video_modified":False,
      "new_film_rendered":False,
      "warnings":[
        "A previously collected 1912 archive photograph is not automatically commercially licensed.",
        "A 60% figure is a floor, not permission to pad with repeated unrelated Titanic photos.",
        "Caption or scene-file naming does not verify the image depicts the exact narrated claim.",
        "No footage of Titanic's actual sinking exists; use clearly labeled reconstructions only where necessary.",
        "Wreck and modern sonar footage from commercial providers cannot be assumed reusable.",
        "Cannot certify a 9/10 release from FFmpeg decode, contact sheets or source filenames."
      ],
      "release_approved":False,
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"titanic_302_source_first_gap_audit.json").write_text(json.dumps(evidence,indent=2))
    (OUT/"titanic_302_editorial_worklist.json").write_text(json.dumps(rows,indent=2))
    with (OUT/"titanic_302_editorial_worklist.csv").open("w",newline="",encoding="utf8") as fh:
        writer=csv.DictWriter(fh,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    # Run the repo's real source-first validator against *actual* legacy ledger data,
    # not a fabricated "approved" example manifest.
    spec=importlib.util.spec_from_file_location("real_source_policy",POLICY)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    legacy=[{
       "id":x["scene_id"],"spoken_text":x["narration_paragraph"],
       "start_seconds":x.get("in_time"),"end_seconds":x.get("out_time"),
       "shot_subject":x["asset_id"].replace("_"," "),
       "why_this_visual":"Legacy source selection requires fresh review",
       "visual_kind":"ARCHIVAL_PHOTO" if x["asset_type"]=="archive" else "DOCUMENTARY_DIAGRAM",
       "editor_approved_by":None,
       "editorial_status":"PENDING_SOURCE_FIRST_REPAIR",
       "authentic_source_searches":[]
    } for x in shots]
    status=mod.validate({"shots":legacy,"source_first_editorial_approval":"NOT_APPROVED"},phase="plan")
    assert status["status"]=="FAIL" and status["total_shots"]==302
    assert status["authentic_fraction"]<.6
    evidence["actual_repo_validator"]="FAIL_EXPECTED_AND_CONFIRMED"
    evidence["schema_errors_sample"]=status["errors"][:12]
    (OUT/"titanic_302_source_first_gap_audit.json").write_text(json.dumps(evidence,indent=2))
    print("TITANIC_SOURCE_FIRST_STATUS_FAIL",json.dumps({k:evidence[k] for k in
        ("old_total_shots","legacy_archive_shots","legacy_graphics","minimum_required_at_302_shots","baseline_shortfall","candidate_status_counts","actual_repo_validator")}))
    return evidence

if __name__=="__main__":
    main()
