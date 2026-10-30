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
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from director_logic import framing_action, validate_framing, float_diagnostic, material_parameter_warnings

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
    obj.collision.damping_factor = 0.40
    # Keep the rubbery underside fixed on stone; the quartz cylinder itself
    # is optically smooth and should not pull the entire gel sideways.
    if hasattr(obj.collision, "friction_factor"):
        obj.collision.friction_factor = 0.85 if obj is ground else 0.07

bpy.context.view_layer.objects.active = body
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
if not any(m.type == "SOFT_BODY" for m in body.modifiers):
    bpy.ops.object.modifier_add(type="SOFT_BODY")
# Blender 4.5 exposes properties directly on bpy.types.SoftBodySettings.
# body.soft_body IS the settings object; it has no nested '.settings'.
settings = body.soft_body
# A jelly placed on a polished slab must remain in shot when the roller
# lifts. Weight the sticky underside strongly, but leave the crown free to
# deform: genuine simulated elastic squish, not shape-key pinning.
base_group = body.vertex_groups.get("Tacky gelatin underside")
if base_group is None:
    base_group = body.vertex_groups.new(name="Tacky gelatin underside")
for vert in body.data.vertices:
    height = max(0.0, min(1.0, (vert.co.z + .257) / .514))
    # A dense cohesive jelly holds a realistic resting thickness before
    # the tool starts compressing it, rather than collapsing under gravity.
    anchoring = .60 + .39 * (1.0 - height)**2
    base_group.add([vert.index], anchoring, "REPLACE")
settings.use_goal = True
settings.vertex_group_goal = base_group.name
settings.goal_default = .75
settings.goal_min = .03
settings.goal_max = .999
settings.goal_spring = .968
settings.goal_friction = 12.0
settings.use_edges = True
settings.pull = 0.90
settings.push = 0.90
settings.damping = 18.0
settings.bend = 8.0
# Cohesive supported gel: avoid collapsing before roller arrives.
settings.effector_weights.gravity = 0.36
settings.use_stiff_quads = True
settings.shear = 0.65

# Simulate at a stable collision-aware density and smooth the evaluated
# geometry AFTER the physical solve. This avoids costly unstable ~2k vertex
# stiff simulations without manufacturing fake deformation or extra keyframes.
if not any(m.type == "SUBSURF" for m in body.modifiers):
    smooth_surface=body.modifiers.new("Rendered micro-smooth simulated jelly","SUBSURF")
    smooth_surface.levels=1
    smooth_surface.render_levels=2

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

# Whole-shot validity, not just one hand-picked frame.
# It is a serious quality failure if the gel slides off screen after
# the tool releases. Detect that at the cheap physics stage.
bounds_report=[]
for frame in (1, 30, 48, 70, 90, 105, 120):
    scene.frame_set(frame)
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    try:
        coords = [evaluated.matrix_world @ v.co for v in mesh.vertices]
        mins = [min(v[axis] for v in coords) for axis in range(3)]
        maxs = [max(v[axis] for v in coords) for axis in range(3)]
        centers = [sum(v[axis] for v in coords)/len(coords) for axis in range(3)]
        record = {
           "frame": frame,
           "min_xyz": [round(v,5) for v in mins],
           "max_xyz": [round(v,5) for v in maxs],
           "centroid_xyz": [round(v,5) for v in centers]
        }
        bounds_report.append(record)
        print("ASMR_BAKED_FULL_TIMELINE_BOUNDS",json.dumps(record),flush=True)
        if not (-.25 < mins[2] and maxs[2] < 1.0):
            raise RuntimeError("Gel escaped vertical physical studio at frame %d: %r"%(frame,record))
        if not (-.45 <= centers[0] <= .46 and abs(centers[1]) <= .36):
            raise RuntimeError("Gel slid out of tight macro shot at frame %d: %r"%(frame,record))
    finally:
        evaluated.to_mesh_clear()


# Real baked deformation check: a successful Blender bake is NOT evidence
# that the transparent roller touched or compressed the simulated jelly.
contact_rows = []
for sample_frame in (1, 20, 38, 52, 67, 80, 92, 108, 120):
    scene.frame_set(sample_frame)
    deps = bpy.context.evaluated_depsgraph_get()
    ob = body.evaluated_get(deps)
    mesh = ob.to_mesh()
    try:
        points = [ob.matrix_world @ v.co for v in mesh.vertices]
        near_surface = [xyz.z for xyz in points
                        if abs(xyz.x - press.location.x) < .48
                        and abs(xyz.y - press.location.y) < .13]
        if not near_surface:
            raise RuntimeError("No gel surface under roller at frame %s" % sample_frame)
        surface = max(near_surface)
        bottom = press.location.z - .075
        contact_rows.append({"frame": sample_frame,
                             "gel_surface_z": round(surface, 5),
                             "roller_bottom_z": round(bottom, 5),
                             "surface_gap_m": round(bottom - surface, 5)})
    finally:
        ob.to_mesh_clear()
(out / "actual_physics_contact_evidence.json").write_text(json.dumps(contact_rows, indent=2)+"\n")
print("ASMR_REAL_SIMULATED_CONTACT_GAPS",json.dumps(contact_rows),flush=True)
by_frame={row["frame"]:row for row in contact_rows}
rest_height=by_frame[20]["gel_surface_z"]
peak_gap=min(by_frame[f]["surface_gap_m"] for f in (67,80))
peak_height=min(by_frame[f]["gel_surface_z"] for f in (67,80))
if rest_height < .45:
    raise RuntimeError("STOP: gel collapsed under gravity before contact; rest z=%s" % rest_height)
if not (-.025 <= peak_gap <= .013):
    raise RuntimeError("STOP: roller is floating OR has deep mesh penetration; gap %.5fm" % peak_gap)
for row in bounds_report:
    cx, cy = row["centroid_xyz"][:2]
    if abs(cx)> .07 or abs(cy)> .07:
        raise RuntimeError("STOP: entire gel drifted instead of locally deforming: frame %s centroid %s" %
                           (row["frame"],row["centroid_xyz"]))
if not (0.012 <= rest_height - peak_height <= .16):
    raise RuntimeError("STOP: no credible compression response: rest=%.5f peak=%.5f"%
                       (rest_height,peak_height))

# Measure real baked geometry against the actual portrait camera.
# Wide material framing is an independent preflight; never infer it from
# a successful physics bake alone.
from bpy_extras.object_utils import world_to_camera_view
framing = []
for frame_index in (1, 24, 48, 70, 90, 105, 120):
    scene.frame_set(frame_index)
    deps = bpy.context.evaluated_depsgraph_get()
    ob = body.evaluated_get(deps)
    geometry = ob.to_mesh()
    try:
        pixels = [world_to_camera_view(scene, scene.camera, ob.matrix_world @ vert.co)
                  for vert in geometry.vertices]
        extent = {
            "frame": frame_index,
            "min_x": min(p.x for p in pixels),
            "max_x": max(p.x for p in pixels),
            "min_y": min(p.y for p in pixels),
            "max_y": max(p.y for p in pixels),
        }
        framing.append(extent)
        print("ASMR_PHYSICS_CAMERA_EXTENT", extent,flush=True)
    finally:
        ob.to_mesh_clear()
# ACTUAL bounded Blender Production Director: no cloud AI credits needed.
# A small static-lens fix is safer and faster than rebaking physics or
# rendering a knowingly cropped 120-frame expensive video.
director = {"engine": "Blender Python + measurable geometry",
            "model_vision_review": "not_connected",
            "editorial_approval": False,
            "initial_framing": framing}
camera_decision = framing_action(framing, scene.camera.data.lens, margin=.045,
                                 max_zoom_out=.18)
director["camera_decision"] = camera_decision
if camera_decision["action"] == "zoom_out":
    scene.camera.data.lens = camera_decision["lens"]
    print("ASMR_DIRECTOR_AUTOCORRECTED_CAMERA_LENS",camera_decision,flush=True)
    framing = []
    for frame_index in (1, 24, 48, 70, 90, 105, 120):
        scene.frame_set(frame_index)
        deps = bpy.context.evaluated_depsgraph_get()
        ob = body.evaluated_get(deps)
        geometry = ob.to_mesh()
        try:
            pixels = [world_to_camera_view(scene, scene.camera, ob.matrix_world @ vert.co)
                      for vert in geometry.vertices]
            framing.append({"frame": frame_index,
                            "min_x": min(p.x for p in pixels),
                            "max_x": max(p.x for p in pixels),
                            "min_y": min(p.y for p in pixels),
                            "max_y": max(p.y for p in pixels)})
        finally:
            ob.to_mesh_clear()
validate_framing(framing, margin=.025)
director["corrected_framing"] = framing
director["physical_end_state"] = float_diagnostic(bounds_report)
gel_bsdf = gelsh = next(
    (node for mat in body.data.materials
     for node in (mat.node_tree.nodes if mat.use_nodes else [])
     if node.type == "BSDF_PRINCIPLED"), None)
if gelsh is not None:
    director["pbr_diagnostics"] = material_parameter_warnings(
        gelsh.inputs["Transmission Weight"].default_value,
        gelsh.inputs["Subsurface Weight"].default_value,
        gelsh.inputs["Roughness"].default_value)
    if director["pbr_diagnostics"]:
        print("ASMR_DIRECTOR_MATERIAL_REVIEW_WARNINGS",director["pbr_diagnostics"],flush=True)
if director["physical_end_state"]["floating_risk"]:
    # Do not give a false physics repair by merely forcing the mesh down:
    # a different physically directed anchor/deformation bake is needed.
    raise RuntimeError("ASMR_DIRECTOR_FLOATING_RISK; require physics retune, not fake contact: "
                       + json.dumps(director["physical_end_state"]))
(out / "actual_physics_camera_framing.json").write_text(
    json.dumps(framing, indent=2) + "\n")
(out / "director_diagnostic.json").write_text(
    json.dumps(director, indent=2) + "\n")
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
    "timeline_world_bounds": bounds_report,
    "centroid_slip_limit_m": 0.07,
    "contact_evidence": contact_rows,
    "measured_peak_roller_gap_m": peak_gap,
    "sticky_base_vertex_group": base_group.name,
    "director_camera": camera_decision,
    "director_floating_risk": director["physical_end_state"]["floating_risk"],
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
