#!/usr/bin/env python3
"""Fetch 15 distinct existing, CC0, skinned animated Quaternius creatures.

Absolutely no procedural character modelling. Original source is Quaternius'
Cute Animated Monsters (Aug 2020). GitHub mirror is pinned to an immutable
commit for repeatability. The models are stylized game assets, not film rigs.

Usage: python video/import_distinct_cartoon_cast.py OUTPUT_DIR
"""
from __future__ import annotations
import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE_REPO="agentkaerf/FreeModels"
PINNED_COMMIT="db3df04d1e4714298a09510b26fb6de6645138a2"
SOURCE_FOLDER="Cute Animated Monsters - Aug 2020/glTF/"
SOURCE_LICENSE="https://quaternius.com/packs/cutemonsters"
MIRROR_LICENSE="https://github.com/agentkaerf/FreeModels"
CAST={
    "lelli":"Alien",
    "brin":"Alien_Tall",
    "odo":"Pig",
    "tavi":"Panda",
    "miko":"Cactus",
    "pippa":"Chicken",
    "nori":"Crab",
    "kolo":"Cyclops",
    "suri":"Deer",
    "marn":"Mushroom",
    "fen":"Tree",
    "rumi":"Yeti",
    "bex":"Penguin",
    "luma":"Ghost",
    "zaza":"Bee",
}
MAX_BYTES=6_000_000

def fetch(url):
    request=urllib.request.Request(url,headers={"User-Agent":"CartoonStudio-licensed-model-import/1.0"})
    with urllib.request.urlopen(request,timeout=60) as stream:
        blob=stream.read(MAX_BYTES+1)
    if not blob or len(blob)>MAX_BYTES:
        raise ValueError("Missing or oversized source file")
    return blob

def inspect_model(data,key):
    if data.get("asset",{}).get("version")!="2.0":
        raise ValueError("Not glTF 2.0: "+key)
    if len(data.get("skins",[]))<1 or len(data.get("meshes",[]))<1:
        raise ValueError("Character is not a skinned mesh: "+key)
    clips=[a.get("name","") for a in data.get("animations",[])]
    if "Idle" not in clips and "Flying" not in clips:
        raise ValueError("Character lacks idle/flying cycle: "+key)
    if len(clips)<4:
        raise ValueError("Too few animation clips: "+key)
    if not data.get("buffers") or any(
        not str(buffer.get("uri","")).startswith("data:") for buffer in data["buffers"]
    ):
        raise ValueError("Model is not self-contained: "+key)
    if any(image.get("uri") and not image["uri"].startswith("data:")
           for image in data.get("images",[])):
        raise ValueError("Model contains an external image reference: "+key)
    blend_targets=sum(
        len(p.get("targets",[]))
        for mesh in data["meshes"]
        for p in mesh.get("primitives",[])
    )
    return {"mesh_count":len(data["meshes"]),"skeletons":len(data["skins"]),
            "animations":clips,"blend_target_sets":blend_targets,
            "has_lip_sync_blendshapes":False}

def run(output):
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    if len(CAST)!=15 or len(set(CAST.values()))!=15:
        raise ValueError("Fifteen uniquely sourced model files required")
    manifest={
        "status":"imported_distinct_cc0_characters_not_old_procedural",
        "license":"CC0-1.0",
        "artist":"Quaternius",
        "source_home":"https://quaternius.com/packs/cutemonsters",
        "source_mirror":"https://github.com/"+SOURCE_REPO,
        "source_mirror_revision":PINNED_COMMIT,
        "character_count":15,
        "characters":{},
        "visual_quality":"stylized game-ready; NOT feature-film-quality",
        "facial_status":"No per-phoneme lip-sync blend shapes verified",
        "canon_note":"Original story speaker keys and dialogue preserved; visual species replacement awaiting review.",
        "note":"Files downloaded, not sculpted/generated; source project on GitHub is publicly accessible.",
    }
    for key,source_model in CAST.items():
        relative=SOURCE_FOLDER+source_model+".gltf"
        quoted=urllib.parse.quote(relative,safe="/")
        url=f"https://raw.githubusercontent.com/{SOURCE_REPO}/{PINNED_COMMIT}/{quoted}"
        binary=fetch(url)
        try:
            parsed=json.loads(binary)
        except (UnicodeError,json.JSONDecodeError) as e:
            raise ValueError("Invalid GLTF JSON: "+key) from e
        evidence=inspect_model(parsed,key)
        file=output/(key+".gltf")
        file.write_bytes(binary)
        manifest["characters"][key]=dict(
            source_name=source_model,filename=file.name,source_path=relative,
            sha256=hashlib.sha256(binary).hexdigest(),bytes=len(binary),**evidence
        )
        print("REAL_IMPORTED_CC0_CHARACTER",key,source_model,len(binary),
              "skin=",evidence["skeletons"],"clips=",len(evidence["animations"]),flush=True)
    (output/"production_cast_manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("DISTINCT_CC0_CAST_READY models=15 original_procedural_models=0 no_render=true",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("output")
    args=p.parse_args()
    run(args.output)
