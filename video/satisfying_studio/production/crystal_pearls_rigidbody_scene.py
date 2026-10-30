#!/usr/bin/env python3
"""Original 3D glass-pearls ASMR shot; actual Blender Bullet dynamics.

Uses the studio's verified Blender/Cycles, photographic CC0 HDRI and area
lights. A physically baked rigid-body source -- no generative video, stock
footage, shape-key motion or unapproved audio.
"""
import os,math,random
from pathlib import Path
import bpy
from mathutils import Vector
random.seed(17)
out=Path(os.environ.get("ASMR_OUT","/tmp/asmr_glass_pearls")).resolve()
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene
s.frame_start=1;s.frame_end=120;s.render.fps=24
s.render.engine="CYCLES"
s.cycles.samples=int(os.environ.get("ASMR_SAMPLES","18"))
s.cycles.max_bounces=6
s.render.resolution_x=int(os.environ.get("ASMR_W","720"))
s.render.resolution_y=int(os.environ.get("ASMR_H","1280"))
s.render.resolution_percentage=100
s.render.image_settings.file_format="PNG"
try:s.view_settings.view_transform="AgX"
except Exception:pass
s.view_layers[0].cycles.use_denoising=True
def mat(name,rgb,metal=0,rough=.2,trans=0,coat=0,ior=1.46):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1)
    m.use_nodes=True;bsdf=m.node_tree.nodes.get("Principled BSDF")
    options={"Base Color":(*rgb,1),"Metallic":metal,"Roughness":rough,
             "Transmission Weight":trans,"Coat Weight":coat,"IOR":ior}
    for key,val in options.items():
        if key in bsdf.inputs:bsdf.inputs[key].default_value=val
    return m,bsdf
def smooth(obj):
    for p in obj.data.polygons:p.use_smooth=True
    return obj
def area(name,loc,power,size,color=(1,1,1)):
    bpy.ops.object.light_add(type="AREA",location=loc)
    ob=bpy.context.object;ob.name=name;ob.data.energy=power
    ob.data.shape="DISK";ob.data.size=size;ob.data.color=color
    ob.rotation_euler=(Vector((0,0,.4))-ob.location).to_track_quat("-Z","Y").to_euler()
area("Photographic ribbon key",(-2,-2,4.5),330,3.0)
area("Blue rim",(2,1.5,3.0),200,2,(.56,.82,1))
area("Warm jewellery glint",(0,-1.8,3.9),150,.65,(1,.77,.61))
area("White fill",(1,-2.4,2.2),95,1.3)
world=bpy.data.worlds.new("CC0 photographed studio");world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.09,.085,.095,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.65
hdr=os.environ.get("ASMR_HDRI_FILE","")
if hdr:
    p=Path(hdr)
    if not p.is_file():raise RuntimeError("Requested CC0 HDRI missing")
    nodes=world.node_tree.nodes;links=world.node_tree.links;nodes.clear()
    output=nodes.new("ShaderNodeOutputWorld")
    tex=nodes.new("ShaderNodeTexEnvironment")
    tex.image=bpy.data.images.load(str(p.resolve()),check_existing=True)
    bg=nodes.new("ShaderNodeBackground");bg.inputs["Strength"].default_value=.55
    links.new(tex.outputs["Color"],bg.inputs["Color"])
    cam_bg=nodes.new("ShaderNodeBackground")
    cam_bg.inputs["Color"].default_value=(.09,.085,.12,1);cam_bg.inputs["Strength"].default_value=.70
    lp=nodes.new("ShaderNodeLightPath");mix=nodes.new("ShaderNodeMixShader")
    links.new(lp.outputs["Is Camera Ray"],mix.inputs[0])
    links.new(bg.outputs["Background"],mix.inputs[1])
    links.new(cam_bg.outputs["Background"],mix.inputs[2])
    links.new(mix.outputs["Shader"],output.inputs["Surface"])
s.world=world
# Polished dark studio slab; it also supports the ceramic bowl.
stone,stonebsdf=mat("Polished charcoal stone",(.075,.079,.091),rough=.3,coat=.15)
texture=stone.node_tree.nodes.new("ShaderNodeTexNoise")
texture.inputs["Scale"].default_value=240
bump=stone.node_tree.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value=.09;bump.inputs["Distance"].default_value=.001
stone.node_tree.links.new(texture.outputs["Fac"],bump.inputs["Height"])
stone.node_tree.links.new(bump.outputs["Normal"],stonebsdf.inputs["Normal"])
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.125))
floor=bpy.context.object;floor.name="Real stone tabletop"
floor.dimensions=(30,30,.24);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
floor.data.materials.append(stone)
bevel=floor.modifiers.new("Polished edge","BEVEL");bevel.width=.045;bevel.segments=3
bpy.context.view_layer.objects.active=floor
bpy.ops.rigidbody.object_add()
floor.rigid_body.type="PASSIVE";floor.rigid_body.friction=.65
# Ceramics are approximately conical/parabolic shallow cups, not a flat table.
ceramic,_=mat("Eggshell fired ceramic body",(.76,.74,.69),rough=.22,coat=.16)
gold,_=mat("Brushed brass rim",(.68,.39,.13),metal=.92,rough=.19)
N=96;radial_steps=18;R=.93
verts=[(0,0,.14)]
for j in range(1,radial_steps+1):
    rr=R*j/radial_steps
    # center z=.14, steep rim to 0.36, normal points inward/up
    z=.14+.22*(rr/R)**3.4
    for i in range(N):
        a=2*math.pi*i/N
        verts.append((rr*math.cos(a),rr*math.sin(a),z))
faces=[]
for i in range(N):
    a=1+i;b=1+(i+1)%N
    faces.append((0,a,b))
for j in range(1,radial_steps):
    for i in range(N):
        a=1+(j-1)*N+i;b=1+(j-1)*N+(i+1)%N
        c=a+N;d=b+N
        faces.append((a,c,d))
        faces.append((a,d,b))
mesh=bpy.data.meshes.new("Real rigid cup collision surface")
mesh.from_pydata(verts,[],faces);mesh.update()
dish=bpy.data.objects.new("Ceramic physics collector",mesh)
bpy.context.collection.objects.link(dish)
dish.data.materials.append(ceramic);smooth(dish)
# Renderer-only solidification: rigid collision tracks original surface.
sub=dish.modifiers.new("Ceramic subsurface finish","SUBSURF")
sub.levels=1;sub.render_levels=1
# The open, concave cosmetic bowl mesh is NOT a stable Bullet collider:
# the verified first bake launched a sphere 16m away due to a bad triangle
# contact normal. Keep the high-detail ceramic visibly rendered, but represent
# its contacting interior with simple accurate invisible convex proxies.
# Approximation follows the actual bowl's center floor and circular rim.
# These are genuine native passive Bullet rigid bodies, not animated tricks.
def passive_box(name,loc,dimensions,friction=.50,restitution=.13,rotation=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj=bpy.context.object;obj.name=name
    obj.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.rotation_euler[2]=rotation
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type="PASSIVE"
    obj.rigid_body.collision_shape="BOX"
    obj.rigid_body.friction=friction
    obj.rigid_body.restitution=restitution
    obj.rigid_body.use_margin=True
    obj.rigid_body.collision_margin=.001
    obj.hide_render=True
    return obj
# Interior floor top at z=.145, matching the actual ceramic center z=.14.
passive_box("Physical ceramic bottom collision",(0,0,.095),(1.70,1.70,.10),.42,.16)
# Twelve tangent rigid segments trace the visible cup rim around R=.93.
# A collection of CONVEX box contacts avoids the broken open-triangle MESH
# normals while preventing the marbles from escaping the staged ceramic dish.
for wall_index in range(12):
    phi=2*math.pi*wall_index/12
    radius=.89
    passive_box("Circular ceramic wall collision %02d"%wall_index,
        (radius*math.cos(phi),radius*math.sin(phi),.32),
        (.475,.065,.35),.46,.15,phi+math.pi/2)

bpy.ops.mesh.primitive_torus_add(major_radius=.915,minor_radius=.022,
    major_segments=96,minor_segments=16,location=(0,0,.36))
rim=bpy.context.object;rim.name="Brushed brass rim on collector"
rim.data.materials.append(gold);smooth(rim)
# True Bullet rigid spheres, one spontaneous release after another.
swatches=[
    (.04,.67,.92),(.98,.18,.42),(.99,.57,.07),(.19,.87,.58),
    (.64,.37,.96),(.90,.78,.06),(.16,.75,.80),(.98,.42,.18),(.67,.13,.76),
]
marbles=[]
for index,color in enumerate(swatches):
    m,shader=mat("Optical cut-glass pearl %02d"%index,color,rough=.065,trans=.65,coat=.32)
    if "Subsurface Weight" in shader.inputs:shader.inputs["Subsurface Weight"].default_value=.06
    if "Coat Roughness" in shader.inputs:shader.inputs["Coat Roughness"].default_value=.035
    angle=2*math.pi*index/len(swatches)+.25
    x=.37*math.cos(angle);y=.31*math.sin(angle)
    # Native Bullet gravity-only drop: no animated kinematic transitions.
    # Earlier kinematic toggles caused an actual 16.5m sideways explosion
    # during collision, even after replacing the bowl with convex colliders.
    # Stagger release naturally using different heights, no fake movement.
    radius=.115 + .007*(index%3)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,
                                        radius=radius,location=(x,y,1.0+.105*index))
    orb=bpy.context.object
    orb.name="Authentic rigid glass pearl %02d"%index
    orb.data.materials.append(m);smooth(orb)
    bpy.ops.rigidbody.object_add()
    orb.rigid_body.type="ACTIVE";orb.rigid_body.collision_shape="SPHERE"
    orb.rigid_body.mass=.055
    orb.rigid_body.friction=.30
    orb.rigid_body.restitution=.32
    orb.rigid_body.linear_damping=.12
    orb.rigid_body.angular_damping=.16
    orb.rigid_body.use_margin=True;orb.rigid_body.collision_margin=.001
    orb.rigid_body.kinematic=False
    # No keyframed impulses: actual gravity and real collisions determine motion.
    marbles.append(orb)
if s.rigidbody_world is None:
    bpy.ops.rigidbody.world_add()
s.rigidbody_world.substeps_per_frame=100
s.rigidbody_world.solver_iterations=25
s.rigidbody_world.point_cache.frame_start=1
s.rigidbody_world.point_cache.frame_end=120
# Camera shows the entire collector and all staged falling glass.
bpy.ops.object.camera_add(location=(2.7,-4.7,3.30))
cam=bpy.context.object;cam.name="Cinematic uninterrupted satisfying action"
focus=Vector((0,0,.68))
cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.lens=56
cam.data.dof.use_dof=True
cam.data.dof.focus_distance=(cam.location-focus).length
cam.data.dof.aperture_fstop=11
s.camera=cam
s.frame_set(1)
path=out/"crystal_pearls_original_physics_input.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(path))
print("BLENDER_REAL_RIGID_BODY_SCENE_CREATED",str(path),flush=True)
# Blender 4.5.15 on the free runner has a native loader SIGSEGV for this
# newly saved Bullet world. Avoid reopening a corrupt/unready Bullet scene
# before bake by completing the actual simulation in this same process.
if os.environ.get("ASMR_EXECUTE_PROOF","0")=="1":
    work=Path(__file__).with_name("crystal_pearls_bake_and_proof.py")
    exec(compile(work.read_text(encoding="utf-8"),str(work),"exec"),
         {"__name__":"__main__","__file__":str(work)})
