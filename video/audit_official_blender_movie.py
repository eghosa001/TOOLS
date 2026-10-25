#!/usr/bin/env python3
"""Safely ingest official Blender Studio splash/shot ZIP, audit actual .blend files.

Do not accept screenshots or a render scene as proof of reusable cast rigs.
Source: first party https://download.blender.org/demo/ assets. Outputs audit
report and original art provenance; does not generate or change character art.
"""
import argparse,json,hashlib,re,shutil,urllib.request,zipfile,sys
from pathlib import Path,PurePosixPath

SOURCES={
"sprite-fright-shot":"https://download.blender.org/demo/sprite_fright_030_0020_A.zip",
"pet-projects-splash":"https://download.blender.org/demo/splash/blender-3.6-splash.zip",
}
def import_archive(key,dest):
    dest=Path(dest).resolve()
    dest.mkdir(parents=True,exist_ok=True)
    url=SOURCES[key]
    target=dest/(key+".zip")
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"CartoonStudio-CCBY-study/1.0"}),timeout=180) as io,target.open("wb") as out:
        total=0
        while True:
            chunk=io.read(1<<20)
            if not chunk:break
            total+=len(chunk)
            if total>320_000_000:raise ValueError("Source over 320 MB cap")
            out.write(chunk)
    if not zipfile.is_zipfile(target):raise ValueError("Official file is not a ZIP")
    files=[]
    with zipfile.ZipFile(target) as z:
        members=z.infolist()
        if len(members)>3000 or sum(m.file_size for m in members)>2_000_000_000:
            raise ValueError("Archive unsafe size/file count")
        for info in members:
            p=PurePosixPath(info.filename.replace("\\","/"))
            if p.is_absolute() or ".." in p.parts:
                raise ValueError("Unsafe zip member path")
            if info.is_dir():continue
            if info.file_size>700_000_000:
                raise ValueError("Oversized member")
            relative=Path(*p.parts)
            if relative.suffix.lower() not in (".blend",".png",".jpg",".jpeg",".exr",".txt",".md",".json",".webp",".hdr",".tif",".tiff",".tga",".bmp",".tx"):
                continue
            dst=dest/"source"/relative
            dst.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as i,dst.open("wb") as o:
                shutil.copyfileobj(i,o,1<<20)
            if dst.suffix.lower()==".blend":
                files.append({"filename":str(dst),"size":dst.stat().st_size})
    if not files:
        raise RuntimeError("Official movie archive has no real Blender scene")
    record={"download_url":url,"publisher":"Blender Studio / blender.org",
            "license":"CC-BY (verify credits per individual asset)",
            "archive_sha256":hashlib.file_digest(target.open("rb"),"sha256").hexdigest(),
            "archive_bytes":target.stat().st_size,
            "blender_scenes":files,"purpose":"audit original studio files for separable reusable cast",
            "status":"not a production-ready rig until detailed inspection passes"}
    (dest/"OFFICIAL_SOURCE.json").write_text(json.dumps(record,indent=2)+"\n")
    print("OFFICIAL_STUDIO_SCENE_INGESTED",key,"blend_count",len(files),
          "bytes",record["archive_bytes"],flush=True)
    for file in files:
        print("OFFICIAL_BLENDER_FILE",file["filename"],file["size"],flush=True)
    return files

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("source_key",choices=tuple(SOURCES))
    p.add_argument("output")
    args=p.parse_args()
    import_archive(args.source_key,args.output)
