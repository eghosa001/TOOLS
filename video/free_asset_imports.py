#!/usr/bin/env python3
"""Fetch original CC0 Kenney characters/environment for CartoonStudio.

Build-time download only, by explicit allowlisted HTTPS URLs. No Kaggle GPU.
Output is a compact ZIP with the rigged FBX, texture skins, .gltf environments,
and licence/source provenance. No site scraping, unlicensed random downloads,
or changes to the returning characters' appearance.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import pathlib
import re
import urllib.request
import zipfile

SOURCES = (
    dict(id="kenney_animated_1", category="rigged_character",
         url="https://opengameart.org/sites/default/files/kenney_animated-characters-1.zip",
         page="https://opengameart.org/content/animated-characters-1", license="CC0-1.0",
         max_bytes=3_000_000),
    dict(id="kenney_animated_2", category="rigged_character",
         url="https://opengameart.org/sites/default/files/kenney_animated-characters-2.zip",
         page="https://opengameart.org/content/animated-characters-2", license="CC0-1.0",
         max_bytes=3_000_000),
    dict(id="kenney_animated_3", category="rigged_character",
         url="https://opengameart.org/sites/default/files/kenney_animated-characters-3.zip",
         page="https://opengameart.org/content/animated-characters-3", license="CC0-1.0",
         max_bytes=3_000_000),
    dict(id="quaternius_animation_standard", category="animation_pack",
         url="https://opengameart.org/sites/default/files/universal_animation_librarystandard.zip",
         page="https://opengameart.org/content/universal-animation-library",
         license="CC0-1.0", max_bytes=18_000_000),
    dict(id="kenney_platformer_4", category="environment_prop",
         url="https://opengameart.org/sites/default/files/kenney_platformer-kit_4.1.zip",
         page="https://opengameart.org/content/platformer-kit-0", license="CC0-1.0",
         max_bytes=12_000_000),
)
MAX_ENTRIES = 2500
MAX_UNCOMPRESSED = 180_000_000


def download(source):
    request = urllib.request.Request(source["url"], headers={
        "User-Agent":"CartoonStudio-license-conscious-asset-builder/1.0",
        "Accept":"application/zip",
    })
    with urllib.request.urlopen(request, timeout=90) as response:
        result=response.read(source["max_bytes"] + 1)
    if len(result)>source["max_bytes"] or not zipfile.is_zipfile(io.BytesIO(result)):
        raise RuntimeError("Download exceeded safety limit or wasn't ZIP: "+source["id"])
    return result


def clean_name(name):
    item=pathlib.PurePosixPath(name.replace("\\","/"))
    if item.is_absolute() or ".." in item.parts or not item.parts:
        raise ValueError("Unsafe path in downloaded asset archive")
    if any(part.startswith(".") for part in item.parts):
        raise ValueError("Dotfiles not permitted in imported asset archives")
    return "/".join(item.parts)


def build(output, sources=SOURCES):
    manifest={"schema":1,"created_by":"CartoonStudio asset import workflow",
              "selection":"Deterministic per episode/speaker; never randomize established main cast",
              "sources":[],"assets":[]}
    output=pathlib.Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as destination:
        for entry in sources:
            raw=download(entry)
            digest=hashlib.sha256(raw).hexdigest()
            file_rows=[]
            with zipfile.ZipFile(io.BytesIO(raw)) as package:
                infos=package.infolist()
                if len(infos)>MAX_ENTRIES or sum(f.file_size for f in infos)>MAX_UNCOMPRESSED:
                    raise RuntimeError("Unexpectedly large archive contents: "+entry["id"])
                for info in infos:
                    if info.is_dir():
                        continue
                    original=clean_name(info.filename)
                    extension=pathlib.PurePosixPath(original).suffix.lower()
                    # Keep rig, idle/jump/run clips, skins, and glTF/GLB scenery.
                    valid={".fbx",".gltf",".glb",".bin",".png",".jpg",".jpeg",".txt",".md"}
                    if extension not in valid:
                        continue
                    if info.file_size>28_000_000:
                        continue
                    target="imports/"+entry["id"]+"/"+original
                    content=package.read(info)
                    destination.writestr(target,content)
                    file_rows.append((original,target,extension))
            if entry["category"]=="rigged_character":
                models=[row for row in file_rows if row[2]==".fbx"]
                if not models:
                    raise RuntimeError("No rigged FBX files in "+entry["id"])
                preferred=sorted(models,key=lambda row:(0 if "idle" in row[0].lower() else 1,
                              0 if "character" in row[0].lower() else 1,len(row[0])))
                safe_skins=[row for row in file_rows if row[2]==".png"
                            and "/skins/" in ("/"+row[0].lower())
                            and not any(term in row[0].lower() for term in ("zombie","criminal","cyborg"))]
                if not safe_skins:
                    raise RuntimeError("No child-friendly skin files available in "+entry["id"])
                chosen_skin=sorted(safe_skins,key=lambda row:(
                    0 if any(term in row[0].lower() for term in ("human","skater","survivor")) else 1,
                    row[0]))[0][1]
                asset={"id":entry["id"],"role":"background_character","file":preferred[0][1],
                       "skin":chosen_skin,
                       "source":entry["page"],"license":"CC0-1.0",
                       "file_count":len(models),
                       "motions":sorted({label for row in models for label in ("idle","jump","run")
                                         if label in row[0].lower()})}
                manifest["assets"].append(asset)
            elif entry["category"]=="animation_pack":
                motion_models=[row for row in file_rows if row[2] in (".fbx",".glb",".gltf")]
                if not motion_models:
                    raise RuntimeError("Quaternius animation pack lacks a supported animation model")
                preferred=sorted(motion_models,key=lambda row:(
                    0 if row[2]==".glb" else 1,
                    0 if "godot" in row[0].lower() else 1,len(row[0])))
                manifest["assets"].append({
                    "id":entry["id"],"role":"retarget_animation_library",
                    "file":preferred[0][1],"license":"CC0-1.0",
                    "source":entry["page"],"animation_files":len(motion_models),
                    "rig_compatibility":"Must retarget to a compatible humanoid skeleton; not plug-and-play for clay meshes",
                })
            else:
                environment=[row for row in file_rows if row[2] in (".gltf",".glb")]
                if not environment:
                    raise RuntimeError("No glTF scenery in "+entry["id"])
                allowed=("fence-","flag.","flowers","grass.","hedge","mushrooms",
                         "plant.","rocks.","stones.","tree","heart.","star.","sign.")
                safe=[(original,target) for original,target,_ in environment
                      if any(pathlib.PurePosixPath(original).name.lower().startswith(term)
                             for term in allowed)]
                if len(safe)<15:
                    raise RuntimeError("Not enough child-safe scenery in "+entry["id"])
                for original,target in sorted(safe):
                    asset={"id":entry["id"]+"_"+re.sub(r"[^a-z0-9]+","_",original.lower())[-60:],
                           "role":"environment_prop","file":target,
                           "source":entry["page"],"license":"CC0-1.0"}
                    manifest["assets"].append(asset)
            manifest["sources"].append({"id":entry["id"],"page":entry["page"],
                                         "download_url":entry["url"],"license":entry["license"],
                                         "archive_sha256":digest,"included_files":len(file_rows)})
            print("IMPORTED_CC0",entry["id"],"files=",len(file_rows),
                  "assets=",len(manifest["assets"]),"sha256=",digest,flush=True)
        destination.writestr("asset_manifest.json",json.dumps(manifest,indent=2)+"\n")
    if output.stat().st_size>55_000_000:
        raise RuntimeError("Prepared asset pack unexpectedly large for notebook distribution")
    print("FREE_ASSET_PACK_READY",str(output),output.stat().st_size,
          len(manifest["assets"]),"asset records",flush=True)
    return manifest


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    build(args.output)
