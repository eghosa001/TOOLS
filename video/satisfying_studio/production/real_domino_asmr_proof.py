#!/usr/bin/env python3
"""First real three-second CGI ASMR proof: physically colliding wooden dominoes.

Run inside Blender 4.5.15, not normal Python. Produces actual original editable
.blend, evaluated per-frame tilt evidence, 72 independent Cycles-rendered
picture frames, and a contact event sheet. It never fabricates a sound, labels
source Foley approved or self-awards artistic approval.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from blender_mechanical_rigs import build
from types import SimpleNamespace

ROOT=Path(os.environ.get("ASMR_PROOF_DIR","/tmp/asmr_first_proof")).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
SCENE=ROOT/"domino_baked_original.blend"
FRAME_COUNT=72
CINEMATIC=os.environ.get("ASMR_CINEMATIC","0")=="1"
SOURCE_SLOWMO=2.3 if CINEMATIC else 1.0
SAMPLES=int(os.environ.get("ASMR_RENDER_SAMPLES","12"))
W=int(os.environ.get("ASMR_RENDER_W","540"))
H=int(os.environ.get("ASMR_RENDER_H","960"))
if W < 540 or H < 960 or SAMPLES < 8:
    raise RuntimeError("Native CGI first proof requires at least 540x960 and 8 Cycles samples")

# Existing solver, real physical bakes and seven camera bounds, not a new
# visual toy that pretends to implement rigid-body contact.
rig=build(SimpleNamespace(rig="domino",output=SCENE,aspect="9:16",
                          bake=True,still=False))
if not rig["baked_point_cache"]:
    raise RuntimeError("Blender baked rigid-body proof missing")

scene=bpy.context.scene
scene.render.resolution_x=W
scene.render.resolution_y=H
scene.cycles.samples=SAMPLES
scene.cycles.use_denoising=True
scene.cycles.max_bounces=5
scene.render.fps=24
scene.render.image_settings.file_format="PNG"
scene.frame_end=120
scene.render.film_transparent=False
scene.view_settings.view_transform="AgX"

def pbr_wood(name,color):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    bsdf=nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(*color,1)
    bsdf.inputs["Roughness"].default_value=.38
    bsdf.inputs["Coat Weight"].default_value=.16
    tex=nodes.new("ShaderNodeTexWave")
    tex.wave_type="BANDS"
    tex.bands_direction="X"
    tex.inputs["Scale"].default_value=7.5
    tex.inputs["Distortion"].default_value=7
    micro=nodes.new("ShaderNodeTexNoise")
    micro.inputs["Scale"].default_value=120
    micro.inputs["Detail"].default_value=4
    bump=nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.10
    bump.inputs["Distance"].default_value=.004
    links.new(tex.outputs["Color"],bump.inputs["Height"])
    links.new(micro.outputs["Fac"],bump.inputs["Normal"])
    links.new(bump.outputs["Normal"],bsdf.inputs["Normal"])
    return mat

wood=[
    pbr_wood("Honey amber hardwood with real grain",(.64,.29,.092)),
    pbr_wood("Dark polished walnut with real grain",(.25,.11,.051)),
    pbr_wood("Warm cherry timber with real grain",(.49,.13,.073)),
]
dots=bpy.data.materials.new("Matte inlaid ivory pips")
dots.use_nodes=True
dots.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.93,.89,.74,1)
dots.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.57

all_dominos=sorted((o for o in scene.objects if o.name.startswith("Porcelain domino")),
                   key=lambda o:o.name)
if len(all_dominos)!=13:
    raise RuntimeError("Expected 13 original 3D wooden domino bodies")
# Original materials become genuine wood; source sound must be authentic wood hits.
for i,ob in enumerate(all_dominos):
    ob.data.materials.clear()
    ob.data.materials.append(wood[i%len(wood)])
    ob.name=ob.name.replace("Porcelain","Wooden")
    # Original proof had protruding pips. Premium mode keeps a clean coherent
    # solid profile instead of fake disconnected dots.
    if CINEMATIC:
        continue
    # Small slightly inset numbered pips on the visible front faces.
    # They are children of the real rigid-body blocks and move with the bake.
    for k in range(i%3+1):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=16,ring_count=8,radius=1,
            location=(ob.location.x+(-.026+.026*k),-.1502,
                      ob.location.z+(-.10+.095*k)))
        pip=bpy.context.object
        pip.name="Ivory embedded identifying pip"
        pip.scale=(.016,.0025,.018)
        pip.data.materials.append(dots)
        pip.parent=ob
        pip.matrix_parent_inverse=ob.matrix_world.inverted()

# Real animated rigid bodies are verified per evaluated frame. A pile of
# static blocks, or a pretty fake keyframe slide, cannot pass this check.
tilts={}
for frame in range(1,121):
    scene.frame_set(frame)
    angles=[]
    for ob in all_dominos:
        evaluated=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        up=(evaluated.matrix_world.to_3x3() @ Vector((0,0,1))).normalized()
        angles.append(math.degrees(math.acos(max(-1,min(1,up.z)))))
    tilts[frame]=angles

events=[]
for i,ob in enumerate(all_dominos):
    initial=.30 if i==0 else .22
    first=next((frame for frame in range(1,FRAME_COUNT+1)
                if tilts[frame][i]>initial*180/math.pi),None)
    if first is not None:
        events.append({"domino_index":i+1,"event":"first_physical_tip",
                       "frame":first,"contact_time_seconds":round((first-1)*SOURCE_SLOWMO/24,5),
                       "source_physics_frame":first,
                       "actual_3d_camera_follow":CINEMATIC,
                       "wood_material":wood[i%len(wood)].name,
                       "source":"real Blender evaluated baked rigid-body transform",
                       "foley_id":f"wood-contact-{i+1:02d}",
                       "source_film_is_cgi":True})
events.sort(key=lambda a:a["frame"])
if len(events)<7:
    (ROOT/"rejected_3d_motion.json").write_text(json.dumps({
        "reason":"No convincing multi-domino physical cascade; not enough real tips",
        "events":events,"angles":tilts},indent=2))
    raise RuntimeError("PHYSICS REVIEW STOP: cascade did not topple >=7 separate dominoes")

# All moving surfaces and camera are deliberately framed as a complete
# physical tabletop scene, no 2D crop/pan added at assembly.
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(SCENE))
source_hash=hashlib.sha256(SCENE.read_bytes()).hexdigest()
report={
    "source_blend":SCENE.name,
    "source_blend_sha256":source_hash,
    "format_id":"domino-marble",
    "cgi_only":True,
    "solver":"blender_rigidbody",
    "baked_point_cache":True,
    "cached_frames":120,
    "frame_rate":24,
    "rendered_frames":FRAME_COUNT,
    "resolution":[W,H],
    "cycles_samples":SAMPLES,
    "cinematic_physics_retiming":SOURCE_SLOWMO,
    "camera_tracks_active_contacts":CINEMATIC,
    "decorative_floating_pips_removed":CINEMATIC,
    "actual_3d_rigidbody_events":len(events),
    "scene_reuses_existing_blender_mechanical_rigs":True,
    "human_review_approved":False,
}
(ROOT/"actual_cgi_evidence.json").write_text(json.dumps(report,indent=2)+"\n")
(ROOT/"visual_contact_events.json").write_text(json.dumps(events,indent=2)+"\n")
frames_dir=ROOT/"frames"
frames_dir.mkdir(exist_ok=True)
if CINEMATIC:
    # Tight native-portrait close-up of the *active* physical dominoes rather
    # than tiny wide objects abandoned in a mostly-empty 9:16 image.
    scene.camera.data.lens=65
    scene.camera.data.dof.aperture_fstop=13
    scene.camera.data.clip_start=.02
    bpy.ops.object.light_add(type="AREA", location=(0,-1.8,2.0))
    fill=bpy.context.object
    fill.name="Broad clear warm front macro fill"
    fill.data.energy=410
    fill.data.shape="DISK"
    fill.data.size=2.6
    fill.data.color=(1,.91,.79)
    # Scene must be saved after lookdev edits. The editor can reopen the
    # editable source; exact SHA is updated below.
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(SCENE))
    report["source_blend_sha256"]=hashlib.sha256(SCENE.read_bytes()).hexdigest()
    (ROOT/"actual_cgi_evidence.json").write_text(json.dumps(report,indent=2)+"\\n")

for frame in range(1,FRAME_COUNT+1):
    if CINEMATIC:
        # Slow the *actual evaluated* rigid-body timeline, not a repeated
        # still photograph or synthetic object tween. Native Cycles renders
        # every new output frame at a corresponding real physics subframe.
        source=1+(frame-1)/SOURCE_SLOWMO
        whole=int(math.floor(source))
        scene.frame_set(whole, subframe=source-whole)
        # Camera pans with the wave of actual contact, keeps the leading
        # active 4–5 dominoes in the portrait while maintaining real depth.
        p=max(0.,min(1.,(source-5)/27))
        p=p*p*(3-2*p)
        xx=-1.22+1.8*p
        cam=scene.camera
        cam.location=(xx,-1.65,1.55)
        target=Vector((xx,0,.31))
        cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.data.dof.focus_distance=(target-cam.location).length
    else:
        scene.frame_set(frame)
    scene.render.filepath=str(frames_dir/f"frame_{frame:04d}.png")
    bpy.ops.render.render(write_still=True)
    print("REAL_CYCLES_CGI_FRAME",frame,"/",FRAME_COUNT,flush=True)
print("REAL_CGI_VIDEO_NOT_YET_AUDIO_APPROVED",json.dumps(report),flush=True)
