#!/usr/bin/env python3
"""Bake genuine Blender soft-body contact physics for the five-second ASMR gel.

Run with verified Blender 4.5 LTS:
    blender -b scene.blend --python blender_softbody_prepare.py

This does NOT claim that a physical simulation is automatically beautiful. It
creates a reproducible, editable .blend with a baked physics point cache and
fails rather than silently falling back to artist-only shape keys.
"""
import hashlib
import json
import os
from pathlib import Path

import bpy

out = Path(os.environ.get("ASMR_OUT", "/kaggle/working/prismatic_asmr")).resolve()
out.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
assert scene.frame_start == 1 and scene.frame_end == 120 and scene.render.fps == 24
body = bpy.data.objects.get("One continuous volumetric deforming jewel")
press = bpy.data.objects.get("Clear round ASMR roller — visible jelly contact")
ground = bpy.data.objects.get("ASMR studio stone collider")
if not all((body, press, ground)):
    raise RuntimeError("ASMR physical source scene has changed: gel, roller or stone missing")
if body.type != "MESH" or len(body.data.vertices) < 500:
    raise RuntimeError("Low-detail or invalid jelly mesh rejected before physics")

# Shape keys can mask the actual evaluated physics and are intentionally removed.
# We must see the collision/bake deformation, not a pre-keyed substitute.
if body.data.shape_keys:
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.ops.object.shape_key_remove(all=True)
    if body.data.shape_keys:
        raise RuntimeError("Failed to eliminate non-physical deformation shape keys")

for obj in (ground, press):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    if not any(m.type == "COLLISION" for m in obj.modifiers):
        bpy.ops.object.modifier_add(type="COLLISION")
    obj.collision.thickness_outer = 0.008
    obj.collision.damping_factor = 0.25

bpy.context.view_layer.objects.active = body
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
if not any(m.type == "SOFT_BODY" for m in body.modifiers):
    bpy.ops.object.modifier_add(type="SOFT_BODY")
# Blender 4.5 exposes properties directly on bpy.types.SoftBodySettings.
# body.soft_body IS the settings object; it has no nested '.settings'.
settings = body.soft_body
settings.use_goal = True
settings.goal_default = 0.16
settings.goal_spring = 0.9
settings.goal_friction = 2.0
settings.use_edges = True
settings.pull = 0.75
settings.push = 0.75
settings.damping = 15.0
settings.bend = 7.0
settings.use_stiff_quads = True
settings.shear = 0.65

# The cache lives on the SoftBodyModifier, NOT Object.soft_body
# (which is a SoftBodySettings instance in Blender 4.5).
soft_mod = next((modifier for modifier in body.modifiers
                 if modifier.type == "SOFT_BODY"), None)
if soft_mod is None:
    raise RuntimeError("Missing actual soft-body modifier after setup")
cache = soft_mod.point_cache
cache.frame_start, cache.frame_end = 1, 120
cache.frame_step = 1

scene.frame_set(1)
blend = out / "premium_softbody_physics_source.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))

# Disk cache is kept outside the GitHub repository but inside the render artifact.
cache.use_disk_cache = True
# bake_all targets the scene's actual soft-body cache without relying on
# stale UI area context in background Blender. There is only one sim body.
result = bpy.ops.ptcache.bake_all(bake=True)
if "FINISHED" not in result:
    raise RuntimeError("Blender native point-cache baking returned "+repr(result))
if not cache.is_baked:
    raise RuntimeError("Blender soft-body cache was not baked; no animation allowed")

scene.frame_set(70)
deps = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(deps)
mesh = evaluated.to_mesh()
try:
    coords = [evaluated.matrix_world @ v.co for v in mesh.vertices]
    minimum = min(v.z for v in coords)
    maximum = max(v.z for v in coords)
    centroid = sum((v.z for v in coords), 0.0) / len(coords)
    xspread = (min(v.x for v in coords), max(v.x for v in coords))
    yspread = (min(v.y for v in coords), max(v.y for v in coords))
    print("BAKED_FRAME70_WORLD_BOUNDS", {
        "min_z": round(minimum, 5),
        "max_z": round(maximum, 5),
        "centroid_z": round(centroid, 5),
        "x_range": [round(v, 5) for v in xspread],
        "y_range": [round(v, 5) for v in yspread],
    },flush=True)
    if not (minimum > -0.25 and maximum < 1.0):
        raise RuntimeError("Baked jelly escaped contact region: min_z=%s max_z=%s"
                           % (round(minimum, 5), round(maximum, 5)))
finally:
    evaluated.to_mesh_clear()

scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
sha = hashlib.sha256(blend.read_bytes()).hexdigest()
proof = {
    "source_blend": blend.name,
    "source_blend_sha256": sha,
    "native_solver": "Blender 4.5 LTS soft body, collision",
    "solver": "blender_softbody",
    "cached_frames": 120,
    "fps": 24,
    "baked_point_cache": bool(cache.is_baked),
    "press_collision": True,
    "stone_collision": True,
    "material_subject": "elastic gel compression",
    "editorial_approval": False,
}
(out / "physics_bake_manifest.json").write_text(json.dumps(proof, indent=2) + "\n")
print("ASMR_REAL_PHYSICS_CACHE_BAKED", json.dumps(proof), flush=True)
if os.environ.get("ASMR_RENDER_ANIMATION", "0") == "1":
    frames = out / "frames"
    frames.mkdir(exist_ok=True)
    scene.frame_set(1)
    scene.render.image_settings.file_format = "PNG"
    scene.render.use_file_extension = True
    scene.render.filepath = str(frames / "frame_")
    bpy.ops.render.render(animation=True)
    rendered = sorted(frames.glob("frame_*.png"))
    if len(rendered) != 120:
        raise RuntimeError("Physical simulation rendered only %s/120 frames" % len(rendered))
    print("ASMR_BAKED_PHYSICS_ANIMATION_FRAMES", len(rendered), flush=True)
