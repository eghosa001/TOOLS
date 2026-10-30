#!/usr/bin/env python3
"""Render contact/release frames from an ACTUALLY baked Blender 4.5 scene.

This is a cheap real-Cycles QA proof. It NEVER grants ASMR artistic approval.
Run with a previously baked premium_softbody_physics_source.blend file.
"""
import hashlib
import json
import os
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view

out = Path(os.environ["ASMR_OUT"]).resolve()
proof_dir = out / "lookdev_proof"
proof_dir.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
body = bpy.data.objects.get("One continuous volumetric deforming jewel")
roller = bpy.data.objects.get("Clear round ASMR roller — visible jelly contact")
assert body is not None and roller is not None and scene.camera is not None, "Source objects missing"
soft = next((m for m in body.modifiers if m.type == "SOFT_BODY"), None)
assert soft and soft.point_cache.is_baked, "Cannot render an unbaked fake softbody"
assert scene.frame_start == 1 and scene.frame_end == 120 and scene.render.fps == 24
assert scene.render.engine == "CYCLES", "Must test actual production Cycles pipeline"
scene.cycles.device = "CPU"
scene.cycles.samples = int(os.environ.get("ASMR_PROOF_SAMPLES", "12"))
scene.render.resolution_x = 360
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
if "scene.camera" not in str(scene.camera):
    assert scene.camera.data.type == "PERSP"
frame_rows = []
for frame in (1, 42, 70, 105):
    scene.frame_set(frame)
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        pixels = [
            world_to_camera_view(scene, scene.camera, evaluated.matrix_world @ v.co)
            for v in mesh.vertices
        ]
        extents = {
            "min_x": min(v.x for v in pixels),
            "max_x": max(v.x for v in pixels),
            "min_y": min(v.y for v in pixels),
            "max_y": max(v.y for v in pixels),
        }
    finally:
        evaluated.to_mesh_clear()
    if extents["min_x"] < -.01 or extents["max_x"] > 1.01 or extents["min_y"] < -.01 or extents["max_y"] > 1.01:
        raise RuntimeError("Blender framing wrong at frame %s: %s" % (frame, extents))
    scene.render.filepath = str(proof_dir / ("baked_contact_%03d.png" % frame))
    bpy.ops.render.render(write_still=True)
    img = Path(scene.render.filepath)
    if not img.is_file() or img.stat().st_size < 1000:
        raise RuntimeError("No decoded Cycles frame at %s" % frame)
    frame_rows.append({
        "frame": frame,
        "file": str(img.relative_to(out)),
        "sha256": hashlib.sha256(img.read_bytes()).hexdigest(),
        "size_bytes": img.stat().st_size,
        "framing": extents,
    })
report = {
    "schema_version": 1,
    "scene_source": "Blender 4.5 LTS Cycles + baked softbody",
    "source_blend": "premium_softbody_physics_source.blend",
    "frame_count_tested": len(frame_rows),
    "sample_count": scene.cycles.samples,
    "native_production_master_claim": False,
    "artistic_approval": False,
    "headphone_foley_review": "NOT RUN — this is still-frame physics/render preflight",
    "frames": frame_rows,
}
(out / "BLENDER_CONTACT_PROOF_UNAPPROVED.json").write_text(json.dumps(report, indent=2) + "\n")
print("REAL_BLENDER_BAKED_PHYSICS_CONTACT_PROOF", json.dumps(report), flush=True)
