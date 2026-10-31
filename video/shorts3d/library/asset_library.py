#!/usr/bin/env python3
"""Browsable CC0/notice-aware 3D Shorts asset library. Imports originals, never makes models.

Repository indexes pin each original Git blob's SHA1; downloaded data must match.
No image-to-narration auto-selection. Models are *candidates* until a director approves a shot.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, os, re, shutil, sys, zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parent
INDEX=ROOT/'library'
KENNEY="https://raw.githubusercontent.com/Hidencod/tge-assets/"
FORGE="https://raw.githubusercontent.com/npmiaman/game-forge/"
CC0="https://creativecommons.org/publicdomain/zero/1.0/"
LICENSE_ROCKETBOX="https://raw.githubusercontent.com/npmiaman/game-forge/2b25427358dbfb6badd47f658ba71a6de748e548/assets/models/rocketbox/LICENSE.md"
PACK_GENRES={
 "medieval": ["kenney:castle-kit","kenney:pirate-kit","kenney:graveyard-kit","forge:models/kaykit-medieval-hexagon","forge:models/kaykit-adventurers","forge:models/kaykit-dungeon-remastered","forge:models/fantasy-town-kit"],
 "city": ["kenney:city-kit-commercial","kenney:city-kit-roads","kenney:city-kit-suburban","kenney:car-kit","forge:models/kaykit-city-builder"],
 "nature": ["kenney:nature-kit","kenney:cube-pets","forge:models/kaykit-prototype-bits"],
 "space": ["kenney:space-kit","kenney:blaster-kit","forge:models/kaykit-space-base"],
 "horror": ["kenney:graveyard-kit","kenney:mini-dungeon","forge:models/kaykit-halloween-bits","forge:models/kaykit-skeletons"],
 "interiors": ["kenney:furniture-kit","kenney:food-kit","forge:models/kaykit-city-builder"],
 "action": ["kenney:tower-defense-kit","kenney:platformer-kit","forge:models/kaykit-adventurers"],
 "realism": ["forge:models/polyhaven"],
 "audio": ["forge:sounds/impact-sounds","forge:sounds/rpg-audio","forge:sounds/interface-sounds","forge:sounds/sci-fi-sounds","forge:sounds/music-jingles"],
 "lighting": ["forge:hdri"],
}

def slug(value: str) -> str:
    return re.sub(r'[^a-z0-9_-]','_',value.lower())

def _source_for_forge(path):
    rest=path.removeprefix("assets/")
    parts=rest.split("/")
    group=parts[1] if len(parts)>1 else ''
    if rest.startswith("models/rocketbox/"):
        return "https://github.com/microsoft/Microsoft-Rocketbox","MIT","notice-required"
    if rest.startswith("models/polyhaven/"):
        return "https://polyhaven.com/a/"+Path(rest).stem,"CC0-1.0",""
    if rest.startswith("models/kaykit-"):
        return "https://github.com/KayKit-Game-Assets", "CC0-1.0", ""
    if rest.startswith("models/quaternius-ual/"):
        return "https://opengameart.org/content/universal-animation-library","CC0-1.0",""
    if rest.startswith("models/"):
        return "https://kenney.nl/assets/"+group,"CC0-1.0",""
    if rest.startswith("sounds/"):
        return "https://kenney.nl/assets/"+group,"CC0-1.0",""
    if rest.startswith("hdri/"):
        return "https://polyhaven.com/a/"+Path(rest).stem,"CC0-1.0",""
    if rest.startswith("textures/"):
        return "https://ambientcg.com/view?id="+group,"CC0-1.0",""
    raise ValueError("Unregistered provider path "+path)

def catalog():
    k=json.loads((INDEX/'kenney_3d_index.json').read_text())
    f=json.loads((INDEX/'extended_free_index.json').read_text())
    result={}
    for path,size,blobsha in k["entries"]:
        pack,name=Path(path).parts[1],Path(path).name
        ident="kenney__"+slug(pack)+"__"+slug(Path(name).stem)
        url=KENNEY+k["source"]["revision"]+"/"+path
        result[ident]={"id":ident,"provider":"kenney","pack":pack,"kind":"model","path":path,
           "size":size,"blob_sha":blobsha,"url":url,"license":"CC0-1.0","license_url":CC0,
           "source_url":"https://kenney.nl/assets/"+pack}
    for path,size,blobsha in f["entries"]:
        rel=path.removeprefix("assets/")
        key=Path(rel)
        provider_pack=key.parent.as_posix()
        ident="forge__"+slug(provider_pack.replace("/", "__"))+"__"+slug(key.stem)
        ext=key.suffix.lower()
        kind=("model" if ext==".glb" else "hdr" if ext==".hdr" else "audio" if ext in (".wav",".ogg",".mp3") else "texture")
        source,license_name,notice=_source_for_forge(path)
        result[ident]={"id":ident,"provider":"forge","pack":provider_pack,"kind":kind,"path":path,
            "size":size,"blob_sha":blobsha,"url":FORGE+f["source"]["revision"]+"/"+path,
            "source_url":source,"license":license_name,
            "license_url":("https://opensource.org/licenses/MIT" if notice else CC0),
            "notice_required":bool(notice)}
    return result

def chosen(items,ids=(),packs=(),genres=(),kinds=(),query=None,allow_mit=False):
    for genre in genres:
        if genre not in PACK_GENRES:raise ValueError("Unknown genre "+genre)
    chosen_packs=list(packs)+[p for genre in genres for p in PACK_GENRES[genre]]
    for p in chosen_packs:
        if not re.fullmatch(r'(kenney|forge):[a-zA-Z0-9/_-]+',p):raise ValueError("Invalid pack "+p)
    if ids:
        unknown=set(ids)-set(items)
        if unknown:raise ValueError("Unknown asset IDs: "+str(sorted(unknown)[:6]))
    selection=[]
    for key,item in items.items():
        if key in ids or any(item["provider"]+":"+item["pack"]==p for p in chosen_packs):
            if kinds and item["kind"] not in kinds:continue
            if query and query.lower() not in key.lower():continue
            if item["license"]=="MIT" and not allow_mit:continue
            selection.append(item)
    return selection

def git_blob_sha(content:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(content)).encode()+b"\\0"+content).hexdigest()

def validate_media(data:bytes,item):
    if len(data)!=item["size"]:raise ValueError("size mismatch")
    if git_blob_sha(data)!=item["blob_sha"]:raise ValueError("upstream blob SHA mismatch")
    ext=Path(item["path"]).suffix.lower()
    if ext==".glb":
        if len(data)<20 or data[:4]!=b"glTF" or int.from_bytes(data[4:8],"little")!=2 or int.from_bytes(data[8:12],"little")!=len(data):
            raise ValueError("invalid binary glTF")
    elif ext==".hdr" and not (data.startswith(b"#?RADIANCE") or data.startswith(b"#?RGBE")):
        raise ValueError("invalid HDRI")
    elif ext==".png" and not data.startswith(bytes.fromhex("89504e470d0a1a0a")):
        raise ValueError("invalid PNG")
    elif ext in (".jpg",".jpeg") and not data.startswith(bytes.fromhex("ffd8ff")):
        raise ValueError("invalid JPEG")
    elif ext==".wav" and not (data.startswith(b"RIFF") and data[8:12]==b"WAVE"):
        raise ValueError("invalid WAV")
    elif ext==".ogg" and not data.startswith(b"OggS"):
        raise ValueError("invalid Ogg")
    elif ext==".mp3" and not (data.startswith(b"ID3") or data[:1]==b"\\xff"):
        raise ValueError("invalid MP3")

def write_one(item,root,max_file_bytes):
    if item["size"]>max_file_bytes:raise ValueError("single file beyond download cap")
    if urlparse(item["url"]).hostname!="raw.githubusercontent.com":
        raise ValueError("unsafe download host")
    suffix=Path(item["path"]).suffix.lower()
    folder=root/("models" if item["kind"]=="model" else item["kind"])
    folder.mkdir(parents=True,exist_ok=True)
    output=folder/(item["id"]+suffix)
    data=output.read_bytes() if output.exists() else None
    if data is None:
        req=Request(item["url"],headers={"User-Agent":"TOOLS-3D-Shorts-Asset-Importer/2026.10"})
        with urlopen(req,timeout=65) as response:data=response.read(max_file_bytes+1)
    validate_media(data,item)
    if not output.exists():
        temp=output.with_suffix(output.suffix+".part")
        temp.write_bytes(data)
        temp.replace(output)
    return {"id":item["id"],"kind":item["kind"],"path":str(output.relative_to(root)),
            "sha256":hashlib.sha256(data).hexdigest(),"size":len(data),
            "url":item["url"],"source_url":item["source_url"],"license":item["license"],
            "license_url":item["license_url"],"human_approved_for_shot":False}

def import_assets(selection,root,max_mb=400,max_file_mb=60,workers=10):
    if not selection:raise ValueError("No matching assets; choose exact IDs or packs")
    total=sum(x["size"] for x in selection)
    if total>max_mb*1048576:raise ValueError(f"Selected {total/1048576:.1f} MB exceeds {max_mb} MB cloud cap; split into packs")
    results,errors=[],[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(workers,12))) as pool:
        running={pool.submit(write_one,item,root,max_file_mb*1048576):item["id"] for item in selection}
        for future in concurrent.futures.as_completed(running):
            try:results.append(future.result())
            except Exception as exc:errors.append({"id":running[future],"error":str(exc)})
    if any(row["license"]=="MIT" for row in results):
        # Full original MIT notice from the source mirror, checked into same artifact.
        notice_path=root/"LICENSE-Microsoft-Rocketbox-MIT.txt"
        with urlopen(Request(LICENSE_ROCKETBOX,headers={"User-Agent":"TOOLS-Shorts3D/1.0"}),timeout=40) as r:
            license_text=r.read(16_384).decode("utf8")
        if not license_text.startswith("MIT License") or "Copyright (c) 2020 Microsoft" not in license_text:
            raise ValueError("MIT license notice cannot be verified")
        notice_path.write_text(license_text)
    results.sort(key=lambda x:x["id"])
    output={"summary":{"selected":len(selection),"verified":len(results),"failed":len(errors),
                       "bytes":sum(x["size"] for x in results)},
             "original_files_only":True,"source_license_checks_required_for_release":True,
             "assets":results,"errors":errors}
    root.mkdir(parents=True,exist_ok=True)
    (root/"provenance-expanded.json").write_text(json.dumps(output,indent=2)+"\n")
    if errors:raise RuntimeError(f"{len(errors)} source downloads/validations failed; see provenance-expanded.json")
    return output

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--search",help="Filter candidate names in manifest; no media download")
    p.add_argument("--list-packs",action="store_true")
    p.add_argument("--genres",nargs="+",default=[])
    p.add_argument("--packs",nargs="+",default=[])
    p.add_argument("--ids",nargs="+",default=[])
    p.add_argument("--kinds",nargs="+",choices=["model","audio","hdr","texture"])
    p.add_argument("--output",type=Path,default=ROOT/"library"/"imported")
    p.add_argument("--max-mb",type=int,default=400)
    p.add_argument("--max-file-mb",type=int,default=60)
    p.add_argument("--workers",type=int,default=10)
    p.add_argument("--allow-mit",action="store_true",help="Include Rocketbox only with its full MIT notice")
    p.add_argument("--download",action="store_true",help="Explicit confirmation to download selected originals")
    a=p.parse_args()
    items=catalog()
    if a.list_packs:
        from collections import Counter
        print(json.dumps(dict(sorted(Counter(x["provider"]+":"+x["pack"] for x in items.values()).items())),indent=2))
        return
    if a.search and not (a.packs or a.genres or a.ids):
        matches=[x for x in items.values() if a.search.lower() in x["id"].lower()]
    else:matches=chosen(items,a.ids,a.packs,a.genres,a.kinds,a.search,a.allow_mit)
    total=sum(x["size"] for x in matches)
    print(json.dumps({"indexed":len(items),"selected":len(matches),"estimated_mb":round(total/1048576,2),
       "sample":[{"id":x["id"],"mb":round(x["size"]/1048576,2),"license":x["license"],"source":x["source_url"]} for x in matches[:20]],
       "download_requested":a.download},indent=2))
    if a.download:import_assets(matches,a.output,a.max_mb,a.max_file_mb,a.workers)

if __name__=="__main__":main()
