#!/usr/bin/env python3
"""Audit the published CC0 Vitruvian head/body/hair asset trio in real Blender.

No hair cards or body/face mesh generated. The upstream Godot HairSpring
simulation is not run in Blender: this checks rigged hair skin and actual
attachment/follow to the source head bone, not spring collision dynamics.
"""
from __future__ import annotations
import hashlib,json,sys,math
from pathlib import Path
import bpy
from mathutils import Quaternion,Matrix,Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from assemble_vitruvian_original_actor import attach_head_roots,matching_armature,mesh_points,difference,verify_pose_follow
from audit_imported_high_detail_visemes import candidate

def digest(path):
    with path.open("rb") as stream:return hashlib.file_digest(stream,"sha256").hexdigest()

def center(obj):
    pts=[obj.matrix_world @ Vector(v) for v in obj.bound_box]
    return sum(pts,Vector())/len(pts)

def main(head,body,hair,output):
    head,body,hair,output=(Path(p).resolve() for p in (head,body,hair,output))
    for src in (head,body,hair):
        if not src.is_file() or src.stat().st_size<500_000:raise FileNotFoundError(src)
    checksums={p.name:digest(p) for p in (head,body,hair)}
    output.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(body))
    body_objects=set(bpy.data.objects)
    rig=matching_armature(body_objects)
    bpy.ops.import_scene.gltf(filepath=str(head))
    face_objects=set(bpy.data.objects)-body_objects
    faces=[o for o in face_objects if o.type=="MESH" and o.data.shape_keys
           and candidate("Mouth_Large_Opened",list(o.data.shape_keys.key_blocks)[1:])]
    if not faces:raise RuntimeError("Original 26-morph FACS head absent")
    face=max(faces,key=lambda x:len(x.data.vertices))
    head_anchor,head_roots=attach_head_roots(face_objects,rig)
    bpy.context.view_layer.update()
    neutral=mesh_points(face)
    bpy.ops.import_scene.gltf(filepath=str(hair))
    hair_objects=set(bpy.data.objects)-body_objects-face_objects-{head_anchor}
    hair_meshes=[o for o in hair_objects if o.type=="MESH" and len(o.data.vertices)>100]
    hair_rigs=[o for o in hair_objects if o.type=="ARMATURE"]
    if not hair_meshes or not hair_rigs:
        raise RuntimeError("Original rigged hair must have real authored polygon meshes AND armature")
    weighted=[]
    for m in hair_meshes:
        arm=[x for x in m.modifiers if x.type=="ARMATURE" and x.object in hair_rigs]
        if arm or m.parent in hair_rigs:
            weighted.append(m)
    if not weighted:
        raise RuntimeError("Published Hair Tool card meshes do not follow original hair bones")
    vertices=sum(len(m.data.vertices) for m in weighted)
    if vertices<1000:
        raise RuntimeError("Original skinned hair unexpectedly lacks high-detail geometry")

    roots=[o for o in hair_objects if o.parent not in hair_objects]
    for root in roots:
        original=root.matrix_world.copy()
        root.parent=head_anchor
        root.matrix_world=original
    bpy.context.view_layer.update()
    initial_hair={o.name:center(o) for o in weighted}
    positions=[mesh_points(o,150) for o in weighted[:3]]
    if difference(neutral,mesh_points(face))["maximum_world_motion"]>0.0005:
        raise RuntimeError("Attaching hair changed the neutral head/eyes transform")

    pose=rig.pose.bones.get("mixamorig:Head")
    if pose is None: raise RuntimeError("Matching source Mixamo head bone unavailable")
    saved_mode=pose.rotation_mode
    pose.rotation_mode="QUATERNION"
    saved_rot=pose.rotation_quaternion.copy()
    pose.rotation_quaternion=saved_rot @ Quaternion((0,0,1),math.radians(16))
    bpy.context.view_layer.update()
    moved_face=difference(neutral,mesh_points(face))
    moved_hair=[difference(before,mesh_points(mesh,150))
                for before,mesh in zip(positions,weighted[:3])]
    pose.rotation_quaternion=saved_rot
    pose.rotation_mode=saved_mode
    bpy.context.view_layer.update()
    restored_face=difference(neutral,mesh_points(face))
    restored_hair=[difference(before,mesh_points(mesh,150))
                   for before,mesh in zip(positions,weighted[:3])]
    if moved_face["moved_samples"]<20:
        raise RuntimeError("Head did not respond to original bone pose with hair attached")
    if not any(x["moved_samples"]>=10 and x["maximum_world_motion"]>0.003 for x in moved_hair):
        raise RuntimeError("Original hair meshes did not follow attached Mixamo head bone")
    if restored_face["maximum_world_motion"]>0.0004 or any(x["maximum_world_motion"]>0.0004 for x in restored_hair):
        raise RuntimeError("Head or hair failed to return to original neutral pose")
    if any(digest(path)!=checksums[path.name] for path in (head,body,hair)):
        raise RuntimeError("Downloaded original source was unexpectedly modified")
    report={
        "source":"ibrews/VitruvianGodot pinned original high-detail GLBs",
        "input_sha256":checksums,
        "original_body_bones":len(rig.data.bones),
        "original_hair_armature_bones":[{"name":o.name,"bone_count":len(o.data.bones)} for o in hair_rigs],
        "original_real_skinned_hair_mesh_count":len(weighted),
        "original_skinned_hair_vertices":vertices,
        "source_hair_meshes":[o.name for o in weighted],
        "hair_head_follow_bone":"mixamorig:Head",
        "head_mesh_motion_test":moved_face,
        "original_hair_mesh_motion_test":moved_hair,
        "original_hair_restoration_test":restored_hair,
        "hair_follow_actually_measured":True,
        "spring_bone_collision_dynamics_tested":False,
        "exact_original_godot_shader_visual_parity_verified":False,
        "source_mixamo_action_playback_already_verified_separately":True,
        "character_speech_animation_published":False,
        "cast_mapping_approved":False,
        "episode_rendered":False,
    }
    (output/"authentic-rigged-hair-head-body-integration.json").write_text(json.dumps(report,indent=2)+"\n")
    print("THREE_ORIGINAL_IMPORTED_ASSETS_RIGGED_HAIR_ACTUALLY_FOLLOWS_HEAD",
          json.dumps({"body_bones":report["original_body_bones"],
          "hair_bones":report["original_hair_armature_bones"],"hair_vertices":vertices,
          "hair_moving_vertices":moved_hair,
          "spring_collision_tested":False,"episode_rendered":False}),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=4:raise SystemExit("Usage blender --python audit_original_vitruvian_hair.py -- head.glb body.glb hair_rigged.glb report_dir")
    main(*args)
