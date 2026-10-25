#!/usr/bin/env python3
"""Export a genuine artist-authored Blender Studio rig to a real skin+face GLB.

No procedural geometry built. This is an interoperability test, not a claim
that intricate CloudRig controller behaviour is fully transferable to glTF.
Retain original Blender .blend as highest-fidelity master.
"""
import json,sys
from pathlib import Path
import bpy

def main(source,destination):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(Path(source).resolve()),load_ui=False)
    # Avoid context-dependent operators: downloaded files may open with no 3D viewport.
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    selected=[]
    for obj in bpy.context.view_layer.objects:
        if obj.type=="ARMATURE" or (obj.type=="MESH" and not obj.hide_render):
            if obj.type=="MESH" and not obj.data.vertices:
                continue
            obj.select_set(True)
            selected.append(obj)
    if not any(x.type=="ARMATURE" for x in selected):
        raise RuntimeError("No skeleton in professional source")
    if not any(x.type=="MESH" for x in selected):
        raise RuntimeError("No render geometry in professional source")
    target=Path(destination).resolve()
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(target),export_format="GLB",
        use_selection=True,
        export_skins=True,
        export_morph=True,
        export_apply=False,
        export_animations=False,
        export_materials="EXPORT")
    if not target.is_file() or target.stat().st_size<500000:
        raise RuntimeError("Real rigged GLB failed to export")
    with target.open("rb") as io:
        header=io.read(12)
        if header[:4]!=b"glTF":
            raise RuntimeError("Not a GLB binary")
    print("REAL_PROFESSIONAL_GLTF_EXPORTED",target.name,target.stat().st_size,len(selected),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2: raise SystemExit("Usage: blender --python export_professional_blend_to_glb.py -- SOURCE.blend OUTPUT.glb")
    main(*args)
