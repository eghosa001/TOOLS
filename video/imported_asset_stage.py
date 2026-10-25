"""Optional imported CC0 character extras and ready-made glTF environment props.

Uses the actual downloaded source models. No procedural replacement for extras.
Never overrides Lelli, Brin or Odo, and never changes story dialogue.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import bpy
from mathutils import Vector

MAIN_CAST = frozenset({"lelli", "brin", "odo"})


def choose_by_episode(episode, items, n):
    """Repeatable pseudo-random episode selection; stable for the same title."""
    if not items:
        return []
    score=lambda item: hashlib.sha256((episode+"|"+item["id"]).encode("utf-8")).hexdigest()
    return sorted(items,key=score)[:n]


def add_imported_assets(episode=""):
    root_string=os.environ.get("CARTOON_IMPORT_LIBRARY","")
    if not root_string:
        print("IMPORTED_ASSETS: no licensed asset library attached; keeping original cast",flush=True)
        return {"characters":0,"props":0}
    root=Path(root_string).resolve()
    metadata=root/"asset_manifest.json"
    if not metadata.is_file():
        raise FileNotFoundError("Licensed imported asset library missing its manifest: "+str(metadata))
    manifest=json.loads(metadata.read_text(encoding="utf-8"))
    choices=manifest.get("assets",[])
    if not manifest.get("sources") or any(src.get("license")!="CC0-1.0" for src in manifest["sources"]):
        raise ValueError("Cannot load unverified/non-CC0 imported asset sources")
    backgrounds=[a for a in choices if a.get("role")=="background_character"]
    decorations=[a for a in choices if a.get("role")=="environment_prop"]
    outcomes={"characters":0,"props":0}
    for index,entry in enumerate(choose_by_episode(episode,backgrounds,2)):
        filepath=(root/entry["file"]).resolve()
        if not filepath.is_relative_to(root) or filepath.suffix.lower()!=".fbx" or not filepath.is_file():
            raise ValueError("Unsafe or missing imported rigged FBX: "+str(filepath))
        old=set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(filepath),automatic_bone_orientation=False)
        new=[obj for obj in bpy.data.objects if obj not in old]
        meshes=[obj for obj in new if obj.type=="MESH"]
        arms=[obj for obj in new if obj.type=="ARMATURE"]
        if not meshes or not arms:
            raise RuntimeError(f"Imported asset {entry['id']} lacks mesh or armature")
        # Group imported hierarchy under an external transform without
        # rebinding skeletons or changing mesh weights.
        imported_roots=[obj for obj in new if obj.parent not in new]
        wrapper=bpy.data.objects.new("cc0_extra_"+str(index),None)
        bpy.context.collection.objects.link(wrapper)
        bpy.context.view_layer.update()
        for obj in imported_roots:
            matrix=obj.matrix_world.copy()
            obj.parent=wrapper
            obj.matrix_world=matrix
        bpy.context.view_layer.update()
        bounds=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
        low=min(v.z for v in bounds)
        high=max(v.z for v in bounds)
        size=max(high-low,.001)
        wrapper.scale=(1.5/size,)*3
        # Put extras toward the back so they never replace the three speakers.
        wrapper.location=(-3.6 if index==0 else 3.6,2.0,-low*wrapper.scale.z)
        bpy.context.view_layer.update()
        animated=0
        for armature in arms:
            if armature.animation_data and armature.animation_data.action:
                animated+=1
                action=armature.animation_data.action
                try:
                    for fc in action.fcurves:
                        fc.modifiers.new("CYCLES")
                except (AttributeError,TypeError):
                    pass
        outcomes["characters"]+=1
        print("IMPORTED_RIGGED_EXTRA",entry["id"],"mesh_count",len(meshes),
              "armatures",len(arms),"actions_playing",animated,flush=True)
    # Stage props are decorative and intentionally limited to a few glTFs.
    # Never import arbitrary scripts, blend files, or unverified URL references.
    for index,entry in enumerate(choose_by_episode(episode,decorations,3)):
        filepath=(root/entry["file"]).resolve()
        if not filepath.is_relative_to(root) or filepath.suffix.lower() not in (".glb",".gltf"):
            continue
        if not filepath.is_file():
            continue
        before=set(bpy.data.objects)
        try:
            bpy.ops.import_scene.gltf(filepath=str(filepath))
        except RuntimeError as exc:
            print("IMPORTED_PROP_SKIPPED",entry["id"],str(exc)[:150],flush=True)
            continue
        new=[obj for obj in bpy.data.objects if obj not in before]
        meshes=[obj for obj in new if obj.type=="MESH"]
        if not meshes:
            continue
        top=bpy.data.objects.new("cc0_prop_"+str(index),None)
        bpy.context.collection.objects.link(top)
        bpy.context.view_layer.update()
        for obj in (o for o in new if o.parent not in new):
            world=obj.matrix_world.copy()
            obj.parent=top
            obj.matrix_world=world
        bb=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
        height=max(v.z for v in bb)-min(v.z for v in bb)
        top.scale=(min(1.0,1.0/max(height,.001)),)*3
        top.location=((-4.2,2.8,0),(4.2,2.9,0),(-4.4,-.5,0))[index]
        outcomes["props"]+=1
    print("CC0_IMPORTS_READY",outcomes,flush=True)
    return outcomes
