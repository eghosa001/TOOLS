#!/usr/bin/env python3
"""Collect only the actual new Ninefold voice-audition output ZIP from Kaggle.

Run by the same temporary GitHub Actions workflow as the private GPU launch.
Never downloads pretrained model caches or any other Kaggle notebook outputs.
Never deletes anything. Audition audio remains explicitly UNAPPROVED.
"""
import argparse
import io
import json
import os
import pathlib
import subprocess
import sys
import time
import wave
import zipfile

def kaggle(*args, timeout=85):
    run=subprocess.run(["kaggle",*args],capture_output=True,text=True,timeout=timeout)
    return run.returncode,run.stdout,run.stderr

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--kernel",required=True)
    ap.add_argument("--destination",required=True)
    ap.add_argument("--minutes",type=int,default=38)
    args=ap.parse_args()
    if not args.kernel.endswith("/ninefold-tide-qwen3-voice-cast-auditions"):
        raise ValueError("Refusing to monitor an unrelated Kaggle kernel")
    target=pathlib.Path(args.destination)
    target.mkdir(parents=True,exist_ok=True)
    deadline=time.monotonic() + args.minutes*60
    status="UNKNOWN"
    observed=[]
    while time.monotonic()<deadline:
        rc,text,err=kaggle("kernels","status",args.kernel,timeout=65)
        if rc!=0:
            print("Kaggle status temporarily unavailable; retrying",flush=True)
            time.sleep(40)
            continue
        status=text.strip()[-450:]
        # Safe: this notebook is newly created and its URL is user-authored work.
        print("NINEFOLD_KERNEL_STATUS:",status.replace("\n"," ")[:280],flush=True)
        normalized=status.lower()
        if "complete" in normalized or "success" in normalized or "error" in normalized or "failed" in normalized:
            break
        time.sleep(40)
    (target/"kaggle_run_status.json").write_text(json.dumps({
        "kernel":args.kernel, "kaggle_status":status,"human_approved":False},indent=2),encoding="utf8")
    # Retrieve only our small output ZIP, never an entire notebook's caches.
    rc,out,err=kaggle("kernels","output",args.kernel,
            "--file-pattern",r".*ninefold_voice_ep101_UNAPPROVED\.zip$",
            "-p",str(target),"--quiet",timeout=240)
    if rc:
        print("Kaggle output not yet available; no WAV claimed",flush=True)
        return 2
    archives=list(target.glob("*UNAPPROVED.zip"))
    if not archives:
        print("No matching audition archive was returned",flush=True)
        return 2
    reports=[]
    for archive in archives:
        with zipfile.ZipFile(archive) as z:
            names=z.namelist()
            refs=[x for x in names if x.startswith("references/") and x.lower().endswith(".wav")]
            takes=[x for x in names if x.startswith("takes/") and x.lower().endswith(".wav")]
            for member in refs+takes:
                try:
                    with wave.open(io.BytesIO(z.read(member)),"rb") as wav:
                        if wav.getframerate()<22050 or wav.getnframes()<=0:
                            raise ValueError("Not a nonempty valid voice WAV")
                except (ValueError,wave.Error,EOFError) as exc:
                    raise RuntimeError(f"Invalid generated WAV {member}: {exc}")
            report={"archive":archive.name, "valid_reference_wavs":len(refs),
                    "valid_dialogue_takes":len(takes),
                    "ready_for_human_review":len(refs)>=3 and len(takes)>=21,
                    "human_approved":False}
            status_names=[x for x in names if x.endswith("voice_run_status.json")]
            if status_names:
                report["production_record"]=json.loads(z.read(status_names[0]))
            reports.append(report)
    (target/"voice_audio_verification.json").write_text(json.dumps(reports,indent=2),encoding="utf8")
    print("VOICE_AUDITION_WAV_VERIFICATION:",json.dumps(reports),flush=True)
    return 0 if all(x["ready_for_human_review"] for x in reports) else 3

if __name__=="__main__":
    try:
        sys.exit(main())
    except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired) as exc:
        print("COLLECTION_BLOCKED:",str(exc)[:450],file=sys.stderr)
        sys.exit(1)
