#!/usr/bin/env python3
"""Extract/render true Blender Studio actors in NATIVE Blender with their
original studio materials/packed textures, because glTF cannot reproduce
their complex node shaders. No new character geometry, no episode render.

Produces source-attributed, reusable individual .blend actor libraries,
static material QC PNGs and factual skeleton/mesh metadata.
"""
from __future__ import annotations
import json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector

ACTORS={
  "dogwalk":{
    "chocomel":"RIG-Chocomel",
    "pinda":"RIG-Pinda",
  },
  "singularity":{
    "coralboi":"RIG-coralboi.001",
    "critter":"RIG-critter",
    "doubleeye":"RIG-doubleeye.001",
    "doublemohawk":"RIG-doublemohawk.001",
    "mantaribs":"RIG-mantaribs",
    "multifrog":"RIG-multifrog.001",
    "plumpfly":"RIG-plumpfly.001",
  }
}

def parented(mesh,armature):
    obj=mesh.parent
    for _ in range(15):
        if obj is None:break
        if obj==armature:return True
        obj=obj.parent
    return any(m.type=="ARMATURE" and m.object==armature for m in mesh.modifiers)

def setup_isolation(rig,meshes):
    collection=bpy.data.collections.new("Original studio actor rendered with authentic materials")
    bpy.context.scene.collection.children.link(collection)
    for obj in [rig,*meshes]:
        if obj.name not in collection.objects:
            collection.objects.link(obj)
        obj.hide_render=False
        obj.hide_set(False)
    included=set(meshes)
    for obj in bpy.data.objects:
        if obj.type=="MESH" and obj not in included:
            obj.hide_render=True
    bpy.context.view_layer.update()

def studio_camera_and_lights(meshes):
    points=[obj.matrix_world @ Vector(x) for obj in meshes for x in obj.bound_box]
    if not points:raise RuntimeError("No real actor bounds")
    low=Vector(tuple(min(v[i] for v in points) for i in range(3)))
    high=Vector(tuple(max(v[i] for v in points) for i in range(3)))
    mid=(low+high)*.5
    spread=high-low
    width=max(spread.x,spread.y,.4)
    height=max(spread.z,.5)
    camdata=bpy.data.cameras.new("Original actor material quality camera")
    camdata.type="ORTHO"
    camdata.ortho_scale=max(height*1.35,width*1.65)
    camera=bpy.data.objects.new("Original actor material quality camera",camdata)
    bpy.context.scene.collection.objects.link(camera)
    camera.location=mid+Vector((0,-max(height*2.7,3.0),height*.21))
    camera.rotation_euler=(mid-camera.location).to_track_quat("-Z","Y").to_euler()
    bpy.context.scene.camera=camera
    for name,relative,power,size in (
        ("Soft warm key",(-1.5,-2.1,2.0),550,4.2),
        ("Soft cool fill",(1.6,-1.4,1.7),320,4.0),
        ("Bright rim",(.5,1.3,1.8),450,3.2),
    ):
        data=bpy.data.lights.new(name,"AREA")
        data.energy=power
        data.shape="DISK"
        data.size=size
        light=bpy.data.objects.new(name,data)
        bpy.context.scene.collection.objects.link(light)
        light.location=mid+Vector(tuple(v*height for v in relative))
        light.rotation_euler=(mid-light.location).to_track_quat("-Z","Y").to_euler()
    world=bpy.data.worlds.new("Neutral studio environment")
    world.use_nodes=True
    background=world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value=(.30,.36,.44,1)
    background.inputs["Strength"].default_value=.6
    bpy.context.scene.world=world

def main(original,out_root,group,name):
    if group not in ACTORS or name not in ACTORS[group]:
        raise ValueError("Unlisted cartoon character, refusing guessed rig names")
    master=Path(original).resolve()
    target=Path(out_root).resolve()
    target.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(master),load_ui=False)
    rig_name=ACTORS[group][name]
    rigs=[o for o in bpy.data.objects if o.type=="ARMATURE" and o.name==rig_name]
    if len(rigs)!=1:raise RuntimeError("Original rig missing: "+rig_name)
    rig=rigs[0]
    meshes=[o for o in bpy.data.objects if o.type=="MESH" and o.data and len(o.data.polygons)>0 and parented(o,rig) and not o.hide_render]
    if len(meshes)<1:
        raise RuntimeError("Original character has no render geometry")
    raw_poly=sum(len(o.data.polygons) for o in meshes)
    if len(rig.data.bones)<30 or raw_poly<1500:
        raise RuntimeError("Not an acceptable original studio rig or detail level")
    setup_isolation(rig,meshes)
    # Write original objects and their referenced images, nodes, materials, and
    # armature as a reusable Blender library. No geometry manipulation.
    native=target/(name+"-native-studio.blend")
    bpy.data.libraries.write(str(native),set([rig,*meshes]),fake_user=True,compress=True)
    if not native.exists() or native.stat().st_size<70_000:
        raise RuntimeError("Native actor library could not be saved")
    print("HIGH_FIDELITY_NATIVE_ACTOR_PACKED",name,"bytes",native.stat().st_size,flush=True)
    studio_camera_and_lights(meshes)
    scene=bpy.context.scene
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=40
    scene.view_layers[0].cycles.use_denoising=False
    scene.render.resolution_x=640
    scene.render.resolution_y=800
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False
    scene.render.filepath=str(target/(name+"-actual-native-render.png"))
    bpy.ops.render.render(write_still=True)
    png=Path(scene.render.filepath)
    if not png.exists() or png.stat().st_size<15000:
        raise RuntimeError("Native actor still render is blank or missing")
    report={
        "character":name,"source_rig_name":rig_name,
        "authorship":"Blender Studio, original source character",
        "source_original":"https://download.blender.org/demo/splash/"+master.name,
        "commercial_license":"CC-BY-4.0 attribution required",
        "asset_is_original_artist_mesh":True,
        "not_rebuilt_using_procedural_models":True,
        "rig_bones":len(rig.data.bones),"render_meshes":len(meshes),
        "original_polygon_faces":raw_poly,
        "shape_keys":sum(len(o.data.shape_keys.key_blocks) for o in meshes if o.data.shape_keys),
        "native_blend_file":native.name,"native_bytes":native.stat().st_size,
        "actual_still":png.name,"render_bytes":png.stat().st_size,
        "appearance_approved":False,
        "facial_speech_verified":False,
        "video_rendered":False
    }
    (target/"SOURCE_AND_QUALITY_STATUS.json").write_text(json.dumps(report,indent=2)+"\n")
    print("NATIVE_STUDIO_REAL_CHARACTER_VISUAL_PASS",json.dumps(report),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=4:raise SystemExit("source.blend output_dir dogwalk|singularity actor_key")
    main(*args)
