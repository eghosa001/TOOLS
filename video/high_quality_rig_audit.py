#!/usr/bin/env python3
"""Audit genuine artist-authored Blender Studio rigs without regenerating geometry.

Safe: no Kaggle runs, no canonical changes, no Blender render of an episode.
External .blend files are opened with Blender --disable-autoexec; their Python
custom UI scripts are not executed by this audit.
"""
import json
import sys
from pathlib import Path

try:
    import bpy
except ImportError:
    raise SystemExit("Run with Blender --background --disable-autoexec --python video/high_quality_rig_audit.py -- INPUT REPORT")

def main(inp,out):
    source=Path(inp)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(source.resolve()),load_ui=False)
    count={"source_file":str(source.name),"source_bytes":source.stat().st_size,
           "mesh_objects":0,"faces":0,"armatures":0,"pose_bones":0,
           "material_slots":0,"shape_keys":0,"face_like_keys":[],
           "cameras":len(bpy.data.cameras),
           "actions":len(bpy.data.actions),
           "missing_external_images":[],
           "packed_image_count":0,"licensed_asset_verified_internally":False}
    for obj in bpy.data.objects:
        if obj.type=="ARMATURE":
            count["armatures"]+=1
            count["pose_bones"]+=len(obj.pose.bones)
        if obj.type=="MESH":
            count["mesh_objects"]+=1
            count["faces"]+=len(obj.data.polygons)
            count["material_slots"]+=len(obj.material_slots)
            if obj.data.shape_keys:
                keys=[k.name for k in obj.data.shape_keys.key_blocks]
                count["shape_keys"]+=len(keys)
                count["face_like_keys"].extend(
                    k for k in keys if any(t in k.lower() for t in
                    ["eye","blink","mouth","lip","jaw","smile","brow","phon","visem"]))
    for image in bpy.data.images:
        if image.packed_file or image.packed_files:
            count["packed_image_count"]+=1
        elif image.source=="FILE" and image.filepath and not Path(
             bpy.path.abspath(image.filepath)).is_file():
            count["missing_external_images"].append(image.name)
    # Mesh geometry, rig and high-poly thresholds; not a subjective quality grade.
    count["technical_gate"]=bool(count["armatures"]>=1 and count["pose_bones"]>=30
                                  and count["faces"]>=9000)
    target=Path(out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(count,indent=2)+"\n",encoding="utf-8")
    print("HQ_RIG_AUDIT",json.dumps(count),flush=True)
    if not count["technical_gate"]:
        raise SystemExit("Rejected: not a fully rigged medium/high detail character")

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:
        raise SystemExit("Usage: blender -b --disable-autoexec --python this.py -- FILE.blend REPORT.json")
    main(*args)
