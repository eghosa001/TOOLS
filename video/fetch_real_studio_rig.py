#!/usr/bin/env python3
"""Pin and import an independently published real Blender Studio Rain rig.

Rain v2.6 is a historical fallback. Current Rain v3 and Snow v4 must be
downloaded from Blender Studio's own free download controls. Never rename an
older version as the newer rig, or substitute low-poly stock placeholders.
Do not commit copied binaries to the public TOOLS repository.
"""
import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

UPSTREAM_REPO="PacktPublishing/Realizing-3D-Animation-in-Blender"
UPSTREAM_REF="main"
UPSTREAM_FILENAME="rain_v2_6_packt.zip"
GH_BLOB_SHA1="4c411879a92f62df764defaaffb2578d946840b6"
UPSTREAM_URL="https://raw.githubusercontent.com/"+UPSTREAM_REPO+"/"+UPSTREAM_REF+"/"+UPSTREAM_FILENAME
MAX_TOTAL=250_000_000
MAX_ENTRY=130_000_000

def get_zip(output):
    target=Path(output)
    target.mkdir(parents=True,exist_ok=True)
    cache=target/UPSTREAM_FILENAME
    request=urllib.request.Request(UPSTREAM_URL,headers={"User-Agent":"CartoonStudio-HQ-Rain-audit"})
    with urllib.request.urlopen(request,timeout=100) as response,cache.open("wb") as file:
        count=0
        while True:
            b=response.read(1024*1024)
            if not b:break
            count+=len(b)
            if count>40_000_000: raise RuntimeError("Unexpected large source download")
            file.write(b)
    raw=cache.read_bytes()
    gh_sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if gh_sha!=GH_BLOB_SHA1:
        raise RuntimeError("Refusing changed/unauthenticated source archive")
    blend_files=[]
    with zipfile.ZipFile(cache) as z:
        entries=z.infolist()
        if len(entries)>500: raise ValueError("Unsafe archive file count")
        if sum(info.file_size for info in entries)>MAX_TOTAL:
            raise ValueError("Unsafe archive expanded size")
        for entry in entries:
            p=PurePosixPath(entry.filename.replace("\\","/"))
            if p.is_absolute() or ".." in p.parts or entry.file_size>MAX_ENTRY:
                raise ValueError("Unsafe archive entry")
            if entry.is_dir():continue
            dest=target/"source"/Path(*p.parts)
            dest.parent.mkdir(parents=True,exist_ok=True)
            with z.open(entry) as i,dest.open("wb") as out:
                shutil.copyfileobj(i,out,1024*1024)
            if dest.suffix.lower()==".blend":
                blend_files.append(dest)
    if len(blend_files)!=1:
        raise RuntimeError("Expected exactly one Blender Rain production rig, found "+str(blend_files))
    model=blend_files[0]
    first=model.open("rb").read(96)
    print("ARCHIVE_RIG_FILE_EVIDENCE",model.name,"bytes=",model.stat().st_size,"header=",repr(first[:96]),flush=True)
    if first[:7]!=b"BLENDER" and first[:4] not in (b"\x28\xb5\x2f\xfd",b"\x1f\x8b\x08\x00"):
        raise RuntimeError("Downloaded .blend file has neither Blender nor supported compressed-Blender header")
    manifest={"asset":"Blender Studio Rain historical v2.6, education archive",
              "label":"RAIN_HISTORICAL_NOT_CURRENT_V3",
              "published_by":"Blender Foundation / Studio; redistributed by Packt",
              "model_license":"CC BY 4.0 attribution required",
              "publisher_source":"https://studio.blender.org/characters/rain/v3/",
              "archive_source":UPSTREAM_URL,"archive_github_sha1":gh_sha,
              "archive_sha256":hashlib.sha256(raw).hexdigest(),
              "model_file":str(model.relative_to(target)),
              "asset_status":"UNVERIFIED_UNTIL_BLENDER_AUDIT",
              "canonical_hero_replacement":False,
              "episode_render":False}
    (target/"IMPORT_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("PACKT_RAIN_RIG_FETCHED",model.name,"archive_sha256",manifest["archive_sha256"],flush=True)
    return model

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    p.add_argument("--env-file")
    x=p.parse_args()
    model=get_zip(x.output)
    if x.env_file:
        with open(x.env_file,"a",encoding="utf-8") as out:
            out.write("RAIN_MODEL="+str(model.resolve())+"\n")
