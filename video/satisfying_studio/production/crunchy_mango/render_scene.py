#!/usr/bin/env python3
"""Premium-look dev, original physically segmented lacquered mango candy in Blender.
Commercial rights: scene geometry authored; CC0 Poly Haven HDRI, original Foley not used in render.
No user reference video pixels or audio are used.
"""
import bpy, math, os, sys, json, random
from pathlib import Path
from mathutils import Vector
from math import pi, sin, cos
rng=random.Random(20261031)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
def arg(name,default):
 return args[args.index(name)+1] if name in args and args.index(name)+1<len(args) else default
OUT=Path(arg('--out','/tmp/crunchy_mango'));OUT.mkdir(parents=True,exist_ok=True)
LOOKDEV=('--lookdev' in args)
FRAME_LIST=[1,24,45,54,57,72,92,116,144] if LOOKDEV else list(range(1,145))
W,H=(360,640) if LOOKDEV else (720,1280)
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
scene=bpy.context.scene
scene.render.film_transparent=False
scene.render.resolution_x=W;scene.render.resolution_y=H;scene.render.resolution_percentage=100
scene.frame_start=1;scene.frame_end=144;scene.render.fps=24
for e in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE','CYCLES'):
 try:
  scene.render.engine=e
  break
 except Exception:pass
print('RENDER ENGINE',scene.render.engine,'BLENDER',bpy.app.version_string,flush=True)
if scene.render.engine=='CYCLES':
 scene.cycles.samples=24 if LOOKDEV else 32
else:
 if hasattr(scene,'eevee') and hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=64
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.film_transparent=False
scene.render.use_file_extension=True
try:scene.view_settings.view_transform='AgX'
except Exception:scene.view_settings.view_transform='Filmic'
try:scene.view_settings.look='Medium High Contrast'
except Exception:pass
scene.view_settings.exposure=0.0;scene.view_settings.gamma=1.0
scene.render.image_settings.color_depth='8'
# --- Materials: coherent, high-gloss layered lacquer over orange mango gel ---
def mat(name,color,rough=.2,metal=0,coat=.0,subsurface=0,transmission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF')
 def prop(key,value):
  if key in p.inputs:p.inputs[key].default_value=value
 prop('Base Color',(*color,1));prop('Roughness',rough);prop('Metallic',metal)
 prop('Coat Weight',coat);prop('Coat Roughness',.09)
 prop('Subsurface Weight',subsurface);prop('Transmission Weight',transmission)
 return m
shell=mat('SUGAR_GLASS | polished ruby-gold lacquer',(.95,.16,.035),.115,.18,.75)
p=shell.node_tree.nodes.get('Principled BSDF');n=shell.node_tree.nodes
tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=5.4;tex.inputs['Detail'].default_value=4.0;tex.inputs['Roughness'].default_value=.6
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.17;ramp.color_ramp.elements[0].color=(.75,.04,.055,1)
ramp.color_ramp.elements[1].position=.86;ramp.color_ramp.elements[1].color=(1,.46,.055,1)
ramp.color_ramp.elements.new(.51).color=(.96,.14,.024,1)
shell.node_tree.links.new(tex.outputs['Fac'],ramp.inputs[0]);shell.node_tree.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
# Very fine lacquer microtexture at true photographic macro scale.
noise2=n.new('ShaderNodeTexNoise');noise2.inputs['Scale'].default_value=112;noise2.inputs['Detail'].default_value=2
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.095;bump.inputs['Distance'].default_value=.012
shell.node_tree.links.new(noise2.outputs['Fac'],bump.inputs['Height']);shell.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
core=mat('JUICY_FIBROUS_INNER | deep apricot gel',(.97,.28,.023),.17,0,.66,.23,.07)
cp=core.node_tree.nodes.get('Principled BSDF');nn=core.node_tree.nodes
ct=nn.new('ShaderNodeTexNoise');ct.inputs['Scale'].default_value=19;ct.inputs['Detail'].default_value=3
cb=nn.new('ShaderNodeBump');cb.inputs['Strength'].default_value=.085;cb.inputs['Distance'].default_value=.025
core.node_tree.links.new(ct.outputs['Fac'],cb.inputs['Height']);core.node_tree.links.new(cb.outputs['Normal'],cp.inputs['Normal'])
pressmat=mat('Glossy porcelain press and golden rim',(.11,.115,.12),.145,.52,.3)
gold=mat('Champagne gold pressed collar',(.7,.4,.16),.18,.8,.42)
base=mat('Deep rose-graphite display plinth',(.028,.036,.04),.23,.25,.37)
edge=mat('Champagne gold display rim',(.64,.38,.14),.19,.77,.49)
back=mat('Backdrop | sophisticated emerald charcoal',(.012,.03,.035),.46,.05)
black=mat('Fine engraved fracture grooves',(.14,.045,.022),.34,0)
# --- Scanned shell shape replaced with authored polished candy geometry ---
CX,CY,CZ=0,0,1.26
def surf(theta,phi,inner=1):
 # asymmetric mango silhouette, narrowed shoulders, soft cheek, non-potato proportions.
 q=cos(theta)
 rf=(1-.16*q+.025*cos(3*phi+.6)*sin(theta))
 xx=.92*rf*sin(theta)*cos(phi)
 yy=.77*rf*sin(theta)*sin(phi)
 zz=CZ+1.07*q + .05*sin(theta)*cos(phi+.45)
 return Vector((CX+inner*xx,CY+inner*yy,CZ+(zz-CZ)*inner))
# continuous intact skin; its replacement fragments are tangent-aligned at the moment of fracture.
def mesh_obj(name,verts,faces,material):
 mesh=bpy.data.meshes.new(name+' mesh');mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
 obj.data.materials.append(material)
 for polygon in obj.data.polygons:polygon.use_smooth=True
 return obj
verts=[];faces=[];NN=64;MM=96
for i in range(NN+1):
 th=.001+(pi-.002)*i/NN
 for j in range(MM+1):verts.append(tuple(surf(th,-pi+2*pi*j/MM)))
for i in range(NN):
 for j in range(MM):
  a=i*(MM+1)+j;faces.append((a,a+1,a+MM+2,a+MM+1))
whole=mesh_obj('Unbroken seamless ruby gold coating',verts,faces,shell)
whole.modifiers.new('Physical sugar glaze thickness','SOLIDIFY').thickness=.019
# Orange fleshy core is physically within the shell and only revealed after real shell pieces move.
coreverts=[tuple(surf(.001+(pi-.002)*i/NN,-pi+2*pi*j/MM,inner=.94)) for i in range(NN+1) for j in range(MM+1)]
objcore=mesh_obj('Soft wet orange mango center',coreverts,faces,core)
objcore.scale=(1,1,1)
for f,s in ((1,(1,1,1)),(52,(1,1,1)),(86,(1.045,1.035,.955)),(126,(1.035,1.04,.97)),(144,(1.04,1.04,.97))):
 objcore.scale=s;objcore.keyframe_insert(data_path='scale',frame=f)
# multiple contiguous shell tiles, including real extruded edges. Random selected tile groups physically break.
shards=[]
NTH,NPH=10,16
for i in range(NTH):
 for j in range(NPH):
  # polygons follow the original smooth continuous surface, 7x7 subdivided
  va=[];fa=[];Q=6
  for iy in range(Q+1):
   th=.001+(pi-.002)*(i+iy/Q)/NTH
   for ix in range(Q+1):
    ph=-pi+2*pi*(j+ix/Q)/NPH
    va.append(surf(th,ph))
  pivot=sum(va,Vector((0,0,0)))/len(va)
  for iy in range(Q):
   for ix in range(Q):
    a=iy*(Q+1)+ix;fa.append((a,a+1,a+Q+2,a+Q+1))
  ob=mesh_obj(f'Physically separate lacquer fragment {i:02d}_{j:02d}',[tuple(p-pivot) for p in va],fa,shell)
  ob.location=pivot
  thick=ob.modifiers.new('Brittle shell 18 mm','SOLIDIFY');thick.thickness=.018
  # No bevel during initial match to avoid disjoint overlarge seams.
  ob.hide_render=True;ob.keyframe_insert(data_path='hide_render',frame=1)
  ob.hide_render=True;ob.keyframe_insert(data_path='hide_render',frame=54)
  ob.hide_render=False;ob.keyframe_insert(data_path='hide_render',frame=55)
  # Front negative Y; zone of fracture near pressure point and first lower front edge.
  front=math.sin(-pi+2*pi*(j+.5)/NPH)<-.25
  mid=(1<=i<=8)
  priority=rng.random()
  detach=front and mid and (priority<.78)
  base_loc=pivot.copy()
  if detach:
   # physical outward displacement, gravity and torque follow contact-pressure impulse.
   direction=Vector((pivot.x*.64,(pivot.y-.12)*.55,-.14)).normalized()
   travel=.12+rng.random()*.32
   finish=base_loc+direction*travel+Vector(((rng.random()-.5)*.12,-.05,-.13-rng.random()*.15))
   qrot=(rng.random()-.5)*.65
   at=55+int(rng.random()*18)
   for frame,t in ((1,0),(54,0),(55,0),(at,0),(min(144,at+20),.6),(144,1)):
    ob.location=base_loc.lerp(finish,t)
    ob.rotation_euler=(qrot*t,.10*t,(rng.random()-.5)*.20*t)
    ob.keyframe_insert(data_path='location',frame=frame)
    ob.keyframe_insert(data_path='rotation_euler',frame=frame)
  else:
   # Nearby coating remains attached while front brittle shell visibly fractures.
   ob.location=base_loc
  shards.append({'name':ob.name,'detaches':bool(detach),'center':[round(c,4) for c in pivot]})
whole.hide_render=False;whole.keyframe_insert(data_path='hide_render',frame=1)
whole.hide_render=False;whole.keyframe_insert(data_path='hide_render',frame=54)
whole.hide_render=True;whole.keyframe_insert(data_path='hide_render',frame=55)
# Gently embossed knife-free candy press with rounded porcelain rim; no potato cleaver.
def cylinder(name,radius,depth,z,ma,bevel=.08):
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=radius,depth=depth,location=(0,0,z))
 ob=bpy.context.object;ob.name=name;ob.data.materials.append(ma)
 if bevel>0:
  mod=ob.modifiers.new('Rounded professional product detail','BEVEL');mod.width=bevel;mod.segments=5
  ob.modifiers.new('Smooth corners','WEIGHTED_NORMAL')
 return ob
pad=cylinder('Rounded porcelain pressure pad',.56,.24,3.5,pressmat,.10)
ring=cylinder('Golden contact cap',.54,.065,3.40,gold,.02)
stem=cylinder('Polished press shaft',.15,1.0,4.08,pressmat,.035)
for ob in (pad,ring,stem):
 z=ob.location.z
 for f, dz in ((1,.0),(24,-.18),(53,-1.00),(70,-1.09),(92,-1.10),(116,-.52),(144,.02)):
  ob.location.z=z+dz;ob.keyframe_insert('location',frame=f)
# Elegant base, not a rustic potato board.
plinth=cylinder('Reflective black stone platter',2.25,.25,.025,base,.09)
rim=cylinder('Fine golden platter lip',2.24,.045,-.065,edge,.012)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.14));ground=bpy.context.object;ground.name='Seamless forest-green infinity studio floor';ground.data.materials.append(back)
# A couple detached tiny shell shards genuinely descend during secondary crunch.
# Tiny flakes stay within the local fracture region, not CGI sparkle confetti.
for k in range(18):
 i=rng.randint(3,7);j=rng.randint(9,13)
 theta=pi*(i+.5)/NTH;phi=-pi+2*pi*(j+.5)/NPH
 P=surf(theta,phi)*1.015
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.028+rng.random()*.024,location=P)
 fl=bpy.context.object;fl.name=f'Brittle sugar lacquer microfragment {k:02d}';fl.data.materials.append(shell)
 f0=rng.randrange(57,92)
 fl.hide_render=True;fl.keyframe_insert('hide_render',frame=1);fl.keyframe_insert('hide_render',frame=f0-1)
 fl.hide_render=False;fl.keyframe_insert('hide_render',frame=f0)
 A=P.copy();B=P+Vector(((rng.random()-.5)*.5,-.12-rng.random()*.16,-.36-rng.random()*.45))
 for f,t in ((f0,0),(f0+14,.45),(min(f0+44,144),1)):
  fl.location=A.lerp(B,t);fl.keyframe_insert('location',frame=f)
# camera, studio HDRI and 3-point calibrated softboxes
bpy.ops.object.camera_add(location=(4.2,-7.0,4.05));cam=bpy.context.object
D=Vector((0,0,1.55))-cam.location;cam.rotation_euler=D.to_track_quat('-Z','Y').to_euler();scene.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=4.55;cam.data.lens=65
for f,x in ((1,4.55),(144,4.23)):
 cam.data.ortho_scale=x;cam.data.keyframe_insert('ortho_scale',frame=f)
world=bpy.data.worlds.new('Poly Haven Studio Small 09 | CC0 lighting');scene.world=world;world.use_nodes=True
bg=world.node_tree.nodes.get('Background');bg.inputs['Strength'].default_value=.46
env=world.node_tree.nodes.new('ShaderNodeTexEnvironment')
path=Path(os.environ.get('CRUNCH_ASSETS','/tmp/crunchy_mango_assets'))/'studio_small_09_1k.hdr'
if path.exists():env.image=bpy.data.images.load(str(path));world.node_tree.links.new(env.outputs['Color'],bg.inputs['Color'])
else:bg.inputs['Color'].default_value=(.10,.14,.16,1)
def softbox(name,where,power,color,size,target=(0,0,1.2)):
 bpy.ops.object.light_add(type='AREA',location=where);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size
 o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
softbox('Vivid golden key',(-3,-4,6),720,(1,.80,.64),5.0)
softbox('Blue-silver lacquer rim',(3,2,5.5),980,(.62,.83,1),3.2)
softbox('White reflective vertical strip',(1,-5,4),320,(1,1,1),1.4)
softbox('Back peach rim',(-2.5,3,4.2),480,(1,.52,.31),2.0)
# Minimal factual manifest; not a subjective release approval.
metadata={'title':'Candy-Coated Mango Fracture â 3D ASMR Original', 'actual_medium':'CGI_3D','lookdev':LOOKDEV,'fps':24,
 'shell_tiles':len(shards),'shell_detaching':sum(int(x['detaches']) for x in shards),'visible_first_fracture_frame':55,
 'crunch_cues_frames':[55,85],'render_engine':scene.render.engine,'assets':'CC0 Poly Haven studio_small_09 HDRI',
 'visuals_from_uploaded_reference':False,'quality_status':'UNAPPROVED_LOOKDEV'}
(OUT/'3D_RENDER_METADATA.json').write_text(json.dumps(metadata,indent=2))
scene.render.image_settings.compression=35
for frame in FRAME_LIST:
 scene.frame_set(frame)
 scene.render.filepath=str(OUT/f'frame_{frame:03d}.png')
 bpy.ops.render.render(write_still=True)
 print('FINISHED_FRAME',frame,scene.render.filepath,flush=True)
print('RENDERED_FRAMES',len(FRAME_LIST),flush=True)
