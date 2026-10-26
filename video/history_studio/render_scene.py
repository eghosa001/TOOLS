#!/usr/bin/env python3
"""Render an actual licensed glTF stage as a Blender cinematic B-roll shot.
Runs inside Blender: blender -b --python this.py -- --asset scene.glb --output shot.mp4
No automatic character creation, facial acting or unverifiable reconstruction.
"""
import argparse
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--asset",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--frames",type=int,default=72)
    p.add_argument("--fps",type=int,default=24)
    p.add_argument("--samples",type=int,default=64)
    args=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    if not args.asset.is_file() or args.asset.suffix.lower() not in (".glb",".gltf"):
        raise SystemExit("A real reviewed .glb/.gltf stage file is required; no placeholder video")
    if not 24<=args.frames<=720 or args.fps not in (24,25,30) or not 16<=args.samples<=256:
        raise SystemExit("Unsafe render configuration")
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(args.asset.resolve()))
    objs=[obj for obj in bpy.context.scene.objects if obj.type=="MESH"]
    if not objs:raise SystemExit("Imported stage has no real geometry")
    coords=[obj.matrix_world @ Vector(corner) for obj in objs for corner in obj.bound_box]
    lo=Vector(tuple(min(v[i] for v in coords) for i in range(3)))
    hi=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
    center=(lo+hi)/2
    radius=max((hi-lo).length * 0.8, 3.0)
    bpy.ops.object.camera_add()
    camera=bpy.context.object;camera.name="DocumentaryDollyCamera"
    scene=bpy.context.scene
    scene.camera=camera
    camera.data.type="PERSP";camera.data.lens=45
    focus=center+Vector((0,0,(hi.z-lo.z)*0.08))
    for f in range(1,args.frames+1):
        t=(f-1)/max(args.frames-1,1)
        angle=math.radians(-15+30*t)
        camera.location=focus+Vector((radius*math.cos(angle),-radius*math.sin(angle)-radius*0.9,radius*0.45))
        direction=focus-camera.location
        camera.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
        camera.keyframe_insert(data_path="location",frame=f)
        camera.keyframe_insert(data_path="rotation_euler",frame=f)
    scene.frame_start=1;scene.frame_end=args.frames
    bpy.ops.object.light_add(type="AREA",location=(center.x+radius*0.5,center.y-radius*0.4,hi.z+radius))
    bpy.context.object.data.energy=1100;bpy.context.object.data.shape="DISK";bpy.context.object.data.size=radius
    scene.render.engine="CYCLES"
    scene.cycles.samples=args.samples
    scene.render.resolution_x=1920;scene.render.resolution_y=1080
    scene.render.resolution_percentage=100;scene.render.fps=args.fps
    args.output.parent.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(args.output.resolve())
    scene.render.image_settings.file_format="FFMPEG"
    scene.render.ffmpeg.format="MPEG4"
    scene.render.ffmpeg.codec="H264"
    scene.render.ffmpeg.constant_rate_factor="HIGH"
    scene.render.film_transparent=False
    bpy.ops.render.render(animation=True)
    if not args.output.is_file():raise SystemExit("Blender did not write the MP4")
    print("RENDERED_ACTUAL_ASSET",args.output,args.output.stat().st_size)

if __name__=="__main__":main()
