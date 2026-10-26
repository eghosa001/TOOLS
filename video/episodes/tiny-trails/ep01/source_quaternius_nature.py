#!/usr/bin/env python3
"""Download and validate original CC0 Quaternius Nature MegaKit Standard bytes.

No model generation, render, repo binary commits or Kaggle calls.
The uploader (quaternius) posted this Standard edition under CC0 on
OpenGameArt: https://opengameart.org/content/stylized-nature-megakit
The free Standard ZIP contains ~68 models, not the full paid Source 116.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import stat
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

URL="https://opengameart.org/sites/default/files/stylized_nature_megakitstandard.zip"
SOURCE="https://opengameart.org/content/stylized-nature-megakit"
CREATOR="Quaternius"
MAX_DOWNLOAD=125_000_000
MAX_UNCOMPRESSED=2_000_000_000
EXTENSIONS={".glb",".gltf",".fbx",".obj",".png",".jpg",".jpeg",".webp",".mtl",".blend"}

def digest(path):
    sha=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for blob in iter(lambda:stream.read(1048576),b""):
            sha.update(blob)
    return sha.hexdigest()

def download(dest):
    dest=Path(dest)
    dest.parent.mkdir(parents=True,exist_ok=True)
    p=urllib.parse.urlparse(URL)
    if p.scheme!="https" or p.hostname!="opengameart.org":
        raise RuntimeError("Unapproved model download host")
    req=urllib.request.Request(URL,headers={
        "User-Agent":"Mozilla/5.0 CartoonStudio-Licensed-Assets/1.0"})
    with urllib.request.urlopen(req,timeout=120) as response, dest.open("wb") as output:
        actual=urllib.parse.urlparse(response.geturl())
        if actual.scheme!="https" or actual.hostname!="opengameart.org":
            raise RuntimeError("Unexpected download redirect")
        read=0
        while True:
            blob=response.read(1048576)
            if not blob:break
            read+=len(blob)
            if read>MAX_DOWNLOAD:
                raise RuntimeError("Unapproved download size")
            output.write(blob)
    if read<10_000_000:
        raise RuntimeError("Official asset archive unexpectedly small")
    return dest

def inspect(archive):
    archive=Path(archive)
    if archive.stat().st_size>MAX_DOWNLOAD:raise RuntimeError("ZIP exceeds file cap")
    with zipfile.ZipFile(archive) as zp:
        infos=zp.infolist()
        if len(infos)<25 or len(infos)>10000:
            raise RuntimeError("Unexpected archive entry count")
        count=0
        models=[]
        total=0
        for zi in infos:
            name=zi.filename.replace("\\","/")
            segments=Path(name).parts
            if zi.flag_bits&0x1 or not segments or name.startswith("/") or ".." in segments or "\x00" in name:
                raise RuntimeError("Unsafe ZIP member")
            if zi.is_dir():continue
            mode=(zi.external_attr>>16)
            if stat.S_ISLNK(mode):
                raise RuntimeError("Refuse symlink in external ZIP")
            total+=zi.file_size
            if zi.file_size>150_000_000 or total>MAX_UNCOMPRESSED:
                raise RuntimeError("ZIP decompression size cap exceeded")
            count+=1
            if Path(name).suffix.lower() in {".glb",".gltf",".fbx",".blend",".obj"}:
                models.append(name)
        if len(models)<20:
            raise RuntimeError("Pack has too few genuine 3D source models")
        broken=zp.testzip()
        if broken:
            raise RuntimeError("ZIP CRC failure for "+broken[:120])
    return {
        "publisher":CREATOR,"source":SOURCE,"archive_url":URL,
        "archive_sha256":digest(archive),
        "archive_bytes":archive.stat().st_size,
        "license":"CC0-1.0 (publisher upload)",
        "license_verified_by":"Publisher OpenGameArt listing",
        "variant":"free-standard-only",
        "full_paid_source_not_included":True,
        "zip_entries":count,"uncompressed_bytes":total,
        "3d_source_files":len(models),
        "model_names":models[:450],
        "raw_models_committed_to_public_repo":False,
        "import_into_existing_episode_verified":False,
        "characters_replaced":False,
        "preview_rendered":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--no-download",action="store_true")
    args=p.parse_args()
    if not args.no_download:
        download(args.archive)
    report=inspect(args.archive)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("EP01_STYLIZED_NATURE_CC0_REAL_3D_ARCHIVE_VERIFIED",
          report["3d_source_files"],"models",report["archive_bytes"],"bytes")
    print("EP01_PREVIEW_NOT_RENDERED_AND_ORIGINAL_STORY_UNTOUCHED")

if __name__=="__main__":
    main()
