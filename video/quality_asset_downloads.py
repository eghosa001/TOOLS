#!/usr/bin/env python3
"""Fetch small, real CC0 HDRI/PBR assets through the official Poly Haven API.

No hardcoded fake asset URLs, user tokens, unlicensed files or vendor source code.
Build-time only. The manifest is the cross-engine reference for Blender/Godot.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request

API = "https://api.polyhaven.com"
ALLOWED = {"api.polyhaven.com", "dl.polyhaven.org", "cdn.polyhaven.com"}
MAX_FILE=12_000_000
MAX_TOTAL=45_000_000
REQUEST_HEADERS={"User-Agent":"CartoonStudio-CC0-Material-Library/1.0","Accept":"application/json,*/*"}


def get(url, limit=MAX_FILE):
    parsed=urllib.parse.urlparse(url)
    if parsed.scheme!="https" or parsed.hostname not in ALLOWED:
        raise ValueError("Refused non-allowlisted external download host")
    request=urllib.request.Request(url,headers=REQUEST_HEADERS)
    with urllib.request.urlopen(request,timeout=100) as response:
        effective=urllib.parse.urlparse(response.geturl())
        if effective.scheme!="https" or effective.hostname not in ALLOWED:
            raise ValueError("Asset URL redirected to unapproved host")
        data=response.read(limit+1)
    if len(data)>limit:
        raise RuntimeError("Downloaded file exceeds 12 MB cap")
    return data


def api_json(path):
    data=get(API+path,limit=9_000_000)
    return json.loads(data)


def file_candidates(data,path=()):
    """Flatten /files/{slug} without assuming a fixed provider schema."""
    if isinstance(data,dict):
        if isinstance(data.get("url"),str):
            yield path,data
        else:
            for key,value in data.items():
                yield from file_candidates(value,path+(str(key).lower(),))
    elif isinstance(data,list):
        for index,value in enumerate(data):
            yield from file_candidates(value,path+(str(index),))


def pick(data,resolution,kind):
    candidates=[]
    for path,entry in file_candidates(data):
        url=entry.get("url","")
        label="/".join(path)
        filename=urllib.parse.urlparse(url).path.lower()
        if resolution not in label or not filename.endswith((".hdr",".jpg",".jpeg",".png",".exr")):
            continue
        if kind=="hdri":
            good=("hdri" in label or "hdr" in label) and filename.endswith(".hdr")
        elif kind=="color":
            good=any(t in label for t in ("diffuse","color","colour","_diff","basecolor","albedo"))
            good=good and filename.endswith((".jpg",".jpeg",".png"))
        elif kind=="normal":
            good=any(t in label for t in ("nor_gl","normalgl","normal","_nor"))
        elif kind=="roughness":
            good="rough" in label
        else:
            raise ValueError(kind)
        if not good:
            continue
        size=entry.get("size",0)
        if isinstance(size,(int,float)) and size>MAX_FILE:
            continue
        candidates.append((label,entry))
    candidates.sort(key=lambda p:(0 if "jpg" in p[0] else 1,p[0]))
    if not candidates:
        raise RuntimeError(f"No {resolution} {kind} file in Poly Haven API response: {list(data)[:8]}")
    return candidates[0][1]


def write_asset(output, manifest, slug, category, role, record):
    url=record["url"]
    filename=pathlib.Path(urllib.parse.urlparse(url).path).name
    filename=re.sub(r"[^A-Za-z0-9_.-]","_",filename)
    relative=pathlib.PurePosixPath(category)/slug/filename
    content=get(url)
    if len(content)<2048:
        raise RuntimeError("Asset suspiciously small: "+slug+" "+role)
    (output/relative).parent.mkdir(parents=True,exist_ok=True)
    (output/relative).write_bytes(content)
    item={"asset":slug,"role":role,"file":str(relative),"bytes":len(content),
          "sha256":hashlib.sha256(content).hexdigest(),"source_url":url,
          "page":"https://polyhaven.com/a/"+slug,"license":"CC0-1.0"}
    manifest["files"].append(item)
    print("QUALITY_CC0",slug,role,len(content),flush=True)
    return item


def select_textures(catalog):
    # Prioritize kid-friendly nature/ground materials; never choose a weapon prop.
    suggestions=[]
    for slug,meta in catalog.items():
        if not isinstance(meta,dict):
            continue
        tags=" ".join([slug,str(meta.get("name","")),
                       " ".join(str(t) for t in meta.get("categories",[]))]).lower()
        if any(term in tags for term in ("blood","rusty","graffiti","weapon","horror")):
            continue
        if any(term in tags for term in ("grass","forest_ground","meadow")):
            suggestions.append((0,slug))
        elif any(term in tags for term in ("wood","timber","planks")):
            suggestions.append((1,slug))
        elif any(term in tags for term in ("stone","pebbles","gravel","cobble")):
            suggestions.append((2,slug))
    suggestions.sort()
    return suggestions


def build(directory, resolution="1k"):
    output=pathlib.Path(directory).resolve()
    output.mkdir(parents=True,exist_ok=True)
    manifest={"schema":1,"provider":"Poly Haven","api":API,
              "api_credit":"Powered by Poly Haven — https://polyhaven.com",
              "license":"CC0-1.0","files":[],"materials":[],
              "note":"Resolution profile is chosen to fit Kaggle resource limits. PBR is not facial animation.", "resolution":resolution}
    hdri="studio_garden"
    record=pick(api_json("/files/"+hdri),resolution,"hdri")
    manifest["environment"]=write_asset(output,manifest,hdri,"hdris","lighting",record)["file"]
    catalog=api_json("/assets?t=textures")
    textures=[]
    seen_categories=set()
    for category,slug in select_textures(catalog):
        if category in seen_categories or len(textures)==3:
            continue
        try:
            data=api_json("/files/"+slug)
            maps={}
            for role in ("color","normal","roughness"):
                maps[role]=pick(data,resolution,role)
        except (RuntimeError,ValueError,KeyError):
            continue
        total=sum(int(v.get("size",0)) for v in maps.values())
        if total>MAX_FILE*2:
            continue
        seen_categories.add(category)
        textures.append((slug,maps))
    if len(textures)<2:
        raise RuntimeError("Unable to source at least two complete CC0 PBR materials from Poly Haven")
    for slug,maps in textures:
        row={"asset":slug,"page":"https://polyhaven.com/a/"+slug,"license":"CC0-1.0","maps":{}}
        for role,record in maps.items():
            entry=write_asset(output,manifest,slug,"materials",role,record)
            row["maps"][role]=entry["file"]
        manifest["materials"].append(row)
    if sum(row["bytes"] for row in manifest["files"])>MAX_TOTAL:
        raise RuntimeError("Total quality assets exceed size budget")
    (output/"quality_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    if not pathlib.Path(output/manifest["environment"]).is_file():
        raise RuntimeError("Missing HDRI")
    print("QUALITY_LIBRARY_READY",len(manifest["materials"]),
          "PBR materials;",len(manifest["files"]),"files",flush=True)
    return manifest


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    parser.add_argument("--resolution",choices=("1k","2k"),default="1k")
    args=parser.parse_args()
    build(args.output,args.resolution)
