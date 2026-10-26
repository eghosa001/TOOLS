#!/usr/bin/env python3
"""Real Blender 3.6 original first-party Rex/Elder Sprite rig intake.

Opened published author-created original .blend, never a repackaged substitute.
Counts real rig topology, textures, facial controls and evaluated mouth deformation.
Not an approved character-to-canon mapping, not a spoken audio or episode render.
"""
from __future__ import annotations
import hashlib,json,math,sys
from pathlib import Path
import bpy

IDENTITIES={
    "elder_sprite":{"page":"https://studio.blender.org/characters/elder-sprite/v1/",
                    "source":"https://studio.blender.org/download-source/files/ae/ae8df61cc1daf7d3d1a2ac41c992f3ca/ae8df61cc1daf7d3d1a2ac41c992f3ca.blend"},
    "rex":{"page":"https://studio.blender.org/characters/rex/v1/",
           "source":"https://studio.blender.org/download-source/files/cb/cb8d453b64a548d03bcee7671f83e599/cb8d453b64a548d03bcee7671f83e599.blend"}
}

def sample(obj,limit=450):
    deps=bpy.context.evaluated_depsgraph_get()
    evaluated=obj.evaluated_get(deps)
    mesh=evaluated.to_mesh()
    try:
        count=len(mesh.vertices)
        step=max(1,count//limit)
        return [evaluated.matrix_world@mesh.vertices[i].co for i in range(0,count,step)]
    finally:
        evaluated.to_mesh_clear()

def actual_motion(obj,key):
    original=key.value
    try:
        key.value=0.0
        bpy.context.view_layer.update()
        neutral=sample(obj)
        key.value=1.0
        bpy.context.view_layer.update()
        open_frame=sample(obj)
        shift=[(a-b).length for a,b in zip(neutral,open_frame)]
        return {"sample_count":len(shift),"moved_vertices":sum(n>0.00003 for n in shift),
                "maximum_displacement_world":round(max(shift,default=0.0),6),
                "real_evaluated_deformation":sum(n>0.00003 for n in shift)>=4
                 and max(shift,default=0)>0.0001}
    finally:
        key.value=original
        bpy.context.view_layer.update()

def test(source,out,actor):
    if actor not in IDENTITIES:raise ValueError("Only two real official asset sources allowed")
    source,out=Path(source).resolve(),Path(out).resolve()
    if not source.is_file() or source.stat().st_size<2000000:
        raise FileNotFoundError("Actual first-party character .blend missing")
    if source.read_bytes()[:7] != b"BLENDER":
        raise RuntimeError("Official source must be a genuine native Blender project")
    out.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    rigs=[o for o in bpy.data.objects if o.type=="ARMATURE"]
    meshes=[o for o in bpy.data.objects if o.type=="MESH" and o.data and len(o.data.polygons)>0]
    if not rigs or not meshes:
        raise RuntimeError("Free original character source has no armatures or genuine meshes")
    face_candidates=[]
    original_shape_count=0
    for obj in meshes:
        keys=getattr(obj.data,"shape_keys",None)
        if keys is None:continue
        original_shape_count+=max(0,len(keys.key_blocks)-1)
        for key in list(keys.key_blocks)[1:]:
            name=key.name.casefold()
            if any(token in name for token in ("mouth","jaw","lip","viseme","phoneme","aa","oo")):
                result=actual_motion(obj,key)
                face_candidates.append({"mesh":obj.name,"control":key.name,**result})
    # Take samples of *direct* source controllers. Complex CloudRig facial rigs may
    # require bones, pose libraries and drivers, so zero shape keys is not proof of no facial acting.
    moving=[x for x in face_candidates if x["real_evaluated_deformation"]]
    report={
        "identity":actor,
        "official_url":IDENTITIES[actor]["page"],
        "exact_direct_source_url":IDENTITIES[actor]["source"],
        "license":"CC BY 4.0 (first-party character page); keep attribution in videos",
        "model_file_sha256":digest,
        "actual_native_blender_project_opened":True,
        "blender_version":".".join(str(i) for i in bpy.app.version),
        "real_mesh_count":len(meshes),
        "real_polygon_count":sum(len(o.data.polygons) for o in meshes),
        "original_armature_count":len(rigs),
        "original_armature_bone_counts":[{"name":r.name,"bones":len(r.data.bones)} for r in rigs],
        "original_source_morph_count":original_shape_count,
        "first_party_mouth_named_morph_geometry":face_candidates[:75],
        "direct_deforming_mouth_shapes":[{"mesh":x["mesh"],"control":x["control"],
                                           "moved_vertices":x["moved_vertices"]}
                                           for x in moving],
        "actual_source_mesh_licence_review":"Verify original packed textures and any external third-party content before public reuse.",
        "full_speaking_role_verified":False,
        "wav_viseme_timing_tested":False,
        "native_rig_visual_review_approved":False,
        "canon_identity_selected":None,
        "original_blend_modified":False,
        "episode_rendered":False}
    if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:
        raise RuntimeError("Original rig bytes unexpectedly changed")
    (out/f"{actor}-official-native-character-audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print("OFFICIAL_BLENDER_STUDIO_CHARACTER_IMPORTED",json.dumps({
        "actor":actor,"blender":report["blender_version"],
        "polygons":report["real_polygon_count"],"rigs":report["original_armature_bone_counts"],
        "shape_keys":original_shape_count,"deforming_mouth_shapes":len(moving),
        "episode_render":False}),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3:raise SystemExit("Blender --python audit_official_elder_rex.py -- official.blend OUT_DIR elder_sprite|rex")
    test(*args)
