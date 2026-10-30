#!/usr/bin/env python3
"""Read-only CAM03B v07/v08 Blender scene evidence probe.

Run with Blender 4.5 LTS or later:
  blender -b /private/NINEFOLD_EP101.blend \
      --python video/ninefold_tide/ops/cam03b_blender_probe.py \
      -- --out /kaggle/working/e101_cam03b_scene_probe.json

Inspects scene coordinates and editable GPv3 actors. Never changes/saves a .blend
and never declares an image artist-approved merely because its objects exist.
"""
import argparse
import json
import math
import sys
import bpy
from mathutils import Vector


def find_gp(name):
    matches = [
        obj for obj in bpy.data.objects
        if obj.type == "GREASEPENCIL" and name.lower() in obj.name.lower()
    ]
    return matches[0] if matches else None


def find_object(*terms):
    for obj in bpy.data.objects:
        if all(term in obj.name.lower() for term in terms):
            return obj
    return None


def xyz(location):
    return [round(float(value), 5) for value in location]


def camera_look_at(cam):
    if cam is None:
        return None
    origin = Vector(cam.matrix_world.translation)
    target = Vector((2.1, -3.17, 4.15))
    distance = (target - origin).length
    direction = cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    return xyz(origin + direction * distance)


def actor_spec(name, fallback_height):
    obj = find_gp(name)
    if obj is None:
        return {"height_m": 0.0, "grease_pencil_layers": 0, "is_2d": False}
    # A blank GP drawing has no measurable silhouette. The artist must stamp
    # the intended height as custom data, never infer a body from an empty object.
    return {
        "height_m": float(obj.get("canon_height_m", obj.get("height_m", 0.0))),
        "grease_pencil_layers": len(obj.data.layers),
        "is_2d": True,
        "gp_object": obj.name,
        "drawn_frames": sum(len(layer.frames) for layer in obj.data.layers),
        "model_height_target_m": fallback_height,
    }


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    scene = bpy.context.scene
    cam = scene.camera
    hand = (find_object("naya", "rail", "grip") or
            find_object("hand", "contact") or
            find_object("grip", "target"))
    naya = find_gp("naya")
    proxies = [
        obj.name for obj in bpy.data.objects
        if (("temp" in obj.name.lower() and any(
            k in obj.name.lower() for k in ("naya", "kito", "iri", "actor")))
            and not obj.hide_render)
    ]
    rope_aliases = {
        "messenger": ("messenger", "spool"),
        "hawser": ("hawser", "bow_rope"),
        "safety": ("safety_line", "safety_rope"),
    }
    rope_hits = {}
    for label, words in rope_aliases.items():
        rope_hits[label] = [
            obj.name for obj in bpy.data.objects
            if any(word in obj.name.lower() for word in words)
        ]
    # This is a name-based rope identity check; exact geometry/load-path
    # analysis still requires the director's physical-action storyboard gate.
    report = {
        "blender_version": list(bpy.app.version[:3]),
        "active_camera": cam.name if cam else None,
        "cam_xyz": xyz(cam.matrix_world.translation) if cam else None,
        "look_at": camera_look_at(cam),
        "naya_root": xyz(naya.matrix_world.translation) if naya else None,
        "hand_target": xyz(hand.matrix_world.translation) if hand else None,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "fps": scene.render.fps,
        "actors": {name: actor_spec(name, height) for name, height in (
            ("naya", 1.64), ("kito", 1.45), ("iri", 1.72)
        )},
        "temporary_actor_planes_visible": bool(proxies),
        "temporary_proxies": proxies,
        "distinct_rope_systems": sum(bool(names) for names in rope_hits.values()),
        "rope_name_evidence": rope_hits,
        "manual_art_approval": False,
        "notice": "Read-only Blender evidence; GP layers can be empty. No art, acting, or final render approved.",
    }
    with open(args.out, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
    print(json.dumps({
        "probe_saved": args.out,
        "actor_objects": [name for name, info in report["actors"].items() if info["is_2d"]],
        "manual_art_approval": False
    }))
    return 0


if __name__ == "__main__":
    sys.exit(run())
