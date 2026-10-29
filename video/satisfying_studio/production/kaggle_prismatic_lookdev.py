#!/usr/bin/env python3
"""Single still-first Blender/Kaggle test for an original premium 5s scene.
No automatic quality sign-off, no user media copying, no AI generation.
"""
import os, pathlib, shutil, subprocess, time
WORK=pathlib.Path("/kaggle/working/satisfying_prismatic")
WORK.mkdir(parents=True,exist_ok=True)
script=pathlib.Path(__file__).with_name("prismatic_gel_scene.py")
if not script.is_file():raise RuntimeError("Missing actual Blender production scene source")
if shutil.which("blender") is None:
    print("Installing official Ubuntu Blender package for reproducible scene source",flush=True)
    subprocess.run(["apt-get","update","-qq"],check=True,timeout=240)
    subprocess.run(["apt-get","install","-y","-qq","blender"],check=True,timeout=360)
env=os.environ.copy()
env.update({
    "ASMR_OUT":str(WORK),"ASMR_MODE":"STILL",
    "ASMR_DEVICE":"CPU","ASMR_W":"720","ASMR_H":"1280",
    "ASMR_SAMPLES":"24","ASMR_STILL_FRAME":"70"
})
root=pathlib.Path("/kaggle/input")
for ledger in root.rglob("ASSET_PROVENANCE.json"):
    print("FOUND_LICENSED_ASSETS",ledger.parent)
    env["ASMR_ASSETS"]=str(ledger.parent)
    break
else:
    print("WARN: Private materials unavailable in this notebook; use original internal procedural materials, mark as limitation",flush=True)
start=time.monotonic()
try:
    cmd=["blender","-b","-t","4","--python",str(script)]
    print("BEGIN_REAL_3D_LOOKDEV",cmd,flush=True)
    subprocess.run(cmd,env=env,check=True,timeout=360)
except subprocess.TimeoutExpired as e:
    raise RuntimeError("Lookdev Blender render exceeded 360s; no auto-approval") from e
print("LOOKDEV_RENDER_SECONDS",round(time.monotonic()-start,2),flush=True)
still=WORK/"lookdev.png"
blend=WORK/"prismatic_gel_scene.blend"
if not still.is_file() or not blend.is_file() or still.stat().st_size<50000:
    raise RuntimeError("Blender did not export valid image plus editable source")
(WORK/"NOT_APPROVED_READ_ME.txt").write_text(
    "Original 3D Blender lookdev only. NOT a five-second video. Quality 9/10 not yet verified.\n"
    "Review materials, edge sheen, depth, contact and actual compressing gel silhouette.\n"
    "If quality is insufficient, STOP before 120-frame rendering.\n"
)
print("LOOKDEV_SOURCE_AND_IMAGE_READY",still,still.stat().st_size,blend.stat().st_size,flush=True)
