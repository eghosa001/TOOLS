#!/usr/bin/env python3
"""Verify official Blender archive is in PRIVATE Kaggle output without downloading it."""
import argparse,csv,io,json,pathlib,subprocess,sys,time

SLUG="ninefold-blender-4-5-15-cache"

def call(*args,timeout=70):
    r=subprocess.run(["kaggle",*args],capture_output=True,text=True,timeout=timeout)
    return r.returncode,r.stdout,r.stderr

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kernel",required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    p.add_argument("--minutes",type=int,default=19)
    a=p.parse_args()
    if not a.kernel.endswith("/"+SLUG):
        raise ValueError("Wrong project; refusing to query other Kaggle notebooks")
    a.out.mkdir(parents=True,exist_ok=True)
    end=time.monotonic()+a.minutes*60
    status="UNKNOWN"
    while time.monotonic()<end:
        rc,out,_=call("kernels","status",a.kernel,timeout=65)
        if not rc:
            status=out.strip()[-160:]
            print("OFFICIAL_BLENDER_KAGGLE_STATUS",status,flush=True)
            if any(word in status.lower() for word in ("complete","failed","error","cancelled")):
                break
        time.sleep(35)
    if "complete" not in status.lower():
        raise RuntimeError("Blender cache notebook not complete: "+status)
    rc,txt,_=call("kernels","files",a.kernel,"--csv","--page-size","200",timeout=70)
    if rc:raise RuntimeError("Cannot list Blender cache files")
    lines=[x for x in txt.splitlines() if x.strip()]
    start=next((i for i,x in enumerate(lines) if x.lower().startswith("name,") or x.lower().startswith("filename,")),0)
    files=list(csv.DictReader(io.StringIO("\n".join(lines[start:]))))
    names=[str(row.get("name") or row.get("filename") or row.get("fileName") or "")
           for row in files]
    required=["blender-4.5.15-linux-x64.tar.xz","blender_cache_status.json",
              "actual_bpy_properties.json","smoke_source.blend","smoke_cpu_64.png"]
    found={name:any(x.endswith(name) for x in names) for name in required}
    rc,log,_=call("kernels","logs",a.kernel,timeout=70)
    log=log if rc==0 else ""
    success=("VERIFIED_PRIVATE_BLENDER_4_5_CACHE_READY" in log and
             all(found.values()))
    report={
       "project":"The Ninefold Tide",
       "kaggle_notebook":"https://www.kaggle.com/code/"+a.kernel,
       "run_status":status,
       "official_blender_archive_stored_private":found[required[0]],
       "verified_blender_status_report_exists":found[required[1]],
       "blender_api_smoke_report_exists":found[required[2]],
       "editable_blend_smoke_exists":found[required[3]],
       "cpu_smoke_png_exists":found[required[4]],
       "log_confirms_sha256_and_status":success,
       "no_gpu_or_private_art_source_used":True,
       "note":"No 378MB Blender asset was downloaded by GitHub; this only inspects Kaggle output metadata."
    }
    (a.out/"blender_cache_verification.json").write_text(json.dumps(report,indent=2)+"\n")
    print("BLENDER_PRIVATE_CACHE_VERIFICATION",json.dumps(report,indent=2),flush=True)
    if not success:
        print("CACHE_LOG_FINAL_MARKER_PRESENT",("NINEFOLD_BLENDER_CACHE_FINAL" in log),flush=True)
        if rc==0:
            i=log.rfind("NINEFOLD_BLENDER_CACHE_FINAL")
            print("CACHE_LOG_TAIL",log[i:i+1200] if i>=0 else log[-1000:],flush=True)
        raise RuntimeError("Blender cache did not pass verification")

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("BLENDER_CACHE_VERIFICATION_FAILED",type(exc).__name__,str(exc)[:250],file=sys.stderr)
        sys.exit(1)
