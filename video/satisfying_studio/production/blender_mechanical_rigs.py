#!/usr/bin/env python3
"""Original editable Blender mechanical starting rigs, NOT release-quality films.

Invoke using an existing free Blender 4.5 LTS installation:
  blender -b -t 4 --python blender_mechanical_rigs.py -- \
      --rig domino --output /absolute/path/rig.blend --still
  blender -b -t 4 --python blender_mechanical_rigs.py -- \
      --rig fidget --output /absolute/path/rig.blend --bake

Rig authors must tune material scale, collision geometry, physics and Foley.
No recorded soundtrack or creative approval is fabricated. Compatible with
physics_verify.py solver=blender_rigidbody only after genuine cache baking.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


def args_after_blender():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rig", required=True, choices=["domino", "fidget", "colour-sort"])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--aspect", default="9:16", choices=["9:16", "16:9"])
    parser.add_argument("--bake", action="store_true")
    parser.add_argument("--still", action="store_true")
    return parser.parse_args(args)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def build(options):
    try:
        import bpy
        from mathutils import Vector
    except ImportError as exc:
        raise RuntimeError("Only run this authoring script inside Blender Python") from exc

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end, scene.render.fps = 1, 120, 24
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32  # technical lookdev ONLY; artist must grade final render
    scene.render.resolution_percentage = 100
    scene.render.resolution_x, scene.render.resolution_y = (
        (720, 1280) if options.aspect == "9:16" else (1280, 720)
    )
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.07, 0.07, 0.07)
    scene.gravity = (0, 0, -9.81)

    def material(name, color, metallic=0.0, roughness=0.3):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        p = mat.node_tree.nodes.get("Principled BSDF")
        p.inputs["Base Color"].default_value = (*color, 1)
        p.inputs["Metallic"].default_value = metallic
        p.inputs["Roughness"].default_value = roughness
        return mat

    studio = material("Ground satin slate", (.065, .07, .075), .0, .4)
    base_mat = material("Fine matte porcelain", (.82, .77, .89), .0, .28)
    cyan = material("Deep glossy teal", (.04, .52, .64), .18, .22)
    pink = material("Aubergine magenta", (.58, .04, .30), .13, .24)
    amber = material("Warm resin finish", (.89, .44, .03), .08, .24)

    def cube(name, pos, scale, mat, rigid=None, mass=0.1, bevel=.025):
        bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
        obj = bpy.context.object
        obj.name = name
        obj.dimensions = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(mat)
        if bevel:
            mod = obj.modifiers.new("Soft manufactured edges", "BEVEL")
            mod.width = bevel
            mod.segments = 3
            obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
        if rigid:
            bpy.ops.rigidbody.object_add()
            obj.rigid_body.type = rigid
            obj.rigid_body.collision_shape = "CONVEX_HULL" if rigid == "ACTIVE" else "BOX"
            obj.rigid_body.friction = .6
            obj.rigid_body.restitution = .06
            if rigid == "ACTIVE":
                obj.rigid_body.mass = mass
        return obj

    floor = cube("Matte tactile presentation plinth", (0, 0, -.17),
                 (5, 4, .3), studio, "PASSIVE", bevel=.07)

    if options.rig == "domino":
        # Genuine rigid-body contact; no keyframe fake bounce.
        # The initial falling block is deliberately offset and tilted.
        for i in range(13):
            d = cube(f"Porcelain domino {i + 1:02d}", (-1.22 + .20 * i, 0, .32),
                     (.10, .31, .62), (cyan, pink, amber)[i % 3],
                     "ACTIVE", mass=.085, bevel=.013)
            if i == 0:
                d.rotation_euler[1] = -.20
                d.location.x -= .055
    elif options.rig == "fidget":
        base = cube("Tactile switch base", (0, 0, .12),
                    (1.8, 1.55, .43), studio, "PASSIVE", bevel=.10)
        buttons = []
        for i, x in enumerate((-.55, 0, .55)):
            button = cube(f"Keycap {i+1}", (x, 0, .43),
                          (.36, .40, .17), (cyan, pink, amber)[i],
                          "ACTIVE", mass=.05, bevel=.065)
            # A physics-aware animated kinematic rigid body is a guide;
            # final spring-force motion/contact sound needs editor inspection.
            button.rigid_body.kinematic = True
            for frame, offset in ((1, 0), (18+12*i, -.11),
                                  (26+12*i, -.11), (36+12*i, 0), (120, 0)):
                button.location.z = .43 + offset
                button.keyframe_insert(data_path="location", frame=frame)
            buttons.append(button)
    else:
        # Authentic rigid-body beads and passive sorting compartments.
        # The final color separation is not guaranteed; inspect the sim.
        for x in (-.75, -.25, .25, .75):
            cube("Sort rail at %.2f" % x, (x, -.25, .20),
                 (.038, 1.1, .48), studio, "PASSIVE", bevel=.01)
        for i in range(12):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16,
                radius=.105, location=(-.65 + (i % 4)*.43,
                                       .55 + (i//4)*.21, .25 + (i//4)*.23))
            obj=bpy.context.object
            obj.name="Unique sorting bead %02d"%(i+1)
            obj.data.materials.append((cyan, pink, amber)[i % 3])
            bpy.ops.rigidbody.object_add()
            obj.rigid_body.type="ACTIVE"
            obj.rigid_body.mass=.05
            obj.rigid_body.collision_shape="SPHERE"

    def area(name, location, energy, size, temperature):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = temperature

    area("Main softbox", (-2.1, -2.2, 4), 750, 3.2, (0.86, .93, 1.0))
    area("Warm edge softbox", (2.5, 2.2, 3), 560, 2.2, (1.0, .85, .74))
    bpy.ops.object.camera_add(location=(0, -4.1, 3.0))
    cam=bpy.context.object
    direction=Vector((0, 0, .35)) - cam.location
    cam.rotation_euler=direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera=cam
    cam.data.type="PERSP"
    cam.data.lens=38 if options.aspect == "9:16" else 45
    cam.data.dof.use_dof=True
    cam.data.dof.focus_distance=4.35
    cam.data.dof.aperture_fstop=8

    output=options.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if options.bake:
        world=scene.rigidbody_world
        if world is None:
            raise RuntimeError("Rigid-body world did not initialize")
        world.point_cache.frame_start=1
        world.point_cache.frame_end=120
        bpy.ops.wm.save_as_mainfile(filepath=str(output))
        done=bpy.ops.ptcache.bake_all(bake=True)
        if "FINISHED" not in done or not world.point_cache.is_baked:
            raise RuntimeError("Rigid-body physics bake did not complete; reject source")
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    if options.still:
        scene.frame_set(1)
        scene.render.filepath=str(output.with_suffix(".lookdev.png"))
        bpy.ops.render.render(write_still=True)

    report = {
        "rig":options.rig, "source_blend":output.name,
        "source_blend_sha256":sha256(output),
        "solver":"blender_rigidbody",
        "baked_point_cache":bool(options.bake and scene.rigidbody_world
                                 and scene.rigidbody_world.point_cache.is_baked),
        "cached_frames":120 if options.bake else 0,
        "artistic_approval":False,
        "audio_recorded":False,
        "material_action_sync_approved":False,
        "warning":"Editable starter rig only; genuine Foley and complete AV approval required."
    }
    report_file=output.parent / "physics_bake_manifest.json"
    report_file.write_text(json.dumps(report, indent=2)+"\n",encoding="utf-8")
    print("BLENDER_MECHANICAL_STARTER_UNAPPROVED",json.dumps(report))
    return report


if __name__=="__main__":
    build(args_after_blender())
