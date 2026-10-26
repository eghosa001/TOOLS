#!/usr/bin/env python3
"""Isolated speech-to-native-rig engineering audition; never renders an episode.

Drives an existing, measured mouth control from a spoken PCM WAV envelope,
writes a separate keyframed Blender copy, and checks evaluated real mesh motion.
This is amplitude-driven mouth opening, NOT phoneme/viseme lip-sync approval.
No new characters, meshes, models, canon changes, or production shots.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import sys
import wave
from pathlib import Path

import bpy

FPS = 24
MODELS = {"rain": ("shape", "mouth_open"), "sprite": ("bone", "DEF-Jaw"),
          "elder_sprite": ("bone", "DEF-Jaw"), "rex": ("bone", "DEF-Jaw")}


def read_wav(path):
    with wave.open(str(path), "rb") as handle:
        channels, width, rate = handle.getnchannels(), handle.getsampwidth(), handle.getframerate()
        if handle.getcomptype() != "NONE" or width != 2 or channels not in (1, 2):
            raise ValueError("Audition needs uncompressed mono/stereo 16-bit PCM WAV")
        frames = handle.readframes(handle.getnframes())
    import array
    values = array.array("h")
    values.frombytes(frames)
    if sys.byteorder != "little":
        values.byteswap()
    return values, channels, rate, hashlib.sha256(frames).hexdigest()


def envelope(samples, channels, rate):
    count = len(samples) // channels
    duration = count / rate
    if not (0.4 < duration < 30):
        raise ValueError("Spoken diagnostic sample length is outside 0.4–30 s")
    raw = []
    nframes = math.ceil(duration * FPS)
    for frame in range(nframes):
        center = round((frame + 0.5) * rate / FPS)
        half = max(1, round(0.045 * rate))
        low, high = max(0, center - half), min(count, center + half)
        stride = max(1, (high - low) // 2000)
        values = [samples[k * channels] / 32768 for k in range(low, high, stride)]
        raw.append(math.sqrt(sum(v * v for v in values) / len(values)) if values else 0.0)
    smoothed = [(raw[max(0, i - 1)] + 2 * raw[i] + raw[min(len(raw) - 1, i + 1)]) / 4
                for i in range(len(raw))]
    peak = max(smoothed, default=0)
    if peak <= 0.004:
        raise ValueError("WAV contains no measurable spoken audio")
    floor = max(0.004, 0.17 * peak)
    mouth = [round(max(0.0, min(1.0, (r - floor) / max(1e-6, peak - floor))) ** 0.7, 5)
             for r in smoothed]
    if sum(v > 0.2 for v in mouth) < 3 or sum(v < 0.04 for v in mouth) < 2:
        raise ValueError("Voice waveform must include both audible syllables and silence")
    return duration, smoothed, mouth


def mesh_vertices(mesh, sample_size=900):
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(deps)
    data = evaluated.to_mesh()
    try:
        step = max(1, len(data.vertices) // sample_size)
        return [evaluated.matrix_world @ data.vertices[k].co for k in range(0, len(data.vertices), step)]
    finally:
        evaluated.to_mesh_clear()


def select_real_control(actor):
    kind, name = MODELS[actor]
    if kind == "shape":
        matches = []
        for mesh in bpy.data.objects:
            if mesh.type != "MESH" or not mesh.data.shape_keys:
                continue
            blocks = mesh.data.shape_keys.key_blocks
            if name not in blocks:
                continue
            key, base = blocks[name], blocks[0]
            moved = sum(1 for a, b in zip(key.data, base.data) if (a.co - b.co).length > 0.00003)
            if moved > 3:
                matches.append((moved, mesh, key))
        if not matches:
            raise RuntimeError("Rain original native mesh has no geometrically moving mouth_open shape")
        _, mesh, key = max(matches, key=lambda item: item[0])
        return {"kind":kind, "name":name, "mesh":mesh, "control":key, "rig":None}
    choices = []
    for rig in bpy.data.objects:
        if rig.type != "ARMATURE" or name not in rig.pose.bones:
            continue
        for mesh in bpy.data.objects:
            if mesh.type != "MESH" or name not in mesh.vertex_groups:
                continue
            if mesh.parent != rig and not any(
                modifier.type == "ARMATURE" and modifier.object == rig for modifier in mesh.modifiers
            ):
                continue
            weights = sum(1 for vert in mesh.data.vertices for group in vert.groups
                          if mesh.vertex_groups[group.group].name == name and group.weight > 0)
            if weights:
                choices.append((weights, rig, mesh))
    if not choices:
        raise RuntimeError("Sprite original DEF-Jaw is not bound to any evaluated real mesh")
    _, rig, mesh = max(choices, key=lambda item: item[0])
    return {"kind":kind, "name":name, "mesh":mesh, "control":rig.pose.bones[name], "rig":rig}


def apply_control(record, openness, base_angle):
    if record["kind"] == "shape":
        record["control"].value = openness
    else:
        record["control"].rotation_euler.x = base_angle + math.radians(18) * openness
    bpy.context.view_layer.update()


def main(master, wav, output, actor):
    if actor not in MODELS:
        raise ValueError("Only independently sourced and previously measured native jaw/morph actors are available for this test")
    master, wav, output = Path(master).resolve(), Path(wav).resolve(), Path(output).resolve()
    if not master.is_file() or not wav.is_file():
        raise FileNotFoundError("Original professional .blend rig or voice WAV is missing")
    master_digest = hashlib.sha256(master.read_bytes()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    samples, channels, rate, audio_digest = read_wav(wav)
    duration, rms, values = envelope(samples, channels, rate)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(master), load_ui=False)
    scene = bpy.context.scene
    control = select_real_control(actor)
    scene.render.fps = FPS
    scene.render.fps_base = 1
    scene.frame_start = 1
    scene.frame_end = len(values)
    posed = control["control"]
    if control["kind"] == "bone":
        posed.rotation_mode = "XYZ"
        base_angle = posed.rotation_euler.x
    else:
        base_angle = 0
        posed.slider_min = min(posed.slider_min, 0.0)
        posed.slider_max = max(posed.slider_max, 1.0)

    for index, openness in enumerate(values, 1):
        scene.frame_set(index)
        apply_control(control, openness, base_angle)
        if control["kind"] == "shape":
            posed.keyframe_insert(data_path="value", frame=index, group="CartoonStudio audio diagnostics")
        else:
            posed.keyframe_insert(data_path="rotation_euler", frame=index, group="CartoonStudio audio diagnostics")

    # Test genuine evaluated vertices at audible times, not just animation curve data.
    indices = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    tests = []
    for index in indices[:min(8, len(indices))]:
        scene.frame_set(index + 1)
        apply_control(control, 0.0, base_angle)
        zero = mesh_vertices(control["mesh"])
        apply_control(control, values[index], base_angle)
        opened = mesh_vertices(control["mesh"])
        distances = [(a - b).length for a, b in zip(zero, opened)]
        tests.append({"frame":index + 1, "audio_time_seconds":round(index / FPS, 4),
                      "mouth_open_value":values[index],
                      "moved_sample_vertices":sum(d > 0.00003 for d in distances),
                      "max_evaluated_world_movement":round(max(distances, default=0.0), 7)})
    observed = [t for t in tests if t["moved_sample_vertices"] >= 4
                and t["max_evaluated_world_movement"] > 0.00015]
    if not observed:
        print("NATIVE_MOUTH_GEOMETRY_NOT_PROVEN", actor, "audible_checks", json.dumps(tests), flush=True)

    # Restore evaluated animation, then save the audition as a NEW Blender file.
    scene.frame_set(1)
    bpy.context.view_layer.update()
    audio_copy = output / "technical-spoken-sample.wav"
    shutil.copyfile(wav, audio_copy)
    # Keep an external audio copy beside the native rehearsal file for manual playback.
    native_copy = output / (actor + "-native-wav-mouth-test.blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(native_copy), check_existing=False, compress=True)
    report = {
        "actor_original_source":actor, "original_master_sha256":master_digest,
        "original_master_not_overwritten":hashlib.sha256(master.read_bytes()).hexdigest() == master_digest,
        "voice_sample_pcm_sha256":audio_digest, "wave_sample_rate":rate,
        "voice_is_canon":False, "audio_sample_is_only_audition":True,
        "audio_duration_seconds":round(duration, 4), "animation_fps":FPS,
        "keyframed_speech_frames":len(values), "control_kind":control["kind"],
        "existing_native_control":control["name"], "actual_mesh":control["mesh"].name,
        "frame_envelope":[{"frame":i + 1, "time_s":round(i/FPS, 4),
                           "rms":round(rms[i], 6), "mouth_open":values[i]}
                          for i in range(len(values))],
        "evaluated_geometry_checks":tests,
        "geometry_reacts_to_audio_amplitude":bool(observed),
        "technically_audio_synchronized":bool(observed),
        "phoneme_visemes_verified":False,
        "lip_readability_verified":False,
        "teeth_and_lips_verified":False,
        "video_mp4_rendered":False,
        "episode_rendered":False,
        "canon_model_mapping_changed":False,
        "evaluation_limit":"Amplitude-open/close only. Rain's exposed shape may primarily deform gums/tongue; visual lips and multi-viseme acting remain unverified.",
        "native_audition_file":native_copy.name,
        "audio_file":audio_copy.name,
    }
    (output / (actor + "-wav-to-real-mesh-evidence.json")).write_text(json.dumps(report, indent=2) + "\n")
    print("ORIGINAL_PROFESSIONAL_CHARACTER_WAV_DRIVEN_MESH_RESULT",actor,
          "frames",len(values),"positive_geometry_samples",len(observed),
          "actual_evaluated_geometry_moving",bool(observed),
          "phonemes_verified=false","episode_rendered=false",flush=True)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 4:
        raise SystemExit("Usage Blender --python verify_native_wav_face_sync.py -- ORIGINAL.blend SPEECH.wav OUTPUT_DIR rain|sprite|elder_sprite|rex")
    main(*args)
