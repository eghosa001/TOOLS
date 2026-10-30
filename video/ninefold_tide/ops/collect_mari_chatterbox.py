#!/usr/bin/env python3
"""Collect only the new private Mari Chatterbox output with real audio verification."""
import argparse,io,json,pathlib,subprocess,sys,time,wave,zipfile
SLUG="ninefold-mari-chatterbox-voice-01"
def api(*args,timeout=75):
    p=subprocess.run(["kaggle",*args],capture_output=True,text=True,timeout=timeout)
    return p.returncode,p.stdout,p.stderr
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kernel",required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    p.add_argument("--minutes",type=int,default=24)
    a=p.parse_args()
    if not a.kernel.endswith("/"+SLUG):raise ValueError("Wrong kernel; refusing another user's work")
    a.out.mkdir(parents=True,exist_ok=True)
    end=time.monotonic()+a.minutes*60
    status="UNKNOWN"
    while time.monotonic()<end:
        rc,out,err=api("kernels","status",a.kernel)
        if not rc:
            status=out.strip()[-250:]
            print("MARI_KAGGLE_STATUS",status,flush=True)
            if any(w in status.lower() for w in ("complete","failed","error","cancelled")):break
        time.sleep(35)
    (a.out/"mari_status_readback.json").write_text(json.dumps({"kaggle":status,"human_approved":False},indent=2))
    rc,out,err=api("kernels","output",a.kernel,"-p",str(a.out),"--quiet",timeout=220)
    if rc:raise RuntimeError("Could not fetch dedicated private notebook's outputs")
    archives=list(a.out.glob("ninefold_mari_chatterbox_UNAPPROVED.zip"))
    if len(archives)!=1:raise RuntimeError("Missing Mari Chatterbox audition archive")
    with zipfile.ZipFile(archives[0]) as z:
        report=json.loads(z.read("mari_recast_status.json"))
        names=[n for n in z.namelist() if n.startswith("mari_chatterbox_") and n.endswith(".wav")]
        if len(names)!=4 or report["candidate_count"]!=4 or report["state"]!="ALL_FOUR_ORIGINAL_RETAKES_GENERATED":
            raise RuntimeError("Not all four Mari samples generated; see preserved notebook output")
        for n in names:
            with wave.open(io.BytesIO(z.read(n)),"rb") as w:
                if w.getsampwidth()!=2 or w.getframerate()<22050 or w.getnframes()==0:
                    raise ValueError("Bad generated WAV "+n)
    print("MARI_CHATTERBOX_ALL_FOUR_WAVS_VERIFIED",archives[0].stat().st_size,flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("MARI_CHATTERBOX_COLLECTION_BLOCKED",str(e)[:250],file=sys.stderr)
        sys.exit(1)
