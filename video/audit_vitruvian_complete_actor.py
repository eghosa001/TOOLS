#!/usr/bin/env python3
"""Independently inspect matching original Vitruvian head/body GLBs in Blender.

Reuse published CC0 CharMorph-derived head + published source rigged body;
DO NOT generate replacement geometry or assert Adobe Mixamo clip redistribution
permission. Render only two non-episode cast-review stills, never story/video.
"""
from pathlib import Path
import sys,json,hashlib
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_imported_high_detail_visemes import screenshot,candidate,compare

def material_health(objects):
    out=[]
    for obj in objects:
        for mat in obj.data.materials:
            if not mat:
                continue
            external=[]
            images=[]
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type=="TEX_IMAGE" and node.image:
                        img=node.image
                        images.append(img.name)
                        if img.source=="FILE" and not img.packed_file and img.filepath:
                            path=Path(bpy.path.abspath(img.filepath))
                            if not path.exists():external.append(str(path))
            out.append({"object":obj.name,"material":mat.name,"images":images,
                        "missing_external_images":external})
    return out

def main(head_path,body_path,target):
    head_path,body_path,target=(Path(x).resolve() for x in (head_path,body_path,target))
    for file in (head_path,body_path):
        if file.suffix.lower()!=".glb" or file.stat().st_size<1_000_000:
            raise RuntimeError("Real previously published Vitruvian binary required: "+str(file))
    target.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(head_path))
    hmesh=[o for o in bpy.data.objects if o.type=="MESH"]
    before_arms={o.name for o in bpy.data.objects if o.type=="ARMATURE"}
    if not hmesh:raise RuntimeError("Original head absent from CC0 glTF import")
    bpy.ops.import_scene.gltf(filepath=str(body_path))
    imported=[o for o in bpy.data.objects if o.type=="MESH" and o not in hmesh]
    arms=[o for o in bpy.data.objects if o.type=="ARMATURE" and o.name not in before_arms]
    if not imported or not arms:
        raise RuntimeError("Original matching GLB did not contain a real skinned body rig")
    skin=[o for o in imported if any(m.type=="ARMATURE" and m.object in arms for m in o.modifiers)
          or o.parent in arms]
    if not skin:
        raise RuntimeError("Body original contains no mesh actually attached to an imported armature")
    skinned=sum(len(o.data.vertices) for o in skin)
    if skinned<2000:
        raise RuntimeError("Unexpectedly low amount of original skinned body geometry")
    head_morph=[o for o in hmesh if o.data.shape_keys and candidate("Mouth_Large_Opened",list(o.data.shape_keys.key_blocks)[1:])]
    if not head_morph:raise RuntimeError("High-detail head visemes missing after full actor import")
    face=max(head_morph,key=lambda o:len(o.data.vertices))
    blocks=list(face.data.shape_keys.key_blocks)[1:]
    direct={}
    for label in ("Mouth_Large_Opened","Jaw_Lower","aa","ow","p_b_m"):
        morph=candidate(label,blocks)
        if morph:
            direct[label]={"original_name":morph.name,**compare(face,morph,1.0)}
            morph.value=0
    true_shapes=[key for key,val in direct.items() if val["real_world_deformation"]]
    if len(true_shapes)<4:
        raise RuntimeError("Combined full actor lost original FACS face morph deformations")
    evidence={
        "provenance":"ibrews/VitruvianGodot; imported matching full-body and separate facial GLBs",
        "source_license_notice":"Published CC0 face. Body animation source includes Mixamo; redistributing its animated body without separate licence review is not approved here.",
        "face_source_sha256":hashlib.sha256(head_path.read_bytes()).hexdigest(),
        "body_source_sha256":hashlib.sha256(body_path.read_bytes()).hexdigest(),
        "existing_body_armatures": [{"name":a.name,"bones":len(a.data.bones)} for a in arms],
        "real_body_skinned_mesh_names":[o.name for o in skin],
        "total_skin_vertex_count":skinned,
        "original_body_mesh_count":len(imported),
        "original_face_mesh_count":len(hmesh),
        "face_morphs_after_full_body_import":direct,
        "available_animation_action_names":[a.name for a in bpy.data.actions],
        "head_attached_to_body_rig":any(
            o.parent in arms or any(m.type=="ARMATURE" and m.object in arms for m in o.modifiers)
            for o in hmesh),
        "missing_material_image_paths":[],
        "user_cast_identity_approved":False,
        "actor_ready_for_episode":False,
        "phoneme_wav_alignment_approved":False,
        "original_canonical_story_changed":False,
        "episode_preview_mp4_rendered":False,
        "original_glbs_repackaged_for_redistribution":False,
    }
    mats=material_health(hmesh+imported)
    evidence["missing_material_image_paths"]=sorted(set(x for mat in mats for x in mat["missing_external_images"]))
    evidence["material_sample"]=mats[:35]
    scene=bpy.context.scene
    for shape in blocks:shape.value=0
    screenshot(hmesh+imported,scene,target/"vitruvian-original-head-body-neutral-review.png")
    opener=candidate("Mouth_Large_Opened",blocks)
    opener.value=1
    scene.render.filepath=str(target/"vitruvian-original-head-body-mouth-open-review.png")
    bpy.ops.render.render(write_still=True)
    evidence["review_stills"]=["vitruvian-original-head-body-neutral-review.png",
                               "vitruvian-original-head-body-mouth-open-review.png"]
    (target/"full-body-source-and-quality-evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print("VITRUVIAN_ORIGINAL_FULL_BODY_AND_FACE_IMPORTED",json.dumps({
        "bone_counts":[len(a.data.bones) for a in arms],
        "skin_vertices":skinned,"true_morphs":true_shapes,
        "head_attached":evidence["head_attached_to_body_rig"],
        "missing_texture_paths":len(evidence["missing_material_image_paths"]),
        "episode_rendered":False}),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3:raise SystemExit("Usage Blender --python audit_vitruvian_complete_actor.py -- HEAD.glb BODY.glb OUTPUT")
    main(*args)
