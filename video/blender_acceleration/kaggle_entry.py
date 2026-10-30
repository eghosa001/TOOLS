#!/usr/bin/env python3
"""Standalone private Kaggle setup: never touch another notebook or auto-render."""
import importlib.util,json,subprocess,sys
from pathlib import Path
import kaggle_boost
out=Path("/kaggle/working/blender_boost")
out.mkdir(parents=True,exist_ok=True)
result=kaggle_boost.install(allow_apt=True)
result["profile"]="free_non_destructive_core"
result["free_python_tools"]={}
for module,package in (("PIL","Pillow"),("trimesh","trimesh"),("pygltflib","pygltflib")):
    if importlib.util.find_spec(module):
        result["free_python_tools"][package]="already_present"
        continue
    process=subprocess.run([sys.executable,"-m","pip","install","--disable-pip-version-check",
                            "--no-input",package],capture_output=True,text=True,timeout=240)
    result["free_python_tools"][package]=("installed" if process.returncode==0 else "failed_optional_install")
result["other_notebooks_modified"]=False
result["frames_rendered"]=0
result["requires_manual_quality_review"]=True
(out/"runtime_report.json").write_text(json.dumps(result,indent=2)+"\n")
print("FREE_KAGGLE_BLENDER_SETUP="+json.dumps(result),flush=True)
if result["status"]!="ready":
    raise RuntimeError("Blender/FFmpeg setup incomplete; see runtime report")
