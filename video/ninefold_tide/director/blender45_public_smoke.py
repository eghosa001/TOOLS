#!/usr/bin/env python3
"""Real Blender 4.5 headless API smoke for v07 without PRIVATE production art.

The test deliberately creates a substitute primitive scene only to prove Blender
Grease Pencil, 3D occlusion, packing and camera rendering work on CI. It does
NOT represent or approve Ninefold characters or the director's episode.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

if bpy.app.version[:2] < (4, 5):
    raise RuntimeError("Ninefold v07 requires Blender 4.5+")

out = Path(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else Path("/tmp/ninefold-v07-api-smoke")
out.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 4
scene.render.threads_mode = "FIXED"
scene.render.threads = 2
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 15  # 192x108 low-cost internal technical still
scene.render.fps = 24
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.filepath = str(out / "original_blender45_api_smoke.png")
scene.view_settings.view_transform = "Standard"

bpy.ops.mesh.primitive_cube_add(size=2, location=(2.1, -3.17, 3.20))
deck = bpy.context.object
deck.name = "TEST_ONLY_STAGE_GEOMETRY"
deck.scale = (3, 3, 0.15)
bpy.ops.mesh.primitive_cube_add(size=2, location=(2.4, -2.68, 4.16))
rail = bpy.context.object
rail.name = "TEST_ONLY_RAIL_OCCLUSION"
rail.scale = (2.2, 0.12, 0.10)

bpy.ops.object.camera_add(location=(10.0, -1.7, 6.4))
camera = bpy.context.object
camera.name = "CAM_03B_NAYA_RAIL_CONTACT"
camera.rotation_euler = (Vector((2.1, -3.17, 4.15)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.lens = 55.0
camera.data.sensor_width = 36.0
scene.camera = camera
bpy.context.view_layer.update()  # matrix_world must reflect new camera transform before projection
foot=(2.1, -3.17, 3.355)
grip=(2.36, -2.685, 4.16)
shoulder=(2.32, -3.17, 4.57)
def screen_pixel(point):
    co=world_to_camera_view(scene, camera, Vector(point))
    return [round(1280*co.x, 2), round(720*(1-co.y), 2)]
foot_px=screen_pixel(foot)
grip_px=screen_pixel(grip)
shoulder_to_grip=(Vector(grip)-Vector(shoulder)).length
assert abs(foot_px[0]-640)<3 and abs(foot_px[1]-535)<3, foot_px
assert abs(grip_px[0]-745)<3 and abs(grip_px[1]-380)<3, grip_px
assert abs(shoulder_to_grip-0.636)<0.015, shoulder_to_grip
bpy.ops.object.light_add(type="AREA", location=(5, -1, 8))
bpy.context.object.data.energy = 550
bpy.context.object.data.shape = "DISK"
bpy.context.object.data.size = 5
world = bpy.data.worlds.new("TEST_ONLY_WORLD") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65

actors = []
for who, height, xyz in (
    ("NAYA", 1.64, (2.1, -3.17, 3.355)),
    ("KITO", 1.45, (-7.9, -8.6, 5.93)),
    ("IRI", 1.72, (-6.55, -6.5, 5.93)),
):
    root = bpy.data.objects.new("ACTOR_ROOT_" + who + "_FOOT_WORLD", None)
    scene.collection.objects.link(root)
    root.location = xyz
    root["height_m_LOCKED"] = height
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.grease_pencil_add(
        type="EMPTY", use_in_front=False, stroke_depth_order="3D",
        location=xyz, rotation=(math.pi / 2, 0, 0), scale=(1, 1, 1)
    )
    drawing = bpy.context.object
    drawing.name = "DRAW_" + who + "_FRAME_BY_FRAME_2D"
    drawing.parent = root
    drawing.location = (0, 0, 0)
    drawing["canon_height_m"] = height
    # Blender 4.5 adds one default layer even when type="EMPTY".
    # Remove it before creating the director-specified nine editable layers.
    for previous in tuple(drawing.data.layers):
        drawing.data.layers.remove(previous)
    for label in (
        "00_MODEL_GUIDE_NONRENDER", "01_ROUGH_KEY_DRAWINGS",
        "02_BREAKDOWNS_AND_INBETWEENS", "03_FINAL_INK_LINEWORK",
        "04_FLAT_COLOURS", "05_SHADOW_AND_LIGHT_PLANES",
        "06_EYES_BROWS_MOUTH_ACTING", "07_HANDS_AND_PROP_GRIPS",
        "08_HAIR_AND_CLOTH_FOLLOWTHROUGH",
    ):
        layer = drawing.data.layers.new(label, set_active=True)
        layer.frames.new(1)
        if label == "00_MODEL_GUIDE_NONRENDER":
            layer.hide = True
    actors.append({"name":who, "type":drawing.type,
                   "height":height, "layers":len(drawing.data.layers)})

bpy.ops.file.pack_all()
blend = out / "TEST_ONLY_v07_blender45_api.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
scene.frame_set(1)
bpy.ops.render.render(write_still=True)
image = out / "original_blender45_api_smoke.png"
if not image.exists() or image.stat().st_size < 1000:
    raise RuntimeError("No actual Blender camera render")
print("ACTUAL_BLENDER45_GREASE_PENCIL_SHAPE", json.dumps(actors), flush=True)
assert all(x["type"] == "GREASEPENCIL" and x["layers"] == 9 for x in actors)
report = {
    "blender":bpy.app.version_string, "mode":"PUBLIC SYNTHETIC API COMPATIBILITY TEST ONLY",
    "renders_real_3d_scene":True,
    "user_art_included":False,
    "characters_drawn":False,
    "actual_v05_v07_assets_imported":False,
    "grease_pencil":actors,
    "render_bytes":image.stat().st_size,
    "blend_bytes":blend.stat().st_size,
    "cam03b_camera":"CAM_03B_NAYA_RAIL_CONTACT",
    "projected_naya_foot_px":foot_px,
    "projected_grip_px":grip_px,
    "shoulder_to_grip_m":round(shoulder_to_grip, 4),
    "art_approval":False,
}
(out / "compatibility_report.json").write_text(json.dumps(report, indent=2))
print("NINEFOLD_BLENDER45_PUBLIC_SMOKE_RESULT",json.dumps(report,sort_keys=True))
