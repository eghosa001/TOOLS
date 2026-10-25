#!/usr/bin/env python3
"""Assemble actual professionally authored Blender Studio rigs for review.

Artist's original native rig masters remain untouched. This is a reuse library,
NOT automatic canon replacement, and never includes legacy Quaternius/KayKit or
procedural clay models. Each model identity is distinct (not a recolour).
"""
from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path

REAL_RIG_LIBRARY={
    "rain":"Blender Studio Rain (historical, via Packt)",
    "cat":"Blender Studio Pet Projects Cat",
    "dog":"Blender Studio Pet Projects Dog",
    "sprite":"Blender Studio Sprite Fright Sprite",
    "butterfly":"Blender Studio Sprite Fright Butterfly",
    "ladybug":"Blender Studio Sprite Fright Ladybug",
    "snail":"Blender Studio Sprite Fright Snail",
    "spider":"Blender Studio Sprite Fright Spider",
}
DOGWALK=("chocomel","pinda")
SINGULARITY=("critter","doublemohawk","multifrog","mantaribs","doubleeye","plumpfly","coralboi")
SOURCE_URLS={
    "dogwalk":"https://download.blender.org/demo/splash/blender-4.5-splash.blend",
    "singularity":"https://download.blender.org/demo/splash/blender-5.1-splash.blend",
}
REJECTED_WORDS=("quaternius","kaykit","_original_clay","_proposed_clay",
                "procedural_clay","low-poly","low_poly","prototype")
def checksum(path):
    with path.open("rb") as reader:
        return hashlib.file_digest(reader,"sha256").hexdigest()

def pack(eight,dogwalk,singularity,output):
    eight=Path(eight).resolve()
    dogwalk=Path(dogwalk).resolve()
    singularity=Path(singularity).resolve()
    output=Path(output).resolve()
    if output.exists():shutil.rmtree(output)
    output.mkdir(parents=True)
    registered={}
    # Original master library includes necessary licensed external material
    # files, Blender shader nodes, other 3D characters and texture support.
    m=json.loads((eight/"ASSET_PROVENANCE_AND_LIMITS.json").read_text())
    if m["count"]!=8 or len(m["models"])!=8:
        raise RuntimeError("Incorrect original high-quality master source package")
    native_master=output/"original-masters"
    shutil.copytree(eight,native_master,symlinks=False)
    for key in REAL_RIG_LIBRARY:
        meta=m["models"].get(key)
        if not meta:raise RuntimeError("Missing high-quality historical master "+key)
        relative=Path(meta["relative_file"])
        file=native_master/relative
        if not file.is_file() or file.stat().st_size<100000:
            raise RuntimeError("Original studio model is missing "+key)
        if checksum(file)!=meta["sha256"]:
            raise RuntimeError("Original Blender source rig changed unexpectedly "+key)
        registered[key]={"studio_source":meta["source"],"license":"CC BY 4.0",
               "artist":meta["artist"],"asset_file":str(Path("original-masters")/relative),
               "sha256":checksum(file),"asset_bytes":file.stat().st_size,
               "rig_and_geometry":"Original real Blender studio mesh, rig, and facial controls (unmodified)",
               "artist_material_status":"External textures included when published",
               "animation_test_status":"Not verified for new episode",
               "facial_speech_test_status":"Not verified",
               "approved_for_series_canon":False}
    for collection,keys,folder in (("dogwalk",DOGWALK,dogwalk),("singularity",SINGULARITY,singularity)):
        destination=output/collection
        destination.mkdir(exist_ok=True)
        for key in keys:
            original=folder/(key+"-native-studio.blend")
            still=folder/(key+"-actual-native-render.png")
            if not original.is_file() or original.stat().st_size<100000:
                print("MISSING_PUBLISHER_CHARACTER",collection,key,flush=True)
                continue
            if not still.is_file() or still.stat().st_size<15000:
                print("CHARACTER_WITH_NO_REAL_QUALITY_STILL_NOT_INCLUDED",collection,key,flush=True)
                continue
            target=destination/original.name
            shutil.copy2(original,target)
            shutil.copy2(still,destination/still.name)
            source_note=folder/(key+"-SOURCE_AND_QUALITY_STATUS.json")
            if source_note.is_file():
                shutil.copy2(source_note,destination/source_note.name)
            registered[key]={"studio_source":SOURCE_URLS[collection],
                 "license":"CC BY 4.0",
                 "artist":"Blender Studio; "+collection,
                 "asset_file":str(Path(collection)/original.name),
                 "preview_file":str(Path(collection)/still.name),
                 "sha256":checksum(target),"asset_bytes":target.stat().st_size,
                 "rig_and_geometry":"Real author-created Blender character",
                 "artist_material_status":"Native Blender original shader materials; GLB conversions rejected if white",
                 "animation_test_status":"Original rig present; must verify animation and acting independently",
                 "facial_speech_test_status":"Unverified; these supporting creatures may lack blend shape visemes",
                 "approved_for_series_canon":False}
    # Same artist, but every source *.blend and armature name is a distinct
    # character; no one source model is reused under multiple cast keys.
    if len(registered)<15:
        raise RuntimeError(f"Not 15 distinct genuine reusable authored rigs (found {len(registered)}); do not pad with clones")
    digests=[v["sha256"] for v in registered.values()]
    if len(set(digests))!=len(digests):
        raise RuntimeError("Same source model duplicated as a distinct actor")
    if any(any(reject in info["asset_file"].lower() for reject in REJECTED_WORDS)
           for info in registered.values()):
        raise RuntimeError("Rejected older low-detail models mistakenly included")
    result={"purpose":"Artist-made licensed authentic high-quality 3D character SOURCE inventory",
            "license":"CC BY commercial allowed with credit/attribution",
            "model_count":len(registered),
            "at_least_15_distinct_original_model_sources":len(registered)>=15,
            "models":registered,
            "visual_approval_status":"candidate; no user approval of final identity mapping",
            "canonical_character_keys_unchanged":True,
            "dialogue_text_unchanged":True,
            "actual_episode_video_rendered":False,
            "godot_compatibility":"Not every native Blender rig can retain high-quality shader nodes in GLB/Godot",
            "spoke_lip_sync_quality":"Not verified for all models",
            "quality_warning":"Faces, lip sync, actions, and consistent appearance must be approved before professional full-render"}
    (output/"PROFESSIONAL_REUSABLE_CAST_CANDIDATES.json").write_text(
       json.dumps(result,indent=2)+"\n")
    print("STUDIO_GENUINE_3D_CANDIDATE_LIBRARY_INVENTORY",len(registered),
          "licensed_artist_authored_native_blend_files=YES",
          "clay_models=0","canon_approved=false",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--eight",required=True)
    p.add_argument("--dogwalk",required=True)
    p.add_argument("--singularity",required=True)
    p.add_argument("--output",required=True)
    x=p.parse_args()
    pack(x.eight,x.dogwalk,x.singularity,x.output)
