#!/usr/bin/env python3
"""Apply inspected vision-agent instructions DIRECTLY to editable Blender.

Usage:
  ASMR_DIRECTOR_COMMANDS_JSON=/path/reviewed.json blender -b premium_softbody_physics_source.blend \
      --python director_apply.py

No Blender MCP daemon, hosted inference or video-generation credits required for
this ACTUATOR. An external connected agent/reviewer is still required to
*author* real artistic decisions; this script must not pretend to judge them.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from director_commands import validate_directive
from director_logic import validate_framing

import bpy
from bpy_extras.object_utils import world_to_camera_view


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


out = Path(os.environ["ASMR_OUT"]).resolve()
instructions = Path(os.environ["ASMR_DIRECTOR_COMMANDS_JSON"]).resolve()
assert instructions.is_file(), "Missing actual reviewed AI/director recommendations"
manifest = out / "physics_bake_manifest.json"
assert manifest.is_file(), "Do not direct/edit a scene lacking physics evidence"
physics = json.loads(manifest.read_text())
blend = out / physics["source_blend"]
assert blend.is_file() and digest(blend) == physics["source_blend_sha256"], (
    "Blender editable scene differs from certified physical cache; refusing change")

scene = bpy.context.scene
jelly = bpy.data.objects.get("One continuous volumetric deforming jewel")
key = bpy.data.objects.get("Huge white product photography key")
assert jelly and key and scene.camera, "Expected authored scene assets missing"
soft = next((m for m in jelly.modifiers if m.type == "SOFT_BODY"), None)
assert soft and soft.point_cache.is_baked, "Unbaked or missing physics cannot be directed"
bsdf = next((node for mat in jelly.data.materials for node in
             (mat.node_tree.nodes if mat.use_nodes else [])
             if node.type == "BSDF_PRINCIPLED"), None)
assert bsdf, "Missing original physically based gelatin material"
present = {
    "camera_lens_mm": scene.camera.data.lens,
    "gel_roughness": bsdf.inputs["Roughness"].default_value,
    "gel_transmission": bsdf.inputs["Transmission Weight"].default_value,
    "gel_subsurface": bsdf.inputs["Subsurface Weight"].default_value,
    "key_light_energy": key.data.energy,
}
data = json.loads(instructions.read_text(encoding="utf-8"))
if data.get("source_blend_sha256") != physics["source_blend_sha256"]:
    raise RuntimeError("Creative correction based on a DIFFERENT Blender source")
changes = validate_directive(data, present)
if "camera_lens_mm" in changes:
    scene.camera.data.lens = changes["camera_lens_mm"]
if "gel_roughness" in changes:
    bsdf.inputs["Roughness"].default_value = changes["gel_roughness"]
if "gel_transmission" in changes:
    bsdf.inputs["Transmission Weight"].default_value = changes["gel_transmission"]
if "gel_subsurface" in changes:
    bsdf.inputs["Subsurface Weight"].default_value = changes["gel_subsurface"]
if "key_light_energy" in changes:
    key.data.energy = changes["key_light_energy"]

# New lens must preserve the physically simulated subject in the frame.
if "camera_lens_mm" in changes:
    rows = []
    for frame in (1, 24, 48, 70, 90, 105, 120):
        scene.frame_set(frame)
        deps = bpy.context.evaluated_depsgraph_get()
        evaluated = jelly.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        try:
            positions = [world_to_camera_view(scene, scene.camera,
                         evaluated.matrix_world @ v.co) for v in mesh.vertices]
            rows.append({"frame": frame, "min_x": min(p.x for p in positions),
                         "max_x": max(p.x for p in positions),
                         "min_y": min(p.y for p in positions),
                         "max_y": max(p.y for p in positions)})
        finally:
            evaluated.to_mesh_clear()
    validate_framing(rows, margin=.025)
    (out / "actual_physics_camera_framing.json").write_text(json.dumps(rows, indent=2)+"\n")

scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
if not soft.point_cache.is_baked:
    raise RuntimeError("Edit invalidated Blender physical bake: do not render")
physics["source_blend_sha256"] = digest(blend)
physics["director_creative_changes"] = changes
physics["director_approval"] = False
manifest.write_text(json.dumps(physics, indent=2)+"\n")
report = {
    "source_sha256_before": data["source_blend_sha256"],
    "source_sha256_after": physics["source_blend_sha256"],
    "changes": changes, "reason": data["reason"],
    "original_values": {k: present[k] for k in changes},
    "agent_artistic_approval": False,
    "rendered_frame_reinspection_required": True,
}
(out / "director_edit_audit.json").write_text(json.dumps(report, indent=2)+"\n")
print("ASMR_DIRECTOR_ACTUALLY_APPLIED_EDITABLE_BLENDER_CHANGES",json.dumps(report),flush=True)
