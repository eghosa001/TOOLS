#!/usr/bin/env python3
"""Run only inside Blender. Render selected frames; never save the source scene."""
import argparse,sys
from pathlib import Path
import bpy

p=argparse.ArgumentParser()
for name in ("start","end","samples","resolution"):
    p.add_argument("--"+name,type=int,required=True)
p.add_argument("--out",type=Path,required=True)
p.add_argument("--engine",choices=("cycles","eevee"),required=True)
p.add_argument("--device",choices=("CPU","CUDA","OPTIX"),required=True)
args=p.parse_args(sys.argv[sys.argv.index("--")+1:])
scene=bpy.context.scene
if args.engine=="cycles":
    scene.render.engine="CYCLES"
    scene.cycles.samples=args.samples
    if args.device=="CPU":
        scene.cycles.device="CPU"
    else:
        prefs=bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type=args.device
        prefs.get_devices()
        GPUs=[d for d in prefs.devices if d.type==args.device]
        if not GPUs:
            raise RuntimeError("Requested NVIDIA GPU unavailable: refusing silent CPU fallback")
        for d in prefs.devices:d.use=d in GPUs
        scene.cycles.device="GPU"
else:
    if args.device!="CPU":
        raise RuntimeError("EEVEE does not accept a Cycles GPU-device selector")
    engines={item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    chosen=next((v for v in ("BLENDER_EEVEE_NEXT","BLENDER_EEVEE") if v in engines),None)
    if not chosen:raise RuntimeError("EEVEE unavailable in installed Blender")
    scene.render.engine=chosen
scene.frame_start=args.start
scene.frame_end=args.end
scene.render.resolution_percentage=args.resolution
scene.render.image_settings.file_format="PNG"
scene.render.use_file_extension=True
scene.render.filepath=str(args.out/"frame_")
print("BLENDER_ACCELERATION_RENDER",args.start,args.end,scene.render.engine,flush=True)
bpy.ops.render.render(animation=True)
print("TECHNICAL_RENDER_ONLY_NOT_REVIEWED",flush=True)
