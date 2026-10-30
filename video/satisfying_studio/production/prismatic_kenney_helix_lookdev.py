#!/usr/bin/env python3
"""Original Blender 3D marble spiral using commercially reusable Kenney CC0 mesh.
Preview/lookdev only. Never claims physical/audiovisual or editorial approval.
"""
from pathlib import Path
from mathutils import Vector
import bpy,math,os,hashlib,json
out=Path(os.environ.get("ASMR_OUT","/tmp/asmr_prismatic_track")).resolve()
out.mkdir(parents=True,exist_ok=True)
asset=Path(os.environ["ASMR_TRACK_GLB"]).resolve()
assert asset.is_file() and asset.suffix.lower()==".glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.frame_start=1;sc.frame_end=120;sc.render.fps=24
sc.render.engine="CYCLES"
sc.cycles.samples=int(os.environ.get("ASMR_SAMPLES","12"))
sc.cycles.max_bounces=8
sc.render.resolution_x=int(os.environ.get("ASMR_W","540"))
sc.render.resolution_y=int(os.environ.get("ASMR_H","304"))
sc.render.resolution_percentage=100
sc.view_layers[0].cycles.use_denoising=True
sc.render.image_settings.file_format="PNG"
try:sc.view_settings.view_transform="AgX"
except Exception:pass

def mat(name,base,metal=0,rough=.2,trans=0,ior=1.47):
    m=bpy.data.materials.new(name);m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    for k,v in [("Base Color",(*base,1)),("Metallic",metal),("Roughness",rough),("Transmission Weight",trans),("IOR",ior)]:
        if k in b.inputs:b.inputs[k].default_value=v
    return m

bpy.ops.import_scene.gltf(filepath=str(asset))
tracks=[ob for ob in bpy.context.scene.objects if ob.type=="MESH"]
if not tracks:raise RuntimeError("CC0 asset did not import actual track meshes")
# The glTF contains existing vertices: inspect actual scale/orientation before modifying.
bbox=[]
for ob in tracks:
    for vertex in ob.bound_box:
        bbox.append(ob.matrix_world @ Vector(vertex))
mins=[min(p[i] for p in bbox) for i in range(3)]
maxs=[max(p[i] for p in bbox) for i in range(3)]
dims=[maxs[i]-mins[i] for i in range(3)]
if min(dims)<.0001 or max(dims)>200:raise RuntimeError("Unexpected Kenney geometry scale")
origin=Vector([(a+b)/2 for a,b in zip(mins,maxs)])
scale=2.7/max(dims[0],dims[1],.5)
for ob in tracks:
    ob.location=(ob.location-origin)*scale
    ob.scale*=scale
    bpy.context.view_layer.objects.active=ob
    bpy.ops.rigidbody.object_add()
    ob.rigid_body.type="PASSIVE";ob.rigid_body.collision_shape="MESH"
    ob.rigid_body.friction=.42;ob.rigid_body.restitution=.10
    for f in ob.data.polygons:f.use_smooth=True
    ob.data.materials.clear();ob.data.materials.append(mat("Satin brass physical rail",(.39,.23,.055),metal=.82,rough=.20))
    mod=ob.modifiers.new("Subtle metal radius","BEVEL");mod.width=.002;mod.segments=2

# Measure the fully transformed world-space geometry instead of guessed coordinates.
verts=[ob.matrix_world@v.co for ob in tracks for v in ob.data.vertices]
z_top=max(v.z for v in verts)
z_bottom=min(v.z for v in verts)
x_min=min(v.x for v in verts);x_max=max(v.x for v in verts)
y_min=min(v.y for v in verts);y_max=max(v.y for v in verts)
top_vertices=[v for v in verts if v.z>=z_top-.02*max(z_top-z_bottom,.01)]
release=top_vertices[len(top_vertices)//2]
radius=max(.035,min((x_max-x_min),(y_max-y_min))*.058)
# Physically released glass sphere, no keyed trajectory.
bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=radius,
                                     location=(release.x,release.y,z_top+.28))
bead=bpy.context.object;bead.name="G01 clear starting marble / Bullet physical"
for p in bead.data.polygons:p.use_smooth=True
glass=mat("True clear glass sphere",(.76,.9,1),rough=.025,trans=.94,ior=1.52)
bead.data.materials.append(glass)
bpy.ops.rigidbody.object_add()
bead.rigid_body.type="ACTIVE";bead.rigid_body.collision_shape="SPHERE"
bead.rigid_body.mass=.08;bead.rigid_body.friction=.35;bead.rigid_body.restitution=.17
bead.rigid_body.linear_damping=.08
# Unadorned support plane catches stray marbles; physics cannot invent footage.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,z_bottom-.23))
table=bpy.context.object;table.name="Grounded smoked stone studio slab"
table.dimensions=(max(5,x_max-x_min+1),max(5,y_max-y_min+1),.4)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
table.data.materials.append(mat("Stone podium",(.020,.023,.034),rough=.48))
bpy.ops.rigidbody.object_add();table.rigid_body.type="PASSIVE"
table.rigid_body.collision_shape="BOX"

world=bpy.data.worlds.new("Studio photographic reflections");world.use_nodes=True
nodes=world.node_tree.nodes;links=world.node_tree.links;nodes.clear()
outnode=nodes.new("ShaderNodeOutputWorld")
hdri=Path(os.environ["ASMR_HDRI_FILE"])
if not hdri.is_file():raise RuntimeError("Missing authenticated CC0 HDRI")
env=nodes.new("ShaderNodeTexEnvironment");env.image=bpy.data.images.load(str(hdri))
bg=nodes.new("ShaderNodeBackground");bg.inputs["Strength"].default_value=.43
links.new(env.outputs["Color"],bg.inputs["Color"])
lp=nodes.new("ShaderNodeLightPath");camera_bg=nodes.new("ShaderNodeBackground")
camera_bg.inputs["Color"].default_value=(.012,.018,.025,1)
camera_bg.inputs["Strength"].default_value=.5
mix=nodes.new("ShaderNodeMixShader")
links.new(lp.outputs["Is Camera Ray"],mix.inputs[0])
links.new(bg.outputs["Background"],mix.inputs[1]);links.new(camera_bg.outputs["Background"],mix.inputs[2])
links.new(mix.outputs["Shader"],outnode.inputs["Surface"]);sc.world=world
focus=Vector((0,0,(z_top+z_bottom)/2))
for name,position,energy,colour,area_size in [
  ("Large photographed softbox",( -4,-3,z_top+4),550,(1,.89,.78),4),
  ("Cold specular edge",(3,1,z_top+3),360,(.6,.83,1),2),
  ("Warm gilt reflection",(1,-4,z_top+3),190,(1,.78,.45),1),
]:
    bpy.ops.object.light_add(type="AREA",location=position);ob=bpy.context.object
    ob.name=name;ob.data.energy=energy;ob.data.color=colour;ob.data.size=area_size
    ob.rotation_euler=(focus-ob.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.object.camera_add(location=(4.8,-7.8,z_top+3))
cam=bpy.context.object;cam.name="Wide complete sculpture product camera"
cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.lens=44;cam.data.dof.use_dof=True
cam.data.dof.focus_distance=(cam.location-focus).length;cam.data.dof.aperture_fstop=13
sc.camera=cam
if sc.rigidbody_world is None: bpy.ops.rigidbody.world_add()
sc.rigidbody_world.substeps_per_frame=24
sc.rigidbody_world.solver_iterations=35
sc.rigidbody_world.point_cache.frame_start=1
sc.rigidbody_world.point_cache.frame_end=120
bpy.ops.wm.save_as_mainfile(filepath=str(out/"original_Kenney_CC0_rigidbody_helix.blend"))
print("G01_REAL_GLASS_TRACK_CREATED",asset,dims,flush=True)
mode=os.environ.get("ASMR_MODE","LOOKDEV")
if mode!="SCENE":
    print("BAKING_KENNEY_TRACK_RIGIDBODY")
    r=bpy.ops.ptcache.bake_all(bake=True)
    if "FINISHED" not in r or not sc.rigidbody_world.point_cache.is_baked:
        raise RuntimeError("Bullet physics not baked")
    positions=[]
    for frame in (1,12,24,48,72,96,120):
        sc.frame_set(frame);loc=bead.matrix_world.translation
        positions.append([frame,*[round(v,5) for v in loc]])
        if not all(math.isfinite(v) for v in loc):raise RuntimeError("NaN physics")
    report={"source_model_url":"https://kenney.nl/assets/marble-kit",
            "source_license":"CC0","asset_sha256":hashlib.sha256(asset.read_bytes()).hexdigest(),
            "physics_solver":"Blender Bullet rigidbody","physics_baked":True,
            "sampled_ball_positions":positions,"status":"UNAPPROVED","audio_present":False}
    (out/"G01_PHYSICS_UNAPPROVED.json").write_text(json.dumps(report,indent=2))
    for frame in (1,48,96):
        sc.frame_set(frame);sc.render.filepath=str(out/f"G01_Lookdev_{frame:03d}_UNAPPROVED.png")
        bpy.ops.render.render(write_still=True)
    print("G01_CYCLES_LOOKDEV_AND_PHYSICS_DONE_NOT_VIDEO",flush=True)
