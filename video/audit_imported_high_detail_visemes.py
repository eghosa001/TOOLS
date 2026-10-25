#!/usr/bin/env python3
"""Audit a REAL high-detail CC0 Vitruvian source face and its existing visemes.

Imports published glTF with its actual artist meshes and morph targets; no
procedural character building, no series character reassignment, no episode MP4.
Uses actual WAV audio as a NON-CANON control test. A head is not yet a full
body-rigged speaking lead; body/clothing and licence need separate review.
"""
from __future__ import annotations
import hashlib,json,sys,math,shutil
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_native_wav_face_sync import envelope,read_wav,FPS

NAMES=["Mouth_Large_Opened","Jaw_Lower","aa","ow","p_b_m"]

def normalized(name):
    return "".join(c for c in name.casefold() if c.isalnum())

def candidate(shape_name,blocks):
    needle=normalized(shape_name)
    matches=[x for x in blocks if normalized(x.name)==needle or normalized(x.name).endswith(needle)]
    return matches[0] if matches else None

def verts(mesh,n=1600):
    deps=bpy.context.evaluated_depsgraph_get()
    obj=mesh.evaluated_get(deps)
    evaluated=obj.to_mesh()
    try:
        step=max(1,len(evaluated.vertices)//n)
        return [obj.matrix_world@evaluated.vertices[k].co for k in range(0,len(evaluated.vertices),step)]
    finally:
        obj.to_mesh_clear()

def compare(mesh,shape,value):
    shape.value=0
    bpy.context.view_layer.update()
    closed=verts(mesh)
    shape.value=value
    bpy.context.view_layer.update()
    opened=verts(mesh)
    diff=[(a-b).length for a,b in zip(closed,opened)]
    return {"tested_samples":len(diff),
            "changed_samples":sum(d>0.00003 for d in diff),
            "max_movement":round(max(diff,default=0.0),7),
            "real_world_deformation":sum(d>0.00003 for d in diff)>=5 and max(diff,default=0)>0.0001}

def screenshot(meshes,scene,target):
    # Camera and lights only: never generate a new character or modify its mesh.
    points=[]
    for mesh in meshes:
        if mesh.type!="MESH" or mesh.hide_render:
            continue
        world=mesh.matrix_world
        points.extend(world@Vector(corner) for corner in mesh.bound_box)
    if not points:
        raise RuntimeError("Source glTF contains no renderable geometry")
    center=sum(points,Vector((0,0,0)))/len(points)
    sizes=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
    unit=max(sizes)
    if unit<0.01:
        raise RuntimeError("Invalid imported character head dimensions")
    # Blender Studio face front orientation; two stills for visual assessment.
    camera_pos=center+Vector((0,-2.8*unit,0.2*unit))
    bpy.ops.object.camera_add(location=camera_pos)
    camera=bpy.context.object
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera=camera
    camera.data.type="ORTHO"
    camera.data.ortho_scale=1.4*unit
    for pos,energy in [((-.8,-1.0,.7),550),((.9,-.6,.9),420)]:
        bpy.ops.object.light_add(type="AREA",location=center+Vector(pos)*unit)
        lamp=bpy.context.object
        lamp.data.energy=energy*max(.2,unit)**2
        lamp.data.shape="DISK"
        lamp.data.size=max(unit,0.1)
    scene.render.engine="BLENDER_EEVEE"
    scene.render.resolution_x=640
    scene.render.resolution_y=640
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.render.filepath=str(target)
    bpy.ops.render.render(write_still=True)
    if not target.is_file() or target.stat().st_size<5000:
        raise RuntimeError("Actual imported head rendered no review image")

def main(source,wav,destination):
    source,wav,dest=Path(source).resolve(),Path(wav).resolve(),Path(destination).resolve()
    if source.suffix.lower()!=".glb" or not source.is_file() or source.stat().st_size<1_000_000:
        raise RuntimeError("High-quality original source glTF file missing")
    data,channels,rate,audio_sha=read_wav(wav)
    duration,rms,mouth=envelope(data,channels,rate)
    dest.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[obj for obj in bpy.data.objects if obj.type=="MESH" and obj.data is not None
            and obj.data.shape_keys is not None and len(obj.data.shape_keys.key_blocks)>1]
    if not meshes:
        raise RuntimeError("Third-party CC0 high-detail source has no imported shape-key meshes")
    combos=[]
    for mesh in meshes:
        opener=candidate("Mouth_Large_Opened",list(mesh.data.shape_keys.key_blocks)[1:])
        if opener:
            combos.append((len(mesh.data.vertices),mesh,opener))
    if not combos:
        raise RuntimeError("Source lacks published Mouth_Large_Opened target; cannot call this a third speaker")
    _,face,opener=max(combos,key=lambda x:x[0])
    blocks=list(face.data.shape_keys.key_blocks)[1:]
    shapes={}
    for label in NAMES:
        shape=candidate(label,blocks)
        if not shape:
            shapes[label]={"present":False,"real_world_deformation":False}
            continue
        shapes[label]={"present":True,"actual_name":shape.name,**compare(face,shape,1.0)}
        shape.value=0.0
    if not shapes["Mouth_Large_Opened"].get("real_world_deformation"):
        raise RuntimeError("Published CC0 open-mouth morph lacks visible evaluated head deformation")
    visemes=[name for name in ("aa","ow","p_b_m") if shapes[name].get("real_world_deformation")]
    if len(visemes)<2:
        raise RuntimeError("Two genuine independently deforming speech viseme morphs not verified")

    scene=bpy.context.scene
    scene.render.fps=FPS
    scene.render.fps_base=1
    scene.frame_start=1
    scene.frame_end=len(mouth)
    for i,amount in enumerate(mouth,1):
        scene.frame_set(i)
        opener.value=amount
        opener.keyframe_insert(data_path="value",frame=i)
    peak=max(range(len(mouth)),key=lambda i:mouth[i])
    scene.frame_set(peak+1)
    actual=compare(face,opener,mouth[peak])
    if not actual["real_world_deformation"]:
        raise RuntimeError("Voice-envelope-driven original high-quality face does not actually deform")

    # Evidence only: actual neutral and fully opened face PNGs, no frames of an episode.
    scene.frame_set(1)
    opener.value=0
    screenshot(meshes,scene,dest/"vitruvian-original-neutral-face.png")
    opener.value=1
    scene.render.filepath=str(dest/"vitruvian-original-open-mouth-face.png")
    bpy.ops.render.render(write_still=True)
    scene.frame_set(1)
    opener.value=mouth[0]
    native=dest/"vitruvian-cc0-head-spoken-audition.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(native),check_existing=False,compress=True)
    shutil.copyfile(wav,dest/"technical-verbatim-line.wav")
    evidence={
        "publisher":"ibrews/VitruvianGodot (CharMorph/Antonia CC0 facial asset)",
        "source_url":"https://github.com/ibrews/VitruvianGodot",
        "asset_license_claim":"CC0 1.0 for head; requires preservation of source NOTICE and verification before public release",
        "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_bytes":source.stat().st_size,
        "real_native_glb_import":True,
        "head_mesh":face.name,
        "face_vertices":len(face.data.vertices),
        "morph_count":len(blocks),
        "all_tested_morphs":shapes,
        "measured_visemes":visemes,
        "audio_duration_seconds":duration,
        "audio_sha256":audio_sha,
        "wav_driven_open_mouth_test":actual,
        "wave_frames_keyed":len(mouth),
        "visual_evidence":["vitruvian-original-neutral-face.png","vitruvian-original-open-mouth-face.png"],
        "head_only_not_approved_full_speaking_actor":True,
        "body_rig_and_godot_shader_compatibility_untested":True,
        "story_character_assignment":None,
        "original_dialogue_rewritten":False,
        "approved_series_voice":False,
        "phoneme_audio_alignment_verified":False,
        "user_character_canon_changed":False,
        "episode_video_rendered":False,
    }
    (dest/"vitruvian-real-cc0-speaking-face-proof.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print("REAL_THIRD_CC0_HIGH_DETAIL_FACE_VISEME_TEST_PASS",json.dumps({
        "vertices":len(face.data.vertices),"morphs":len(blocks),"true_visemes":visemes,
        "actual_audio_mouth_movement":actual,"head_only":True,
        "episode_render":False}),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3:
        raise SystemExit("Usage Blender --python audit_imported_high_detail_visemes.py -- HEAD.glb AUDIO.wav OUTPUT_DIR")
    main(*args)
