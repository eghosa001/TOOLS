#!/usr/bin/env python3
"""GitHub Action → optional private Kaggle dataset + one Blender still job.
No credential material in repo. Must be explicitly workflow-dispatched.
"""
import argparse,json,os,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
SLUG="satisfying-studio-cc0-asmr-v1"
KERNEL="satisfying-studio-blender-lookdev"

def run(*args,timeout=900):
    print("KAGGLE COMMAND", " ".join(args),flush=True)
    return subprocess.run(["kaggle",*args],check=True,timeout=timeout)

def stage(folder,username):
    from asset_pack import build
    ds=folder/"dataset";nb=folder/"kernel"
    ds.mkdir(parents=True,exist_ok=True);nb.mkdir(parents=True,exist_ok=True)
    build(ds,HERE/"build_blender_scene.py")
    if not username:username="NOT_AUTHENTICATED_STAGE_ONLY"
    id_=username+"/"+SLUG
    dataset={
      "title":"Satisfying Studio — CC0 Materials and ASMR Foley",
      "id":id_,"licenses":[{"name":"CC0-1.0"}],
      "description":"Private production assets with provenance, actual PBR maps and recorded Foley."
    }
    (ds/"dataset-metadata.json").write_text(json.dumps(dataset,indent=2)+"\n")
    shutil.copy2(HERE/"kaggle_job.py",nb/"kaggle_job.py")
    notebook={
      "id":username+"/"+KERNEL,
      "title":"Satisfying Studio — Blender 3D Lookdev (Non-AI)",
      "code_file":"kaggle_job.py",
      "language":"python","kernel_type":"script",
      "is_private":True,"enable_gpu":True,"enable_internet":True,
      "dataset_sources":[id_],
      "competition_sources":[],"kernel_sources":[],"model_sources":[]
    }
    (nb/"kernel-metadata.json").write_text(json.dumps(notebook,indent=2)+"\n")
    print("STAGING DONE (not a Kaggle upload)",ds,flush=True)
    return ds,nb,id_,notebook["id"]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--publish",action="store_true")
    p.add_argument("--root",default="artifacts/satisfying-studio-kaggle")
    args=p.parse_args()
    username=os.environ.get("KAGGLE_USERNAME","").strip()
    if args.publish:
        if not username:raise SystemExit("STOP: Repository variable KAGGLE_USERNAME missing")
        if not os.environ.get("KAGGLE_API_TOKEN") and not os.environ.get("KAGGLE_KEY"):
            raise SystemExit("STOP: GitHub Actions Kaggle token missing; do not pretend uploaded")
        if not shutil.which("kaggle"):raise SystemExit("STOP: Kaggle CLI unavailable")
    ds,nb,dataset_id,notebook_id=stage(Path(args.root).resolve(),username)
    if not args.publish:
        print("STAGE ONLY: licensed library available as workflow artifact; Kaggle NOT changed")
        return
    exists=subprocess.run(["kaggle","datasets","files",dataset_id,"--page-size","1"],
                          capture_output=True,text=True,timeout=60).returncode==0
    if exists:
        run("datasets","version","-p",str(ds),"-m","Refresh verified licensed ASMR materials")
    else:
        run("datasets","create","-p",str(ds))  # private by default; NEVER -u
    run("kernels","push","-p",str(nb)) # submits a single still-render notebook
    print("PRIVATE DATASET UPLOAD ACCEPTED",dataset_id)
    print("PRIVATE KAGGLE NOTEBOOK SUBMITTED",notebook_id)
    print("No final Blender output, quality approval or channel upload asserted.")

if __name__=="__main__":main()
