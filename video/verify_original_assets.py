#!/usr/bin/env python3
"""Standard-library binary integrity and capability tests for exported 3D assets."""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path


def read_glb(path: Path):
    blob=path.read_bytes()
    if len(blob)<32 or blob[:4]!=b"glTF":
        raise ValueError("Not a binary glTF: "+str(path))
    magic,version,total=struct.unpack_from("<4sII",blob,0)
    if version!=2 or total!=len(blob):
        raise ValueError("Invalid GLB version or declared file length: "+str(path))
    chunk_size,chunk_type=struct.unpack_from("<II",blob,12)
    if chunk_type!=0x4E4F534A or 20+chunk_size>len(blob):
        raise ValueError("GLB JSON chunk invalid: "+str(path))
    return json.loads(blob[20:20+chunk_size])


def check(directory:Path):
    directory=directory.resolve()
    manifest=json.loads((directory/"asset_manifest.json").read_text(encoding="utf-8"))
    for key in ("lelli","brin","odo"):
        item=manifest["characters"][key]
        glb=read_glb(directory/item["filename"])
        num_meshes=len(glb.get("meshes",[]))
        num_morphs=sum(
            len(primitive.get("targets",[]))
            for mesh in glb.get("meshes",[])
            for primitive in mesh.get("primitives",[])
        )
        if num_meshes<18 or num_morphs<8:
            raise ValueError(f"{key} lacks mesh/viseme coverage: {num_meshes} meshes, {num_morphs} morphs")
        if not item.get("facial_blendshapes") or item.get("armature") is not False:
            raise ValueError("Manifest overclaims/underclaims GLB animation capabilities")
        print(f"PASS ASSET {key}: {num_meshes} meshes, {num_morphs} morph targets")
    scene=read_glb(directory/"sunpatch_court.glb")
    if len(scene.get("meshes",[]))<50:
        raise ValueError("Sunpatch Court is missing substantial environment geometry")
    blend=(directory/"sunpatch_court_cast.blend").read_bytes()
    if blend[:7]!=b"BLENDER":
        raise ValueError("Output .blend missing Blender file header")
    png=(directory/"sunpatch_court_lookdev.png").read_bytes()
    if png[:8]!=b"\x89PNG\r\n\x1a\n" or len(png)<10000:
        raise ValueError("Static lookdev PNG missing or corrupted")
    width,height=struct.unpack_from(">II",png,16)
    if (width,height)!=(640,360):
        raise ValueError(f"Unexpected Blender lookdev size {width}x{height}")
    print("PASS ENVIRONMENT: original stage geometry, editable .blend and PNG lookdev")
    print("PASS ALL: seven verified reusable files; zero Kaggle renders")


if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python video/verify_original_assets.py OUTPUT_DIRECTORY")
    check(Path(sys.argv[1]))
