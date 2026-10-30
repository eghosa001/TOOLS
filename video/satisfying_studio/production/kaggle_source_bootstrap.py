#!/usr/bin/env python3
"""One-entrypoint Kaggle runner for original Blender ASMR, no credits.

Run in a GPU-enabled Kaggle notebook with the creator's existing private
licensed CC0 Foley dataset attached. This fetches only small Python source
files at ONE pinned GitHub commit (not a repo clone), then delegates large
Blender downloads and rendering to the Kaggle cloud GPU. It never self-approves.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
from urllib.request import Request, urlopen

OWNER_REPO="eghosa001/TOOLS"
PREFIX="video/satisfying_studio/production/"
SOURCE_FILES=(
    "official_blender.py", "prismatic_gel_scene.py", "blender_softbody_prepare.py",
    "director_logic.py", "hand_authored_foley.py", "render_contact_proof.py",
    "render_cached_preview.py", "contact_foley.py", "kaggle_five_second_preview.py",
)

def read_url(url, cap):
    request=Request(url,headers={"User-Agent":"SatisfyingStudio-SourcePin/1.0"})
    with urlopen(request,timeout=65) as res: data=res.read(cap+1)
    if not data or len(data)>cap:
        raise RuntimeError("Missing or unexpectedly large version-pinned studio file: "+url)
    return data

def run():
    import shutil
    if not shutil.which("nvidia-smi"):
        raise RuntimeError("Kaggle GPU accelerator is not enabled; no paid or CPU full-render fallback")
    probe=subprocess.run(["nvidia-smi","-L"],capture_output=True,text=True,timeout=20)
    if probe.returncode or not probe.stdout.strip():
        raise RuntimeError("No accessible GPU. Enable the free Kaggle GPU accelerator.")
    datasets=list(Path("/kaggle/input").rglob("ASSET_PROVENANCE.json"))
    if len(datasets)!=1:
        raise RuntimeError("Attach the original licensed ASMR Foley dataset once (requires exactly one ASSET_PROVENANCE.json)")
    chosen=os.environ.get("ASMR_SOURCE_GIT_SHA","").strip().lower()
    if not chosen:
        metadata=json.loads(read_url(
            "https://api.github.com/repos/"+OWNER_REPO+"/commits/main",350_000))
        chosen=str(metadata.get("sha",""))
    if len(chosen)!=40 or any(c not in "0123456789abcdef" for c in chosen):
        raise RuntimeError("Could not independently pin the exact studio source commit")
    stage=Path("/kaggle/working/satisfying_asmr_source_snapshot")
    stage.mkdir(parents=True,exist_ok=True)
    lock={}
    for name in SOURCE_FILES:
        data=read_url(
            "https://raw.githubusercontent.com/"+OWNER_REPO+"/"+chosen+"/"+PREFIX+name,
            260_000)
        compile(data,name,"exec")
        dest=stage/name
        dest.write_bytes(data)
        lock[name]=hashlib.sha256(data).hexdigest()
    (stage/"PINNED_SOURCE_FILES.json").write_text(json.dumps({
        "github_repository":OWNER_REPO,
        "commit":chosen,
        "license_assets_provenance":str(datasets[0]),
        "source_files_sha256":lock,
        "approval_status":"technical production only, full AV inspection required",
    },indent=2)+"\n")
    env=os.environ.copy()
    env["ASMR_SOURCE_GIT_SHA"]=chosen
    print("PINNED_ASMR_SOURCE",chosen,"GPU",probe.stdout.strip(),"assets",str(datasets[0]),flush=True)
    subprocess.run([sys.executable,str(stage/"kaggle_five_second_preview.py")],
                   env=env,check=True,timeout=3000)

if __name__=="__main__":
    run()
