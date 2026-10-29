#!/usr/bin/env python3
"""Render real physical before/after checkpoints for a cheap visual AI director.

Never renders synthetic replacement frames or a final 120-frame video.
Actual Blender bakes required. Each image is a small 360x640 Cycles render.
"""
import os
from pathlib import Path
import bpy

scene = bpy.context.scene
subject = bpy.data.objects.get("One continuous volumetric deforming jewel")
assert subject, "No actual physical gel"
sim = next((mod for mod in subject.modifiers if mod.type=="SOFT_BODY"),None)
assert sim and sim.point_cache.is_baked, "No real softbody cache: no AI review"
out=Path(os.environ["ASMR_OUT"])/"director_checkpoints"
out.mkdir(parents=True,exist_ok=True)
prefix=os.environ.get("ASMR_CHECKPOINT_PREFIX","before")
assert prefix in ("before","after")
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=8
scene.cycles.use_denoising=True
scene.view_layers[0].cycles.use_denoising=True
scene.render.resolution_x=360
scene.render.resolution_y=640
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
for f in (1,70,120):
    scene.frame_set(f)
    scene.render.filepath=str(out/f"{prefix}_{f:03d}.png")
    bpy.ops.render.render(write_still=True)
    if not Path(scene.render.filepath).is_file():
        raise RuntimeError("Real Blender checkpoint PNG absent at frame %s"%f)
    print("ASMR_DIRECTOR_REAL_CHECKPOINT_RENDERED",prefix,f,flush=True)
print("ASMR_DIRECTOR_ACTUAL_BAKED_IMAGE_TRIO_COMPLETE",prefix,flush=True)
