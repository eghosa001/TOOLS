#!/usr/bin/env python3
"""Import already-authored CC0 rigged character GLBs; do NOT rebuild meshes.

Downloads five fully rigged animated KayKit GLBs only once per asset build.
Presents fifteen reusable keyed variants (five base rigs x three colour/style
presets) without pretending fifteen independently modeled meshes exist.
Safe public artifact: CC0 originals, original provenance, no Kaggle/secrets.
"""
import argparse
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

from verify_original_assets import read_glb

OWNER_REPO="KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0"
REVISION="672074b73ba276876a19e8816ecdc5241817ab47"
BASE="https://raw.githubusercontent.com/"+OWNER_REPO+"/"+REVISION+"/"
SOURCE_ROOT="addons/kaykit_character_pack_adventures/Characters/gltf/"
MODELS=("Barbarian","Knight","Mage","Rogue","Rogue_Hooded")
CAST=("lelli","brin","odo","tavi","miko","pippa","nori","kolo",
      "suri","marn","fen","rumi","bex","luma","zaza")
SHADES=("#16b2ba","#bf7f30","#e76579","#b18ad7","#6eae82",
        "#edab83","#7cc8d3","#8d73aa","#eaca6b","#779fb9",
        "#96cbbb","#ba8c72","#6474b7","#d991b1","#9eb965")


def download(url,target,maximum):
    req=urllib.request.Request(url,headers={"User-Agent":"CartoonStudio-free-CC0-build/1.0"})
    with urllib.request.urlopen(req,timeout=75) as response, target.open("wb") as stream:
        size=0
        while True:
            chunk=response.read(1024*1024)
            if not chunk:
                break
            size+=len(chunk)
            if size>maximum:
                raise ValueError("Unexpected download size: "+url)
            stream.write(chunk)
    return hashlib.sha256(target.read_bytes()).hexdigest()


def build(destination):
    target=Path(destination).resolve()
    target.mkdir(parents=True,exist_ok=True)
    registry={"format":"CartoonStudio online rigged CC0 cast selection",
              "source":"https://github.com/"+OWNER_REPO,
              "source_commit":REVISION,
              "license":"CC0-1.0",
              "approval":"stock character replacement candidates; not updated series canon",
              "original_models":{},"variants":{}}
    for model in MODELS:
        name=model+".glb"
        filename=target/name
        checksum=download(BASE+SOURCE_ROOT+name,filename,15_000_000)
        data=read_glb(filename)
        if len(data.get("meshes",[]))<1 or len(data.get("skins",[]))<1 or len(data.get("animations",[]))<5:
            raise RuntimeError("Downloaded model lacks skinning or multiple real animation clips: "+name)
        registry["original_models"][model]={
            "filename":name,"source_path":SOURCE_ROOT+name,"sha256":checksum,
            "meshes":len(data["meshes"]),"skeleton_skins":len(data["skins"]),
            "built_in_animations":len(data["animations"]),
            "animation_names":[a.get("name","unnamed") for a in data["animations"]]}
        print("READY_RIGGED_ASSET",name,"meshes",len(data["meshes"]),"animations",len(data["animations"]),flush=True)
    # KayKit's source GLB folders include optional external PNG atlases.
    for atlas in ("barbarian_texture.png","knight_texture.png",
                  "mage_texture.png","rogue_texture.png"):
        download(BASE+SOURCE_ROOT+atlas,target/atlas,1_000_000)
    for model in MODELS:
        blob=read_glb(target/(model+".glb"))
        for image in blob.get("images",[]):
            uri=image.get("uri","")
            if uri and not uri.startswith("data:") and not (target/uri).is_file():
                raise RuntimeError("Required external GLB texture not copied: "+uri)
    license_path=target/"LICENSE.txt"
    download(BASE+"LICENSE.txt",license_path,100_000)
    txt=license_path.read_text(encoding="utf-8",errors="replace")
    if "CC0" not in txt or "commercial" not in txt.lower():
        raise RuntimeError("Source license text changed and needs manual review")
    for index,key in enumerate(CAST):
        registry["variants"][key]={
            "model":MODELS[index%len(MODELS)],
            "tint":SHADES[index],
            "scale":round((0.85,1.0,1.14)[index//5],3),
            "original_character_key":key,
            "approved_canon":False,
            "note":"Shared ready-made rig, unique tint/scale, NOT unique sculpt or voice"}
    (target/"ready_cast_manifest.json").write_text(json.dumps(registry,indent=2)+"\n",encoding="utf-8")
    assert len(registry["variants"])==15 and len(registry["original_models"])==5
    print("ONLINE_READY_CAST_COMPLETE base_glbs=5 skinned_variants=15; no Kaggle, no modified story")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("output")
    args=parser.parse_args()
    build(args.output)
