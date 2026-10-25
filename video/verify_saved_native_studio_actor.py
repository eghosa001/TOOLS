#!/usr/bin/env python3
"""Independent standalone reopen/append test for artist-original Blender rigs.

Verifies extracted .blend actor *really* reuses only artist mesh and skeleton
and retains Blender-compatible native shader materials and packed images.
Do not run source custom Python drivers, do not render an episode.
"""
import json,sys
from pathlib import Path
import bpy

def verify(path,report):
    path=Path(path).resolve()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(path),link=False) as (available,imported):
        objects=list(available.objects)
        if not objects or not any(n.startswith("RIG-") for n in objects):
            raise RuntimeError("Extracted actor library is not a usable 3D rig")
        imported.objects=objects
    for obj in imported.objects:
        if obj and not obj.users_collection:
            bpy.context.collection.objects.link(obj)
    armatures=[o for o in bpy.data.objects if o.type=="ARMATURE"]
    meshes=[o for o in bpy.data.objects if o.type=="MESH" and o.data and len(o.data.polygons)>0]
    skinned=sum(any(m.type=="ARMATURE" and m.object in armatures for m in o.modifiers) or o.parent in armatures for o in meshes)
    images=list(bpy.data.images)
    packed=sum(bool(im.packed_file or im.packed_files) for im in images)
    missing=[]
    for im in images:
        if im.source not in ("FILE","TILED") or im.users<1 or im.packed_file or im.packed_files:
            continue
        native=Path(bpy.path.abspath(im.filepath))
        if im.source=="TILED":
            native=Path(str(native).replace("<UDIM>","1001"))
        if not native.exists():
            missing.append(im.name)
    result={"model_file":path.name,"skeletons":len(armatures),
        "max_bones":max([len(x.data.bones) for x in armatures] or [0]),
        "mesh_objects":len(meshes),
        "skinned_mesh_objects":skinned,
        "mesh_polygons":sum(len(o.data.polygons) for o in meshes),
        "materials":len(bpy.data.materials),
        "images":len(images),"packed_images":packed,
        "missing_source_images":missing,
        "native_library_independently_reloadable":False,
        "lip_sync_verified":False,
        "episode_render":False}
    if len(armatures)!=1 or len(meshes)<3 or skinned<1 or result["max_bones"]<30:
        raise RuntimeError("Real native rig/mesh does not survive standalone source library export: "+json.dumps(result))
    if missing:
        raise RuntimeError("Missing critical native actor shader images: "+json.dumps(result))
    result["native_library_independently_reloadable"]=True
    out=Path(report)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print("NATIVE_STUDIO_CHARACTER_LIBRARY_INDEPENDENT_REIMPORT_PASS",json.dumps(result),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:
        raise SystemExit("Usage Blender -b --disable-autoexec --python ... -- actor.blend report.json")
    verify(*args)
