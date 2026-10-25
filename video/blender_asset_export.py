"""Run inside free headless Blender to produce reusable CartoonStudio assets.

Usage: blender -b -t 2 --python video/blender_asset_export.py -- SOURCE_ROOT OUTPUT_DIR
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def export(path):
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB")
    if not path.is_file() or path.stat().st_size < 2500:
        raise RuntimeError(f"GLB export missing or too small: {path}")
    print("ASSET_GLTF", path.name, path.stat().st_size, flush=True)


def main():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(argv)!=2:
        raise SystemExit("Expected source root and output directory")
    source_root=Path(argv[0]).expanduser().resolve()
    destination=Path(argv[1]).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0,str(source_root))
    from cartoon_studio.studio_world import (
        build_sunpatch_court, make_character, animate_character_polish
    )
    colors={"lelli":"#16b2ba","brin":"#bf7f30","odo":"#e76579"}
    manifest={
        "format":"CartoonStudio reusable Blender assets v2",
        "authorship":"Original procedural Blender geometry, no external mesh downloads",
        "license":"Original project artwork; creator controls distribution",
        "limitation":"GLBs include viseme/smile/blink morph targets but lack skeletal armatures and motion clips",
        "characters":{},
        "environment":{},
    }
    for name,color in colors.items():
        clear()
        actor=make_character(name,0,color)
        if actor is None or actor.get("root") is None:
            raise RuntimeError("No geometry for "+name)
        meshes=[ob for ob in bpy.data.objects if ob.type=="MESH"]
        if len(meshes)<15:
            raise RuntimeError(f"Character {name} lacks the expected mesh details")
        morph_names={
            key.name
            for mesh in meshes if mesh.data.shape_keys
            for key in mesh.data.shape_keys.key_blocks
        }
        required={"viseme_aa","viseme_PP","viseme_O","eyeBlinkLeft","eyeBlinkRight"}
        if not required.issubset(morph_names):
            raise RuntimeError(f"Character {name} missing facial morph targets: {sorted(required-morph_names)}")
        path=destination / f"{name}_original_clay.glb"
        export(path)
        manifest["characters"][name]={"filename":path.name,"color":color,
                                    "meshes":len(meshes),"articulated":True,
                                    "armature":False,"facial_blendshapes":True,"blendshape_names":sorted(morph_names)}
    clear()
    build_sunpatch_court()
    stage_meshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]
    if len(stage_meshes)<35:
        raise RuntimeError("Sunpatch Court props or geometry were not built")
    environment=destination/"sunpatch_court.glb"
    export(environment)
    manifest["environment"]={"filename":environment.name,
                             "meshes":len(stage_meshes),"stage":"sunpatch_court",
                             "props":["stepping stones","yellow fence","daisy",
                                     "blue watering can","route card",
                                     "three-dot flag","hedges","trees"]}
    clear()
    build_sunpatch_court()
    cast={}
    for index,(name,color) in enumerate(colors.items()):
        actor=make_character(name,(index-1)*1.7,color)
        if actor is None:
            raise RuntimeError("Unable to build model in look-development scene")
        cast[name]=actor
    # The .blend project includes editable facial/gesture keyframes for review.
    animate_character_polish(cast,[
        {"speaker":"lelli","start":0.1,"end":0.7,"emotion":"happy"},
        {"speaker":"brin","start":0.72,"end":1.35,"emotion":"surprised"},
        {"speaker":"odo","start":1.38,"end":1.96,"emotion":"excited"},
    ],24,48)
    arm=cast["odo"]["arms"][1]
    for frame,tilt in ((1,0.0),(10,-1.05),(16,-1.55),(24,0.0)):
        arm.rotation_euler[1]=tilt
        arm.keyframe_insert(data_path="rotation_euler",frame=frame)
    scene=bpy.context.scene
    scene.frame_start=1
    scene.frame_end=48
    scene.frame_set(1)
    camera=bpy.data.cameras.new("Preview camera")
    camera_object=bpy.data.objects.new("Preview camera",camera)
    bpy.context.collection.objects.link(camera_object)
    camera_object.location=(0,-8.5,3.05)
    direction=Vector((0,0.35,1.52))-camera_object.location
    camera_object.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    scene.camera=camera_object
    camera.lens=39
    for name,location,energy,size in (
        ("Softbox key",(-3.5,-3.5,6.5),1050,5.5),
        ("Garden fill",(4,-2.0,5.5),550,5.0),
    ):
        lamp=bpy.data.lights.new(name,"AREA")
        lamp.energy=energy
        lamp.size=size
        obj=bpy.data.objects.new(name,lamp)
        bpy.context.collection.objects.link(obj)
        obj.location=location
        direction=Vector((0,0,1.2))-obj.location
        obj.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=32
    scene.cycles.use_denoising=False  # System Blender may lack OpenImageDenoiser
    scene.render.resolution_x=640
    scene.render.resolution_y=360
    scene.render.resolution_percentage=100
    scene.view_settings.view_transform="Standard"
    scene.view_settings.exposure=-1.15
    try:
        scene.view_settings.look="Medium High Contrast"
    except (TypeError, ValueError):
        pass
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(destination/"sunpatch_court_lookdev.png")
    scene.render.film_transparent=False
    scene.world.use_nodes=True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value=(.31,.52,.78,1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value=.42
    bpy.ops.wm.save_as_mainfile(filepath=str(destination/"sunpatch_court_cast.blend"))
    bpy.ops.render.render(write_still=True)
    thumbnail=destination/"sunpatch_court_lookdev.png"
    if not thumbnail.is_file() or thumbnail.stat().st_size<2500:
        raise RuntimeError("Blender lookdev PNG did not render")
    manifest["lookdev"]={"filename":thumbnail.name,
                         "note":"Static visual preview only; speech/lip sync not tested here"}
    manifest["editable_animation_demo"]={
        "file":"sunpatch_court_cast.blend",
        "frames":48,"fps":24,
        "controls":["head tilt","facial smile","eye blink morph targets","hand wave"],
        "note":"Keyframed Blender puppet demonstration; not a completed episode",
    }
    (destination/"asset_manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("ASSET_EXPORT_SUCCESS",len(manifest["characters"]),
          "characters; stage; .blend file; PNG",flush=True)


if __name__=="__main__":
    main()
