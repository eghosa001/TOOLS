#!/usr/bin/env python3
"""Validate real Blender-generated proposed-cast GLBs; reject capability overclaims."""
import json
import sys
from pathlib import Path
from verify_original_assets import read_glb


def validate(path):
    path=Path(path)
    data=json.loads((path/"proposed_cast_manifest.json").read_text(encoding="utf-8"))
    source=json.loads((path/"proposed_cast.json").read_text(encoding="utf-8"))
    if source.get("status")!="proposed_not_canon" or len(source.get("candidates",[]))!=12:
        raise ValueError("Exported cast registry is missing or claims approval")
    if any(row.get("approved") for row in source["candidates"]):
        raise ValueError("Unexpectedly promoted supporting cast to canon")
    if data.get("status")!="proposed_not_canon" or data.get("count")!=12:
        raise ValueError("Approval state or candidate count incorrect")
    if set(data.get("existing_protected",[]))!={"lelli","brin","odo"}:
        raise ValueError("Existing heroes were not protected")
    if data.get("story_modified") or data.get("kaggle_render"):
        raise ValueError("Unexpected story/render claim")
    files=data.get("characters",{})
    if len(files)!=12:
        raise ValueError("Twelve independently exported characters expected")
    for key,entry in files.items():
        if entry.get("canon") or entry.get("skeletal_rig"):
            raise ValueError("Unsupported canon or rig claim for "+key)
        model=read_glb(path/entry["filename"])
        meshes=model.get("meshes",[])
        morphs=sum(len(primitive.get("targets",[])) for mesh in meshes for primitive in mesh.get("primitives",[]))
        if len(meshes)<18 or morphs<8:
            raise ValueError("Missing model detail or morphs for "+key)
    preview=(path/"proposed_cast_contact_sheet.png").read_bytes()
    if not preview.startswith(b"\x89PNG\r\n\x1a\n") or len(preview)<3000:
        raise ValueError("Character gallery image missing or invalid")
    print("PASS 12 exported GLBs + facial target meshes + gallery; proposals are not canon")


if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: verify_expanded_cast.py ARTIFACT_DIR")
    validate(sys.argv[1])
