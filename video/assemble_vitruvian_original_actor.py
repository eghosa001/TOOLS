#!/usr/bin/env python3
"""Assemble genuine third-party Vitruvian body/head and test speech visemes.

No invented character mesh, no canon mapping, no episode render. Source binaries
are read from input and never written into repository or uploaded as raw output.
Rhubarb cues must come from real spoken WAV with exact text (separate workflow).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import wave
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

# Blender --python does not always add the script folder to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_imported_high_detail_visemes import candidate, compare, screenshot

BONE_NAME = "mixamorig_Head"
FPS = 24
SHAPES = ("Mouth_Large_Opened", "Jaw_Lower", "aa", "ow", "p_b_m", "f_v", "ey_eh_uh")
# Official Rhubarb 2D mouth cues A=closed MBP, B=teeth, C=EH,
# D=wide open, E=rounded O, F=puckered U, G=F/V, H=tongue/L, X=rest.
# Existing artist-authored FACS morphs are used, not sculpted substitutes.
MAP = {
    "A": {"p_b_m": 0.96},
    "B": {"ey_eh_uh": 0.34},
    "C": {"ey_eh_uh": 0.64, "Mouth_Large_Opened": 0.13},
    "D": {"aa": 0.9, "Mouth_Large_Opened": 0.22},
    "E": {"ow": 0.8},
    "F": {"ow": 0.95},
    "G": {"f_v": 0.9},
    "H": {"ey_eh_uh": 0.52},
    "X": {},
}


def hashfile(path):
    with path.open("rb") as reader:
        return hashlib.file_digest(reader, "sha256").hexdigest()


def mesh_points(mesh, count=200):
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data = evaluated.to_mesh()
    try:
        step = max(1, len(data.vertices) // count)
        return [evaluated.matrix_world @ data.vertices[i].co for i in range(0, len(data.vertices), step)]
    finally:
        evaluated.to_mesh_clear()


def difference(before, after):
    if len(before) != len(after):
        raise RuntimeError("Unexpected head mesh topology changed during attachment")
    values = [(p - q).length for p, q in zip(before, after)]
    return {"moved_samples": sum(x > 0.0001 for x in values),
            "maximum_world_motion": round(max(values, default=0), 7)}


def read_cues(path, audio):
    with wave.open(str(audio), "rb") as wav:
        duration = wav.getnframes() / wav.getframerate()
        if wav.getsampwidth() != 2 or wav.getnchannels() not in (1, 2):
            raise ValueError("Require 16-bit PCM diagnostic WAV")
    raw = json.loads(path.read_text(encoding="utf-8"))
    cues = raw.get("mouthCues")
    if not isinstance(cues, list) or not 3 <= len(cues) < 1000:
        raise ValueError("Actual Rhubarb mouthCues missing")
    previous = 0.0
    unique = set()
    for cue in cues:
        if not isinstance(cue, dict) or cue.get("value") not in MAP:
            raise ValueError("Unexpected Rhubarb 2D mouth cue")
        start, end = cue.get("start"), cue.get("end")
        if type(start) not in (float, int) or type(end) not in (float, int):
            raise ValueError("Missing numeric lip cue boundaries")
        if start < previous - 0.005 or end <= start or end > duration + 0.1:
            raise ValueError("Overlapping/out-of-order/out-of-audio Rhubarb cue")
        previous = end
        unique.add(cue["value"])
    if len(unique - {"X"}) < 3:
        raise RuntimeError("Speech sample did not produce three distinctive lip-cue types")
    return cues, duration, unique


def matching_armature(objects):
    """Godot's Mixamo head bone name may be normalized during Blender glTF import."""
    global BONE_NAME
    arms = [o for o in objects if o.type == "ARMATURE"]
    def normalize(name):
        return "".join(letter for letter in name.casefold() if letter.isalnum())
    # Don't pick a neck or auxiliary end bone just because it contains 'Head'.
    preferred = []
    for arm in arms:
        matching = [p.name for p in arm.pose.bones if normalize(p.name) == "mixamorighead"]
        if not matching:
            matching = [p.name for p in arm.pose.bones
                        if normalize(p.name) == "head" or normalize(p.name).endswith("mixamorighead")]
        if matching:
            preferred.append((arm, matching[0]))
    if len(preferred) != 1:
        diagnostics = {arm.name: [p.name for p in arm.pose.bones if "head" in p.name.casefold()]
                       for arm in arms}
        raise RuntimeError("Cannot identify unique original human Head bone: " + repr(diagnostics))
    armature, BONE_NAME = preferred[0]
    print("ORIGINAL_MIXAMO_HEAD_BONE_RESOLVED",armature.name,BONE_NAME,flush=True)
    return armature


def attach_head_roots(head_objects, rig):
    """Maintain original head/eye transforms with an evaluated Child Of bone anchor."""
    scene = bpy.context.scene
    anchor = bpy.data.objects.new("CartoonStudio_imported_original_head_follow_bone", None)
    scene.collection.objects.link(anchor)
    anchor.empty_display_type = "PLAIN_AXES"
    anchor.matrix_world = Matrix.Identity(4)
    roots = [o for o in head_objects if o.parent not in head_objects]
    if not roots:
        raise RuntimeError("No imported original head/eye hierarchy roots")
    for original in roots:
        original_world = original.matrix_world.copy()
        original.parent = anchor
        original.matrix_world = original_world
    bpy.context.view_layer.update()
    constraint = anchor.constraints.new("CHILD_OF")
    constraint.name = "Original_Mixamo_Head_Follow"
    constraint.target = rig
    constraint.subtarget = BONE_NAME
    # Neutralizes the source bone's rest transform, avoiding double-offset.
    bone_world = rig.matrix_world @ rig.pose.bones[BONE_NAME].matrix
    constraint.inverse_matrix = bone_world.inverted_safe()
    bpy.context.view_layer.update()
    return anchor, roots


def drive_visemes(face, frames, controls, cues):
    scene = bpy.context.scene
    current = {name: 0.0 for name in MAP["D"] | MAP["A"] | MAP["B"] | MAP["E"] | MAP["G"] | MAP["H"]}
    current.update({name: 0.0 for name in controls})
    records = []
    for frame in range(1, frames + 1):
        t = (frame - 1) / FPS
        cue = next((c["value"] for c in cues if c["start"] <= t < c["end"]), "X")
        target = MAP[cue]
        scene.frame_set(frame)
        for label, shape in controls.items():
            # Two-frame low-pass on cue switches; no mouth movement over silence.
            current[label] = max(0.0, min(1.0, 0.48 * current[label] + 0.52 * target.get(label, 0)))
            shape.value = current[label]
            shape.keyframe_insert(data_path="value", frame=frame)
        records.append({"frame": frame, "time": round(t, 4), "rhubarb": cue,
                        "facs": {label: round(current[label], 3) for label in controls
                                 if current[label] > 0.04}})
    return records


def verify_pose_follow(rig, face, anchor):
    scene = bpy.context.scene
    pose = rig.pose.bones[BONE_NAME]
    scene.frame_set(1)
    bpy.context.view_layer.update()
    before = mesh_points(face)
    anchor_neutral = anchor.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()
    original_rotation_mode = pose.rotation_mode
    pose.rotation_mode = "QUATERNION"
    original_rotation = pose.rotation_quaternion.copy()
    pose.rotation_quaternion = original_rotation @ Quaternion((0, 0, 1), math.radians(16))
    bpy.context.view_layer.update()
    moved = mesh_points(face)
    anchor_pose = anchor.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()
    delta = difference(before, moved)
    pose.rotation_quaternion = original_rotation
    pose.rotation_mode = original_rotation_mode
    bpy.context.view_layer.update()
    baseline_restored = difference(before, mesh_points(face))
    if delta["moved_samples"] < 20 or delta["maximum_world_motion"] < 0.003:
        raise RuntimeError("Actual original head vertices do not follow changed body head bone")
    if baseline_restored["maximum_world_motion"] > 0.0003:
        raise RuntimeError("Head failed to return to neutral after body bone movement")
    if (anchor_pose.translation - anchor_neutral.translation).length < 0.0003 and (
            anchor_pose.to_quaternion().rotation_difference(anchor_neutral.to_quaternion()).angle < 0.01):
        raise RuntimeError("Head anchor did not follow the original body head bone")
    return {"head_bone": BONE_NAME, "measured_pose_samples": delta,
            "returned_to_rest": baseline_restored,
            "original_head_bone_changed_rig": True}



def verify_real_body_action(rig):
    """Play an existing author-retargeted Mixamo action and measure actual bone pose."""
    scene = bpy.context.scene
    ad = rig.animation_data or rig.animation_data_create()
    original_action = ad.action
    track_states = [(track, track.mute) for track in ad.nla_tracks]
    actions = [a for a in bpy.data.actions
               if any("pose.bones" in fc.data_path for fc in a.fcurves)]
    actions.sort(key=lambda a: (
        0 if "walk" in a.name.casefold() else
        1 if "wave" in a.name.casefold() else
        2 if "sway" in a.name.casefold() else 3, a.name))
    if not actions:
        raise RuntimeError("The original body has no imported pose-bone animation actions")
    for track,_ in track_states:
        track.mute = True
    recorded = []
    try:
        for action in actions[:8]:
            ad.action = action
            low, high = map(float, action.frame_range)
            frames = sorted(set([int(round(low)), int(round(low+(high-low)*.25)),
                                 int(round(low+(high-low)*.50)), int(round(low+(high-low)*.75))]))
            if len(frames)<3:
                continue
            results = []
            for frame in frames:
                scene.frame_set(frame)
                bpy.context.view_layer.update()
                results.append({p.name: (p.matrix.translation.copy(),p.matrix.to_quaternion().copy())
                                for p in rig.pose.bones})
            baseline = results[0]
            translation = 0.0
            rotation = 0.0
            for result in results[1:]:
                for bone,(location,quat) in result.items():
                    first_location,first_quat=baseline[bone]
                    translation=max(translation,(location-first_location).length)
                    rotation=max(rotation,first_quat.rotation_difference(quat).angle)
            recorded.append({"source_action":action.name,"sample_frames":frames,
                             "max_bone_position_change":round(translation,6),
                             "max_bone_rotation_change_rad":round(rotation,6),
                             "real_skeletal_motion":translation>0.01 or rotation>0.04})
            print("ORIGINAL_MIXAMO_ACTION_BONE_MOVEMENT",action.name,
                  round(translation,5),round(rotation,5),flush=True)
            if recorded[-1]["real_skeletal_motion"]:
                break
    finally:
        ad.action = original_action
        for track,muted in track_states:
            track.mute = muted
        scene.frame_set(1)
        bpy.context.view_layer.update()
    if not any(r["real_skeletal_motion"] for r in recorded):
        raise RuntimeError("Original full-body source actions have no measured skeletal motion")
    return {"body_skeleton_action_playback_verified":True,
            "actual_motion_actions":recorded,
            "original_animation_actions_unmodified":True}

def main(head, body, audio, cue_file, output):
    head, body, audio, cue_file, output = map(lambda p: Path(p).resolve(),
                                              (head, body, audio, cue_file, output))
    if not all(path.is_file() for path in (head, body, audio, cue_file)):
        raise FileNotFoundError("One of original head/body, real spoken WAV or Rhubarb cue files is absent")
    if not 1_000_000 < head.stat().st_size < 100_000_000:
        raise RuntimeError("Expected genuine imported original full-quality human head GLB")
    if not 1_000_000 < body.stat().st_size < 100_000_000:
        raise RuntimeError("Expected genuine imported original full-quality rigged body GLB")
    input_hashes = {p.name: hashfile(p) for p in (head, body, audio, cue_file)}
    cues, duration, unique = read_cues(cue_file, audio)
    output.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    bpy.ops.import_scene.gltf(filepath=str(body))
    body_objs = set(bpy.data.objects)
    rig = matching_armature(body_objs)
    skinned = [o for o in body_objs if o.type == "MESH" and
               (o.parent == rig or any(m.type == "ARMATURE" and m.object == rig for m in o.modifiers))]
    if sum(len(o.data.vertices) for o in skinned) < 10_000:
        raise RuntimeError("Authentic body lacks high-resolution skinned armature meshes")
    body_actions = sorted(a.name for a in bpy.data.actions)
    if not body_actions:
        raise RuntimeError("Original rigged body has no imported animation action assets")
    bpy.ops.import_scene.gltf(filepath=str(head))
    head_objs = set(bpy.data.objects) - body_objs
    faces = [o for o in head_objs if o.type == "MESH" and o.data.shape_keys and
             candidate("Mouth_Large_Opened", list(o.data.shape_keys.key_blocks)[1:])]
    if not faces:
        raise RuntimeError("Original head import missing CC0 actual FACS morphs")
    face = max(faces, key=lambda o: len(o.data.vertices))
    keys = list(face.data.shape_keys.key_blocks)[1:]
    controls = {label: candidate(label, keys) for label in SHAPES}
    if any(controls[label] is None for label in ("Mouth_Large_Opened", "aa", "ow", "p_b_m", "f_v", "ey_eh_uh")):
        raise RuntimeError("Required original full mouth FACS shape set incomplete")
    controls = {label: shape for label, shape in controls.items() if shape is not None}
    actual = {}
    for label, key in controls.items():
        actual[label] = compare(face, key, 1.0)
        key.value = 0
    if not all(actual[label]["real_world_deformation"] for label in ("Mouth_Large_Opened","aa","ow","p_b_m")):
        raise RuntimeError("Source FACS visemes failed actual evaluated deforming-mesh check")
    bpy.context.view_layer.update()
    baseline = mesh_points(face)
    anchor, roots = attach_head_roots(head_objs, rig)
    rest = difference(baseline, mesh_points(face))
    if rest["maximum_world_motion"] > 0.001:
        raise RuntimeError("Attaching head to body caused a visible neutral-rest position jump")

    # Clear mouth before following test; armature actions imported, never overwritten.
    pose_result = verify_pose_follow(rig, face, anchor)
    body_motion = verify_real_body_action(rig)
    scene.frame_start = 1
    scene.frame_end = math.ceil(duration * FPS)
    # Use actual Rhubarb recognizer output rather than an RMS-only mouth-open toggle.
    animation = drive_visemes(face, scene.frame_end, controls, cues)
    scene.frame_set(1)
    neutral_frame = next((x["frame"] for x in animation if x["rhubarb"]=="X"),1)
    open_frames = [x for x in animation if x["rhubarb"] in ("C","D","E","F")]
    if not open_frames:
        raise RuntimeError("Real audio recognizer produced no open-mouth phoneme frames")

    # Frames remain an isolated test. Never render a canonical scene or full episode.
    for shape in controls.values():
        shape.value = 0
    scene.frame_set(neutral_frame)
    for shape in controls.values():
        shape.value = 0
    screenshot([o for o in head_objs | body_objs if o.type=="MESH"],
               scene, output / "original-body-following-head-neutral.png")
    strongest = max(open_frames,key=lambda f: sum(f["facs"].values()))
    scene.frame_set(strongest["frame"])
    scene.render.filepath = str(output / "original-speech-viseme-frame.png")
    bpy.ops.render.render(write_still=True)

    evidence = {
        "source":"ibrews/VitruvianGodot original authored CC0 FACS head + rigged Mixamo-derived body",
        "input_source_hashes":input_hashes,
        "body_bones":len(rig.data.bones),
        "actual_existing_skinned_body_vertices":sum(len(o.data.vertices) for o in skinned),
        "body_animation_actions_in_source":body_actions,
        "original_face_mesh_vertices":len(face.data.vertices),
        "original_facials_measured":actual,
        "head_parent_constraint":"Original_Mixamo_Head_Follow",
        "original_head_imported_hierarchy_roots":[o.name for o in roots],
        "head_did_not_jump_on_attachment":rest["maximum_world_motion"] <= 0.001,
        "head_follows_original_body_head_bone":pose_result,
        "recognizer":"DanielSWolf/Rhubarb Lip Sync, real WAV + unchanged dialogue, speaker-independent mouth cues",
        "actual_rhubarb_cues":len(cues),
        "distinct_mouth_cues":sorted(unique),
        "mapped_original_viseme_keys":sorted(controls.keys()),
        "animation_keyframed_frames":len(animation),
        "cue_frame_excerpt":animation[:16],
        "original_character_can_keep_moving_with_bone":True,
        "body_action_playback_deformation_tested": body_motion["body_skeleton_action_playback_verified"],
        "measured_original_animation":body_motion,
        "visual_lip_sync_quality_approved":False,
        "complete_studio_shading_verified":False,
        "head_and_body_materials_replaced_with_procedural":False,
        "actual_episode_rendered":False,
        "full_preview_rendered":False,
        "canon_or_voice_changed":False,
        "approved_main_character_mapping":False,
        "raw_body_or_mixamo_animations_uploaded":False,
        "license_gate":"CC0 face/CharMorph output; Adobe Mixamo permits commercial films, avoid redistributing raw animation files; confirm upstream and Adobe terms before production."
    }
    (output / "native-rig-attachment-and-real-rhubarb-lip-cues.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    if any(hashfile(p)!=digest for p,digest in [(head,input_hashes[head.name]),
       (body,input_hashes[body.name]),(audio,input_hashes[audio.name]),(cue_file,input_hashes[cue_file.name])]):
        raise RuntimeError("Original source file bytes changed during engineering audit")
    print("ACTUAL_IMPORTED_BODY_HEAD_ATTACHMENT_LIPSYNC_CUES_PASS",
          "bones",len(rig.data.bones),"viseme_frames",len(animation),
          "head_moved",pose_result["measured_pose_samples"],
          "rhubarb_shapes",sorted(unique),"mp4=false","canon=false", flush=True)

if __name__ == "__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=5:
        raise SystemExit("Blender --python assemble_vitruvian_original_actor.py -- HEAD.glb BODY.glb SPEECH.wav RHUBARB.json OUTPUT_DIR")
    main(*args)
