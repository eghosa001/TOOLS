#!/usr/bin/env python3
"""Render real 120-frame 720p animated Cycles preview using its BAKED cache.

It must be run after render_contact_proof.py and never grants editorial approval.
"""
import hashlib
import json
import os
from pathlib import Path
import bpy

out=Path(os.environ["ASMR_OUT"]).resolve()
proof=json.loads((out/"physics_bake_manifest.json").read_text())
source=out/proof["source_blend"]
if hashlib.sha256(source.read_bytes()).hexdigest()!=proof["source_blend_sha256"]:
    raise RuntimeError("Baked Blender source changed since physics approval")
if not (out/"BLENDER_CONTACT_PROOF_UNAPPROVED.json").is_file():
    raise RuntimeError("Missing actual Cycles contact proof preflight")
if not proof.get("contact_evidence"):
    raise RuntimeError("No measured REAL roller-gel contact evidence; refusing 120-frame render")
if min(row["surface_gap_m"] for row in proof["contact_evidence"] if row["frame"] in (67,80))>.013:
    raise RuntimeError("Roller did not contact the gel in real physics")
scene=bpy.context.scene
assert scene.frame_start==1 and scene.frame_end==120 and scene.render.fps==24
assert scene.render.engine=="CYCLES"
body=bpy.data.objects.get("One continuous volumetric deforming jewel")
assert body and next((m for m in body.modifiers if m.type=="SOFT_BODY" and m.point_cache.is_baked),None)
# Actual renderer owns its GPU setup. No CPU fallback on a GPU-directed run.
if os.environ.get("ASMR_REQUIRE_GPU")=="1":
    prefs=bpy.context.preferences.addons["cycles"].preferences
    backend=None
    for option in ("OPTIX","CUDA"):
        try:
            prefs.compute_device_type=option
            prefs.get_devices()
            devs=[dev for dev in prefs.devices if dev.type==option]
            if devs:
                for dev in prefs.devices:dev.use=dev in devs
                backend=option
                break
        except Exception:
            pass
    if not backend:
        raise RuntimeError("No NVIDIA GPU for Blender/Cycles; refusing silent CPU fallback")
    scene.cycles.device="GPU"
    print("GPU_SELECTED_FOR_ASMR",backend,flush=True)
else:
    scene.cycles.device="CPU"
scene.cycles.samples=int(os.environ.get("ASMR_SAMPLES","36"))
scene.render.resolution_x=int(os.environ.get("ASMR_W","720"))
scene.render.resolution_y=int(os.environ.get("ASMR_H","1280"))
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.use_file_extension=True
frames=out/"frames"
frames.mkdir(exist_ok=True)
scene.render.filepath=str(frames/"frame_")
scene.frame_set(1)
bpy.ops.render.render(animation=True)
rendered=sorted(frames.glob("frame_*.png"))
if len(rendered)!=120:
    raise RuntimeError("Expected 120 baked 3D frames, got "+str(len(rendered)))
print("REAL_ASMR_CYCLES_120_FRAME_TECHNICAL_PREVIEW_NOT_APPROVED",len(rendered),flush=True)
