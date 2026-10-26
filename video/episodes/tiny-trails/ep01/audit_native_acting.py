#!/usr/bin/env python3
"""Read-only inventory of real Blender Studio artist acting controls (NO render).

Outputs prospective native actions, facial bones and shape keys, not a claim that
an action is retargetable or approved. Operates on the unchanged original files.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
import bpy

POSE_PATH = re.compile(r'pose\.bones\["([^"]+)"\]')
FACIAL = ('jaw', 'mouth', 'lip', 'cheek', 'eye', 'lid', 'brow', 'face', 'tongue')
KEYWORDS = ('idle', 'blink', 'walk', 'talk', 'face', 'smile', 'head', 'breath')


def choose(objects, label):
    scored = []
    for rig in objects:
        if rig.type != 'ARMATURE':
            continue
        meshes = [o for o in objects if o.type == 'MESH' and (o.find_armature() == rig or o.parent == rig)]
        if meshes:
            scored.append((len(rig.data.bones), sum(len(m.data.polygons) for m in meshes), rig, meshes))
    if not scored:
        raise RuntimeError('Original source has no skinned armature: ' + label)
    _, _, rig, meshes = max(scored, key=lambda x: (x[0], x[1]))
    return rig, meshes


def inventory(rig, meshes, actions, label):
    bone_names = set(rig.pose.bones.keys())
    face_controls = sorted(n for n in bone_names if any(w in n.lower() for w in FACIAL))
    morphs = []
    for m in meshes:
        if m.data.shape_keys:
            morphs.extend(k.name for k in m.data.shape_keys.key_blocks if k.name.lower() != 'basis')
    candidates = []
    for action in actions:
        try:
            curves = list(action.fcurves)
        except AttributeError:
            continue
        controlled = {p for f in curves for p in POSE_PATH.findall(f.data_path)}
        shared = controlled & bone_names
        compatible = len(shared)
        if compatible >= 5 or any(k in action.name.lower() for k in KEYWORDS):
            candidates.append({'action': action.name, 'channels': len(curves),
                               'matching_rig_bones': compatible,
                               'eligible_for_use_without_retarg': False})
    candidates.sort(key=lambda d: (-d['matching_rig_bones'], d['action']))
    library = getattr(rig, 'pose_library', None)
    return {'key': label, 'armature': rig.name, 'bone_count': len(bone_names),
            'skin_meshes': len(meshes), 'facial_bone_count': len(face_controls),
            'facial_bone_examples': face_controls[:35],
            'source_shape_key_count': len(morphs), 'source_shape_key_examples': sorted(set(morphs))[:35],
            'pose_library_action': library.name if library else None,
            'current_source_action': rig.animation_data.action.name if rig.animation_data and rig.animation_data.action else None,
            'candidate_original_action_count': len(candidates),
            'possible_native_actions': candidates[:35],
            'native_clip_safe_to_play_without_visual_test': False,
            'phoneme_complete_lipsync_implemented': False}


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--elder', type=Path, required=True)
    ap.add_argument('--sprite', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args(args)
    if a.elder.open('rb').read(7) != b'BLENDER' or a.sprite.open('rb').read(4) != b'glTF':
        raise RuntimeError('Missing real original source actor files')
    bpy.ops.wm.open_mainfile(filepath=str(a.elder.resolve()), load_ui=False)
    elder_rig, elder_meshes = choose(list(bpy.data.objects), 'elder_sprite')
    elder_actions = list(bpy.data.actions)
    elder = inventory(elder_rig, elder_meshes, elder_actions, 'elder_sprite')
    before_objects = set(bpy.data.objects)
    before_actions = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=str(a.sprite.resolve()))
    imported = list(set(bpy.data.objects) - before_objects)
    sprite_rig, sprite_meshes = choose(imported, 'sprite')
    sprite_actions = list(set(bpy.data.actions) - before_actions)
    sprite = inventory(sprite_rig, sprite_meshes, sprite_actions, 'sprite')
    out = {'original_rig_controls_observed': True, 'artist_action_playback_verified': False,
           'facial_expressiveness_visual_verified': False, 'characters_replaced': False,
           'no_render': True, 'actors': {'sprite': sprite, 'elder_sprite': elder}}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    print('EP01_ORIGINAL_NATIVE_ACTING_CONTROLS_INVENTORIED_NO_RENDER',
          sprite['candidate_original_action_count'], elder['candidate_original_action_count'])


if __name__ == '__main__':
    main()
