#!/usr/bin/env python3
"""Read-only Blender scene inspection for a director-selected Ninefold Tide shot.

Example: blender -b /path/to/layout.blend --python blender_probe.py -- --shot ep101_006 --out /kaggle/working/shot006_scene.json
The probe never saves/mutates the original .blend.
"""
import argparse,json,os,sys
from pathlib import Path
import bpy

parser=argparse.ArgumentParser()
parser.add_argument("--shot",required=True)
parser.add_argument("--out",type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
scene=bpy.context.scene
missing=[]
for image in bpy.data.images:
    if image.source != "FILE" or image.packed_file is not None or not image.filepath:
        continue
    try:
        resolved=Path(bpy.path.abspath(image.filepath))
        if not resolved.is_file(): missing.append({"image":image.name,"filepath":image.filepath})
    except Exception:
        missing.append({"image":image.name,"filepath":"unresolvable"})
poly_count=sum(len(obj.data.polygons) for obj in bpy.data.objects
               if obj.type=="MESH" and hasattr(obj.data,"polygons"))
animated=sum(bool(obj.animation_data and obj.animation_data.action)
             for obj in bpy.data.objects)
report={
    "shot":args.shot,
    "scene_name":scene.name,
    "blender_version":".".join(map(str,bpy.app.version)),
    "camera":scene.camera.name if scene.camera else None,
    "has_camera":bool(scene.camera),
    "fps":scene.render.fps,
    "resolution_x":scene.render.resolution_x,
    "resolution_y":scene.render.resolution_y,
    "resolution_percentage":scene.render.resolution_percentage,
    "render_engine":scene.render.engine,
    "frame_start":scene.frame_start,
    "frame_end":scene.frame_end,
    "poly_count":poly_count,
    "object_count":len(bpy.data.objects),
    "animated_object_count":animated,
    "armature_count":sum(obj.type=="ARMATURE" for obj in bpy.data.objects),
    "light_count":sum(obj.type=="LIGHT" for obj in bpy.data.objects),
    "material_count":len(bpy.data.materials),
    "missing_external_files":missing,
    "object_labels":[{"name":obj.name,"type":obj.type} for obj in bpy.data.objects][:300],
    "evidence_limits":["Object names are not proof of correct contact or mechanics",
                       "This does not evaluate emotions, facial identity, lighting taste or final film quality",
                       "An absent Blender animation does not mean 2D drawings are absent"],
    "source_blend_not_modified":True,
}
args.out.parent.mkdir(parents=True,exist_ok=True)
args.out.write_text(json.dumps({"shots":{args.shot:{"scene":report}}},indent=2)+"\n",encoding="utf-8")
print("NINEFOLD_READ_ONLY_SCENE_PROBE",json.dumps({"out":str(args.out),
    "camera":report["camera"],"missing":len(missing),"objects":report["object_count"]}),flush=True)
