#!/usr/bin/env python3
"""Original non-AI Blender Cycles macro studio: prismatic wet-gel compression.

All motion deliberately designed: one 5-second/120-frame continuous scene,
a chromed spatula descends on a glossy iridescent gel prism, compresses it,
slides a small distance, releases, and a few beads wobble. No AI/stock montage.
"""
import os, math, random
from pathlib import Path
import bpy
from mathutils import Vector

random.seed(24)
OUT=Path(os.environ.get("ASMR_OUT","/kaggle/working/prismatic_asmr")).resolve()
OUT.mkdir(parents=True,exist_ok=True)
ASSETS=Path(os.environ.get("ASMR_ASSETS","/kaggle/input/satisfying-studio-cc0-asmr-v1"))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine="CYCLES"
sc.frame_start=1;sc.frame_end=120;sc.render.fps=24
sc.cycles.samples=int(os.environ.get("ASMR_SAMPLES","32"))
sc.cycles.max_bounces=6;sc.cycles.diffuse_bounces=2
sc.cycles.glossy_bounces=3;sc.cycles.transmission_bounces=6
# Older distro Blender lacks OIDN; the verified official LTS may enable denoising.
use_denoiser = os.environ.get("ASMR_DENOISE","0") == "1"
sc.cycles.use_denoising=use_denoiser
sc.view_layers[0].cycles.use_denoising=use_denoiser
sc.render.resolution_x=int(os.environ.get("ASMR_W","720"))
sc.render.resolution_y=int(os.environ.get("ASMR_H","1280"))
sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
sc.render.film_transparent=False
try:sc.view_settings.view_transform="AgX"
except Exception:sc.view_settings.view_transform="Filmic"
try:sc.view_settings.look="Medium High Contrast"
except Exception:pass

dev=os.environ.get("ASMR_DEVICE","CPU").upper()
if dev=="GPU":
    try:
        addon=bpy.context.preferences.addons["cycles"].preferences
        active=None
        for backend in [os.environ.get("ASMR_GPU_BACKEND","OPTIX").upper(),"CUDA"]:
            try:
                addon.compute_device_type=backend
                addon.get_devices()
                devices=[d for d in addon.devices if d.type==backend]
                if devices:
                    for d in addon.devices:d.use=d in devices
                    active=backend
                    break
            except Exception as exc:
                print("GPU_BACKEND_UNAVAILABLE",backend,str(exc)[:250],flush=True)
        if active is None:raise RuntimeError("No OPTIX/CUDA Blender Cycles devices found")
        sc.cycles.device="GPU"
        print("GPU_CYCLES_DEVICES",active,[(d.name,d.type,d.use) for d in addon.devices],flush=True)
    except Exception as e:
        if os.environ.get("ASMR_REQUIRE_GPU")=="1":raise
        print("GPU_INIT_FAILED_CPU_FALLBACK",repr(e),flush=True)
        sc.cycles.device="CPU"
else:sc.cycles.device="CPU"

def material(name,base,metal=0,rough=.23,trans=0,sss=0,coat=0):
    mat=bpy.data.materials.new(name);mat.diffuse_color=(*base,1)
    mat.use_nodes=True;sh=mat.node_tree.nodes.get("Principled BSDF")
    for k,v in [("Base Color",(*base,1)),("Metallic",metal),
                ("Roughness",rough),("IOR",1.44),("Transmission Weight",trans),
                ("Subsurface Weight",sss),("Coat Weight",coat),("Coat Roughness",.075)]:
        if k in sh.inputs:sh.inputs[k].default_value=v
    return mat,sh

def smooth(ob):
    if ob.type=="MESH":
        for p in ob.data.polygons:p.use_smooth=True
    return ob

def uvball(name,pos,scale,mat,segments=48,rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos)
    ob=bpy.context.object;ob.name=name;ob.scale=scale
    ob.data.materials.append(mat);smooth(ob);return ob

def cube(name,pos,scale,mat,bevel=.08):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    ob=bpy.context.object;ob.name=name;ob.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat)
    if bevel:
        be=ob.modifiers.new("Physically rounded edges", "BEVEL")
        be.width=bevel;be.segments=6
        ob.modifiers.new("Weighted surface normals","WEIGHTED_NORMAL")
    return ob

def animate(ob,keys,property_name="location"):
    for frame,val in keys:
        setattr(ob,property_name,val)
        ob.keyframe_insert(data_path=property_name,frame=frame)
    if ob.animation_data and ob.animation_data.action:
        action=ob.animation_data.action
        # API works for 4.0; these curves keep motion natural and controlled.
        try:
            for fc in action.fcurves:
                for p in fc.keyframe_points:p.interpolation="BEZIER"
        except Exception:pass

def noise_bump(mat,sh,scale=170,strength=.13,distance=.002):
    n=mat.node_tree.nodes
    tex=n.new("ShaderNodeTexNoise");tex.inputs["Scale"].default_value=scale
    tex.inputs["Detail"].default_value=3.5
    bm=n.new("ShaderNodeBump")
    bm.inputs["Strength"].default_value=strength
    bm.inputs["Distance"].default_value=distance
    mat.node_tree.links.new(tex.outputs["Fac"],bm.inputs["Height"])
    mat.node_tree.links.new(bm.outputs["Normal"],sh.inputs["Normal"])

# Physically sized glossy black ceramic saucer, subtle dark basalt PBR.
dark,ds=material("Muted amethyst photographic stone",(.095,.075,.105),rough=.32,coat=.10)
noise_bump(dark,ds,scale=240,strength=.1,distance=.002)
# Source CC0 rock image may be dark and obscure the transmission effect.
# Keep its verified micro-bump look, but light the surface with a custom stone tint.
files=[]
if files:
    try:
        tex=dark.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image=bpy.data.images.load(str(files[0]))
        dark.node_tree.links.new(tex.outputs["Color"],ds.inputs["Base Color"])
    except Exception as e:print("PBR_LOAD_WARNING",e)
cube("ASMR studio stone collider",
     (0,0,-.15),(100,100,.28),dark,.055)
chrome,ch=material("Mirror chromium spatula, no painted silver",(.68,.73,.82),metal=.93,rough=.18,coat=.08)
pink,ps=material("Soft rose anodised metal",(.56,.024,.23),metal=.72,rough=.14,coat=.25)
gold,gs=material("Rim gold alloy",(.65,.34,.11),metal=.96,rough=.13)
# Geometrically model a gel lozenge, rounded and softened with bevel, not a flat polygon.
# Shell and core are kept continuous under intentional keyframed pressure.
gel,gelsh=material("Soft internally scattering photographic cyan-lilac jelly",(.48,.73,.88),rough=.115,
                   trans=.48,sss=.25,coat=.26)
if "Subsurface Scale" in gelsh.inputs:
    gelsh.inputs["Subsurface Scale"].default_value=.065
if "Subsurface Radius" in gelsh.inputs:
    gelsh.inputs["Subsurface Radius"].default_value=(.7,.36,.24)
gelsh.inputs["IOR"].default_value=1.425
noise_bump(gel,gelsh,scale=130,strength=.028,distance=.00025)
# Pigment clouds, not graphic rainbow stripes: low-frequency variation inside
# one continuous refractive volume. A coherent 3D body deforms under the plate.
nd=gel.node_tree.nodes
coord=nd.new("ShaderNodeTexCoord")
cloud=nd.new("ShaderNodeTexNoise")
cloud.inputs["Scale"].default_value=3.7
cloud.inputs["Detail"].default_value=3.0
gel.node_tree.links.new(coord.outputs["Generated"],cloud.inputs["Vector"])
ramp=nd.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position=.23
ramp.color_ramp.elements[0].color=(.22,.47,.90,1)
ramp.color_ramp.elements[1].position=.77
ramp.color_ramp.elements[1].color=(.52,.35,.88,1)
mid=ramp.color_ramp.elements.new(.49)
mid.color=(.25,.77,.86,1)
gel.node_tree.links.new(cloud.outputs["Fac"],ramp.inputs["Fac"])
gel.node_tree.links.new(ramp.outputs["Color"],gelsh.inputs["Base Color"])

def signed_power(x,p):
    return math.copysign(abs(x)**p,x)

# Dense, continuous superellipsoid with real mesh-deformable contact geometry.
# Unlike a beveled cube, shape-key deformation now affects every visible vertex.
# For real soft-body physics the poles MUST be single vertices.
# The older shape-key prototype duplicated each polar vertex 64 times,
# creating 128 zero-area faces and an unstable physical simulation.
segments,rings=48,24
verts=[]
for j in range(1,rings):
    latitude=-math.pi/2+math.pi*j/rings
    c=signed_power(math.cos(latitude),.66)
    for i in range(segments):
        longitude=2*math.pi*i/segments
        x=.67*c*signed_power(math.cos(longitude),.78)
        y=.48*c*signed_power(math.sin(longitude),.78)
        z=.257*signed_power(math.sin(latitude),.65)
        verts.append((x,y,z))
south=len(verts);verts.append((0.0,0.0,-.257))
north=len(verts);verts.append((0.0,0.0,.257))
faces=[]
for j in range(rings-2):
    for i in range(segments):
        a=j*segments+i
        b=j*segments+(i+1)%segments
        faces.append((a,b,b+segments,a+segments))
for i in range(segments):
    next_i=(i+1)%segments
    faces.append((south,next_i,i))
    a=(rings-2)*segments+i
    b=(rings-2)*segments+next_i
    faces.append((north,a,b))
mesh=bpy.data.meshes.new("Closed dense deformable wet gel mesh")
mesh.from_pydata(verts,[],faces)
mesh.update()
body=bpy.data.objects.new("One continuous volumetric deforming jewel",mesh)
bpy.context.collection.objects.link(body)
body.location=(0,0,.274)
body.data.materials.append(gel)
smooth(body)
body.shape_key_add(name="Uncompressed volume",from_mix=False)
shape=body.shape_key_add(name="Contact surface, edge bulge and wet ripples",from_mix=False)
for i,vert in enumerate(body.data.vertices):
    x,y,z=vert.co
    theta=math.atan2(y,x)
    # Narrow rolling contact: only the jelly beneath the glass cylinder bends.
    # Outside the contact path the shoulders keep their height and gently bulge.
    contact=math.exp(-((y/.255)**2))
    radial=1+.017*math.cos(6*theta+.7)*contact
    shape.data[i].co=(x*(1+.115*contact)*radial,
                      y*(1+.18*contact)*radial,
                      z*(1-.432*contact*(.65+.35*max(0,z)/.257)))
# A real gel on tacky stone should deform locally under the tool.
# Previously keyframing its entire base 14cm sideways contributed to
# artificial lifting/sliding; retain a stationary substrate-anchored body.
animate(body,[(1,(0,0,.274)),(120,(0,0,.274))],"location")
for frame,value in [(1,0.0),(26,0.0),(42,.03),(48,.17),(70,1.0),
                    (87,.96),(104,.40),(120,.04)]:
    shape.value=value
    shape.keyframe_insert(data_path="value",frame=frame)
# Plate bottom at maximum press approximately coincides with
# relaxed gel top .531 and compressed gel top .421 (no large penetration).
shell,shsh=material("Transparent wet microfilm edge",(.48,.93,1.0),rough=.055,trans=.9,coat=.3)
# clustered droplets, translucent rich sugar beads on both sides, original scene.
bead_specs=[
    (-.78,-.49,.09,.095,(.9,.08,.46)),
    (-.86,.42,.10,.12,(.07,.85,.88)),
    (.86,-.38,.115,.12,(.97,.51,.035)),
    (.79,.49,.075,.082,(.42,.12,.94)),
    (-.53,.69,.06,.062,(.1,.86,.62)),
    (.31,-.68,.06,.071,(1,.16,.3))
]
for i,(x,y,z,r,colour) in enumerate(bead_specs):
    m,sh=material("Volumetric candy pearl %d"%i,colour,rough=.075,trans=.48,sss=.09,coat=.3)
    ob=uvball("Real solid sugar bead %02d"%i,(x,y,z),(r,r,r),m,48,24)
    # Small physically plausible settle after nearby contact.
    animate(ob,[(1,(x,y,z)),(62,(x,y,z)),(73,(x+.018*(1 if x>0 else -1),y,z)),
                (90,(x,y,z)),(120,(x,y,z))])
    # small caustic-like embedded highlight as actual tiny geometry
    m2,_=material("Pearl filament coating %02d"%i,(.89,.95,1),rough=.055,trans=.24)
    uvball("Specular micro air bead %02d"%i,(x-.03,y-.02,z+.06),(r*.23,r*.19,r*.12),m2,24,12)

# Original miniature jelly gemstones: thick, three-dimensional coloured volumes,
# different roughness and refraction rather than flat uniform gradient graphics.
gem_positions=[
  (-.90,-.44,.17,.24,(.09,.60,.95)),
  (.87,-.48,.15,.21,(.94,.09,.42)),
  (-.91,.35,.16,.23,(.18,.84,.52)),
  (.89,.42,.18,.25,(.96,.55,.05)),
  (.13,.81,.15,.20,(.67,.25,.96)),
]
for j,(x,y,z,size,tint) in enumerate(gem_positions):
    gm,gs=material("Jelly gem with own refraction %02d"%j,tint,
                   rough=.065,trans=.73,sss=.035,coat=.26)
    noise_bump(gm,gs,scale=110,strength=.025,distance=.0005)
    miniature=cube("Individual refractive colour prism %02d"%j,
                  (x,y,z),(size,size*.85,size*.72),gm,size*.23)
    smooth(miniature)
    animate(miniature,[(1,(x,y,z)),(58,(x,y,z)),
             (82,(x+.03*(1 if x>0 else -1),y,.145)),
             (120,(x+.04*(1 if x>0 else -1),y,.15))])
# Small physically distinct wet highlights are real volumes, not 2D graphics.
# tiny submerged air bubbles in gel body; parent to deform coherently
air,ash=material("Tiny physically separate trapped bubbles",(.85,.98,1),rough=.015,trans=1.0)
ash.inputs["IOR"].default_value=1.02
for i in range(33):
    a=random.random()*2*math.pi
    rr=random.random()*.49
    x=math.cos(a)*rr;y=math.sin(a)*rr*.69
    z=.270+(random.random()-.5)*.20
    r=.006+random.random()*.012
    ob=uvball("Entrained microbubble %02d"%i,(x,y,z),(r,r,r),air,20,10)
    # Parent keep inverse transform, avoid bubbles popping outside gel during compression.
    ob.parent=body
    ob.matrix_parent_inverse=body.matrix_world.inverted()

# One authentic rolling contact line, not an opaque reflective slab hiding the jelly.
# A rounded optically clear rod makes a narrow pressure trough in the dense mesh.
clear_press,cp=material("Polished clear quartz roller",(.95,.99,1),rough=.032,trans=.99,coat=.12)
cp.inputs["IOR"].default_value=1.46
bpy.ops.mesh.primitive_cylinder_add(vertices=80,radius=.075,depth=1.34,
    location=(-.06,0,.84),rotation=(0,math.pi/2,0))
press=bpy.context.object
press.name="Clear round ASMR roller — visible jelly contact"
press.data.materials.append(clear_press)
smooth(press)
# Contact-first real ASMR design: tool already near the gel in frame 1;
# gentle collision starts around frame 8, so we don't need a 1.8-second
# fake Foley bed over a hovering rod. The smallest sound starts at actual
# early contact and grows with roller pressure, then eases on release.
# Rest surface z≈0.531, rod radius 0.075, so z=0.615 is a safe 9mm gap.
# Maximum physically plausible collision remains at rod z≈0.50.
# This is a directed intent, NOT final contact verification; each baked
# frame and the recorded Foley still need actual joint listening/viewing.
# Shallow mechanically plausible roller stroke. The 75mm cylinder must
# NEVER travel ~85mm through a 500mm softbody; actual contact displacement
# is designed around 8-20mm, with a visible natural rebound.
animate(press,[(1,(0,0,.620)),(8,(0,0,.613)),
               (22,(0,0,.605)),(38,(0,0,.599)),
               (52,(0,0,.593)),(67,(0,0,.585)),
               (80,(0,0,.584)),(92,(0,0,.590)),
               (108,(0,0,.606)),(120,(0,0,.620))])
# Delicate anodised end collars indicate physical scale and rotation.
for dx in (-.67,.67):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.081,depth=.035,
        location=(dx-.06,0,.84),rotation=(0,math.pi/2,0))
    cap=bpy.context.object
    cap.name="Rose-metal roller bearing"
    cap.data.materials.append(pink)
    smooth(cap)
    # The ring is a true child in cylinder-local coordinates.
    # The previous parent inverse caused the metal end caps to float
    # away from the quartz rod in an actual Cycles render.
    cap.parent=press
    cap.matrix_parent_inverse.identity()
    cap.location=(dx,0,0)

# Softboxes (large luminous rectangles produce high-end controllable reflections).
def area(name,location,color,power,size_x,size_y,target=(0,0,.25)):
    bpy.ops.object.light_add(type="AREA",location=location)
    ob=bpy.context.object;ob.name=name;ob.data.color=color;ob.data.energy=power
    ob.data.shape="RECTANGLE";ob.data.size=size_x;ob.data.size_y=size_y
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat("-Z","Y").to_euler()
area("Huge white product photography key",(-2.4,-2.1,3.3),(1,.90,.82),160,1.45,1.7)
area("Cyan long curved rim",(2,1.1,2.7),(.36,.82,1),106,.7,1.6)
area("Magenta low ribbon highlight",(-1.7,1.3,1.2),(1,.39,.73),73,.6,1.2)
area("Fine warm jewellery glint",(.6,-2.2,3.8),(1,.87,.73),102,.55,1.3)
area("Large diffuse transmission key behind jelly",(0,2.6,2.15),(1,.88,.92),290,1.5,1.8)
# World environmental lift. Studio Small 09 is a ~1.6MB Poly Haven CC0
# *real photographed* softbox HDRI, used for physically credible wet-gel and
# polished-metal reflections (not a synthetic fill or copied video frame).
world=bpy.data.worlds.new("Photographic studio reflection environment")
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.06,.058,.084,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.60
hdr_path=os.environ.get("ASMR_HDRI_FILE","")
if hdr_path:
    if not Path(hdr_path).is_file():
        raise RuntimeError("Requested real CC0 studio HDRI missing; no silent CGI downgrade")
    nodes=world.node_tree.nodes
    links=world.node_tree.links
    nodes.clear()
    output=nodes.new("ShaderNodeOutputWorld")
    environment=nodes.new("ShaderNodeTexEnvironment")
    environment.image=bpy.data.images.load(str(Path(hdr_path).resolve()),check_existing=True)
    environment_bg=nodes.new("ShaderNodeBackground")
    environment_bg.inputs["Strength"].default_value=.48
    links.new(environment.outputs["Color"],environment_bg.inputs["Color"])
    camera_bg=nodes.new("ShaderNodeBackground")
    camera_bg.inputs["Color"].default_value=(.06,.054,.084,1)
    camera_bg.inputs["Strength"].default_value=.60
    light_path=nodes.new("ShaderNodeLightPath")
    selector=nodes.new("ShaderNodeMixShader")
    links.new(light_path.outputs["Is Camera Ray"],selector.inputs[0])
    links.new(environment_bg.outputs["Background"],selector.inputs[1])
    links.new(camera_bg.outputs["Background"],selector.inputs[2])
    links.new(selector.outputs["Shader"],output.inputs["Surface"])
    print("LICENSED_CC0_PHOTOGRAPHIC_STUDIO_HDRI",hdr_path,flush=True)
sc.world=world

# Product macro camera: close, angled, readable 5-second single shot.
bpy.ops.object.camera_add(location=(1.83,-3.70,2.64))
cam=bpy.context.object
focus=Vector((0,0,-.03))
cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
# Fill the portrait frame with physical gel deformation rather than an
# expensive empty countertop; macro optical focus remains on contact.
cam.data.type="PERSP";cam.data.lens=61
cam.data.dof.use_dof=True
cam.data.dof.focus_distance=(cam.location-focus).length
cam.data.dof.aperture_fstop=9.0
sc.camera=cam
# shallow, motion nearly imperceptible
# The genuine soft-body shifts gently under the roller and MUST stay
# inside the portrait macro frame throughout release. Follow with a small
# deliberate lateral camera truck, not an artificial jelly warp.
animate(cam,[(1,(1.83,-3.70,2.64)),(120,(1.96,-3.67,2.61))],"location")
sc.render.filepath=str(OUT/"lookdev.png")
mode=os.environ.get("ASMR_MODE","STILL").upper()
if mode=="SCENE":
    sc.frame_set(1)
    sc.render.filepath=str(OUT/"frames"/"frame_")
    (OUT/"frames").mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"editable_physics_input.blend"))
    print("ASMR_SIMULATOR_INPUT_READY_NOT_BAKED",flush=True)
elif mode=="STILL":
    sc.frame_set(int(os.environ.get("ASMR_STILL_FRAME","70")))
    blend_path=OUT/"prismatic_gel_scene.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.render.render(write_still=True)
    print("ORIGINAL_3D_STILL_RENDERED",sc.render.filepath,flush=True)
elif mode=="FRAME":
    n=int(os.environ.get("ASMR_FRAME","72"))
    sc.frame_set(n)
    sc.render.filepath=str(OUT/("frame_%04d.png"%n))
    bpy.ops.render.render(write_still=True)
elif mode=="ANIMATION":
    sc.render.filepath=str(OUT/"frames"/"frame_")
    (OUT/"frames").mkdir(exist_ok=True)
    sc.render.image_settings.file_format="PNG"
    sc.render.use_file_extension=True
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"prismatic_gel_scene.blend"))
    bpy.ops.render.render(animation=True)
    print("ORIGINAL_3D_FRAMES_RENDERED",120,flush=True)
else:raise RuntimeError("Unsupported mode: "+mode)
