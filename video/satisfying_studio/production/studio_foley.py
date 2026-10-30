#!/usr/bin/env python3
"""Reuse studio-owned CC0 Foley packs: shortlist and stage actual audio files.

User uploads: NONE. Reuses existing Kaggle / studio cache (no unnecessary
network traffic); if a pack is missing, report STUDIO ACQUISITION REQUIRED.
No filename/metadata search grants audio fidelity, matching or approval.
The editor/production agent must audition the files against the actual CGI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from studio_formats import get_format

# Verified publisher pages, not guessed raw download URLs.
PACKS={
 "rubberduck_water_slime.zip":{
    "source_url":"https://opengameart.org/content/40-cc0-water-splash-slime-sfx",
    "author":"rubberduck","license":"CC0","tags":["water","slime","bubble","splash","gel","wet"]},
 "rubberduck_wood_metal.zip":{
    "source_url":"https://opengameart.org/content/100-cc0-metal-and-wood-sfx",
    "author":"rubberduck","license":"CC0","tags":["wood","metal","cut","knife","crack","spring","tap","tool"]},
 "rubberduck_breaking_falling.zip":{
    "source_url":"https://opengameart.org/content/75-cc0-breaking-falling-hit-sfx",
    "author":"rubberduck","license":"CC0","tags":["fracture","break","crack","glass","hit","stone","impact"]},
 "kenney_rpg.zip":{
    "source_url":"https://kenney.nl/assets/rpg-audio",
    "author":"Kenney","license":"CC0","tags":["knife","wood","cloth","brush","metal","paper","contact"]},
}
AUDIO={".ogg",".wav",".flac",".mp3"}


def sha(buf: bytes) -> str:
    return hashlib.sha256(buf).hexdigest()


def candidates(cache: Path, format_id: str) -> list[dict]:
    fmt=get_format(format_id)
    tokens=set(re.findall(r"[a-z]{3,}",(fmt["material"]+" "+
                 fmt["action"]+" "+fmt["foley"]).lower()))
    semantic={
        "fracture":["crack","break","glass","hit","metal"],
        "deformation":["slime","splash","bubble","wet","rubber"],
        "particle-fluid":["water","slime","bubble","splash","rain"],
        "mechanical":["switch","spring","metal","wood","tap"],
        "transformation":["scrape","water","wood","metal"],
        "capture":["wood","metal","cloth","knife"],
        "sound-first":["wood","metal","cloth","tap","paper"],
        "ambient":["water","rain","wind","wood"],
        "performance":["cloth","paper","bubble"],
        "editorial":["water","wood","glass","paper"],
    }
    tokens.update(semantic[fmt["group"]])
    found=[]
    for basename,metadata in PACKS.items():
        archive=cache / basename
        if not archive.is_file():
            continue
        with zipfile.ZipFile(archive) as z:
            for entry in z.infolist():
                suffix=Path(entry.filename).suffix.lower()
                if entry.is_dir() or suffix not in AUDIO or entry.file_size<=0:
                    continue
                if entry.file_size>25_000_000:
                    continue  # avoid unexpectedly huge archives/memory
                stem=Path(entry.filename).stem.lower()
                name_tokens=set(re.findall(r"[a-z]{3,}",stem))
                score=len(tokens & name_tokens)*3+len(tokens & set(metadata["tags"]))
                if score<=0:
                    continue
                found.append({
                    "archive":basename,"entry":entry.filename,
                    "score_for_editor_shortlist_only":score,
                    "source_url":metadata["source_url"],
                    "license":metadata["license"],
                    "author":metadata["author"],
                    "matched_words":sorted(tokens & (name_tokens|set(metadata["tags"]))),
                    "auditioned":False,
                    "material_action_match":False,
                    "approved":False,
                })
    return sorted(found,key=lambda item:(-item["score_for_editor_shortlist_only"],
                       item["archive"],item["entry"]))


def stage(cache: Path, project: Path, format_id: str, limit=12) -> dict:
    if limit<1 or limit>48:
        raise ValueError("Choose 1–48 candidate files, not entire sound libraries")
    fmt=get_format(format_id)
    dest=project.resolve() / "recordings" / "studio_candidates"
    suggested=candidates(cache,format_id)[:limit]
    dest.mkdir(parents=True,exist_ok=True)
    log=[]
    for i,record in enumerate(suggested,1):
        with zipfile.ZipFile(cache / record["archive"]) as z:
            content=z.read(record["entry"])
        suffix=Path(record["entry"]).suffix.lower()
        name=f"candidate_{i:02d}_{sha(content)[:12]}{suffix}"
        target=dest / name
        if not target.exists():
            target.write_bytes(content)
        assert sha(target.read_bytes())==sha(content)
        log.append({
            "role":"foley",
            "file":str(target.relative_to(project.resolve())),
            "sha256":sha(content),
            "asset_owner":"studio",
            "license":record["license"],
            "source_url":record["source_url"],
            "author":record["author"],
            "pack":record["archive"],
            "pack_entry":record["entry"],
            "material":fmt["material"],
            "gesture":fmt["action"],
            "reviewed":False,
            "auditioned_against_picture":False,
            "artistic_approval":False,
            "note":"Candidate only; agent must actually listen and inspect CGI contact timing",
        })
    result={
        "format_id":format_id,"user_media_required":False,
        "studio_cache":str(cache),"candidates_staged":len(log),
        "missing_packs":[p for p in PACKS if not (cache/p).is_file()],
        "studio_owned_asset_inventory_candidates":log,
        "quality_status":"UNAPPROVED",
        "instructions":"Agent reviews each candidate against exact rendered CGI material, action and visible intensity; reject mismatch. Never auto-mark reviewed.",
    }
    (project/"foley_candidates_unapproved.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="command",required=True)
    for method in ("inventory","stage"):
        a=sub.add_parser(method)
        a.add_argument("format_id")
        a.add_argument("--cache",type=Path,default=Path(os.environ.get(
            "ASMR_ASSETS","/kaggle/input/satisfying-studio-cc0-asmr-v1")))
        if method=="stage":
            a.add_argument("--project",type=Path,required=True)
            a.add_argument("--limit",type=int,default=12)
    args=p.parse_args()
    try:
        if args.command=="inventory":
            result={"candidates":candidates(args.cache,args.format_id),
                    "missing_packs":[p for p in PACKS if not (args.cache/p).is_file()],
                    "user_media_required":False,"quality_status":"UNAPPROVED"}
        else:
            result=stage(args.cache,args.project,args.format_id,args.limit)
        print(json.dumps(result,indent=2))
        return 0
    except (OSError,zipfile.BadZipFile,ValueError) as exc:
        print("BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    sys.exit(main())
