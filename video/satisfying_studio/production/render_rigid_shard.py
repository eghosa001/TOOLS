#!/usr/bin/env python3
"""Real Blender/Cycles rendering of one 15-frame shard from a SHA-bound bake.

No AI video credits, fake frames, interpolation or artistic approval. Each
worker regenerates the same genuine Bullet cache from the pinned Git SHA.
"""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
import bpy

out=Path(os.environ["ASMR_OUT"]).resolve()
index=int(os.environ["SHARD_INDEX"])
if not 0<=index<=7:
    raise RuntimeError("ASMR shard index must be 0..7")
start=index*15+1
end=start+14
sc=bpy.context.scene
if not sc.rigidbody_world or not sc.rigidbody_world.point_cache.is_baked:
    raise RuntimeError("STOP: Missing actual Blender Bullet baked cache")
if sc.frame_start!=1 or sc.frame_end!=120 or sc.render.fps!=24:
    raise RuntimeError("Blender 5s 24fps master mismatches baked source")
manifest=out/"physics_bake_manifest.json"
if not manifest.is_file():
    raise RuntimeError("STOP: Missing provenance-bound Bullet physics manifest")
info=json.loads(manifest.read_text())
if info.get("solver")!="blender_rigidbody" or not info.get("baked_point_cache"):
    raise RuntimeError("STOP: Wrong physical solver")
src=out/"rigid_cascade_editable.blend"
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
if sha(src)!=info["source_blend_sha256"]:
    raise RuntimeError("STOP: Changed original baked editable Blender source")
events=info.get("measured_bowl_impact_events")
if not events or len(events)!=7:
    raise RuntimeError("STOP: No seven independently measured material impacts")
sc.render.engine="CYCLES"
sc.cycles.device="CPU"
sc.cycles.samples=int(os.environ.get("ASMR_FINAL_SAMPLES","24"))
sc.cycles.use_denoising=True
sc.render.resolution_x=720
sc.render.resolution_y=1280
sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
sc.render.image_settings.color_mode="RGB"
sc.render.image_settings.color_depth="8"
sc.render.image_settings.compression=35
frames=out/"frames"
frames.mkdir(parents=True,exist_ok=True)
files=[]
for frame in range(start,end+1):
    sc.frame_set(frame)
    sc.render.filepath=str(frames/("frame_%04d.png"%frame))
    bpy.ops.render.render(write_still=True)
    path=Path(sc.render.filepath)
    if not path.is_file() or path.stat().st_size<3000:
        raise RuntimeError("STOP: Missing real Cycles frame "+str(frame))
    files.append({"frame":frame,"name":path.name,"size_bytes":path.stat().st_size,
                  "sha256":sha(path)})
report={
    "shard":index,"first_frame":start,"last_frame":end,
    "physics_event_sha256":info["impact_events_sha256"],
    "blender_scene_source_sha256":info["source_blend_sha256"],
    "actual_native_cycles":True,"resolution":[720,1280],
    "cycles_samples":sc.cycles.samples,"fps":24,
    "artistic_approval":False,"frames":files
}
path=out/"shards"/("SHARD_%02d_RENDER_EVIDENCE.json"%index)
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(report,indent=2)+"\n")
print("ORIGINAL_BLENDER_CYCLES_SHARD_COMPLETED",index,len(files),flush=True)
