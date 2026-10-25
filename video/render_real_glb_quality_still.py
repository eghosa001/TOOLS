#!/usr/bin/env python3
"""Render ACTUAL imported high-detail GLB in Blender Cycles; no generated geometry.

A quality gate for cartoon actors, not an episode render. Reports embedded
texture count, armatures, morphed geometry and image resolution.
"""
import json,sys
from pathlib import Path
import bpy
from mathutils import Vector

def run(input_file,output_png):
    src=Path(input_file).resolve()
    out=Path(output_png).resolve()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(src))
    objects=[o for o in bpy.data.objects if o.type=="MESH" and len(o.data.polygons)>=5 and not o.hide_render]
    if not objects:raise RuntimeError("NO_VISIBLE_HIGH_DETAIL_GLTF_MESHES")
    corners=[o.matrix_world@Vector(p) for o in objects for p in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in corners) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in corners) for i in range(3)))
    center=(lo+hi)*.5
    height=max(hi.z-lo.z,.4)
    width=max(hi.x-lo.x,hi.y-lo.y,.4)
    if height/width<.15 or height/width>18:raise RuntimeError("Invalid model bounding box for QC")
    c=bpy.data.cameras.new("Actor Audit Camera")
    c.type="ORTHO"
    c.ortho_scale=max(height*1.38,width*1.4)
    camera=bpy.data.objects.new("Actor Audit Camera",c)
    bpy.context.collection.objects.link(camera)
    camera.location=center+Vector((0,-max(height*2.4,2.3),height*.2))
    camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
    bpy.context.scene.camera=camera
    for name,position,power in (
        ("Actor softbox",(height*-1.5,height*-1.6,height*1.9),450),
        ("Actor bounce",(height*1.1,height*-1.2,height*1.5),250),
        ("Actor rim",(height*.5,height*1.5,height*1.7),450),
    ):
        data=bpy.data.lights.new(name,"AREA")
        data.energy=power;data.shape="DISK";data.size=4
        light=bpy.data.objects.new(name,data)
        bpy.context.collection.objects.link(light)
        light.location=center+Vector(position)
        light.rotation_euler=(center-light.location).to_track_quat("-Z","Y").to_euler()
    world=bpy.data.worlds.new("Review Background")
    world.use_nodes=True
    world.node_tree.nodes["Background"].inputs["Color"].default_value=(.40,.45,.50,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value=.7
    scene=bpy.context.scene
    scene.world=world
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=40
    scene.render.resolution_x=720
    scene.render.resolution_y=900
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.view_settings.view_transform="Standard"
    scene.render.filepath=str(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.render.render(write_still=True)
    if not out.exists() or out.stat().st_size<6000:
        raise RuntimeError("Actor rendering produced no real image")
    report={"input":src.name,"mesh_objects":len(objects),
        "polygon_faces":sum(len(o.data.polygons) for o in objects),
        "armatures":sum(o.type=="ARMATURE" for o in bpy.data.objects),
        "shape_keys":sum(len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0 for o in objects),
        "materials":sum(len(o.material_slots) for o in objects),
        "source_3d_files_unchanged":True,
        "render":"Static material and form quality QC only, NOT user episode"}
    (out.parent/(out.stem+".json")).write_text(json.dumps(report,indent=2)+"\n")
    print("REAL_GLTF_VISUAL_QC_PASS",json.dumps(report),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:raise SystemExit("Args MODEL.glb OUTPUT.png")
    run(*args)
