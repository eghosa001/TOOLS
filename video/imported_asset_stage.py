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
        skin=(root/entry.get("skin","")).resolve()
        if not skin.is_relative_to(root) or skin.suffix.lower()!=".png" or not skin.is_file():
            raise RuntimeError("Friendly skin PNG missing for "+entry["id"])
        img=bpy.data.images.load(str(skin),check_existing=True)
        for obj in meshes:
            for slot in obj.material_slots:
                material=slot.material
                if not material:
                    continue
                material.use_nodes=True
                nodes=material.node_tree.nodes
                shader=next((n for n in nodes if n.type=="BSDF_PRINCIPLED"),None)
                if shader:
                    tex=nodes.new("ShaderNodeTexImage")
                    tex.image=img
                    material.node_tree.links.new(tex.outputs["Color"],shader.inputs["Base Color"])

        # Kenney motion clips are separate FBX skeletons. Import the idle
        # action and bind it only if the actual bone names match.
        motion_file=entry.get("animation_files",{}).get("idle")
        mapped_actions=0
        if motion_file:
            motion_path=(root/motion_file).resolve()
            if not motion_path.is_relative_to(root) or not motion_path.is_file():
                raise FileNotFoundError("Missing licensed Kenney idle motion: "+str(motion_path))
            existing=set(bpy.data.objects)
            bpy.ops.import_scene.fbx(filepath=str(motion_path),
                                     automatic_bone_orientation=False)
            motion_objects=[obj for obj in bpy.data.objects if obj not in existing]
            motion_armatures=[obj for obj in motion_objects if obj.type=="ARMATURE"]
            for animated_rig in motion_armatures:
                candidate=animated_rig.animation_data.action if animated_rig.animation_data else None
                if candidate is None:
                    continue
                imported_bones={bone.name for bone in animated_rig.data.bones}
                for display_rig in arms:
                    display_bones={bone.name for bone in display_rig.data.bones}
                    if imported_bones and imported_bones==display_bones:
                        display_rig.animation_data_create()
                        display_rig.animation_data.action=candidate
                        mapped_actions+=1
                        break
            for item in sorted(motion_objects,key=lambda obj:len(obj.children),reverse=True):
                if item.name in bpy.data.objects:
                    bpy.data.objects.remove(item,do_unlink=True)
            print("CC0_IDLE_RETARGET",entry["id"],mapped_actions,"matching rigs",flush=True)

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
        animated=mapped_actions
        for armature in arms:
            if armature.animation_data and armature.animation_data.action:
                if mapped_actions == 0:
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
