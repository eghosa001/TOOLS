#!/usr/bin/env python3
"""Kaggle-native 3D lookdev job: one Cycles STILL, real audio assets, no AI."""
import json,os,shutil,subprocess,zipfile
from pathlib import Path
DATASET="satisfying-studio-cc0-asmr-v1"
ROOT=Path("/kaggle/input")
WORK=Path("/kaggle/working/satisfying_studio")
WORK.mkdir(parents=True,exist_ok=True)
source=list(ROOT.glob(DATASET+"*/ASSET_PROVENANCE.json"))
if len(source)!=1:raise RuntimeError("Expected one private Kaggle dataset; found "+str(len(source)))
assets=source[0].parent
ledger=json.loads(source[0].read_text())
if len(ledger)<6 or not any(e["type"]=="audio" for e in ledger):
    raise RuntimeError("Missing verified CC0 materials and Foley pack")
audio_archives=0
for item in ledger:
    path=assets/item["name"]
    if item["type"]=="audio":
        # Kaggle automatically extracts uploaded zip files and may hide the source archive.
        if path.is_file():
            with zipfile.ZipFile(path) as archive:
                sound_files=[n for n in archive.namelist() if n.lower().endswith((".wav",".ogg",".flac",".mp3"))]
            if not sound_files:raise RuntimeError("Real Foley archive is empty: "+str(path))
            audio_archives+=1
            print("RAW FOLEY PACK",item["name"],len(sound_files))
        else:
            print("KAGGLE AUTO-EXTRACTED FOLEY ARCHIVE",item["name"])
    elif not path.is_file():
        raise RuntimeError("Required PBR/HDRI/Blender source file missing: "+str(path))
if audio_archives==0:
    playable=[p for p in assets.rglob("*") if p.is_file() and p.suffix.lower() in (".wav",".ogg",".flac",".mp3")]
    print("KAGGLE EXTRACTED REAL FOLEY FILES",len(playable))
    if len(playable)<75:raise RuntimeError("Kaggle extracted too few real Foley recordings; stop")
print("Verified assets available in Kaggle session:",len(ledger))
if not shutil.which("blender"):
    print("Installing traditional Blender; no diffusion or AI generation models")
    subprocess.run(["apt-get","update","-qq"],check=True,timeout=240)
    subprocess.run(["apt-get","install","-y","-qq","blender"],check=True,timeout=360)
if not shutil.which("blender"):raise RuntimeError("Blender install failed; stop")
os.environ["SATISFY_ASSETS"]=str(assets)
os.environ["SATISFY_OUTPUT"]=str(WORK/"lookdev")
try:
    subprocess.run(["blender","-b","-t","4","--python",str(assets/"build_blender_scene.py")],
                   check=True,env=os.environ.copy(),timeout=180)
except subprocess.TimeoutExpired as e:
    raise RuntimeError("Look-dev render exceeded 180s; stop, don't silently spend hours") from e
still=WORK/"lookdev"/"blender_3d_lookdev.png"
source3d=WORK/"lookdev"/"blender_3d_source.blend"
if not still.is_file() or still.stat().st_size<=30000 or not source3d.is_file():
    raise RuntimeError("3D render failed technical size/source checks; do not approve")
(WORK/"lookdev"/"REVIEW_REQUIRED.txt").write_text(
    "Traditional 3D still rendered. NOT a video and NOT automatically premium quality.\n"
    "Inspect PBR detail, reflections, glass transmission and composition.\n"
    "Only a genuinely reviewed still can lead to a short audio-synced 3-5 second proof.\n"
    "Real CC0 Foley packs exist but require MANUAL listening/selection by source.\n")
print("LOOKDEV STILL",still,still.stat().st_size)
print("STOP: actual visual inspection and audio decisions required before any video.")
