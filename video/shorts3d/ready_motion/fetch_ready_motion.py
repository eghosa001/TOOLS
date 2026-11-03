#!/usr/bin/env python3
"""Cache TWO rights-verified, already-animated humanoid packs on a cloud runner.

Do not alter models, create new motions, edit videos or claim scene quality.
Downloaded once; deliver as one archive through Drive for future shots.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

PACKS=[
 {"id":"kaykit_compatible_motion_1_2",
  "source_page":"https://opengameart.org/content/kaykit-character-animations",
  "download":"https://opengameart.org/sites/default/files/kaykit_character_animations_1.2.zip",
  "creator":"Kay Lousberg (KayKit)","license":"CC0-1.0",
  "compatible_with":"Existing KayKit rigged characters; official source says animations match all KayKit character packs",
  "role":"PRIMARY: walking, running, climbing, gestures and combat (free v1.2 snapshot)"},
 {"id":"quaternius_universal_motion_standard",
  "source_page":"https://opengameart.org/content/universal-animation-library",
  "download":"https://opengameart.org/sites/default/files/universal_animation_librarystandard.zip",
  "creator":"Quaternius","license":"CC0-1.0",
  "compatible_with":"Quaternius Universal Base rig; other rigs REQUIRE retargeting",
  "role":"SECONDARY: 45 clips in free Standard release (not paid 120+ library)"}
]

def sha256(path):
    s=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):s.update(b)
    return s.hexdigest()

def fetch(pack, out, cap=35_000_000):
    target=out/(pack["id"]+".zip")
    if not target.is_file():
        req=urllib.request.Request(pack["download"],headers={
            "User-Agent":"Mozilla/5.0 (Licensed-Asset-Cache/1.0)",
            "Accept":"application/zip,application/octet-stream,*/*"})
        temp=target.with_suffix(".download")
        with urllib.request.urlopen(req,timeout=90) as source,open(temp,"wb") as f:
            total=0
            while chunk:=source.read(1024*1024):
                total+=len(chunk)
                if total>cap:raise RuntimeError("File cap exceeded")
                f.write(chunk)
        temp.rename(target)
    if target.stat().st_size<1024:raise RuntimeError("Missing or tiny file: "+str(target))
    with zipfile.ZipFile(target) as archive:
        members=archive.infolist()
        if len(members)>7000:raise ValueError("Unreasonably large ZIP member count")
        total_size=sum(m.file_size for m in members)
        if total_size>800_000_000:raise ValueError("Unreasonably large expanded ZIP")
        for m in members:
            if m.filename.startswith("/") or ".." in Path(m.filename).parts:
                raise ValueError("Unsafe archive path: "+m.filename)
        corrupt=archive.testzip()
        if corrupt:raise ValueError("Corrupt archive member: "+corrupt)
        filenames=[m.filename for m in members if not m.is_dir()]
        animation_candidates=[x for x in filenames if x.lower().endswith((".gltf",".glb",".fbx",".blend"))]
        if not animation_candidates:raise ValueError("No animation-capable 3D files found")
        gltf_clips={}
        for name in filenames:
            if name.lower().endswith(".gltf"):
                try:
                    gltf=json.loads(archive.read(name).decode("utf8"))
                    clips=[c.get("name","<unnamed>") for c in gltf.get("animations",[])]
                    if clips:gltf_clips[name]=clips
                except (ValueError,UnicodeError):pass
    record={**pack,"downloaded_bytes":target.stat().st_size,
           "archive_sha256":sha256(target),"zip_members":len(filenames),
           "rigged_file_count":len(animation_candidates),
           "formats":sorted({Path(f).suffix.lower() for f in animation_candidates}),
           "gltf_animation_clip_count":sum(len(v) for v in gltf_clips.values()),
           "sample_gltf_clips":{n:clips[:12] for n,clips in list(gltf_clips.items())[:5]},
           "first_file_paths":animation_candidates[:16],
           "archive_file":target.name}
    return record

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--output",default="artifacts/shorts3d-ready-motion")
    args=a.parse_args()
    out=Path(args.output)
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    for pack in PACKS:
        result=fetch(pack,out)
        print("MOTION_PACK_READY",pack["id"],result["downloaded_bytes"],"bytes,",
            result["rigged_file_count"],"animated-format members",flush=True)
        records.append(result)
    (out/"MOTION_ASSET_MANIFEST.json").write_text(json.dumps({
        "packs":records,"commercial_use":True,"licenses":["CC0-1.0"],
        "status":"archive_verified_not_yet_retarged_or_rendered",
        "critical_rules":[
            "Never claim a clip plays on a character until Godot validates matching rig and track paths",
            "Do not blend incompatible KayKit and Quaternius rigs without a tested retarget",
            "Use entire already-built environment; preserve actors, lights and cameras between scenes",
            "No per-video model generation, asset creation or re-downloading",
            "Editor must direct each scene and review actual motion and audio before delivery",
            "Only preapproved source models; CC0 does not guarantee artistic quality"
        ]
    },indent=2)+"\n",encoding="utf-8")
    print("TWO_PACK_DOWNLOAD_COMPLETE",sum(r["downloaded_bytes"] for r in records),flush=True)
if __name__=="__main__":main()
