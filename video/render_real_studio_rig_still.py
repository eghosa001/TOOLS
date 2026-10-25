#!/usr/bin/env python3
"""Render a REAL downloaded Blender Studio character, no character generation.

CPU-safe contact-sheet/frame for real-vs-promo visual QC. This is NOT an
episode preview/video; it uses the actual .blend file and does not alter canon.
"""
import json, math, sys
from pathlib import Path

import bpy
from mathutils import Vector

def main(source,target):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(Path(source).resolve()),load_ui=False)
    scene=bpy.context.scene
    scene.frame_set(1)
    points=[]
    usable=[]
    for obj in bpy.data.objects:
        if obj.type!="MESH" or obj.hide_render or not obj.data.vertices:
            continue
        if not obj.visible_get():
            continue
        # Original Blender asset geometry remains unchanged.
        usable.append(obj)
        for p in obj.bound_box:
            points.append(obj.matrix_world@Vector(p))
    if not usable or not points:
        raise RuntimeError("Real studio rig file has no visible render meshes")
    low=Vector((min(p.x for p in points),min(p.y for p in points),min(p.z for p in points)))
    high=Vector((max(p.x for p in points),max(p.y for p in points),max(p.z for p in points)))
    center=(low+high)*0.5
    height=max(high.z-low.z,0.1)
    width=max(high.x-low.x,high.y-low.y,.1)
    # Do not show any extra model in the output.
    camera_data=bpy.data.cameras.new("HQ comparison camera")
    camera_data.type="ORTHO"
    camera_data.ortho_scale=max(height*1.36,width*1.8)
    camera=bpy.data.objects.new("HQ comparison camera",camera_data)
    scene.collection.objects.link(camera)
    camera.location=center+Vector((0,-max(height*2.9,6.0),height*0.23))
    camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
    scene.camera=camera
    for name,pos,power,size in (
        ("Softbox key",(-height*2.0,-height*2.0,height*3.0),750,4.5),
        ("Softbox fill",(height*1.5,-height*1.4,height*1.7),500,3.4),
        ("Rim",(.0,height*1.8,height*2.1),600,2.5),
    ):
        lamp=bpy.data.lights.new(name,"AREA")
        lamp.energy=power
        lamp.shape="DISK"
        lamp.size=size
        ob=bpy.data.objects.new(name,lamp)
        scene.collection.objects.link(ob)
        ob.location=center+Vector(pos)
        ob.rotation_euler=(center-ob.location).to_track_quat("-Z","Y").to_euler()
    world=bpy.data.worlds.new("HQ inspection studio ambient")
    world.use_nodes=True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.37,.44,.57,1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.55
    scene.world=world
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=18
    scene.render.film_transparent=False
    scene.render.resolution_x=720
    scene.render.resolution_y=900
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.view_settings.view_transform="Standard"
    scene.view_settings.look="Medium High Contrast"
    out=Path(target).resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(out)
    bpy.ops.render.render(write_still=True)
    if not out.is_file() or out.stat().st_size<9000:
        raise RuntimeError("Real-model preview render is missing or implausibly small")
    report={"source":Path(source).name,"image":out.name,
            "rendered_mesh_objects":len(usable),
            "computed_bounds":{"low":list(low),"high":list(high)},
            "resolution":[720,900],"render_engine":"Cycles CPU",
            "original_3d_geometry_unchanged":True,
            "episode_video_render":False}
    (out.parent/"VISUAL_QC.json").write_text(json.dumps(report,indent=2)+"\n")
    print("Genuine_HQ_ASSET_STILL_RENDERED",out.stat().st_size,len(usable),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:
        raise SystemExit("Expected SOURCE.blend OUTPUT.png")
    main(*args)
