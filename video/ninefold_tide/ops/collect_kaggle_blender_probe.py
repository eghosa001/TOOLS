#!/usr/bin/env python3
"""Fetch actual Kaggle CPU Blender runtime test and print concise capability report."""
import argparse,json,pathlib,subprocess,sys,time
EXPECTED="ninefold-blender-cpu-probe"

def cli(*args,timeout=75):
    p=subprocess.run(["kaggle",*args],capture_output=True,text=True,timeout=timeout)
    return p.returncode,p.stdout,p.stderr

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kernel",required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    p.add_argument("--minutes",type=int,default=9)
    a=p.parse_args()
    if not a.kernel.endswith("/"+EXPECTED):raise ValueError("Refusing to touch other Kaggle projects")
    a.out.mkdir(parents=True,exist_ok=True)
    end=time.monotonic()+a.minutes*60
    status="UNKNOWN"
    while time.monotonic()<end:
        rc,txt,err=cli("kernels","status",a.kernel)
        if rc==0:
            status=txt.strip()[-200:]
            print("BLENDER_PROBE_JOB_STATUS",status,flush=True)
            if any(x in status.lower() for x in ("complete","failed","error","cancelled")):
                break
        time.sleep(18)
    if "complete" not in status.lower():
        raise RuntimeError("Blender probe did not complete; status "+status)
    rc,txt,err=cli("kernels","output",a.kernel,"-p",str(a.out),"--quiet",timeout=160)
    if rc:raise RuntimeError("Blender probe output not retrievable")
    candidates=list(a.out.rglob("blender_runtime_inventory.json"))
    if len(candidates)!=1:
        files=[{"file":str(p.relative_to(a.out)),"bytes":p.stat().st_size}
               for p in a.out.rglob("*") if p.is_file()][:35]
        print("KAGGLE_BLENDER_OUTPUT_FILE_INVENTORY",json.dumps(files),flush=True)
        # COMPLETE can still mean the notebook had a runtime error. Retain a useful
        # diagnostic without pretending Blender worked.
        for log in a.out.rglob("*.log"):
            print("KAGGLE_NOTEBOOK_LOG_TAIL",log.read_text(errors="replace")[-1800:],flush=True)
        raise RuntimeError("Expected one Blender inventory JSON from Kaggle; got "+str(len(candidates)))
    result=json.loads(candidates[0].read_text())
    if result.get("project")!="The Ninefold Tide" or result.get("gpu_needed") is not False:
        raise RuntimeError("Unexpected notebook or GPU setting")
    print("REAL_KAGGLE_BLENDER_INVENTORY",json.dumps({
        "available":result["blender_available"],
        "version":result.get("blender_version"),
        "grease_pencil_v3":result["blender_grease_pencil_v3_found"],
        "saving_blend":result["blender_save_test"],
        "smoke_render":result["blender_render_test"],
        "v09_runs_without_install":result["would_run_v09_source_without_install"],
        "free_disk_gib":result["working_disk_free_gib"],
        "installer_available":result.get("apt_get_found",False),
        "errors":result["errors"]},indent=2),flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("BLENDER_PROBE_FAILED",type(e).__name__,str(e)[:300],file=sys.stderr)
        sys.exit(1)
