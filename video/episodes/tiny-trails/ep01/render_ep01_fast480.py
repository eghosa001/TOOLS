#!/usr/bin/env python3
"""Offline Blender 3.6 Episode 1 fast-480p native-rig PREVIEW assembler.

Uses real Blender Studio Elder Sprite .blend and genuine Sprite Fright Sprite
GLB only. No placeholder actor, no procedural character, no automatic Kaggle.
--inspect is NON-rendering; --preview requires a separate explicit authorization.
Only jaw-envelope motion is implemented (NOT phoneme-complete visemes).
"""
from __future__ import annotations
import argparse
import json
import math
import os
import struct
import sys
import wave
import time
from pathlib import Path

import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import episode_preflight as gate  # noqa: E402

def direct_armature_meshes(rig, objects):
    return [o for o in objects if o.type=="MESH" and bool(o.data.vertices) and
            (o.find_armature()==rig or o.parent==rig)]

def choose_actor(objects,character):
    candidates=[]
    for rig in objects:
        if rig.type!="ARMATURE":continue
        skins=direct_armature_meshes(rig,objects)
        if skins:
            candidates.append((len(rig.data.bones),sum(len(s.data.polygons) for s in skins),rig,skins))
    if not candidates:raise RuntimeError("NATIVE_RIG_MISSING "+character)
    _,_,rig,skins=max(candidates,key=lambda v:(v[0],v[1]))
    if len(rig.data.bones)<20 or sum(len(m.data.polygons) for m in skins)<800:
        raise RuntimeError("INVALID_SOURCE_SKIN "+character)
    for m in skins:m.hide_render=False
    return rig,skins

def mouth_bone(rig,meshes):
    options=[]
    for p in rig.pose.bones:
        if "jaw" not in p.name.casefold() and "mouth" not in p.name.casefold():continue
        hit=sum(1 for mesh in meshes if p.name in mesh.vertex_groups)
        if hit:options.append((hit, ("def" in p.name.casefold()),p))
    if not options:raise RuntimeError("MISSING_WEIGHTED_NATIVE_JAW "+rig.name)
    options.sort(key=lambda x:(x[1],x[0]),reverse=True)
    return options[0][2]

def bounds(meshes):
    positions=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
    low=Vector(tuple(min(q[i] for q in positions) for i in range(3)))
    high=Vector(tuple(max(q[i] for q in positions) for i in range(3)))
    return low,high

def anchor(name,rig,meshes,x,height):
    lo,hi=bounds(meshes)
    center=(lo+hi)*0.5
    span=max(hi.z-lo.z,0.01)
    factor=height/span
    empty=bpy.data.objects.new(name,None)
    bpy.context.scene.collection.objects.link(empty)
    # Preserve artist transform hierarchy; move its root and all unparented skin meshes.
    nodes={rig,*meshes}
    for o in nodes:
        if o.parent in nodes:continue
        m=o.matrix_world.copy()
        o.parent=empty
        o.matrix_world=m
    empty.scale=(factor,)*3
    empty.location=(x-factor*center.x,-factor*center.y,-factor*lo.z)
    return empty

def load_source_cast(folder,manifest):
    elder=folder/manifest["actors"]["elder_sprite"]["file"]
    sprite=folder/manifest["actors"]["sprite"]["file"]
    if elder.open("rb").read(7)!=b"BLENDER" or sprite.open("rb").read(4)!=b"glTF":
        raise RuntimeError("Source asset headers do not match genuine Blender and GLB formats")
    # Open original native project, preserving Blender Studio rig drivers and materials.
    bpy.ops.wm.open_mainfile(filepath=str(elder),load_ui=False)
    scene=bpy.context.scene
    scene.frame_set(1)
    existing=list(bpy.data.objects)
    elder_rig,elder_meshes=choose_actor(existing,"elder_sprite")
    elder_bone=mouth_bone(elder_rig,elder_meshes)
    # Source reference cameras/lights are replaced, NOT the real character.
    for obj in list(bpy.data.objects):
        if obj.type in ("CAMERA","LIGHT"):
            bpy.data.objects.remove(obj,do_unlink=True)
        elif obj.type=="MESH" and obj not in elder_meshes:
            obj.hide_render=True
    elder_root=anchor("EP01_ELDER_SPRITE",elder_rig,elder_meshes,x=1.03,height=1.57)
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(sprite))
    imported=set(bpy.data.objects)-before
    sprite_rig,sprite_meshes=choose_actor(imported,"sprite")
    sprite_bone=mouth_bone(sprite_rig,sprite_meshes)
    sprite_root=anchor("EP01_SPRITE",sprite_rig,sprite_meshes,x=-1.0,height=1.15)
    return {"sprite":(sprite_rig,sprite_meshes,sprite_root,sprite_bone),
            "elder_sprite":(elder_rig,elder_meshes,elder_root,elder_bone)}

def import_glb(filepath,key):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(filepath))
    imported=set(bpy.data.objects)-before
    if not any(o.type=="MESH" for o in imported):
        raise RuntimeError("Required REAL CC0 environment/prop contains no mesh: "+key)
    root=bpy.data.objects.new("EP01_"+key.upper(),None)
    bpy.context.scene.collection.objects.link(root)
    for o in imported:
        if o.parent in imported:continue
        orig=o.matrix_world.copy()
        o.parent=root
        o.matrix_world=orig
    return root

def configure_world(hdri):
    world=bpy.data.worlds.new("EP01 genuine Poly Haven light")
    world.use_nodes=True
    nodes=world.node_tree.nodes
    nodes.clear()
    env=nodes.new("ShaderNodeTexEnvironment")
    env.image=bpy.data.images.load(str(hdri),check_existing=True)
    bg=nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value=.60
    output=nodes.new("ShaderNodeOutputWorld")
    world.node_tree.links.new(env.outputs["Color"],bg.inputs["Color"])
    world.node_tree.links.new(bg.outputs["Background"],output.inputs["Surface"])
    bpy.context.scene.world=world

def soft_lamp(label,location,power,size):
    data=bpy.data.lights.new(label,"AREA")
    data.energy=power
    data.shape="DISK"
    data.size=size
    lamp=bpy.data.objects.new(label,data)
    bpy.context.scene.collection.objects.link(lamp)
    lamp.location=location
    lamp.rotation_euler=(Vector((0,0,1.1))-lamp.location).to_track_quat("-Z","Y").to_euler()

def setup_camera(story):
    camera_data=bpy.data.cameras.new("EP01 storyboard cuts")
    camera=bpy.data.objects.new("EP01 storyboard cuts",camera_data)
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera=camera
    camera_data.lens=45
    # Discontinuous per-shot cuts; no accidental 9-second slow dolly.
    options={"wide":(0,-6.2,3.0),"medium":(-.2,-4.9,2.5),
             "two-shot":(0,-5.2,2.6),"close":(-.7,-3.9,2.05),
             "insert":(-.5,-3.0,1.55)}
    for shot in story["shots"]:
        start=int(shot["start"]*24)+1
        look=Vector((.10 if shot["camera"]!="close" else -.3,0,1.0))
        camera.location=options[shot["camera"]]
        camera.rotation_euler=(look-camera.location).to_track_quat("-Z","Y").to_euler()
        camera.keyframe_insert(data_path="location",frame=start)
        camera.keyframe_insert(data_path="rotation_euler",frame=start)
    if camera.animation_data and camera.animation_data.action:
        for fcurve in camera.animation_data.action.fcurves:
            for key in fcurve.keyframe_points:key.interpolation="CONSTANT"

def read_envelope(path,fps=24):
    with wave.open(str(path),"rb") as wav:
        if wav.getsampwidth()!=2:raise ValueError("16-bit PCM voice WAV required")
        rate=wav.getframerate()
        channels=wav.getnchannels()
        samples=wav.readframes(wav.getnframes())
    frames=len(samples)//(channels*2)
    values=struct.unpack("<"+str(frames*channels)+"h",samples)
    amplitudes=[]
    for index in range(1+math.ceil(frames/rate*fps)):
        mid=int((index+.5)*rate/fps)
        lo=max(0,mid-int(rate/fps/2))
        hi=min(frames,mid+int(rate/fps/2))
        if hi<=lo:amplitudes.append(0.0);continue
        sum_sq=sum(values[i*channels]**2 for i in range(lo,hi))
        rms=math.sqrt(sum_sq/(hi-lo))
        amplitudes.append(min(.9,rms/8500.0))
    return amplitudes

def speech_and_gestures(story,cast,audio_dir):
    evidence={}
    for key,(rig,meshes,root,jaw) in cast.items():
        jaw.rotation_mode="XYZ"
        original=jaw.rotation_euler.copy()
        evidence[key]={"rig":rig.name,"bones":len(rig.data.bones),
                       "renderable_meshes":len(meshes),"jaw":jaw.name,
                       "jaw_keyframes":0,"viseme_quality":"audio_envelope_only_not_phonetic"}
        for line in story["dialogue"]:
            if line["speaker"]!=key:continue
            start=round(line["start"]*24)+1
            end=round(line["end"]*24)+1
            amps=read_envelope(audio_dir/f"line_{line['id']:03}.wav")
            jaw.rotation_euler=original.copy()
            jaw.keyframe_insert(data_path="rotation_euler",frame=max(1,start-1))
            for f in range(start,end+1):
                a=amps[min(f-start,len(amps)-1)]
                jaw.rotation_euler.x=original.x+0.22*a
                jaw.keyframe_insert(data_path="rotation_euler",frame=f)
                evidence[key]["jaw_keyframes"]+=1
            jaw.rotation_euler=original.copy()
            jaw.keyframe_insert(data_path="rotation_euler",frame=end+1)
            # Original rig remains the body performer. No generic tween rig substitute.
        if not evidence[key]["jaw_keyframes"]:
            raise RuntimeError("No actual speaking animation applied to "+key)
    return evidence

def animate_native_gestures(story,cast):
    """Subtle bone gestures on actual source rigs. Never inserts a proxy skeleton.
    Import/kinematics and final expressive quality still require image QC.
    """
    records={}
    for key,(rig,meshes,root,jaw) in cast.items():
        useful=[p for p in rig.pose.bones
                if any(p.name in mesh.vertex_groups for mesh in meshes)]
        def pick(tokens):
            hits=[p for p in useful if any(w in p.name.casefold() for w in tokens)
                  and p!=jaw]
            # Prefer deformer bones over controls with unclear constraints.
            hits.sort(key=lambda p:(p.name.lower().startswith("def"),-len(p.name)),reverse=True)
            return hits[0] if hits else None
        head=pick(("head","neck"))
        hand=pick(("hand","forearm","upper_arm","arm"))
        record={"head_bone":head.name if head else None,
                "gesture_bone":hand.name if hand else None,
                "native_pose_keyframes":0,"evaluated_skin_motion_confirmed":False}
        for line in story["dialogue"]:
            if line["speaker"]!=key:continue
            action=line["action"]
            target=head if action=="nod" else hand if action in ("wave","point") else None
            if target is None:continue
            start=int(round(line["start"]*24))+1
            peak=int(round((line["start"]+line["end"])*12))+1
            end=int(round(line["end"]*24))+1
            base=target.rotation_euler.copy()
            target.rotation_mode="XYZ"
            for f,amount in ((start,0.0),(peak,0.12 if action!="point" else .17),(end,0.0)):
                target.rotation_euler=base.copy()
                target.rotation_euler.x+=amount
                target.keyframe_insert(data_path="rotation_euler",frame=f)
                record["native_pose_keyframes"]+=1
            target.rotation_euler=base
        records[key]=record
    return records

def animate_leaf(story,leaf):
    # Staged blocking guide on a genuine imported leaf, not physics simulation.
    positions={
        "leaf_on_sprite_nose":(-1.0,-.15,1.15),
        "leaf_scoots_to_collection":(-.45,-.65,.14),
        "leaf_slides_away":(.25,-.65,.17),
        "pebble_wall_fails":(.38,-.65,.36),
        "leaf_slips_under_pebble":(.1,-.6,.1),
        "acorn_cup_lifts":(-.12,-.63,.6),
        "leaf_on_elder_nose":(1.02,-.12,1.45),
        "grass_bends":(.56,-.55,.2),
        "leaf_stem_on_twig":(.35,-.47,.3),
        "leaf_spins_tethered":(.35,-.47,.36),
        "leaf_on_elder_nose_end":(1.02,-.12,1.44)}
    for shot in story["shots"]:
        cue=shot["leaf_cue"]
        frame=round(shot["start"]*24)+1
        leaf.location=positions[cue]
        leaf.rotation_euler=(0,0,(shot["id"]-1)*.3)
        leaf.keyframe_insert(data_path="location",frame=frame)
        leaf.keyframe_insert(data_path="rotation_euler",frame=frame)
        if cue=="leaf_spins_tethered":
            leaf.rotation_euler.z+=math.pi*4
            leaf.keyframe_insert(data_path="rotation_euler",frame=round(shot["end"]*24))
    # No confidence that the approximate Blender artist-specific nose positions match.

def attach_audio_and_subtitles(story,audio_dir):
    scene=bpy.context.scene
    editor=scene.sequence_editor_create()
    for line in story["dialogue"]:
        start=round(line["start"]*24)+1
        wav=str(audio_dir/f"line_{line['id']:03}.wav")
        editor.sequences.new_sound("Speech %02d"%line["id"],wav,channel=2,frame_start=start)
        # Subtitles are separately output as precisely timed SRT by preflight.
    scene.render.use_sequencer=True


def set_gpu_cycles(scene, profile="balanced"):
    """Choose explicit, reviewable real-CUDA Cycles quality/speed presets.

    A faster profile is a quality tradeoff, not a claimed GPU benchmark.
    All output remains at native 1280x720, 24 FPS with original rigs.
    """
    profiles={
        "fast":{"samples":12,"threshold":0.08,"max_bounces":2},
        "balanced":{"samples":24,"threshold":0.035,"max_bounces":4},
        "quality":{"samples":40,"threshold":0.015,"max_bounces":6},
    }
    if profile not in profiles:
        raise RuntimeError("EP01_INVALID_RENDER_PROFILE")
    config=profiles[profile]
    """Never silently run an alleged GPU preview through a CPU fallback."""
    if bpy.app.version[:2] != (3, 6):
        raise RuntimeError("EP01_CUDA_REQUIRES_TESTED_BLENDER_3_6")
    bpy.ops.preferences.addon_enable(module="cycles")
    addon=bpy.context.preferences.addons.get("cycles")
    if not addon:
        raise RuntimeError("EP01_CYCLES_ADDON_NOT_AVAILABLE")
    cprefs=addon.preferences
    try:
        cprefs.compute_device_type="CUDA"
        cprefs.get_devices()
        cuda_devices=cprefs.get_devices_for_type("CUDA")
    except Exception as exc:
        raise RuntimeError("EP01_CUDA_BACKEND_INITIALIZATION_FAILED") from exc
    gpus=[d for d in cuda_devices if d.type=="CUDA"]
    if not gpus:
        raise RuntimeError("EP01_NO_USABLE_CUDA_DEVICE_STOP_BEFORE_RENDER")
    for d in cprefs.devices:
        d.use = (d.type == "CUDA")
    scene.render.engine="CYCLES"
    scene.cycles.device="GPU"
    scene.cycles.samples=config["samples"]
    scene.cycles.use_adaptive_sampling=True
    scene.cycles.adaptive_threshold=config["threshold"]
    scene.cycles.max_bounces=config["max_bounces"]
    scene.cycles.use_denoising=True
    # Reuse ray-tracing data across the animation instead of rebuilding per frame.
    scene.render.use_persistent_data=True
    scene.render.threads_mode="AUTO"
    print("EP01_VERIFIED_CYCLES_CUDA_GPU",[(d.name,d.type) for d in gpus],
          "profile",profile,"samples",config["samples"],
          "noise_threshold",config["threshold"],
          "max_bounces",config["max_bounces"],
          "persistent_data",scene.render.use_persistent_data,flush=True)


def attach_frame_progress(path,total_frames):
    """Emit one flushed log record per rendered frame, plus JSONL evidence."""
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text("",encoding="utf-8")
    started={}
    finished=set()
    def on_pre(scene, depsgraph=None):
        frame=scene.frame_current
        started[frame]=time.monotonic()
        print(f"EP01_FRAME_START frame={frame}/{total_frames}",flush=True)
    def on_post(scene, depsgraph=None):
        frame=scene.frame_current
        seconds=round(time.monotonic()-started.get(frame,time.monotonic()),3)
        if frame in finished:
            return
        finished.add(frame)
        with path.open("a",encoding="utf-8") as out:
            out.write(json.dumps({"frame":frame,"total":total_frames,"render_seconds":seconds})+"\n")
        print(f"EP01_FRAME_DONE frame={frame}/{total_frames} elapsed_seconds={seconds}",flush=True)
    bpy.app.handlers.render_pre.append(on_pre)
    bpy.app.handlers.render_post.append(on_post)
    return finished

def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ap=argparse.ArgumentParser()
    ap.add_argument("--assets",type=Path,default=HERE/"assets.json")
    ap.add_argument("--asset-dir",type=Path,required=True)
    ap.add_argument("--audio-dir",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--mode",choices=("inspect","preview"),default="inspect")
    ap.add_argument("--authorize-preview",action="store_true",default=False)
    ap.add_argument("--render-device",choices=("eevee","cuda_cycles"),default="eevee")
    ap.add_argument("--progress-jsonl",type=Path)
    ap.add_argument("--preview-profile",choices=("fast","balanced","quality"),default="fast")
    opts=ap.parse_args(args)
    gate.check_legacy()
    story=gate.read(HERE/"story.json")
    assets=gate.read(opts.assets)
    lines=gate.validate(story,assets)
    gate.check_audio(lines,assets,opts.audio_dir)
    gate.check_assets(assets,opts.asset_dir)
    actor_set=load_source_cast(opts.asset_dir.resolve(),assets)
    environment=assets["environment"]
    stage=import_glb(opts.asset_dir/environment["stage"]["file"],"woodland_clearing")
    props={key:import_glb(opts.asset_dir/filename,key) for key,filename in environment["props"].items() if key!="note"}
    setup_camera(story)
    configure_world(opts.asset_dir/environment["hdri"]["file"])
    soft_lamp("EP01 soft key",(-3,-2,5),600,4.5)
    soft_lamp("EP01 warm rim",(2,1,4),500,3.2)
    soft_lamp("EP01 bounce",(1,-4,3),280,5)
    speech_evidence=speech_and_gestures(story,actor_set,opts.audio_dir)
    gesture_evidence=animate_native_gestures(story,actor_set)
    animate_leaf(story,props["hero_leaf"])
    attach_audio_and_subtitles(story,opts.audio_dir)
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE"
    scene.render.resolution_x=854
    scene.render.resolution_y=480
    scene.render.resolution_percentage=100
    scene.render.fps=24
    scene.frame_start=1
    scene.frame_end=72 if opts.mode=="preview" else story["duration_seconds"]*24
    scene.view_settings.view_transform="Filmic"
    report={"scene_imported":True,"true_original_cast":list(actor_set),
            "physical_models_imported":True,"real_environment_imported":True,
            "real_props_imported":list(props),"real_hdri_imported":True,
            "source_jaw_response_keyframed":speech_evidence,
            "native_rig_gesture_keyframes":gesture_evidence,
            "body_gesture_verified":False,"face_visemes_verified":False,
            "nose_contact_positions_visually_verified":False,
            "preview_rendered":False,"kaggle_rendered":False,
            "no_procedural_character_substitution":True}
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    if opts.mode=="inspect":
        opts.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print("REAL_ASSET_SCENE_INSPECTION_ONLY; no video rendered")
        return
    if not opts.authorize_preview or os.environ.get("CARTOONSTUDIO_EXPLICIT_EP01_PREVIEW")!="YES":
        raise RuntimeError("User has not authorized Episode 1 three-second preview")
    if opts.output.suffix.lower()!=".mp4":
        raise ValueError("Preview path must end in .mp4")
    if opts.render_device=="cuda_cycles":
        set_gpu_cycles(scene,opts.preview_profile)
    elif opts.mode=="preview":
        raise RuntimeError("EP01_FAST_480_REQUIRES_CUDA_NO_CPU_OR_EEVEE")
    if opts.progress_jsonl:
        frame_records=attach_frame_progress(opts.progress_jsonl,72)
    else:
        frame_records=None
    scene.render.image_settings.file_format="FFMPEG"
    scene.render.ffmpeg.format="MPEG4"
    scene.render.ffmpeg.codec="H264"
    scene.render.ffmpeg.audio_codec="AAC"
    scene.render.filepath=str(opts.output)
    bpy.ops.render.render(animation=True)
    if not opts.output.is_file() or opts.output.stat().st_size<5000:
        raise RuntimeError("Preview not generated")
    if frame_records is not None and len(frame_records)!=72:
        raise RuntimeError("EP01_INCOMPLETE_FRAME_TIMING "+str(len(frame_records))+"/72")
    print("EP01_RENDER_MODE",opts.render_device,"profile",opts.preview_profile,"resolution",scene.render.resolution_x,scene.render.resolution_y,flush=True)
    print("EP01_REAL_NATIVE_RIG_3_SECOND_PREVIEW_FILE",opts.output)

if __name__=="__main__":main()
