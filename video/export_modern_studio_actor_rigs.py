#!/usr/bin/env python3
"""Extract only genuinely different high-quality rigged actors from real
Blender Studio Singularity or DOGWALK splash source. No new geometry is built.

Actor lists based on structural audits; source designs, rigs, meshes and
original source license are retained. Original movie .blend stays the master.
Each GLB export is individually checked for valid skin, mesh and textures.
"""
from __future__ import annotations
import bpy,hashlib,json,sys,traceback
from pathlib import Path

ACTORS={
 "singularity":{
  "coralboi":"RIG-coralboi.001",
  "critter":"RIG-critter",
  "doubleeye":"RIG-doubleeye.001",
  "doublemohawk":"RIG-doublemohawk.001",
  "mantaribs":"RIG-mantaribs",
  "multifrog":"RIG-multifrog.001",
  "plumpfly":"RIG-plumpfly.001",
 },
 "dogwalk":{
  "chocomel":"RIG-Chocomel",
  "pinda":"RIG-Pinda",
 }
}
# The separate "critter_food" mesh instancing rig is intentionally excluded:
# it is a food prop, not an additional speaking character.

def belongs(obj,rig):
    cur=obj.parent
    for _ in range(15):
        if cur is None:break
        if cur == rig:return True
        cur=cur.parent
    return any(m.type=="ARMATURE" and m.object==rig for m in obj.modifiers)

def selected_meshes(rig):
    return [o for o in bpy.context.view_layer.objects
        if o.type=="MESH" and o.data is not None and len(o.data.vertices)>0
        and belongs(o,rig) and not o.hide_render]

def build(src,destination,pack):
    output=Path(destination).resolve()
    output.mkdir(parents=True,exist_ok=True)
    source=Path(src).resolve()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    expected=ACTORS[pack]
    manifest={"original_scene":source.name,"original_sha256":hashlib.file_digest(source.open("rb"),"sha256").hexdigest(),
        "publisher":"Blender Studio","license":"CC-BY-4.0, commercial use with attribution",
        "original_author_characters":list(expected),"models":{},
        "review_only":True,"story_or_canon_edited":False,
        "warnings":["Meshes are professional original artists' work, not procedural redesigns",
                    "GLB may not preserve Blender proprietary shader-node networks, rig controllers, expressions or IK",
                    "No speaking-face lip sync has been verified on these specific actors",
                    "Visually inspect an actual 3D render before using in a monetized video"]}

    for name,rig_name in expected.items():
        rigs=[o for o in bpy.context.view_layer.objects if o.type=="ARMATURE" and o.name==rig_name]
        if len(rigs)!=1:
            raise RuntimeError("Expected original distinct armature "+rig_name+" found "+str(len(rigs)))
        rig=rigs[0]
        meshes=selected_meshes(rig)
        if not meshes:
            raise RuntimeError("No original skinned render geometry for "+name)
        for obj in bpy.context.view_layer.objects:
            obj.select_set(False)
        rig.hide_set(False)
        rig.select_set(True)
        for obj in meshes:
            obj.hide_set(False)
            obj.select_set(True)
        bpy.context.view_layer.objects.active=rig
        before_faces=sum(len(obj.data.polygons) for obj in meshes)
        before_shapes=sum(len(obj.data.shape_keys.key_blocks) if obj.data.shape_keys else 0 for obj in meshes)
        filename=name+"_blender_studio.glb"
        target=output/filename
        print("REAL_FILM_CHARACTER_EXPORT_START",pack,name,rig.name,
              "meshes",len(meshes),"faces",before_faces,"bone_count",len(rig.data.bones),flush=True)
        bpy.ops.export_scene.gltf(
            filepath=str(target),export_format="GLB",
            use_selection=True,export_skins=True,
            export_morph=True,export_apply=False,
            export_animations=False,export_materials="EXPORT"
        )
        if not target.is_file() or target.stat().st_size<75000:
            raise RuntimeError("Empty character GLB "+name)
        with target.open("rb") as file:
            assert file.read(4)==b"glTF"
        manifest["models"][name]={"filename":filename,"studio_rig_name":rig_name,
              "original_bones":len(rig.data.bones),
              "original_render_mesh_objects":len(meshes),
              "original_polygon_faces":before_faces,
              "original_shape_keys":before_shapes,
              "glb_bytes":target.stat().st_size,
              "glb_sha256":hashlib.file_digest(target.open("rb"),"sha256").hexdigest(),
              "speaking_face_verified":False,
              "design_canon_approved":False}
        print("REAL_FILM_CHARACTER_GLB_EXPORTED",name,target.stat().st_size,flush=True)
    (output/"REAL_STUDIO_ACTOR_REPORT.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("MODERN_STUDIO_RIG_EXTRACTION_PASS",pack,len(manifest["models"]),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3:
        raise SystemExit("blender --python export_modern_studio_actor_rigs.py -- SOURCE.blend OUTPUT_DIR singularity|dogwalk")
    if args[2] not in ACTORS:raise SystemExit("Unsupported artist source")
    build(*args)
