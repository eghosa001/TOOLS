#!/usr/bin/env python3
"""Extract *real* current Blender state for a source-bound AI vision directive.

Never ask a vision model to guess PBR values or the source SHA. It may only
choose among bounded existing controls; Blender reports the baselines.
"""
import hashlib
import json
import os
from pathlib import Path
import bpy

out = Path(os.environ["ASMR_OUT"]).resolve()
manifest_path = out / "physics_bake_manifest.json"
physics = json.loads(manifest_path.read_text())
blend = out / physics["source_blend"]
assert blend.is_file() and hashlib.sha256(blend.read_bytes()).hexdigest() == physics["source_blend_sha256"]
jelly = bpy.data.objects["One continuous volumetric deforming jewel"]
key = bpy.data.objects["Huge white product photography key"]
bsdf = next(n for mat in jelly.data.materials for n in
            (mat.node_tree.nodes if mat.use_nodes else [])
            if n.type=="BSDF_PRINCIPLED")
present = {
    "camera_lens_mm": float(bpy.context.scene.camera.data.lens),
    "gel_roughness": float(bsdf.inputs["Roughness"].default_value),
    "gel_transmission": float(bsdf.inputs["Transmission Weight"].default_value),
    "gel_subsurface": float(bsdf.inputs["Subsurface Weight"].default_value),
    "key_light_energy": float(key.data.energy),
}
result = {"source_blend_sha256": physics["source_blend_sha256"],
          "source_blend": blend.name, "present": present,
          "vision_review_is_required": True,
          "editorial_approval": False}
(out/"director_scene_context.json").write_text(json.dumps(result,indent=2)+"\n")
print("ASMR_REAL_BLEND_CONTEXT_FOR_VISION_REVIEW",json.dumps(result),flush=True)
