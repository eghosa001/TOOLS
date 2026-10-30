#!/usr/bin/env python3
"""Bake genuine Bullet glass-marble drops; render 4 Cycles contact/release frames.

A preview is only a QA candidate. This is NOT owner/headphone approval.
"""
import hashlib,json,os
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
out=Path(os.environ["ASMR_OUT"]).resolve()
scene=bpy.context.scene
assert scene.frame_start==1 and scene.frame_end==120 and scene.render.fps==24
assert scene.rigidbody_world is not None
ob=[bpy.data.objects.get("Authentic rigid glass pearl %02d"%i) for i in range(9)]
if not all(ob):raise RuntimeError("Missing real Bullet rigid bodies")
scene.frame_set(1)
cache=scene.rigidbody_world.point_cache
# Blender 4.5.15 SIGSEGV root cause isolated from its native crash backtrace:
# setting RigidBodyWorld.point_cache.use_disk_cache=True dereferences a
# native pointer and crashes, even though SoftBodyModifier caches support it.
# Do NOT set use_disk_cache for Bullet. Bake the in-memory rigidbody cache
# and save the editable .blend with its native baked data.
# The targeted point-cache operator gets the exact scene and cache.
# A Blender crash is never treated as successful bake/quality evidence.
print("TARGETED_BULLET_CACHE_BAKE_BEGIN",cache.frame_start,cache.frame_end,flush=True)
with bpy.context.temp_override(scene=scene, point_cache=cache):
    res=bpy.ops.ptcache.bake(bake=True)
print("TARGETED_BULLET_CACHE_BAKE_COMPLETE",res,cache.is_baked,flush=True)
if "FINISHED" not in res or not cache.is_baked:
    raise RuntimeError("Bullet rigid-body point cache unbaked")
samples=(1,20,38,52,70,91,110,120)
trace=[]
travel=set()
for frame in samples:
    scene.frame_set(frame)
    deps=bpy.context.evaluated_depsgraph_get()
    points=[]
    for o in ob:
        e=o.evaluated_get(deps)
        pos=e.matrix_world.translation
        v=world_to_camera_view(scene,scene.camera,pos)
        points.append({"id":o.name,"xyz":[round(pos.x,4),round(pos.y,4),round(pos.z,4)],
                       "image_xy":[round(v.x,3),round(v.y,3)]})
        if not (-1.3<=pos.x<=1.3 and -1.3<=pos.y<=1.3 and .01<=pos.z<=2.2):
            raise RuntimeError("Marble escapes real physics stage: frame %s %s %s"%
                               (frame,o.name,tuple(pos)))
        if not (-.01<=v.x<=1.01 and -.01<=v.y<=1.01):
            raise RuntimeError("Full collector action cropped: frame %s %s"%
                               (frame,o.name))
        if frame==120 and pos.z < .62:travel.add(o.name)
    trace.append({"frame":frame,"marbles":points})
if len(travel)<4:
    raise RuntimeError("No real collision progress: only %s marbles settled below 0.62m"%len(travel))
report={"type":"genuine_native_blender_bullet_rigid_body","cache_baked":True,
        "frame_count":120,"fps":24,"rigid_bodies":9,"settled_by_end":len(travel),
        "artistic_approval":False,"audio_approval":False,"sample_frames":trace}
(out/"MARBLE_REAL_PHYSICS_PROOF.json").write_text(json.dumps(report,indent=2)+"\n")
scene.frame_set(1)
source=out/"crystal_pearls_original_baked_physics.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(source))
report["source_blend"]=source.name
report["source_blend_sha256"]=hashlib.sha256(source.read_bytes()).hexdigest()
(out/"MARBLE_REAL_PHYSICS_PROOF.json").write_text(json.dumps(report,indent=2)+"\n")
# Inexpensive CPU lookdev frames. Still image cannot certify sound/premium parity.
scene.cycles.device="CPU"
scene.cycles.samples=int(os.environ.get("ASMR_PROOF_SAMPLES","12"))
scene.render.resolution_x=360;scene.render.resolution_y=640
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
path=out/"lookdev_pearls";path.mkdir(exist_ok=True)
for frame in (1,38,70,110):
    scene.frame_set(frame)
    scene.render.filepath=str(path/("real_bullet_%03d.png"%frame))
    bpy.ops.render.render(write_still=True)
    if not Path(scene.render.filepath).is_file():
        raise RuntimeError("Cycles render missing at frame %d"%frame)
print("GENUINE_CGI_RIGID_BODY_LOOKDEV_PASS_NOT_ARTISTICALLY_APPROVED",report["settled_by_end"],flush=True)
