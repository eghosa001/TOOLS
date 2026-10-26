#!/usr/bin/env python3
"""Mount the THREE already exported canonical CartoonStudio GLBs safely.

Reads real asset manifest from verified GitHub artifact ZIP extraction. Creates
character_files.json for the CURRENT Kaggle notebook when requested, without
mutating the canonical story or rendering any episode.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROLES=("lelli","brin","odo")
def sha(p):
    with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()

def make_map(asset_dir,output,story=None):
    asset_dir=Path(asset_dir).expanduser().resolve()
    record=asset_dir/"EXISTING-CANON-CAST-PACKAGE-EVIDENCE.json"
    if not record.is_file():raise FileNotFoundError("Extract the full successful 3-character GitHub artifact, not just a GLB")
    manifest=json.loads(record.read_text(encoding="utf-8"))
    if manifest.get("unchanged_dialogue_entries")!=74 or set(manifest.get("cast",{}))!=set(ROLES):
        raise RuntimeError("Asset pack does not refer to the unchanged canonical three-actor story")
    if story:
        path=Path(story)
        if sha(path)!=manifest["unchanged_story_sha256"]:
            raise RuntimeError("CANNOT_MOUNT_CROSS_EPISODE_ASSETS: original dialogue/story bytes differ")
    mapping={}
    for role in ROLES:
        item=manifest["cast"][role]
        file=(asset_dir/item["source_filename"]).resolve()
        if asset_dir not in file.parents or file.suffix.lower()!=".glb":
            raise RuntimeError("Unsafe original character relative path")
        if not file.is_file() or file.stat().st_size<30000:
            raise FileNotFoundError("Real canonical actor GLB missing for "+role)
        if sha(file)!=item["sha256"]:
            raise RuntimeError("CANON_ASSET_BINARY_MISMATCH "+role)
        mapping[role]=str(file)
    output=Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(mapping,indent=2)+"\n")
    print("EXACT_THREE_CANON_ASSET_PATHS_MOUNTED",json.dumps(mapping))
    print("CANON_STORY_OR_ASSET_SOURCE_UNCHANGED; NO_RENDER_TRIGGERED")
    return mapping

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--asset-dir",required=True,type=Path)
    p.add_argument("--output",default="/kaggle/working/character_files.json",type=Path)
    p.add_argument("--story",type=Path)
    a=p.parse_args()
    make_map(a.asset_dir,a.output,a.story)

if __name__=="__main__":
    main()
