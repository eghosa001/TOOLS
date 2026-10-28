#!/usr/bin/env python3
"""One traditional Blender Cycles 3D macro still. NO generative video or autoplay."""
import math,os
from pathlib import Path
import bpy
from mathutils import Vector

assets=Path(os.environ["SATISFY_ASSETS"])
out=Path(os.environ["SATISFY_OUTPUT"]);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.render.engine="CYCLES"
s.render.resolution_x=540;s.render.resolution_y=960
s.render.image_settings.file_format="PNG"
s.render.filepath=str(out/"blender_3d_lookdev.png")
s.cycles.samples=24;s.cycles.use_denoising=True
s.frame_set(108)
try:
    pref=bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX","CUDA"):
        try:
            pref.compute_device_type=kind;pref.get_devices()
            gpus=[d for d in pref.devices if d.type in ("OPTIX","CUDA")]
            if gpus:
                for d in pref.devices:d.use=(d in gpus)
                s.cycles.device="GPU"
                break
        except Exception as e:print("GPU backend unsupported:",kind,str(e)[:100])
    print("CYCLES RENDER DEVICE",s.cycles.device)
except Exception as e:print("CPU FALLBACK",str(e)[:120])
try:s.view_settings.view_transform="AgX"
except Exception:s.view_settings.view_transform="Filmic"

def mat(name,color,metal=0,rough=.14,trans=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes.get("Principled BSDF")
    n.inputs["Base Color"].default_value=color
    n.inputs["Metallic"].default_value=metal
    n.inputs["Roughness"].default_value=rough
    for k in ("Transmission Weight","Transmission"):
        if k in n.inputs:n.inputs[k].default_value=trans
    return m

def smooth(obj):
    for p in obj.data.polygons:p.use_smooth=True

def cyl(name,z,r,depth,m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=r,depth=depth,location=(0,0,z))
    ob=bpy.context.object;ob.name=name;ob.data.materials.append(m);smooth(ob)
    bevel=ob.modifiers.new("Real chamfer reflections","BEVEL")
    bevel.width=.012;bevel.segments=3

stone=mat("Photographic dark basalt",(.03,.03,.038,1),rough=.43)
node=stone.node_tree.nodes.get("Principled BSDF")
for name,socket in (("dark_rock_diff","Base Color"),("dark_rock_rough","Roughness")):
    files=list(assets.glob(name+".*"))
    if not files:raise RuntimeError("Required CC0 PBR texture missing: "+name)
    tex=stone.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image=bpy.data.images.load(str(files[0]))
    if socket=="Roughness":tex.image.colorspace_settings.name="Non-Color"
    stone.node_tree.links.new(tex.outputs["Color"],node.inputs[socket])
micro=stone.node_tree.nodes.new("ShaderNodeTexNoise");micro.inputs["Scale"].default_value=52
bump=stone.node_tree.nodes.new("ShaderNodeBump")
bump.inputs["Distance"].default_value=.006;bump.inputs["Strength"].default_value=.15
stone.node_tree.links.new(micro.outputs["Fac"],bump.inputs["Height"])
stone.node_tree.links.new(bump.outputs["Normal"],node.inputs["Normal"])
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.08))
slab=bpy.context.object;slab.dimensions=(4,4,.16)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
slab.name="Photographic basalt PBR slab";slab.data.materials.append(stone)

chrome=mat("Reflective polished chrome",(.86,.88,.98,1),metal=1,rough=.08)
violet=mat("Electric violet metallic tube",(.12,.008,.67,1),metal=.9,rough=.1)
cyl("Coloured metallic squeeze tube",1.3,.2,.73,violet)
cyl("Chrome connector",.87,.12,.12,chrome)
bpy.ops.mesh.primitive_cone_add(vertices=96,radius1=.024,radius2=.115,depth=.3,location=(0,0,.65))
nozzle=bpy.context.object;nozzle.name="Polished precision tip"
nozzle.data.materials.append(chrome);smooth(nozzle)

colors=[(.02,.9,1,1),(.96,.03,.32,1),(.98,.63,.02,1),(.03,.92,.35,1),(.55,.16,.98,1)]
for j,color in enumerate(colors):
    glass=mat("Colored transparent glass petal "+str(j),color,rough=.048,trans=.88)
    verts=[];faces=[];n=20
    for row in range(13):
        v=row/12
        width=.27*max(.0001,math.sin(math.pi*v))**.8
        for col in range(n):
            u=2*col/(n-1)-1
            verts.append((width*u,.83*v,.09+.12*v+.05*(1-u*u)*math.sin(math.pi*v)))
    for row in range(12):
        for col in range(n-1):
            i=row*n+col;faces.append((i,i+1,i+n+1,i+n))
    mesh=bpy.data.meshes.new("Volumetric glass petal")
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new("Glass sculpture petal "+str(j),mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(glass)
    ob.rotation_euler[2]=j*2*math.pi/5
    thick=ob.modifiers.new("Real transparent solid depth","SOLIDIFY");thick.thickness=.028
    sub=ob.modifiers.new("Smooth curved silhouette","SUBSURF");sub.levels=1
    for f,scale in ((1,.04),(86,.07),(95,.19),(108,.85),(120,1.0)):
        ob.scale=(scale,scale,scale);ob.keyframe_insert("scale",frame=f)
    smooth(ob)

gel=mat("Wet amber glasslike center",(.98,.11,.025,1),rough=.06,trans=.63)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=.18,location=(0,0,.16))
center=bpy.context.object;center.data.materials.append(gel);smooth(center)
for name,loc,power,color,size in (
    ("Left large softbox",(-2.6,-1.9,3.6),850,(.51,.8,1),3.3),
    ("Amber reflection strip",(2,1.7,2.3),650,(1,.49,.3),2.3),
    ("Mint rim",(0,2.2,4),520,(.45,1,.83),2.4)):
    bpy.ops.object.light_add(type="AREA",location=loc)
    light=bpy.context.object;light.name=name
    light.data.energy=power;light.data.color=color
    light.data.shape="DISK";light.data.size=size

hdri=list(assets.glob("studio_small_09_hdri.*"))
if not hdri:raise RuntimeError("Required studio HDRI missing")
world=bpy.data.worlds.new("Poly Haven CC0 studio")
world.use_nodes=True;s.world=world
env=world.node_tree.nodes.new("ShaderNodeTexEnvironment")
env.image=bpy.data.images.load(str(hdri[0]))
world.node_tree.links.new(env.outputs["Color"],world.node_tree.nodes.get("Background").inputs["Color"])
world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.25

bpy.ops.object.camera_add(location=(2.35,-3.4,2.15))
cam=bpy.context.object;target=Vector((0,0,.46))
cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.lens=70
cam.data.dof.use_dof=True
cam.data.dof.focus_distance=(cam.location-target).length
cam.data.dof.aperture_fstop=6.3;s.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(out/"blender_3d_source.blend"))
bpy.ops.render.render(write_still=True)
print("RENDERED REAL 3D STILL; NO VIDEO OR QUALITY APPROVAL",s.render.filepath)
