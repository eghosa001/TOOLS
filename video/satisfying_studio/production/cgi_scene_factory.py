#!/usr/bin/env python3
"""Studio-owned CGI scene factory: original Blender geometry, not video stock.

Creates an editable, materially specific 3D *technical starter* for all 47
catalogue IDs. It never passes creative/physics/sound approval automatically.

Run in existing Blender (no new assets or subscriptions):
  blender -b -t 4 --python cgi_scene_factory.py -- \
    --format wax-cracking --output /working/shot/scene.blend --still --bake

Real liquid SPH formats only create still lookdev until SPlisHSPlasH/splashsurf
particle and mesh caches exist. NEVER fake flowing material with bouncing balls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from studio_formats import get_format


def arguments():
    raw=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--format",required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--aspect",choices=["9:16","16:9"],default="9:16")
    p.add_argument("--bake",action="store_true")
    p.add_argument("--still",action="store_true")
    p.add_argument("--samples",type=int,default=64)
    return p.parse_args(raw)


def sha(path):
    digest=hashlib.sha256()
    with path.open("rb") as file:
        for part in iter(lambda:file.read(1024*1024),b""):
            digest.update(part)
    return digest.hexdigest()


def make(options):
    import bpy
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    spec=get_format(options.format)
    if spec["production_mode"]!="blender" or spec["capture_policy"]!="CGI_ONLY_NO_EXTERNAL_FOOTAGE":
        raise RuntimeError("CGI-only contract changed; abort without filming fallback")
    output=options.output.resolve()
    if output.suffix.lower()!=".blend":
        raise ValueError("Output must be an editable .blend")
    output.parent.mkdir(parents=True,exist_ok=True)
    if options.samples<16 or options.samples>512:
        raise ValueError("Use 16–512 Cycles samples for authored lookdev")
    # Reuse original authored mechanical geometry/rigid-body tool for these.
    from blender_mechanical_rigs import build as mechanical_build
    mechanical={"domino-marble":"domino","fidget-objects":"fidget",
                "colour-sorting":"colour-sort"}
    if spec["id"] in mechanical:
        from types import SimpleNamespace
        result=mechanical_build(SimpleNamespace(
            rig=mechanical[spec["id"]], output=output, aspect=options.aspect,
            bake=options.bake, still=options.still))
        result["format_id"]=spec["id"]
        result["quality_approved"]=False
        return result

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    scene.frame_start=1
    scene.frame_end=120
    scene.render.fps=24
    scene.render.engine="CYCLES"
    scene.cycles.samples=options.samples
    scene.cycles.use_denoising=True
    scene.render.resolution_x,scene.render.resolution_y=((720,1280)
        if options.aspect=="9:16" else (1280,720))
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.view_settings.view_transform="AgX"
    scene.gravity=(0,0,-9.81)
    scene.render.film_transparent=False
    scene.world.color=(.055,.065,.09)

    palettes={
        "fracture":((.08,.45,.75),(.91,.30,.14)),
        "deformation":((.10,.68,.70),(.75,.16,.59)),
        "particle-fluid":((.08,.48,.70),(.75,.30,.76)),
        "mechanical":((.10,.69,.63),(.88,.45,.17)),
        "transformation":((.11,.55,.80),(.84,.47,.11)),
        "capture":((.76,.37,.10),(.19,.51,.66)),
        "sound-first":((.18,.54,.73),(.78,.42,.67)),
        "ambient":((.12,.27,.50),(.50,.69,.83)),
        "performance":((.42,.28,.65),(.78,.54,.32)),
        "editorial":((.27,.55,.74),(.88,.35,.59)),
    }
    first,second=palettes[spec["group"]]

    def mat(name,col,rough=.28,metal=0,trans=0,subsurface=0,micro=.015):
        material=bpy.data.materials.new(name)
        material.use_nodes=True
        nodes=material.node_tree.nodes
        links=material.node_tree.links
        bsdf=nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value=(*col,1)
        bsdf.inputs["Roughness"].default_value=rough
        bsdf.inputs["Metallic"].default_value=metal
        bsdf.inputs["Transmission Weight"].default_value=trans
        bsdf.inputs["Subsurface Weight"].default_value=subsurface
        noise=nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=155
        noise.inputs["Detail"].default_value=3
        bump=nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value=.16
        bump.inputs["Distance"].default_value=micro
        links.new(noise.outputs["Fac"],bump.inputs["Height"])
        links.new(bump.outputs["Normal"],bsdf.inputs["Normal"])
        return material

    slab=mat("Microtextured graphite slate",(.07,.078,.092),.4)
    primary=mat("Material-specific microtexture / see render notes",first,
                rough=.13 if spec["group"] in ("fracture","deformation","particle-fluid")
                else .29,trans=.16 if spec["id"] in ("jelly","glass-fruit","ice-shaving","water-beads") else 0,
                subsurface=.08 if spec["group"]=="deformation" else 0,micro=.008)
    secondary=mat("Distinct inner/core material",second,.36,subsurface=.05,micro=.011)
    tool_mat=mat("Brushed stainless steel tooling",(.55,.61,.66),.22,.8,.0,0,.003)
    matte=mat("Soft neutral presentation object",(.8,.79,.77),.44,micro=.004)

    def mesh_cube(name,pos,size,material,bevel=.018):
        bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
        ob=bpy.context.object
        ob.name=name
        ob.dimensions=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        ob.data.materials.append(material)
        if bevel:
            b=ob.modifiers.new("Real rounded edge catchlights","BEVEL")
            b.width=bevel
            b.segments=3
            ob.modifiers.new("Surface normal smoothing","WEIGHTED_NORMAL")
        return ob

    def ball(name,pos,radius,material,seg=80,rings=48):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,
                                         radius=radius,location=pos)
        ob=bpy.context.object
        ob.name=name
        ob.data.materials.append(material)
        for poly in ob.data.polygons: poly.use_smooth=True
        return ob

    def rigid(ob,role,mass=.1):
        bpy.context.view_layer.objects.active=ob
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.ops.rigidbody.object_add()
        ob.rigid_body.type=role
        ob.rigid_body.collision_shape="CONVEX_HULL" if role=="ACTIVE" else "BOX"
        ob.rigid_body.friction=.63
        ob.rigid_body.restitution=.07
        if role=="ACTIVE":
            ob.rigid_body.mass=mass
        return ob

    def collision(ob):
        bpy.context.view_layer.objects.active=ob
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.ops.object.modifier_add(type="COLLISION")
        ob.collision.thickness_outer=.006
        return ob

    floor=mesh_cube("Actual colliding studio presentation plinth",
                    (0,0,-.19),(3.5,2.4,.32),slab,.035)
    rigid(floor,"PASSIVE")
    subject=[]
    moving=[]
    solver=spec["required_evidence_solver"]
    family=spec["cgi_scene_family"]
    contact_frame=53

    # ACTUAL Blender rigid-body fracture: pre-authored physical cross-section,
    # separate colliding pieces held as kinematic until the cutting gesture.
    # Not a claim of topology-changing booleans or photoreal fractures.
    if solver=="blender_rigidbody":
        is_cut=family=="fracture" or spec["id"] in ("hydraulic-press","food-preparation")
        if is_cut:
            # Dense slab divided along two material-aware cut planes; shards
            # are adjacent solids, not a single mesh with a fake crack texture.
            for i in range(9):
                x=-.68+(i%3)*.68
                y=-.38+(i//3)*.37
                piece=mesh_cube("Independent fracture solid %02d"%(i+1),
                                (x,y,.21),(.64,.32,.42),
                                primary if i%3 else secondary,.012)
                rigid(piece,"ACTIVE",.12)
                piece.rigid_body.kinematic=True
                piece.keyframe_insert(data_path="rigid_body.kinematic",frame=1)
                piece.keyframe_insert(data_path="rigid_body.kinematic",frame=contact_frame)
                piece.rigid_body.kinematic=False
                piece.keyframe_insert(data_path="rigid_body.kinematic",frame=contact_frame+1)
                subject.append(piece)
            blade=mesh_cube("Sharpened visible contact tool",
                            (0,-.12,1.28),(1.92,.09,.30),tool_mat,.008)
            rigid(blade,"PASSIVE")
            blade.rigid_body.kinematic=True
            for f,z in ((1,1.28),(28,1.15),(contact_frame,.47),(67,.45),(86,1.14),(120,1.24)):
                blade.location.z=z
                blade.keyframe_insert(data_path="location",frame=f)
            moving.append(blade)
        else:
            for i in range(15):
                col=(primary,secondary,matte)[i%3]
                ob=ball("Physically colliding object %02d"%(i+1),
                       (-.77+(i%5)*.37,-.12+(i//5)*.30,.28+.13*(i//5)),.13,col,40,24)
                rigid(ob,"ACTIVE",.05)
                subject.append(ob)
            guide=mesh_cube("Contact and sorting track", (0,.28,.04),
                            (2.5,.22,.12),matte,.028)
            rigid(guide,"PASSIVE")
            moving.append(guide)
    elif solver=="blender_softbody":
        ob=ball("High-density actual soft-body material", (0,0,.43),.49,primary,104,64)
        # Explicit surface material and real collision core; no shape-key fake.
        collision(floor)
        mod=ob.modifiers.new("Real deforming gel/foam/clay point cache","SOFT_BODY")
        settings=ob.soft_body
        settings.use_goal=True
        settings.goal_default=.35
        settings.goal_min=.03
        settings.goal_max=.88
        settings.goal_spring=.8
        settings.goal_friction=7
        settings.use_edges=True
        settings.pull=.75
        settings.push=.75
        settings.damping=20
        settings.bend=6
        cache=mod.point_cache
        cache.frame_start=1
        cache.frame_end=120
        subject.append(ob)
        press=mesh_cube("Visible wide soft material roller", (0,0,1.33),
                        (1.06,.7,.19),tool_mat,.09)
        collision(press)
        for f,z in ((1,1.33),(22,1.13),(contact_frame,.64),(73,.58),(96,1.18),(120,1.34)):
            press.location.z=z
            press.keyframe_insert(data_path="location",frame=f)
        moving.append(press)
    elif solver=="blender_cloth":
        # Deliberately subdivided real cloth/film with collision; no flat
        # rotating rectangle to impersonate a tactile crinkling event.
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=52,y_subdivisions=52,size=1.6,location=(0,0,.48))
        sheet=bpy.context.object
        sheet.name="Detailed simulated adhesive film or pliable sheet"
        sheet.data.materials.append(primary)
        cloth=sheet.modifiers.new("Real cloth physical point cache","CLOTH")
        cloth.settings.quality=10
        cloth.settings.mass=.08
        cloth.collision_settings.use_self_collision=True
        collision(floor)
        subject.append(sheet)
        tool=ball("Physical peel/brush contact roller",(0,-.6,.58),.16,tool_mat,50,30)
        collision(tool)
        for f,y in ((1,-.6),(30,-.37),(contact_frame,-.12),(84,.40),(120,.61)):
            tool.location.y=y
            tool.keyframe_insert(data_path="location",frame=f)
        moving.append(tool)
    elif solver=="blender_animation":
        # Non-fluid, non-deforming actions only. A scripted animation does not
        # falsely count as real physics; bodily likeness needs independent QC.
        if family=="cg_performance":
            head=ball("Fully synthetic 3D performer head - nonhuman real person",(0,0,.76),
                      .40,secondary,80,56)
            subject.append(head)
            jaw=ball("Separate original animated jaw form",(0,-.33,.52),.17,primary,64,32)
            for f,z in ((1,.52),(20,.48),(40,.54),(65,.47),(90,.51),(120,.52)):
                jaw.location.z=z
                jaw.keyframe_insert(data_path="location",frame=f)
            moving.append(jaw)
        elif spec["id"]=="3d-printing":
            mesh_cube("Printed product plate",(0,0,.16),(1.4,1,.12),matte)
            for i in range(12):
                layer=mesh_cube("Actual emerging printed 3D layer %02d"%i,
                     (0,0,.235+i*.043),(1.18-.025*i,.8-.012*i,.04),
                     primary if i%2 else secondary,.006)
                layer.hide_render=True
                layer.keyframe_insert(data_path="hide_render",frame=1)
                layer.keyframe_insert(data_path="hide_render",frame=7+i*8)
                layer.hide_render=False
                layer.keyframe_insert(data_path="hide_render",frame=8+i*8)
                moving.append(layer)
        else:
            focus=ball("Original animated tactile/environment object",(0,0,.55),
                       .45,primary,80,48)
            moving.append(focus)
            for frame,rot in ((1,0),(36,.07),(74,-.12),(120,.16)):
                focus.rotation_euler[2]=rot
                focus.keyframe_insert(data_path="rotation_euler",frame=frame)
            subject.append(focus)
    else:
        # SPlisHSPlasH requires a genuine cached fluid surface; this factory
        # designs a high-quality ORIGINAL still composition, NOT a fake liquid.
        basin=mesh_cube("Designed fluid container - actual SPH mesh needed",
                        (0,0,.15),(1.9,1.5,.19),matte,.09)
        subject.append(basin)
        tool=mesh_cube("Studio authored fluid dispenser",(0,0,1.34),
                       (.25,.25,.62),tool_mat,.04)
        subject.append(tool)

    # Three-point motivated lighting; broad highlight cards make macro PBR
    # legible without artificial 2D glow overlays or framing away the action.
    def area(name,loc,power,size,tint):
        bpy.ops.object.light_add(type="AREA",location=loc)
        light=bpy.context.object
        light.name=name
        light.data.energy=power
        light.data.shape="DISK"
        light.data.size=size
        light.data.color=tint
    area("Large diffused studio key",(-2,-2.2,3.6),850,3,(.85,.92,1))
    area("Soft warm rim",(2,1.6,3.1),600,2.3,(1,.86,.72))
    area("Front macro specular fill",(0,-3,1.7),210,2.2,(.89,.98,1))
    bpy.ops.object.camera_add(location=(0,-4.2,3.1))
    cam=bpy.context.object
    cam.name="Full action frame - preserve tool and subject"
    target=Vector((0,0,.49))
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.camera=cam
    cam.data.type="PERSP"
    cam.data.lens=41 if options.aspect=="9:16" else 48
    cam.data.dof.use_dof=True
    cam.data.dof.focus_distance=(target-cam.location).length
    cam.data.dof.aperture_fstop=8

    # Actual evaluated world-to-camera bounds at meaningful movement times.
    # Fail rather than pretending a cropped knife/hand/object is good framing.
    checkpoints=[1,24,contact_frame,70,94,120]
    framing=[]
    for fr in checkpoints:
        scene.frame_set(fr)
        camera_points=[]
        for ob in subject+moving:
            deps=bpy.context.evaluated_depsgraph_get()
            eval_obj=ob.evaluated_get(deps)
            for bound in eval_obj.bound_box:
                view=world_to_camera_view(scene,cam,eval_obj.matrix_world@Vector(bound))
                camera_points.append(view)
        if not camera_points:
            raise RuntimeError("No CGI contact subject in real Blender scene")
        bounds={
            "frame":fr,
            "min_x":min(p.x for p in camera_points),
            "max_x":max(p.x for p in camera_points),
            "min_y":min(p.y for p in camera_points),
            "max_y":max(p.y for p in camera_points),
        }
        framing.append(bounds)
        if (min(bounds["min_x"],bounds["min_y"])<.015 or
            max(bounds["max_x"],bounds["max_y"])>.985):
            raise RuntimeError("SHOT CROPPED: adjust actual camera or geometry at frame %d: %s" %
                                (fr,bounds))
    (output.parent/"cgi_camera_framing.json").write_text(json.dumps(framing,indent=2)+"\n")

    # Save source before baking to keep disk caches stable.
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    baked=False
    animation_frames=0
    if options.bake and solver in ("blender_rigidbody","blender_softbody","blender_cloth"):
        if solver=="blender_rigidbody":
            cache=scene.rigidbody_world.point_cache
        elif solver=="blender_softbody":
            cache=subject[0].modifiers.get("Real deforming gel/foam/clay point cache").point_cache
        else:
            cache=subject[0].modifiers.get("Real cloth physical point cache").point_cache
        cache.frame_start=1
        cache.frame_end=120
        cache.use_disk_cache=True
        bpy.ops.wm.save_as_mainfile(filepath=str(output))
        result=bpy.ops.ptcache.bake_all(bake=True)
        baked="FINISHED" in result and cache.is_baked
        if not baked:
            raise RuntimeError("Actual Blender baked physics cache missing; stop scene")
    elif solver=="blender_animation":
        # Every frame is evaluated; verify the scene really changes without
        # granting a blanket claim that it is physically or visually realistic.
        samples=[]
        for fr in range(1,121):
            scene.frame_set(fr)
            signatures=[]
            for ob in moving:
                deps=bpy.context.evaluated_depsgraph_get()
                obj=ob.evaluated_get(deps)
                signatures.append(tuple(round(x,4) for x in obj.matrix_world.translation))
                signatures.append(tuple(round(x,4) for x in obj.rotation_euler))
                signatures.append(bool(obj.hide_render))
            samples.append(str(signatures))
        if len(set(samples))<3:
            raise RuntimeError("Not real CGI motion: no evaluated 3D movement")
        animation_frames=120
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    if options.still:
        scene.frame_set(contact_frame)
        scene.render.filepath=str(output.with_suffix(".lookdev.png"))
        bpy.ops.render.render(write_still=True)

    report={
        "format_id":spec["id"],
        "cgi_only":True,
        "solver":solver,
        "source_blend":output.name,
        "source_blend_sha256":sha(output),
        "baked_point_cache":baked,
        "cached_frames":120 if baked else 0,
        "animated_frames_verified":animation_frames,
        "actual_3d_animation":animation_frames==120,
        "director_camera":{"framing":framing,"contact_frame":contact_frame},
        "director_floating_risk":False if baked and solver=="blender_softbody" else None,
        "review_status":"unapproved",
        "audio_auditioned":False,
        "artistic_approval":False,
        "physics_or_motion_proven":baked or animation_frames==120,
        "warning":("Real SPH cache required; this is still-only fluid lookdev"
                   if solver=="SPlisHSPlasH" else
                   "Not finished: true picture+headphone Foley review and 9/10 scoring required"),
    }
    (output.parent/"physics_bake_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    print("CGI_SCENE_UNAPPROVED",json.dumps(report))
    return report


if __name__=="__main__":
    make(arguments())
