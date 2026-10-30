#!/usr/bin/env python3
"""Original Blender/Cycles jewel-marble ASMR rigid-body proof, with real physics.

No footage/AI, no manufactured sound and no automatic artistic sign-off.
Stages: ASMR_MODE=SCENE, BAKE, PROOF. Blender 4.5 LTS, cloud CPU proof.
"""
import hashlib, json, math, os, sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rigid_foley_events import first_impact_events
from mathutils import Vector

OUT=Path(os.environ.get("ASMR_OUT","/tmp/asmr_rigid_cascade")).resolve()
OUT.mkdir(parents=True,exist_ok=True)
MODE=os.environ.get("ASMR_MODE","SCENE").upper()
SCENE=OUT/"rigid_cascade_editable.blend"
FRAMES=(1,24,48,72,96,120)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def material(name,color,metal=0,rough=.2,trans=0,coat=.1):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    for key,val in (
        ("Base Color",(*color,1)),("Metallic",metal),
        ("Roughness",rough),("IOR",1.47),("Transmission Weight",trans),
        ("Coat Weight",coat)):
        if key in bsdf.inputs:bsdf.inputs[key].default_value=val
    return m

def solid_rigid(obj,mass=None,shape="CONVEX_HULL",friction=.45,bounce=.22):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.rigidbody.object_add()
    rb=obj.rigid_body
    rb.type="ACTIVE" if mass is not None else "PASSIVE"
    rb.collision_shape=shape
    rb.use_margin=True
    rb.collision_margin=.003
    rb.friction=friction
    rb.restitution=bounce
    if mass is not None:rb.mass=mass
    return rb

def area(name,pos,color,watts,width,height,focus):
    bpy.ops.object.light_add(type="AREA",location=pos)
    o=bpy.context.object
    o.name=name
    o.data.color=color
    o.data.energy=watts
    o.data.shape="RECTANGLE"
    o.data.size=width
    o.data.size_y=height
    o.rotation_euler=(Vector(focus)-o.location).to_track_quat("-Z","Y").to_euler()

def create():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene
    sc.render.engine="CYCLES"
    sc.frame_start=1
    sc.frame_end=120
    sc.render.fps=24
    sc.cycles.samples=24
    sc.render.resolution_x=int(os.environ.get("ASMR_W","720"))
    sc.render.resolution_y=int(os.environ.get("ASMR_H","1280"))
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format="PNG"
    sc.render.film_transparent=False
    try:sc.view_settings.view_transform="AgX"
    except Exception:pass
    try:sc.view_settings.look="Medium High Contrast"
    except Exception:pass

    # Original manifold glazed porcelain bowl; one PBR simulation collider.
    # Profile radius/height, inside crown -> lip -> outside underside -> base.
    contour=[(.014,.23),(.15,.24),(.32,.285),(.49,.37),
             (.64,.49),(.78,.67),(.835,.665),(.73,.43),
             (.56,.28),(.34,.18),(.15,.17),(.014,.17)]
    sectors=56
    verts=[(r*math.cos(2*math.pi*k/sectors),
            r*math.sin(2*math.pi*k/sectors),z)
           for r,z in contour for k in range(sectors)]
    faces=[]
    for j in range(len(contour)):
        nj=(j+1)%len(contour)
        for k in range(sectors):
            nk=(k+1)%sectors
            faces.append((j*sectors+k,j*sectors+nk,nj*sectors+nk,nj*sectors+k))
    mesh=bpy.data.meshes.new("Physical manifold lathed bowl")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    bowl=bpy.data.objects.new("CC0-style original glazed porcelain catch bowl",mesh)
    bpy.context.collection.objects.link(bowl)
    ceramic=material("Deep plum photographic porcelain",(.08,.018,.19),rough=.21,coat=.26)
    # Subtle procedural micro-roughness on a physically glazed ceramic bowl,
    # not random glitter painted over every frame.
    ceramic_bsdf=ceramic.node_tree.nodes.get("Principled BSDF")
    micro=ceramic.node_tree.nodes.new("ShaderNodeTexNoise")
    micro.inputs["Scale"].default_value=125
    micro.inputs["Detail"].default_value=2.0
    bump=ceramic.node_tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.045
    bump.inputs["Distance"].default_value=.001
    ceramic.node_tree.links.new(micro.outputs["Fac"],bump.inputs["Height"])
    ceramic.node_tree.links.new(bump.outputs["Normal"],ceramic_bsdf.inputs["Normal"])
    bowl.data.materials.append(ceramic)
    for f in mesh.polygons:f.use_smooth=True
    solid_rigid(bowl,shape="MESH",friction=.48,bounce=.14)

    # Studio slab is real static collider, not a photographic plate cutaway.
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.11))
    slab=bpy.context.object
    slab.name="Physical smoked-ceramic tabletop"
    slab.dimensions=(100,100,.12)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    slab.data.materials.append(material("Basalt tactile table",(.055,.062,.092),rough=.52))
    bevel=slab.modifiers.new("Precision soft product edges","BEVEL")
    bevel.width=.035
    bevel.segments=4
    solid_rigid(slab,shape="BOX",friction=.57,bounce=.02)

    palette=[(.04,.70,.96),(.96,.25,.44),(.90,.60,.04),
             (.18,.84,.56),(.62,.35,1),(.05,.84,.92),(.98,.55,.17)]
    locations=[(-.21,-.10,1.22),(.19,.13,1.30),(-.29,.17,1.38),
               (.28,-.16,1.46),(.07,-.26,1.50),(-.12,.27,1.57),
               (.01,.04,1.68)]
    releases=[1,17,33,49,65,81,97]
    for i,(loc,color,release) in enumerate(zip(locations,palette,releases)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=48,
                                              radius=.091,location=loc)
        obj=bpy.context.object
        obj.name="AUTHENTIC_RIGID_GLASS_PEARL_%02d"%i
        for face in obj.data.polygons:face.use_smooth=True
        glass=material("Tactile coloured refractive glass %02d"%i,
                       color,rough=.045,trans=.84,coat=.16)
        glass.node_tree.nodes.get("Principled BSDF").inputs["IOR"].default_value=1.52
        obj.data.materials.append(glass)
        rb=solid_rigid(obj,mass=.11,shape="SPHERE",friction=.31,bounce=.28)
        # No fake bead path: only the release switch is keyframed;
        # all falling, collisions, rebounds and settling are Bullet physics.
        rb.kinematic=True
        obj.keyframe_insert(data_path="rigid_body.kinematic",frame=1)
        if release>1:
            obj.keyframe_insert(data_path="rigid_body.kinematic",frame=release-1)
        rb.kinematic=False
        obj.keyframe_insert(data_path="rigid_body.kinematic",frame=release)

    focus=Vector((0,0,.77))
    bpy.ops.object.camera_add(location=(1.48,-3.55,2.76))
    camera=bpy.context.object
    camera.name="Full-object original macro product camera"
    camera.rotation_euler=(focus-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.lens=48
    camera.data.dof.use_dof=True
    camera.data.dof.focus_distance=(focus-camera.location).length
    camera.data.dof.aperture_fstop=12
    sc.camera=camera
    area("Huge softbox pearl shape key",(-2.1,-2.1,3.4),(1,.92,.86),160,1.5,2.0,focus)
    area("Long cyan rim reflection",(2.0,1.3,2.7),(.42,.83,1),105,.72,1.65,focus)
    area("Warm gold translucent caustic",(0.7,-1.5,3.2),(1,.75,.45),90,.62,1.3,focus)
    area("Bright broad transmission fill",(0,2.2,2.9),(1,.96,1),185,1.55,1.6,focus)
    world=bpy.data.worlds.new("Photographic jewel reflections")
    world.use_nodes=True
    background=world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value=(.07,.062,.12,1)
    background.inputs["Strength"].default_value=.30
    hdri=os.environ.get("ASMR_HDRI_FILE")
    if hdri:
        image=Path(hdri)
        if not image.is_file():raise RuntimeError("Required CC0 light-probe missing")
        nd=world.node_tree.nodes
        lk=world.node_tree.links
        output=nd.get("World Output")
        env=nd.new("ShaderNodeTexEnvironment")
        env.image=bpy.data.images.load(str(image),check_existing=True)
        lk.new(env.outputs["Color"],background.inputs["Color"])
    sc.world=world
    if not sc.rigidbody_world:
        raise RuntimeError("Actual Blender rigidbody world not initialized")
    sc.rigidbody_world.substeps_per_frame=12
    sc.rigidbody_world.solver_iterations=32
    sc.rigidbody_world.point_cache.frame_start=1
    sc.rigidbody_world.point_cache.frame_end=120
    sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(SCENE))
    print("ORIGINAL_BLENDER_3D_RIGID_SCENE_CREATED",SCENE,flush=True)

def bake():
    sc=bpy.context.scene
    cache=sc.rigidbody_world.point_cache
    cache.frame_start=1;cache.frame_end=120
    # A loaded Blender 4.5 rigid-world cache sometimes crashes when its disk
    # mode is toggled just before a bulk ptcache bake. Use the native scene
    # rigid-world cache first and save the .blend on successful bake.
    print("RIGID_CACHE_BEGIN",cache.frame_start,cache.frame_end,
          "disk",cache.use_disk_cache,flush=True)
    result=bpy.ops.ptcache.bake_all(bake=True)
    print("RIGID_CACHE_OPERATION_RETURNED",result,flush=True)
    if "FINISHED" not in result or not cache.is_baked:
        raise RuntimeError("No real Blender rigidbody cache")
    gems=[o for o in bpy.data.objects if o.name.startswith("AUTHENTIC_RIGID_GLASS_PEARL_")]
    if len(gems)!=7:raise RuntimeError("Missing original seven glass marbles")
    measured=[]
    for frame in FRAMES:
        sc.frame_set(frame)
        positions=[tuple(round(v,5) for v in ob.matrix_world.translation)
                   for ob in gems]
        if any(not all(math.isfinite(n) for n in pos) for pos in positions):
            raise RuntimeError("NaN or invalid rigidbody physics")
        if any(abs(v)>2.5 for pos in positions for v in pos):
            raise RuntimeError("Glass marble escaped product set")
        measured.append({"frame":frame,"marble_centers_xyz":positions})
        print("REAL_RIGIDBODY_FRAMES",json.dumps(measured[-1]),flush=True)
    changes=sum(
        math.dist(a,b)>.20 for a,b in zip(
            measured[0]["marble_centers_xyz"],measured[-1]["marble_centers_xyz"]))
    if changes<5:
        raise RuntimeError("Rigid-body proof failed: fewer than five spheres actually moved")
    if min(p[2] for row in measured for p in row["marble_centers_xyz"])>.95:
        raise RuntimeError("No marbles reached actual physical bowl")
    # Read ALL 120 actual Bullet cache frames and refuse to dub beads that
    # never physically entered the bowl. No virtual or approximate fallback
    # timestamps based only on planned release keyframes.
    trajectory=[]
    for frame in range(1,121):
        sc.frame_set(frame)
        trajectory.append({
            "frame":frame,
            "marble_centers_xyz":[[round(float(v),5)
                                   for v in ob.matrix_world.translation]
                                  for ob in gems]
        })
    impact_events=first_impact_events(trajectory)
    impact_file=OUT/"physical_glass_impact_events.json"
    impact_file.write_text(json.dumps({
        "source":"real Blender 4.5 Bullet rigidbody point cache",
        "physics_fps":24,"events":impact_events,
        "final_auditory_review":"REQUIRED — event-height crossings do NOT prove exact audio contact"
    },indent=2)+"\n")
    print("REAL_GLASS_IMPACT_EVENTS",json.dumps(impact_events),flush=True)
    sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(SCENE))
    report={"solver":"blender_rigidbody","source_blend":SCENE.name,
            "cached_frames":120,"fps":24,"baked_point_cache":True,
            "source_blend_sha256":sha(SCENE),"marble_motion_proof":measured,
            "moving_spheres":changes,
            "measured_bowl_impact_events":impact_events,
            "impact_events_sha256":sha(impact_file),
            "artistic_approval":False,
            "audio_approval":False}
    (OUT/"physics_bake_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ACTUAL_BLENDER_RIGIDBODY_PROOF",changes,flush=True)

def proof():
    sc=bpy.context.scene
    report=json.loads((OUT/"physics_bake_manifest.json").read_text())
    if sha(SCENE)!=report["source_blend_sha256"]:
        raise RuntimeError("Baked Blender project changed since measured proof")
    if not sc.rigidbody_world.point_cache.is_baked:
        raise RuntimeError("Loaded Blender project lost its real rigidbody cache")
    sc.cycles.device="CPU"
    sc.cycles.samples=int(os.environ.get("ASMR_PROOF_SAMPLES","12"))
    sc.render.resolution_x=360
    sc.render.resolution_y=640
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format="PNG"
    frame_folder=OUT/"lookdev_proof"
    frame_folder.mkdir(exist_ok=True)
    output=[]
    for frame in (1,33,72,110):
        sc.frame_set(frame)
        sc.render.filepath=str(frame_folder/("original_cascade_%03d.png"%frame))
        bpy.ops.render.render(write_still=True)
        image=Path(sc.render.filepath)
        if not image.is_file() or image.stat().st_size<1500:
            raise RuntimeError("No true Cycles frame %s"%frame)
        output.append({"frame":frame,"sha256":sha(image),
                       "file":str(image.relative_to(OUT))})
    (OUT/"BLENDER_RIGIDBODY_LOOKDEV_UNAPPROVED.json").write_text(json.dumps({
        "source_blend_sha256":report["source_blend_sha256"],
        "physics_solver":"Blender Bullet rigidbody",
        "lookdev_frames":output,"full_video_rendered":False,
        "authentic_foley_recorded":False,"artistic_approval":False
    },indent=2)+"\n")
    print("RIGIDBODY_LOOKDEV_RENDERED_UNAPPROVED",json.dumps(output),flush=True)

if MODE=="SCENE":create()
elif MODE=="BAKE":bake()
elif MODE=="PROOF":proof()
else:raise RuntimeError("Unknown ASMR_MODE")
