#!/usr/bin/env python3
"""Read REAL cached 24fps Blender Bullet marble motion for Foley amplitude gating.

No synthesized movement. Every bowl-roll envelope is based on the exact
center displacement and bowl surface distance of each rendered glass sphere.
Input is an unmodified baked .blend from the existing approved physics render.
"""
import json,math,os
from pathlib import Path
import bpy
SHOT=int(os.environ.get("ASMR_SHOT","-1"))
if SHOT not in range(8):raise RuntimeError("ASMR_SHOT must be 0..7")
OUT=Path(os.environ.get("ASMR_MOTION_ROOT","/tmp/asmr-motion"))/("shot_%d"%SHOT)
OUT.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene
world=s.rigidbody_world
if not world or not world.point_cache.is_baked:
    raise RuntimeError("No actual baked Bullet physics in original .blend")
beads=sorted((x for x in bpy.data.objects if x.name.startswith("REAL_GLASS_SPHERE_")),key=lambda x:x.name)
if len(beads)!=12:raise RuntimeError("Expected exactly 12 real marbles")
positions=[]
for frame in range(1,121):
    s.frame_set(frame)
    pts=[[round(float(y),5) for y in b.matrix_world.translation] for b in beads]
    if any(not math.isfinite(v) for p in pts for v in p):
        raise RuntimeError("Invalid physical marble frame %d"%frame)
    positions.append(pts)
if sum(p[2]<1.0 for p in positions[-1])<10:
    raise RuntimeError("Physical beads were not successfully dropped")
data={"shot":SHOT,"fps":24,"frames":120,"beads":12,
      "positions_xyz":positions,"from":"actual baked Blender Bullet cache",
      "release_frames":json.loads((OUT/"take_plan.json").read_text())["release_frames"]}
(OUT/"marble_motion.json").write_text(json.dumps(data,separators=(",",":")))
print("REAL_MARBLE_ROLL_TRAJECTORY",SHOT,len(positions),len(beads),flush=True)
