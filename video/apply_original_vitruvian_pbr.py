#!/usr/bin/env python3
"""Restore published CharMorph Vitruvian source maps in Blender PBR review.

Never manufacture a material texture or replace character geometry. Map the
original source CC0 face/body albedo, normal and roughness into Blender's
Principled BSDF as a VIEWING translation of the upstream Godot custom shaders.
This is not a claim of pixel-identical Godot render or approved series style.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_imported_high_detail_visemes import screenshot

SOURCE = {
    "VitSkin": ("vit_face_bc.png","vit_face_n.png","vit_face_rough.png"),
    "VitBody": ("vit_body_bc.png","vit_body_n.png","vit_body_rough.png"),
    "VitMouth": ("vit_mouth.png",None,None),
}
# These are source mesh material names, not synthetic texture/color overrides.
def stem(name):
    return name.partition(".")[0]


def load_source(root,name,linear):
    path=root/name
    if not path.is_file() or path.stat().st_size<80_000:
        raise FileNotFoundError("Real first-party CC0 Vitruvian image missing: "+name)
    image=bpy.data.images.load(str(path),check_existing=True)
    if image.size[0]<512 or image.size[1]<512:
        raise RuntimeError("Source texture resolution unexpectedly degraded: "+name)
    image.colorspace_settings.name="Non-Color" if linear else "sRGB"
    return image,hashlib.sha256(path.read_bytes()).hexdigest()


def apply_source_shaders(originals,root):
    fixed=[]
    file_hashes={}
    materials={}
    for obj in originals:
        if obj.type!="MESH":continue
        for mat in obj.data.materials:
            if mat and stem(mat.name) in SOURCE:
                materials[mat.as_pointer()]=mat
    for mat in materials.values():
        category=stem(mat.name)
        color,normal,rough=SOURCE[category]
        mat.use_nodes=True
        nodes=mat.node_tree.nodes
        nodes.clear()
        output=nodes.new("ShaderNodeOutputMaterial")
        output.location=(520,0)
        bsdf=nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location=(230,0)
        bsdf.inputs["Roughness"].default_value=0.53
        mat.node_tree.links.new(bsdf.outputs["BSDF"],output.inputs["Surface"])
        for name,target,is_data,y in [
            (color,"Base Color",False,280),
            (rough,"Roughness",True,20),
            (normal,"Normal",True,-260)
        ]:
            if not name:continue
            image,digest=load_source(root,name,is_data)
            file_hashes[name]=digest
            texture=nodes.new("ShaderNodeTexImage")
            texture.name="Original_Vitruvian_"+name
            texture.image=image
            texture.location=(-570,y)
            if target=="Normal":
                n=nodes.new("ShaderNodeNormalMap")
                n.space="TANGENT"
                n.location=(-80,-220)
                n.inputs["Strength"].default_value=0.75
                mat.node_tree.links.new(texture.outputs["Color"],n.inputs["Color"])
                mat.node_tree.links.new(n.outputs["Normal"],bsdf.inputs["Normal"])
            else:
                channel="Color"
                if target=="Roughness":
                    channel="Color"
                mat.node_tree.links.new(texture.outputs[channel],bsdf.inputs[target])
        fixed.append({"original_author_material":mat.name,
                      "source_map_names":[x for x in SOURCE[category] if x],
                      "principled_material_preview_only":True})
    required={"VitSkin","VitBody","VitMouth"}
    present={stem(x["original_author_material"]) for x in fixed}
    if not required.issubset(present):
        raise RuntimeError("Original imported actor missing expected source material slots: "+
                           repr(sorted(required-present)))
    if len(file_hashes)!=7:
        raise RuntimeError("All seven original CC0 albedo/normal/roughness/mouth images required")
    return fixed,file_hashes


def main(head,body,textures,out):
    head,body,textures,out=(Path(s).resolve() for s in (head,body,textures,out))
    if not textures.is_dir() or not head.is_file() or not body.is_file():
        raise FileNotFoundError("Published original human head/body and texture directory required")
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(body))
    bpy.ops.import_scene.gltf(filepath=str(head))
    meshes=[o for o in bpy.data.objects if o.type=="MESH"]
    original_materials=sum(len(o.data.materials) for o in meshes)
    if original_materials<3:
        raise RuntimeError("Actual original character has no material library")
    fixed,checksums=apply_source_shaders(meshes,textures)
    screenshot(meshes,bpy.context.scene,out/"original-authored-textures-pbr-review.png")
    report={
        "source":"Original VitruvianGodot / CharMorph CC0 head + original source PBR maps",
        "source_repository":"https://github.com/ibrews/VitruvianGodot",
        "published_original_images_sha256":checksums,
        "original_material_assignments":fixed,
        "original_material_slot_count":original_materials,
        "real_source_textures_loaded":len(checksums),
        "blender_pbr_translation_only":True,
        "original_godot_shader_pixel_parity_verified":False,
        "beauty_render_approved":False,
        "series_character_identity_approved":False,
        "no_generated_character_geometry":True,
        "no_synthetic_material_textures":True,
        "no_episode_render":True,
    }
    (out/"original-cc0-source-materials-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ORIGINAL_VITRUVIAN_CC0_PBR_MATERIAL_QA_PASS",
          "source_images",len(checksums),"material_instances",len(fixed),
          "original_character_proportions_unchanged=true","no_video=true",flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=4:
        raise SystemExit("Usage Blender --python apply_original_vitruvian_pbr.py -- HEAD.glb BODY.glb TEXTURES_DIR OUTPUT")
    main(*args)
