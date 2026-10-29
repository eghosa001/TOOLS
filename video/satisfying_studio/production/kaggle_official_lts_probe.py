#!/usr/bin/env python3
"""Kaggle-only: use official signed-off Blender 4.5 LTS binary for one still.

This script creates ZERO video frames and gives ZERO quality approval.
It is entirely distinct from history_studio and uses no AI video/image models.
"""
from pathlib import Path
import importlib.util,json,os,subprocess,time

roots=list(Path("/kaggle/input").rglob("ASSET_PROVENANCE.json"))
if len(roots)!=1:raise RuntimeError("Expected one private CC0 ASMR dataset; found "+str(roots))
assets=roots[0].parent
for filename in ("official_blender.py","prismatic_gel_scene.py"):
    if not (assets/filename).is_file():
        raise RuntimeError("Private Kaggle dataset missing required original source: "+filename)
spec=importlib.util.spec_from_file_location("blender_bootstrap",assets/"official_blender.py")
loader=importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)
binary=loader.install()
output=Path("/kaggle/working/satisfying_official_lts_lookdev");output.mkdir(parents=True,exist_ok=True)
env=os.environ.copy()
env.update(ASMR_ASSETS=str(assets),ASMR_OUT=str(output),
           ASMR_MODE="STILL",ASMR_DEVICE="GPU",ASMR_GPU_BACKEND="OPTIX",
           ASMR_REQUIRE_GPU="1",ASMR_STILL_FRAME="70",
           ASMR_W="540",ASMR_H="960",ASMR_SAMPLES="12")
start=time.monotonic()
print("OFFICIAL_LTS_OPTIX_LOOKDEV_BEGIN",flush=True)
try:
    subprocess.run([str(binary),"-b","-t","4","--python",str(assets/"prismatic_gel_scene.py")],
                   env=env,check=True,timeout=300)
except subprocess.TimeoutExpired as err:
    raise RuntimeError("STOP: official Blender GPU still exceeded 300 seconds") from err
image=output/"lookdev.png"
if not image.is_file() or image.stat().st_size<40000:
    raise RuntimeError("STOP: missing actual Cycles look-dev image")
print("OFFICIAL_LTS_OPTIX_STILL_COMPLETE",round(time.monotonic()-start,2),
      str(image),image.stat().st_size,flush=True)
(output/"NOT_A_QUALITY_PASS.txt").write_text(
    "Official Blender 4.5 LTS actual still exists. No reviewed 5 second video exists.\n"
    "This benchmark measures GPU feasibility, not photorealism or tactile audio quality.\n"
    "Compare the still against the four ASMR references before any 120-frame render.\n")
