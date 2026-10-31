#!/usr/bin/env python3
"""Verify private v09 Kaggle 2D+3D scene runner, including honest missing-kit state.

No source ZIP or big Blender archive is downloaded to GitHub.
"""
import argparse,csv,io,json,pathlib,subprocess,sys,time
SLUG="ninefold-e101-v09-private-build-03"

def call(*args,timeout=75):
    p=subprocess.run(["kaggle",*args],capture_output=True,text=True,timeout=timeout)
    return p.returncode,p.stdout,p.stderr

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kernel",required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    p.add_argument("--minutes",type=int,default=9)
    a=p.parse_args()
    if not a.kernel.endswith("/"+SLUG):
        raise ValueError("Kaggle project mismatch; no other notebooks may be read")
    a.out.mkdir(parents=True,exist_ok=True)
    end=time.monotonic()+a.minutes*60
    status="UNKNOWN"
    while time.monotonic()<end:
        rc,txt,_=call("kernels","status",a.kernel)
        if rc==0:
            status=txt.strip()[-140:]
            print("V09_PRIVATE_SCENE_KAGGLE_STATUS",status,flush=True)
            if any(q in status.lower() for q in ("complete","failed","error","cancelled")):
                break
        time.sleep(25)
    if "complete" not in status.lower():
        raise RuntimeError("Private scene notebook has not completed yet")
    rc,txt,_=call("kernels","logs",a.kernel)
    logs=txt if rc==0 else ""
    private_kit_missing="NINEFOLD_V09_KIT_NOT_ATTACHED" in logs
    scene_executed="BLENDER_PHYSICAL_SCENE_BUILD_EXECUTED_ART_UNAPPROVED" in logs
    result={
      "project":"The Ninefold Tide",
      "kernel_url":"https://www.kaggle.com/code/"+a.kernel,
      "kaggle_status":status,
      "private_blender_cache_kernel_source":"aighewieghosa/ninefold-blender-4-5-15-cache",
      "ready_for_2mb_private_art_input":private_kit_missing,
      "actual_blender_v09_scene_built":scene_executed,
      "source_art_approval":False,
      "finished_animation":False,
      "no_existing_notebooks_modified":True,
      "no_gpu_quota_allocated":True,
      "diagnostic":"BLENDER_STAGE_SUCCESS" if scene_executed else
                   "PRIVATE_ART_ZIP_REQUIRED" if private_kit_missing else
                   "UNEXPECTED_RUNTIME_RESULT"
    }
    (a.out/"private_scene_production_status.json").write_text(json.dumps(result,indent=2)+"\n")
    if private_kit_missing:
        import tempfile,csv,io
        ref="aighewieghosa/ninefold-v09r1-original-archive-bytes"
        rct,stat,_=call("datasets","status",ref,timeout=55)
        result["private_art_dataset_status"]=stat.strip()[-180:] if rct==0 else "DATASET_STATUS_UNAVAILABLE"
        rcf,fileout,_=call("datasets","files",ref,"--csv",timeout=55)
        if rcf==0:
            rows=list(csv.DictReader(io.StringIO(fileout)))
            names=[str(row.get("name") or row.get("Name") or row.get("fileName") or "") for row in rows]
            result["source_kit_zip_present_in_private_dataset"]=any(
                name.endswith("Ninefold_S1_Private_Kaggle_Kit_v09r1.zip") for name in names)
            result["direct_v07_source_zip_present"]=any(
                name.endswith("NINEFOLD_2D_GREASE_PENCIL_KAGGLE_TRANSFER_v07.zip") for name in names)
            result["direct_v08_source_zip_present"]=any(
                name.endswith("The_Ninefold_Tide_E101_CAM03B_v08_Source.zip") for name in names)
            result["private_dataset_file_count"]=len(rows)
            result["dataset_file_csv_keys"]=sorted(str(k) for k in rows[0].keys()) if rows else []
            result["dataset_names_sample"]=names[:6]
            result["private_dataset_listing_head"]=[
                line[:140] for line in fileout.splitlines() if line.strip()
                and not line.strip().startswith("Next Page Token")
            ][:8]
        else:
            result["private_dataset_file_check"]="KAGGLE_API_UNAVAILABLE"
        with tempfile.TemporaryDirectory(prefix="ninefold_private_meta_") as folder:
            rcp,metadataout,_=call("kernels","pull","-k",a.kernel,"-p",folder,"-m",timeout=60)
            path=__import__("pathlib").Path(folder)/"kernel-metadata.json"
            if rcp==0 and path.exists():
                m=json.loads(path.read_text())
                result["kernel_dataset_source_attached"]=ref in m.get("dataset_sources",[])
                result["kernel_blender_cache_attached"]="aighewieghosa/ninefold-blender-4-5-15-cache" in m.get("kernel_sources",[])
        (a.out/"private_scene_production_status.json").write_text(json.dumps(result,indent=2)+"\\n")

    print("V09_PRIVATE_BUILDER_STATE",json.dumps(result,indent=2),flush=True)
    if not private_kit_missing and not scene_executed:
        print("V09_SAFE_LOG_TAIL",(logs[-1600:]),flush=True)
        raise RuntimeError("Notebook finished but source status not clearly reported; investigate before reporting success")

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("V09_COLLECTOR_ERROR",type(exc).__name__,str(exc)[:240],file=sys.stderr)
        sys.exit(1)
