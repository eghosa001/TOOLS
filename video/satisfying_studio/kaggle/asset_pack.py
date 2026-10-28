#!/usr/bin/env python3
"""Curated CC0 Poly Haven PBR/HDRI and real Foley packs for PRIVATE Kaggle assets.
No generative AI, no automatic sound-to-shot mapping. Fail if downloads fail.
"""
import hashlib, json, shutil, sys, zipfile
from pathlib import Path
from urllib.parse import urlparse
import requests

HDRI=("studio_small_09",)
TEXTURES=("dark_rock","metal_plate_02","granite_tile_04")
SOUNDS=(
 ("rubberduck_rpg","https://opengameart.org/sites/default/files/80-CC0-RPG-SFX_0.zip","https://opengameart.org/content/80-cc0-rpg-sfx","rubberduck"),
 ("kenney_rpg","https://opengameart.org/sites/default/files/RPGsounds_Kenney.zip","https://opengameart.org/content/50-rpg-sound-effects","Kenney"),
 ("rubberduck_creature","https://opengameart.org/sites/default/files/80-CC0-creature-SFX_0.zip","https://opengameart.org/content/80-cc0-creature-sfx","rubberduck"),
 ("rubberduck_water_slime","https://opengameart.org/sites/default/files/water-splash-slime-sfx.zip","https://opengameart.org/content/40-cc0-water-splash-slime-sfx","rubberduck"),
 ("rubberduck_wood_metal","https://opengameart.org/sites/default/files/100-CC0-wood-metal-SFX.zip","https://opengameart.org/content/100-cc0-metal-and-wood-sfx","rubberduck"),
 ("rubberduck_breaking_falling","https://opengameart.org/sites/default/files/sfx_breaking_and_falling.zip","https://opengameart.org/content/75-cc0-breaking-falling-hit-sfx","rubberduck")
)
HEADERS={"User-Agent":"SatisfyingStudio/1.1 (non-AI; Poly Haven API credited)"}
MAX_BYTES=80*1024*1024

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as file:
        for chunk in iter(lambda:file.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def entries(tree,keys=()):
    if isinstance(tree,dict):
        if isinstance(tree.get("url"),str):
            yield keys,tree["url"]
        else:
            for k,v in tree.items():yield from entries(v,keys+(str(k).lower(),))
    elif isinstance(tree,list):
        for i,v in enumerate(tree):yield from entries(v,keys+(str(i),))

def poly_files(slug,kind):
    r=requests.get("https://api.polyhaven.com/files/"+slug,headers=HEADERS,timeout=35)
    r.raise_for_status()
    files=list(entries(r.json()))
    for label in (("hdri",) if kind=="hdri" else ("diff","rough","nor_gl")):
        matches=[]
        for keys,url in files:
            p=urlparse(url)
            if p.scheme!="https" or p.hostname not in ("dl.polyhaven.org","cdn.polyhaven.com") or "1k" not in keys:
                continue
            valid=p.path.lower().endswith((".hdr",".exr")) if kind=="hdri" else (label in keys or (label=="diff" and "diffuse" in keys) or (label=="rough" and "roughness" in keys)) and p.path.lower().endswith((".jpg",".png"))
            if valid:matches.append(url)
        if matches:yield label,sorted(matches)[0]
        elif kind=="hdri" or label=="diff":raise RuntimeError("No verified Poly Haven file "+slug+" "+label)

def download(url,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_file() and path.stat().st_size>1024:return path.stat().st_size
    partial=path.with_name(path.name+".part")
    total=0
    try:
        with requests.get(url,headers=HEADERS,stream=True,timeout=(30,90)) as r:
            r.raise_for_status()
            with partial.open("wb") as f:
                for chunk in r.iter_content(chunk_size=256*1024):
                    if not chunk:continue
                    total+=len(chunk)
                    if total>MAX_BYTES:raise RuntimeError("Download exceeded allowed size: "+url)
                    f.write(chunk)
        if total<=1024:raise RuntimeError("Empty download "+url)
        partial.replace(path)
    finally:
        partial.unlink(missing_ok=True)
    return total

def build(output,scene_script):
    root=Path(output).resolve();root.mkdir(parents=True,exist_ok=True)
    ledger=[]
    for typ,slugs in (("hdri",HDRI),("texture",TEXTURES)):
        for slug in slugs:
            for label,url in poly_files(slug,typ):
                path=root/(slug+"_"+label+Path(urlparse(url).path).suffix)
                n=download(url,path)
                ledger.append({"name":path.name,"source":url,"bytes":n,"sha256":sha(path),
                  "license":"CC0","author":"Poly Haven contributors","type":typ,
                  "landing_page":"https://polyhaven.com/a/"+slug,"license_url":"https://polyhaven.com/license"})
                print("VERIFIED",path.name,n,flush=True)
    for slug,url,page,author in SOUNDS:
        path=root/(slug+".zip")
        n=download(url,path)
        if not zipfile.is_zipfile(path):raise RuntimeError("Invalid Foley ZIP "+str(path))
        with zipfile.ZipFile(path) as z:
            count=sum(i.filename.lower().endswith((".wav",".ogg",".flac",".mp3")) for i in z.infolist())
        if count<=0:raise RuntimeError("Foley pack contains no audio: "+str(path))
        ledger.append({"name":path.name,"source":url,"bytes":n,"sha256":sha(path),
            "license":"CC0","author":author,"type":"audio",
            "landing_page":page,"license_url":page,"sounds":count})
        print("VERIFIED FOLEY",path.name,count,flush=True)
    scene=Path(scene_script)
    if not scene.is_file():raise RuntimeError("Missing Blender source scene")
    shutil.copy2(scene,root/"build_blender_scene.py")
    (root/"ASSET_PROVENANCE.json").write_text(json.dumps(ledger,indent=2)+"\n")
    print("SUCCESS: STAGED",len(ledger),"individual downloads",flush=True)

if __name__=="__main__":
    if len(sys.argv)!=3:sys.exit("Usage: asset_pack.py DESTINATION SCENE_SCRIPT")
    build(sys.argv[1],sys.argv[2])
