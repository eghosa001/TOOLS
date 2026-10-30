#!/usr/bin/env python3
"""Two original Blender/Cycles ASMR 5s proof scenes; NOT premium-release approved.
Concepts: pre-cleaved glossy yellow fruit / genuinely simulated soft-body lava gel.
Uses existing official Blender bootstrap + FFmpeg/CC0 production infrastructure.
"""
import bpy, math, random, os, json
from pathlib import Path
from mathutils import Vector
random.seed(314)
MODE=os.environ.get("ASMR_CONCEPT","cut").lower()
OUT=Path(os.environ.get("ASMR_OUT","/tmp/asmr_new_proofs")).resolve()
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine="CYCLES"
sc.cycles.samples=int(os.environ.get("ASMR_SAMPLES","14"))
sc.cycles.use_denoising=True
sc.cycles.max_bounces=5
sc.render.resolution_x=int(os.environ.get("ASMR_W","720"))
sc.render.resolution_y=int(os.environ.get("ASMR_H","1280"))
sc.render.resolution_percentage=100
sc.render.fps=24
sc.frame_start=1
sc.frame_end=120
sc.render.image_settings.file_format="PNG"
try:sc.view_settings.view_transform="AgX"
except Exception:pass
sc.world=bpy.data.worlds.new("Moody product studio")
sc.world.use_nodes=True
sc.world.node_tree.nodes["Background"].inputs["Color"].default_value=(.07,.055,.06,1)
sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value=.43

def mat(name,color,rough=.24,metal=0,trans=0,sss=0,coat=0,emission=None):
 m=bpy.data.materials.new(name);m.use_nodes=True
 p=m.node_tree.nodes.get("Principled BSDF")
 p.inputs["Base Color"].default_value=(*color,1)
 p.inputs["Roughness"].default_value=rough
 p.inputs["Metallic"].default_value=metal
 p.inputs["Transmission Weight"].default_value=trans
 p.inputs["Subsurface Weight"].default_value=sss
 p.inputs["Coat Weight"].default_value=coat
 if emission:
  p.inputs["Emission Color"].default_value=(*emission[0],1)
  p.inputs["Emission Strength"].default_value=emission[1]
 return m
def detail(m,scale=85,strength=.12,distance=.008):
 n=m.node_tree.nodes;l=m.node_tree.links
 p=n.get("Principled BSDF")
 noise=n.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=scale
 bump=n.new("ShaderNodeBump");bump.inputs["Strength"].default_value=strength
 bump.inputs["Distance"].default_value=distance
 l.new(noise.outputs["Fac"],bump.inputs["Height"])
 l.new(bump.outputs["Normal"],p.inputs["Normal"])
def smooth(o):
 if o.type=="MESH":
  for p in o.data.polygons:p.use_smooth=True
 return o
def ball(name,loc,scale,material,seg=32,rings=16):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
 ob=bpy.context.object;ob.name=name;ob.scale=scale
 ob.data.materials.append(material)
 return smooth(ob)
def block(name,loc,scale,material,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
 ob=bpy.context.object;ob.name=name
 ob.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 ob.data.materials.append(material)
 if bevel:
  mod=ob.modifiers.new("manufactured rounded edge","BEVEL")
  mod.width=bevel;mod.segments=3
  ob.modifiers.new("weighted metal normals","WEIGHTED_NORMAL")
 return ob
def light(name,loc,color,power,shape=(2,1),target=(0,0,.6)):
 bpy.ops.object.light_add(type="AREA",location=loc)
 ob=bpy.context.object;ob.name=name
 ob.data.energy=power;ob.data.color=color
 ob.data.shape="RECTANGLE";ob.data.size=shape[0];ob.data.size_y=shape[1]
 ob.rotation_euler=(Vector(target)-ob.location).to_track_quat("-Z","Y").to_euler()
def animated(ob,path,points):
 for f,v in points:
  setattr(ob,path,v)
  ob.keyframe_insert(data_path=path,frame=f)
 for fcurve in (ob.animation_data.action.fcurves if ob.animation_data and hasattr(ob.animation_data.action,"fcurves") else []):
  for kp in fcurve.keyframe_points:kp.interpolation="BEZIER"
def set_camera(loc,target,lens=55):
 bpy.ops.object.camera_add(location=loc)
 ob=bpy.context.object;sc.camera=ob
 ob.rotation_euler=(Vector(target)-ob.location).to_track_quat("-Z","Y").to_euler()
 ob.data.lens=lens
 ob.data.dof.use_dof=True
 ob.data.dof.focus_distance=(Vector(target)-ob.location).length
 ob.data.dof.aperture_fstop=8
 return ob
# Tactile tabletop with macro microstructure.
wood=mat("warm fine-grain cutting surface" if MODE=="cut" else "glossy charcoal stone",(.19,.098,.045) if MODE=="cut" else (.026,.018,.023),rough=.37)
detail(wood,90,.25,.015)
block("tactile real contact surface",(0,0,-.105),(5,5,.19),wood,.036)
light("large diffused warm macro softbox",(-2,-3,4),(1,.80,.61),450,(2.4,3))
light("crisp white specular strip",(2,-.8,3),(1,.95,.93),320,(.85,2.7))
light("electric rim to reveal refraction",(0,2,2.9),(.62,.79,1),370,(1.2,2))
light("amber low bounce",(-2,1,.9),(1,.39,.16),65,(1.3,.7))
if MODE=="cut":
 sc.world.node_tree.nodes["Background"].inputs["Color"].default_value=(.12,.12,.14,1)
 skin=mat("mango-gold microsculpted strawberry skin",(.94,.39,.012),rough=.16,trans=.12,sss=.18,coat=.65)
 detail(skin,130,.22,.006)
 inside=mat("wet amber cut interior",(.97,.51,.035),rough=.09,trans=.52,sss=.09,coat=.48)
 detail(inside,65,.12,.002)
 seeds=mat("pale recessed fruit achenes",(1,.83,.37),rough=.25,coat=.36)
 green=mat("fresh green miniature strawberry crown",(.035,.28,.025),rough=.30,sss=.09)
 steel=mat("precision stainless steel knife",(.64,.72,.79),rough=.13,metal=1)
 blade_dark=mat("blade edge line",(.07,.10,.13),rough=.11,metal=1)
 # One continuous lathed 3D strawberry skin, properly boolean-split into two solid meshes.
 bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,location=(0,0,.02))
 proto=bpy.context.object;proto.name="closed original strawberry geometry"
 for v in proto.data.vertices:
  t=(v.co.z+1)*.5
  waist=max(.03,math.sin(math.pi*max(.003,min(.997,t)))**.66)
  radius=waist*(.69+.22*t)
  v.co.x*=radius
  v.co.y*=radius*.83
  v.co.z=.10+1.23*t
 # Material slot 1 is the actual volumetric cut cap.
 proto.data.materials.append(skin);proto.data.materials.append(inside)
 smooth(proto)
 halves=[]
 for sign,name in ((-1,"left solid strawberry half"),(1,"right solid strawberry half")):
  ob=proto.copy();ob.data=proto.data.copy();bpy.context.collection.objects.link(ob)
  cutter=block("temporary exact boolean half-space",(sign*1.7,0,.8),(3.4,4,3.9),inside)
  mod=ob.modifiers.new("true volumetric bisect, enclosed cut surface","BOOLEAN")
  mod.operation="INTERSECT";mod.solver="EXACT";mod.object=cutter
  bpy.context.view_layer.objects.active=ob
  bpy.ops.object.modifier_apply(modifier=mod.name)
  bpy.data.objects.remove(cutter,do_unlink=True)
  ob.name=name;halves.append(ob)
 bpy.data.objects.remove(proto,do_unlink=True)
 # Core mesh cut faces: thin wet amber layer, seeded bubbles.
 for sign,ob in ((-1,halves[0]),(1,halves[1])):
  # Per-half cut-face pearlescent wet interior, visibly revealed after split.
  for z in (.35,.58,.82,1.04):
   t=(z-.1)/1.23
   rr=max(.02,math.sin(math.pi*t)**.66)*(.69+.22*t)
   b=ball("entrained clear juice bubbles on exposed face",
          (sign*.013,-rr*.30,z),(.012,.016,.018),inside,12,8)
   b.parent=ob;b.matrix_parent_inverse=ob.matrix_world.inverted()
  # preserve exactly joined object until the cutting edge reaches it.
  animated(ob,"location",[(1,(0,0,.02)),(57,(0,0,.02)),
             (75,(sign*.035,0,.02)),(95,(sign*.19,0,.02)),
             (120,(sign*.34,0,.015))])
  animated(ob,"rotation_euler",[(1,(0,0,0)),(75,(0,0,0)),
            (120,(0,sign*.13,sign*.095))])
 # Pearly strawberry seeds follow the corresponding half as it separates.
 for k in range(12):
  t=.12+k*.063
  radius=max(.03,math.sin(math.pi*t)**.66)*(.69+.22*t)
  for j in range(18):
   a=2*math.pi*(j+.5*(k%2))/18
   x=math.cos(a)*radius*.999
   y=math.sin(a)*radius*.83*.999
   z=.12+1.23*t
   sp=ball("individual highlighted strawberry seed", (x,y,z),
           (.017,.013,.024),seeds,8,6)
   sp.rotation_euler=(.20*math.sin(a),.22*math.cos(a),a)
   par=halves[1] if x>=0 else halves[0]
   sp.parent=par;sp.matrix_parent_inverse=par.matrix_world.inverted()
 # Five small organic leafy lobes around the crown.
 for k in range(5):
  ang=2*math.pi*k/5
  leaf=ball("real green crown leaf %d"%k,
            (.23*math.cos(ang),.23*math.sin(ang),1.315),
            (.25,.065,.023),green,20,10)
  leaf.rotation_euler=(0,.16,ang)
  par=halves[1] if math.cos(ang)>=0 else halves[0]
  leaf.parent=par;leaf.matrix_parent_inverse=par.matrix_world.inverted()
 stem=ball("green central stalk",(0,0,1.39),(.052,.055,.12),green,20,12)
 # Knife is a genuine 3D honed steel mesh, not a 2D overlay.
 knife=block("stainless precision knife sharp slab",(0,-.01,2.08),(.038,2.20,.38),steel,.012)
 line=block("bevel cutting edge",(0,-.01,1.89),(.019,2.19,.028),blade_dark,.009)
 line.parent=knife;line.matrix_parent_inverse=knife.matrix_world.inverted()
 animated(knife,"location",[(1,(0,-.01,2.08)),(18,(0,-.01,1.92)),
   (42,(0,-.01,1.68)),(62,(0,-.01,1.27)),(84,(0,-.01,.87)),
   (105,(0,-.01,.56)),(120,(0,-.01,.55))])
 set_camera((2.2,-3.7,2.25),(0,0,.69),58)
else:
 # Real non-AI Blender soft body. Anchored gel pulled by a hook modifier before bake.
 lava=mat("volumetric glowing ember-red translucent goo",(.88,.065,.007),
          rough=.085,trans=.30,sss=.19,coat=.52,emission=((1,.16,.014),.36))
 detail(lava,105,.22,.003)
 dark=mat("porous obsidian charcoal shell",(.017,.017,.018),rough=.64,coat=.06)
 detail(dark,18,.90,.075)
 core=mat("exposed brilliant hot molten orange",(.96,.22,.009),
          rough=.14,trans=.20,sss=.15,coat=.45,emission=((1,.20,.013),1.05))
 dish=mat("dark red ceramic basin",(.17,.014,.015),rough=.21,coat=.55)
 block("wide red glasslike basin",(0,0,.01),(2.45,1.95,.17),dish,.13)
 ball("bright submerged molten center",(0,0,.21),(.67,.57,.24),core,64,32)
 # Distinct dark, fractured-looking lava-stone pieces with displacement.
 for k in range(10):
  a=2*math.pi*k/10
  r=.58+random.random()*.23
  x=r*math.cos(a);y=.68*r*math.sin(a)
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=1,
                                         location=(x,y,.29))
  rock=bpy.context.object
  rock.name="porous irregular black obsidian chunk %02d"%k
  rock.scale=(.18+random.random()*.13,.17+random.random()*.13,.16+random.random()*.12)
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  rock.data.materials.append(dark);smooth(rock)
  tex=bpy.data.textures.new("rock surface fracture %02d"%k,type="CLOUDS")
  tex.noise_scale=.12
  disp=rock.modifiers.new("real meshed rough rock","DISPLACE")
  disp.texture=tex;disp.strength=.07;disp.mid_level=.48
 # Main deformable elastic molten goo: upper goal pulled, lower anchored.
 blob=ball("continuous simulated lava slime", (0,0,.51),(.60,.50,.36),lava,80,40)
 bpy.context.view_layer.objects.active=blob
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bpy.ops.object.empty_add(type="SPHERE",location=(0,0,.51+.36))
 grab=bpy.context.object;grab.name="invisible lifting contact control"
 grab.hide_render=True
 top=blob.vertex_groups.new(name="attached wet lifting apex")
 base=blob.vertex_groups.new(name="anchored sticky slime base")
 for v in blob.data.vertices:
  local=v.co.z/.36
  if local>.40:top.add([v.index],min(1,(local-.4)/.4),"REPLACE")
  base.add([v.index], max(.03,(.5-local)*.95) if local<.2 else .03, "REPLACE")
 hook=blob.modifiers.new("actual upper gel contact lift","HOOK")
 hook.object=grab;hook.vertex_group=top.name
 hook.matrix_inverse=grab.matrix_world.inverted() @ blob.matrix_world
 animated(grab,"location",[(1,(0,0,.87)),(30,(0,0,.87)),
   (55,(0,.035,1.10)),(82,(0,.10,1.75)),(102,(0,.10,1.95)),
   (120,(0,.10,1.60))])
 soft=blob.modifiers.new("genuine native Blender soft-body deformation","SOFT_BODY")
 s=blob.soft_body
 s.use_goal=True;s.vertex_group_goal=base.name
 s.goal_default=.48;s.goal_min=.03;s.goal_max=.999
 s.goal_spring=.86;s.goal_friction=6
 s.use_edges=True;s.pull=.85;s.push=.85;s.damping=17;s.bend=5
 soft.point_cache.frame_start=1;soft.point_cache.frame_end=120
 # Baked geometry rather than procedural shape-key-only goo.
 bpy.context.view_layer.objects.active=blob
 blob.select_set(True)
 soft.point_cache.use_disk_cache=True
 sc.frame_set(1)
 blend=OUT/"editable_lava_scene.blend"
 bpy.ops.wm.save_as_mainfile(filepath=str(blend))
 result=bpy.ops.ptcache.bake_all(bake=True)
 if "FINISHED" not in result or not soft.point_cache.is_baked:
  raise RuntimeError("Real soft-body goo physics failed to bake, rendering blocked")
 # Improve macro contrast: hot red light through obsidian crevices.
 light("lava underglow",(0,0,.36),(1,.07,.015),190,(1.4,1.1),target=(0,0,.5))
 set_camera((1.95,-3.30,2.0),(0,0,.68),55)
# Save editable scene and exact frame sequence.
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/("asmr_"+MODE+"_editable.blend")))
s=int(os.environ.get("ASMR_FRAME_START","1"))
e=int(os.environ.get("ASMR_FRAME_END","120"))
frame_dir=OUT/"frames";frame_dir.mkdir(exist_ok=True)
for frame in range(s,e+1):
 sc.frame_set(frame)
 sc.render.filepath=str(frame_dir/("frame_%04d.png"%frame))
 bpy.ops.render.render(write_still=True)
 print("RENDERED_FRAME",MODE,frame,flush=True)
report={"concept":MODE,"frames_rendered":e-s+1,"first":s,"last":e,
        "fps":24,"resolution":[sc.render.resolution_x,sc.render.resolution_y],
        "premium_approved":False,
        "caveat":"Cut: pre-cleaved boolean geometry with authored separation. Lava: Blender native soft-body bake, needs human quality review."}
(OUT/"technical_proof.json").write_text(json.dumps(report,indent=2))
print("TECHNICAL_VISUAL_PROOF_COMPLETE_NO_ARTISTIC_APPROVAL",report,flush=True)
