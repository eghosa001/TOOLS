#!/usr/bin/env python3
"""Follow new PRIVATE Kaggle supporting cast run and verify its actual output WAV files.

Download only notebook outputs of our exact dedicated slug, not other projects.
Never deletes, changes or retrieves any ASMR notebooks.
"""
import argparse,io,json,pathlib,subprocess,sys,time,wave,zipfile
SLUG="ninefold-tide-20-character-supporting-voice-auditions"

def run(*args,timeout=80):
    p=subprocess.run(["kaggle",*args],capture_output=True,text=True,timeout=timeout)
    return p.returncode,p.stdout,p.stderr

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kernel",required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    p.add_argument("--max-minutes",type=int,default=24)
    args=p.parse_args()
    if not args.kernel.endswith("/"+SLUG):
        raise RuntimeError("Refusing to fetch any other Kaggle kernel")
    args.out.mkdir(parents=True,exist_ok=True)
    deadline=time.monotonic()+args.max_minutes*60
    status="UNKNOWN"
    while time.monotonic()<deadline:
        rc,txt,_=run("kernels","status",args.kernel,timeout=55)
        if rc:
            print("Kaggle status not available yet",flush=True)
        else:
            status=txt.strip()[-180:]
            print("KAGGLE_CAST_STATUS:",status,flush=True)
            lo=status.lower()
            if any(x in lo for x in ("complete","failed","error","cancelled")):
                break
        time.sleep(32)
    (args.out/"kaggle_job_status.json").write_text(json.dumps({
        "kernel":args.kernel,"status":status,"human_approved":False},indent=2))
    rc,txt,err=run("kernels","output",args.kernel,"-p",str(args.out),"--quiet",timeout=190)
    if rc:
        raise RuntimeError("Kaggle output retrieval unsuccessful; status="+status)
    archives=list(args.out.glob("ninefold_17_supporting_cast_UNAPPROVED.zip"))
    if len(archives)!=1:
        raise RuntimeError("Expected exactly one matching supporting cast audio archive")
    archive=archives[0]
    if archive.stat().st_size>150*1024*1024:
        raise RuntimeError("Unexpectedly large output; refuse to consume unnecessary data")
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read("supporting_voice_manifest.json"))
        wavs=[x for x in z.namelist() if x.endswith(".wav")]
        for name in wavs:
            with wave.open(io.BytesIO(z.read(name)),"rb") as wav:
                if wav.getframerate()<22050 or wav.getnframes()==0:
                    raise ValueError("Invalid WAV in voice audition archive")
        ids={x["id"] for x in manifest["candidates"]}
        result={"status":manifest["status"],"character_count":len(ids),
                "candidate_wavs_valid":len(wavs),
                "expected_new_characters":17,"expected_candidates":34,
                "errors":manifest["errors"],
                "needs_artistic_comparative_review":True,"human_approved":False}
    (args.out/"collection_verification.json").write_text(json.dumps(result,indent=2))
    print("VOICE_BANK_VERIFIED",json.dumps(result),flush=True)
    if len(ids)!=17 or len(wavs)!=34 or manifest["status"]!="ALL_GENERATED_UNAPPROVED":
        raise RuntimeError("Incomplete voice audition batch: preserve output but block complete status")

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("SUPPORTING_CAST_COLLECTION_FAILED",str(exc)[:450],file=sys.stderr)
        sys.exit(1)
