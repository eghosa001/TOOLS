#!/usr/bin/env python3
"""Titanic specific fail-CLOSED release gate — does not render or upload.

A preexisting successful 1080p MP4, 302-shot manifest, thumbnail or working
Kokoro narration do NOT amount to source, commercial rights or subjective
production approval. Return nonzero when any stage is not independently done.

A reviewer attestation must name the exact full video SHA256, match the
authentic-source manifest and record actual watch/listen approval. This CLI
only checks documentation; it never claims to have watched the film itself.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,pathlib,sys

HERE=pathlib.Path(__file__).resolve().parent
STUDIO=HERE.parents[3]
POLICY=STUDIO/"source_first_policy.py"

def getpolicy():
    spec=importlib.util.spec_from_file_location("titanic_source_policy",str(POLICY))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def check(manifest,assets_root,master,signoff):
    report={"release_approved":False,"source_first_status":"NOT_VERIFIED",
      "full_continuous_actual_master_review":"NOT_VERIFIED","errors":[]}
    if not manifest.is_file():
        report["errors"].append("MISSING manually approved 302-shot authentic-source manifest")
        return report
    try:
        doc=json.loads(manifest.read_text(encoding="utf8"))
        if len(doc.get("shots",[]))!=302:
            report["errors"].append("Expected 302 individually reviewed shots; replacing shot count requires a separately reviewed edit")
        if doc.get("min_authentic_shot_share",.6)<.6:
            report["errors"].append("Authentic share minimum cannot be weakened for Titanic without explicit approved policy change")
        policy=getpolicy()
        evidence=policy.validate(doc,phase="release",root=assets_root)
        report["source_first_status"]=evidence["status"]
        report["authentic_fraction"]=evidence["authentic_fraction"]
        report["errors"].extend(evidence["errors"][:40])
        if len(evidence["errors"])>40:report["errors"].append(f"{len(evidence['errors'])-40} additional shot errors")
    except Exception as e:
        report["errors"].append("Malformed/rejected source approval manifest: "+str(e)[:300])
        return report
    if not master.is_file():
        report["errors"].append("MISSING new source-first corrected full MP4")
        return report
    digest=sha(master)
    report["reviewed_mp4_sha256"]=digest
    if not signoff.is_file():
        report["errors"].append("MISSING complete editorial signoff referencing exact MP4 SHA256")
        return report
    # Both the exact approved picture/sourcing ledger AND master bytes must be
    # signed. A video hash alone allows a different 302-shot rights manifest to
    # be substituted after the reviewer inspected the original choices.
    approved_manifest_digest=sha(manifest)
    report["source_manifest_sha256"]=approved_manifest_digest
    try:
        record=json.loads(signoff.read_text(encoding="utf8"))
        required={
          "reviewer_name":str,
          "reviewed_mp4_sha256":str,
          "approved_source_manifest_sha256":str,
          "actual_86_minute_full_playback_with_sound":bool,
          "all_302_narration_to_visual_matches_inspected":bool,
          "rights_and_attributions_individually_approved":bool,
          "spoken_final_subscribe_audited":bool,
          "onscreen_final_subscribe_audited":bool,
          "caption_audio_alignment_audited":bool,
          "audio_music_and_narrator_quality_audited":bool,
          "black_frames_focus_and_lighting_audited":bool,
          "reconstruction_labels_inspected":bool,
          "approved_for_youtube_publication":bool
        }
        for key,typ in required.items():
            value=record.get(key)
            if not isinstance(value,typ) or not value:
                report["errors"].append("Missing explicit actual-final-file editorial PASS: "+key)
        if record.get("reviewed_mp4_sha256")!=digest:
            report["errors"].append("SIGNOFF SHA mismatch: signed video differs from actually supplied film")
        if record.get("approved_source_manifest_sha256")!=approved_manifest_digest:
            report["errors"].append("SIGNOFF MANIFEST SHA mismatch: approved 302-shot rights ledger differs from actual supplied source manifest")
        if len(str(record.get("reviewer_name") or "").strip())<4:
            report["errors"].append("Need accountable actual reviewer full name")
    except Exception as e:
        report["errors"].append("Malformed review signoff: "+str(e)[:300])
    report["full_continuous_actual_master_review"]="DOCUMENTED_BY_REAL_REVIEWER" if not report["errors"] else "NOT_VERIFIED"
    report["release_approved"]=not bool(report["errors"])
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=pathlib.Path,required=True)
    ap.add_argument("--assets-root",type=pathlib.Path,required=True)
    ap.add_argument("--master",type=pathlib.Path,required=True)
    ap.add_argument("--signoff",type=pathlib.Path,required=True)
    ap.add_argument("--report",type=pathlib.Path)
    args=ap.parse_args()
    result=check(args.manifest,args.assets_root,args.master,args.signoff)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if not result["release_approved"]:sys.exit(1)

if __name__=="__main__":main()
