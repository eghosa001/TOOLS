#!/usr/bin/env python3
"""Render one editor-chosen range from an ACTUALLY baked Blender soft-body cache.

Designed for four CPU GitHub Actions workers when Kaggle GPUs cancel:
24fps, native 720x1280, original Blender Cycles, no interpolated/faked frames.
"""
import os
from pathlib import Path

import bpy

start = int(os.environ["ASMR_FRAME_START"])
end = int(os.environ["ASMR_FRAME_END"])
if not (1 <= start <= end <= 120 and (end - start + 1) <= 30):
    raise RuntimeError("Worker must render a bounded contiguous 1-30 frame slice")

subject = bpy.data.objects.get("One continuous volumetric deforming jewel")
if subject is None:
    raise RuntimeError("Missing real Blender jelly subject")
physics = next((m for m in subject.modifiers if m.type == "SOFT_BODY"), None)
if physics is None or not physics.point_cache.is_baked:
    raise RuntimeError("Refusing CGI shape-key fallback: physical jelly was not actually baked")

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = int(os.environ.get("ASMR_RENDER_SAMPLES", "12"))
scene.cycles.use_denoising = True
scene.view_layers[0].cycles.use_denoising = True
scene.render.resolution_x = 720
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.use_file_extension = True
scene.render.fps = 24
scene.frame_start = start
scene.frame_end = end
out = Path(os.environ["ASMR_RENDER_OUTPUT"]).resolve()
out.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(out / "frame_")
print("ASMR_BAKED_CPU_CYCLES_FRAMES", start, end, "samples", scene.cycles.samples, flush=True)
bpy.ops.render.render(animation=True)
frames = sorted(out.glob("frame_*.png"))
if len(frames) != end - start + 1:
    raise RuntimeError("Expected %s physical frames, found %s" %
                       (end - start + 1, len(frames)))
print("ASMR_BAKED_FRAMES_COMPLETE", len(frames), flush=True)
