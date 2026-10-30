#!/usr/bin/env python3
"""Original directed Blender tactile-material proof v2.
Design goal: photoreal candy strawberry with real interior / molten sticky lava ASMR.
NOT independent physics or publishing approval. Preview first; use built-in physics for lava base.
"""
import bpy, math, os, random, json
from pathlib import Path
from mathutils import Vector
random.seed(2304)
CONCEPT=os.environ.get("ASMR_CONCEPT","cut").lower()
OUT=Path(os.environ.get("ASMR_OUT","/tmp/asmr_proof")).resolve()
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine="CYCLES"
sc.cycles.samples=int(os.environ.get("ASMR_SAMPLES","18"))
sc.cycles.use_denoising=True
sc.render.resolution_x=int(os.environ.get("ASMR_W","360"))
sc.render.resolution_y=int(os.environ.get("ASMR_H","640"))
sc.render.resolution_percentage=100
sc.render.fps=24
sc.frame_start=1;sc.frame_end=120
sc.render.image_settings.file_format="PNG"
sc.cycles.max_bounces=5
sc.cycles.transmission_bounces=4
sc.world=bpy.data.worlds.new("dark photographic studio bounce")
sc.world.use_nodes=True
sc.world.node_tree.nodes["Background"].inputs["Color"].default_value=(.11,.105,.102,1)
sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value=.28
try:sc.view_settings.view_transform="AgX"
except Exception:pass

def pbr(name,rgba,rough=.3,metal=0,trans=0,sub=0,coat=0,emiss=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgba,1);m.use_nodes=True
 b=m.node_tree.nodes.get("Principled BSDF")
 for key,val in [("Base Color",(*rgba,1)),("Roughness",rough),("Metallic",metal),
                 ("Transmission Weight",trans),("Subsurface Weight",sub),
                 ("Coat Weight",coat)]:
  if key in b.inputs:b.inputs[key].default_value=val
 if emiss:
  b.inputs["Emission Color"].default_value=(*rgba,1)
  b.inputs["Emission Strength"].default_value=emiss
 return m
def procedural(m,scale=25,strength=.13,dist=.006):
 nodes=m.node_tree.nodes;links=m.node_tree.links;b=nodes.get("Principled BSDF")
 n=nodes.new("ShaderNodeTexNoise");n.inputs["Scale"].default_value=scale
 n.inputs["Detail"].default_value=4
 n.inputs["Roughness"].default_value=.66
 bump=nodes.new("ShaderNodeBump");bump.inputs["Strength"].default_value=strength
 bump.inputs["Distance"].default_value=dist
 links.new(n.outputs["Fac"],bump.inputs["Height"])
 links.new(bump.outputs["Normal"],b.inputs["Normal"])
 return n
def sphere(name,loc,scale,material,segments=32,rings=18):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
 o=bpy.context.object;o.name=name;o.scale=scale
 o.data.materials.append(material)
 for face in o.data.polygons:face.use_smooth=True
 return o
def cube(name,loc,dim,material,bevel=.0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
 o=bpy.context.object;o.name=name;o.dimensions=dim
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(material)
 if bevel>0:
  b=o.modifiers.new("soft real edge","BEVEL");b.width=bevel;b.segments=3
  o.modifiers.new("careful normals","WEIGHTED_NORMAL")
 return o
def cyl(name,loc,radius,depth,material,verts=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc)
 o=bpy.context.object;o.name=name;o.data.materials.append(material)
 for f in o.data.polygons:f.use_smooth=True
 return o
def set_keys(o,path,points):
 for frame,val in points:
  setattr(o,path,val)
  o.keyframe_insert(data_path=path,frame=frame)
def light(name,loc,col,power,sx,sy,target):
 bpy.ops.object.light_add(type="AREA",location=loc)
 o=bpy.context.object;o.name=name
 o.data.color=col;o.data.energy=power
 o.data.shape="RECTANGLE";o.data.size=sx;o.data.size_y=sy
 o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
def camera(loc,target,lens=54):
 bpy.ops.object.camera_add(location=loc)
 o=bpy.context.object;o.name="steady macro-camera";sc.camera=o
 o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
 o.data.lens=lens;o.data.dof.use_dof=True
 o.data.dof.focus_distance=(Vector(target)-o.location).length
 o.data.dof.aperture_fstop=11
 return o
def create_mesh(name,coords,faces,mats,matindices=None):
 me=bpy.data.meshes.new(name)
 me.from_pydata(coords,[],faces)
 me.update()
 o=bpy.data.objects.new(name,me)
 bpy.context.collection.objects.link(o)
 for mat in mats:o.data.materials.append(mat)
 for i,f in enumerate(o.data.polygons):
  f.use_smooth=True
  if matindices:f.material_index=matindices[i]
 return o
if CONCEPT=="cut":
 # The original candy stays physically grounded. Its two enclosed halves expose their own distinct soft filling.
 wood=pbr("photographic natural oak butcher board",(.26,.124,.053),rough=.47)
 nodes=wood.node_tree.nodes;links=wood.node_tree.links
 wave=nodes.new("ShaderNodeTexWave");wave.wave_type="BANDS";wave.bands_direction="X"
 wave.inputs["Scale"].default_value=4.2;wave.inputs["Distortion"].default_value=7.2
 noise=nodes.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=88
 mix=nodes.new("ShaderNodeMixRGB");mix.blend_type="MULTIPLY";mix.inputs[0].default_value=.15
 links.new(wave.outputs["Color"],mix.inputs[1]);links.new(noise.outputs["Fac"],mix.inputs[2])
 bump=nodes.new("ShaderNodeBump");bump.inputs["Strength"].default_value=.22
 bump.inputs["Distance"].default_value=.006
 links.new(mix.outputs["Color"],bump.inputs["Height"])
 links.new(bump.outputs["Normal"],nodes.get("Principled BSDF").inputs["Normal"])
 cube("solid grounded maple cutting surface",(0,0,-.16),(4.4,3.6,.32),wood,.065)
 gold=pbr("irregular golden-yellow translucent sugar glass crust",(.985,.36,.002),rough=.245,trans=.07,sub=.07,coat=.32)
 procedural(gold,115,.27,.004)
 rind=pbr("light amber thin outer fruit flesh",(.95,.65,.21),rough=.22,sub=.13,coat=.16)
 cream=pbr("opaque white creamy sugar filling",(.90,.87,.77),rough=.36,sub=.22,coat=.13)
 procedural(cream,68,.21,.009)
 cream2=pbr("porous ivory whipped white core",(.985,.96,.89),rough=.44,sub=.25)
 procedural(cream2,115,.28,.008)
 seed=pbr("tiny amber strawberry micro pits",(.72,.35,.05),rough=.34)
 foliage=pbr("natural broad dark green crown",(.034,.20,.048),rough=.36,sub=.14)
 procedural(foliage,28,.22,.004)
 steel=pbr("brushed steel knife with broad reflection",(.54,.59,.63),rough=.27,metal=1)
 edge=pbr("ground steel honed cutting edge",(.72,.75,.77),rough=.20,metal=1)
 darkmetal=pbr("dark polished handle",(.05,.06,.067),rough=.26,metal=.4)
 C=.19
 YR=64
 N=72
 def radius(x):
  u=max(.0001,min(.9999,(x+.89)/1.79))
  return .58*(math.sin(math.pi*u)**.67)*(.91+.13*u)
 def make_half(side):
  if side<0:xs=[-.889+(.889+C)*i/YR for i in range(YR+1)]
  else:xs=[C+(.899-C)*i/YR for i in range(YR+1)]
  # Actual ring surface; no floating object or disconnected sphere.
  verts=[];faces=[];mi=[]
  for x in xs:
   r=radius(x)
   for j in range(N):
    a=2*math.pi*j/N
    grain=.005*math.sin(3*a+8*x)+.003*math.sin(13*a+4*x)
    verts.append((x, (.95*r+grain)*math.cos(a), .537+(.91*r+grain)*math.sin(a)))
  for i in range(len(xs)-1):
   for j in range(N):
    k=i*N+j;kn=i*N+(j+1)%N
    faces.append((k,kn,kn+N,k+N));mi.append(0)
  # A volume-closing, creamy cut face with an amber ring and pale core.
  ci=0 if side>0 else len(xs)-1
  x=xs[ci]
  outer=radius(x)
  for rad,midx in ((outer*.97,1),(outer*.81,2),(outer*.55,2),(outer*.18,3),(0.0,3)):
   for j in range(N):
    a=2*math.pi*j/N
    jitter=.003*math.sin(11*a+10*j/N) if rad else 0
    verts.append((x+(.001 if side>0 else -.001),
                  (rad+jitter)*.95*math.cos(a),
                  .537+(rad+jitter)*.91*math.sin(a)))
  base=len(xs)*N
  for level in range(4):
   for j in range(N):
    k=base+level*N+j;l=base+level*N+(j+1)%N
    faces.append((k,l,l+N,k+N));mi.append([1,2,2,3][level])
  center=base+4*N
  for j in range(N):
   faces.append((center+j,base+3*N+j,base+3*N+(j+1)%N));mi.append(3)
  ob=create_mesh("watertight candy-fruit shell and white cross section "+str(side),
        verts,faces,[gold,rind,cream,cream2],mi)
  return ob
 left=make_half(-1);right=make_half(1)
 for side,ob in ((-1,left),(1,right)):
  set_keys(ob,"location",[(1,(0,0,0)),(40,(0,0,0)),
   (68,(side*.028,0,0)),(93,(side*.11,0,0)),(120,(side*.24,0,0))])
  set_keys(ob,"rotation_euler",[(1,(0,0,0)),(76,(0,0,0)),(120,(0,side*.055,side*.045))])
 # Physically embedded glossy, recessed seeds; no hovering white beads.
 for k in range(26):
  x=-.80+k*.060
  r=radius(x)
  for j in range(18):
   a=2*math.pi*(j+.5*(k%2))/18
   # underside pits are not worth rendering
   if math.sin(a)<-.28:continue
   rr=r-.011
   ob=sphere("recessed irregular golden achene",
     (x,rr*.95*math.cos(a),.537+rr*.91*math.sin(a)),
     (.011,.007,.007),seed,10,6)
   normal=Vector((.1,math.cos(a),math.sin(a))).normalized()
   ob.rotation_euler=normal.to_track_quat("Z","Y").to_euler()
   parent=left if x<C else right
   ob.parent=parent;ob.matrix_parent_inverse=parent.matrix_world.inverted()
 # Dull organic green sepals are a mesh, not isolated neon plastic spheres.
 for j in range(7):
  a=2*math.pi*j/7
  coords=[];faces=[]
  for k,(u,w) in enumerate([(0,.16),(.20,.20),(.51,.125),(.89,.04),(1,0)]):
   x=.83+u*.34
   coords.append((x, w*math.cos(a-.23),.537+w*math.sin(a-.23)))
   coords.append((x,w*math.cos(a+.23),.537+w*math.sin(a+.23)))
   if k:faces.append((2*k-2,2*k-1,2*k+1,2*k))
  leaf=create_mesh("organic curved leaf %d"%j,coords,faces,[foliage])
  sol=leaf.modifiers.new("real leaf thickness","SOLIDIFY");sol.thickness=.009
  leaf.parent=right;leaf.matrix_parent_inverse=right.matrix_world.inverted()
 stem=cyl("short green berry stalk",(.96,0,.54),.045,.22,foliage)
 stem.rotation_euler=(0,math.pi/2,0)
 stem.parent=right;stem.matrix_parent_inverse=right.matrix_world.inverted()
 # One large, heavy blade with a honed taper and visible handle.
 # Blade lies along Y, has finite thickness in X and is dragged through Z.
 verts=[
  (-.041,-1.15,.38),(.041,-1.15,.38),(-.041,1.10,.38),(.041,1.10,.38),
  (-.033,-1.15,-.35),(.033,-1.15,-.35),(-.033,1.10,-.35),(.033,1.10,-.35),
  (0,-1.15,-.40),(0,1.10,-.40)]
 faces=[(0,2,3,1),(0,1,5,4,8),(2,9,6,7,3),(1,3,7,5),
        (0,4,6,2),(4,5,7,6),(4,8,9,6),(5,7,9,8)]
 knife=create_mesh("wide heavy stainless kitchen knife",verts,faces,[steel])
 bevel=knife.modifiers.new("honed realistically small blade edges","BEVEL")
 bevel.width=.008;bevel.segments=2
 knife.modifiers.new("steel weighted shading","WEIGHTED_NORMAL")
 handle=cube("solid ergonomic black knife handle",(0,1.39,.21),(.18,.80,.19),darkmetal,.06)
 handle.parent=knife;handle.matrix_parent_inverse=knife.matrix_world.inverted()
 for y in (1.20,1.47):
  rivet=sphere("steel handle rivet",(0, y,.31),(.09,.018,.035),edge,16,10)
  rivet.parent=knife;rivet.matrix_parent_inverse=knife.matrix_world.inverted()
 set_keys(knife,"location",[(1,(C,0,1.94)),(24,(C,0,1.53)),
  (42,(C,0,1.23)),(70,(C,0,.76)),(84,(C,0,.54)),
  (95,(.55,0,1.14)),(107,(1.22,0,1.80)),(120,(1.60,0,2.0))])
 # A few physically legible slow ooze droplets only after shell has opened.
 drops=pbr("warm ivory thick cream droplets",(.93,.85,.69),rough=.21,sub=.23,coat=.4)
 for j in range(8):
  a=2*math.pi*j/8
  d=sphere("fresh creamy filling bead %02d"%j,
   (C+.011,(.12+.10*(j%3))*.95*math.cos(a),.537+(.12+.10*(j%3))*.91*math.sin(a)),
   (.012,.02,.017),drops,16,8)
  d.parent=right;d.matrix_parent_inverse=right.matrix_world.inverted()
 light("soft large fruit photograph key",(-2.0,-2.5,3.9),(1,.93,.86),160,2.2,2.1,(0,0,.6))
 light("long cool steel reflection",(2.2,-1.0,2.7),(.81,.91,1),85,.65,2.5,(0,0,.6))
 light("gentle back rim",(0.0,2.1,2.3),(1,.76,.48),145,1.2,1.0,(0,0,.4))
 camera((1.45,-3.55,1.95),(0,0,.62),49)
else:
 # Lava-like red translucent putty: basin, porous obsidian, thick slow-adhering strands.
 ceramic=pbr("deep ruby glass ceramic bowl",(.13,.022,.019),rough=.26,trans=.25,coat=.30)
 slate=pbr("dark matte slate studio",(.035,.030,.030),rough=.64)
 cube("stable black slate slab",(0,0,-.16),(4.6,3.6,.32),slate,.03)
 base=cube("ceramic square slime bowl",(0,0,.11),(2.30,1.72,.23),ceramic,.16)
 baked=pbr("dense dark crimson viscous slime",(.47,.006,.005),rough=.30,trans=.08,sub=.19,coat=.28,emiss=.035)
 procedural(baked,85,.22,.006)
 magma=pbr("small deep orange molten illuminated crevices",(.98,.14,.016),rough=.24,trans=.08,sub=.21,coat=.2,emiss=.17)
 charcoal=pbr("genuinely porous craggy black stone",(.013,.010,.012),rough=.81)
 procedural(charcoal,28,.95,.11)
 silver=pbr("real brushed steel spoon",(.53,.59,.61),rough=.27,metal=1)
 crimson=pbr("translucent burgundy wet goo strands",(.48,.005,.004),rough=.29,trans=.12,sub=.20,coat=.25,emiss=.035)
 procedural(crimson,115,.25,.004)
 # Uneven main red pool: actual genuine soft-body volume with baked cache.
 pool=sphere("physically baked ground-anchored lava core",(0,0,.35),(.76,.54,.19),baked,64,36)
 bpy.context.view_layer.objects.active=pool
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 # Conservative real baked Blender soft-body layer. No faked solver success.
 vg=pool.vertex_groups.new(name="sticky base core")
 for v in pool.data.vertices:
  wt=.985 if v.co.z<-.04 else (.42 if v.co.z<.04 else .075)
  vg.add([v.index],wt,"REPLACE")
 mod=pool.modifiers.new("real baked core soft body","SOFT_BODY")
 st=pool.soft_body;st.use_goal=True;st.vertex_group_goal=vg.name
 st.goal_default=.55;st.goal_min=.05;st.goal_max=.999
 st.goal_spring=.76;st.goal_friction=10
 st.use_edges=True;st.pull=.81;st.push=.81;st.damping=13
 mod.point_cache.frame_start=1;mod.point_cache.frame_end=120
 # Irregular larger porous stones around the *edge* not covering the viscous center.
 for j in range(10):
  a=(j+random.uniform(-.26,.26))*2*math.pi/10
  rr=.79+random.uniform(-.06,.25)
  x=rr*math.cos(a);y=.63*rr*math.sin(a)
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=1,location=(x,y,.40))
  o=bpy.context.object;o.name="angular dark volcanic crust fragment"
  o.scale=(random.uniform(.11,.19),random.uniform(.10,.18),random.uniform(.09,.16))
  o.rotation_euler=(random.random(),random.random(),random.random())
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  o.data.materials.append(charcoal)
  tex=bpy.data.textures.new("individual stone grain %02d"%j,type="CLOUDS")
  tex.noise_scale=.13
  disp=o.modifiers.new("real pumice surface relief","DISPLACE")
  disp.texture=tex;disp.strength=.09
 # A recognizable spoon truly contacts and then lifts goo, not a disconnected black ball.
 # Spoon bowl is slightly cupped hemispherical mesh following lifting controller.
 spoon_ctrl=bpy.data.objects.new("spoon and lifted sauce driver",None)
 bpy.context.collection.objects.link(spoon_ctrl)
 spoon_ctrl.location=(0,0,.52)
 # bowl is a slightly flattened shallow solid spoon.
 bowl=sphere("realistic tablespoon oval scoop",(0,0,.52),(.34,.27,.052),silver,48,24)
 bowl.parent=spoon_ctrl;bowl.matrix_parent_inverse=spoon_ctrl.matrix_world.inverted()
 # Silver handle pointing away from shot action.
 spoon_handle=cyl("silver spoon handle",(0,.77,.59),.049,1.38,silver,32)
 spoon_handle.rotation_euler=(math.pi/2,0,0)
 spoon_handle.parent=spoon_ctrl
 spoon_handle.matrix_parent_inverse=spoon_ctrl.matrix_world.inverted()
 # Thick red putty over spoon so visible lifting stays continuous and tactile.
 scoop=sphere("sticky red putty adhering to spoon",(0,0,.585),(.28,.245,.058),crimson,48,24)
 scoop.parent=spoon_ctrl;scoop.matrix_parent_inverse=spoon_ctrl.matrix_world.inverted()
 set_keys(spoon_ctrl,"location",[(1,(0,0,.00)),(20,(0,0,.00)),
  (45,(0,.02,.20)),(74,(0,.04,.78)),(100,(0,.05,1.19)),(120,(0,.08,1.35))])
 # Primary sticky neck: continuous parametric surface with baked core as foundation.
 # Authored secondary surface, never misrepresented as simulated fluid topology.
 # Morph targets are a bounded representation of viscous elongation.
 def tendon_coords(lift,width,phase=0):
  v=[]
  for k in range(26):
   u=k/25
   z=.435+u*(.095+lift)
   bulge=.073+(width-.07)*(1-u)**3
   top_wet_lip=.13*math.exp(-((u-.96)/.23)**2)
   rad=bulge+top_wet_lip
   x=.025*math.sin(u*math.pi*1.5+phase)+.05*u*u
   y=.045*math.sin(u*math.pi*1.25+phase)
   for j in range(32):
    a=2*math.pi*j/32
    variation=1+.070*math.sin(5*a+11*u+phase)+.025*math.sin(9*a-6*u)
    v.append((x+rad*variation*math.cos(a),
              y+rad*.9*variation*math.sin(a),z))
  return v
 stages=[(1,0,.36),(25,.01,.33),(48,.29,.30),(78,.84,.26),
         (103,1.20,.23),(120,1.29,.22)]
 base_coords=tendon_coords(stages[0][1],stages[0][2])
 faces=[]
 for i in range(25):
  for j in range(32):
   a=i*32+j;b=i*32+(j+1)%32
   faces.append((a,b,b+32,a+32))
 faces.append(tuple(reversed(tuple(range(32)))))
 faces.append(tuple(25*32+j for j in range(32)))
 neck=create_mesh("continuous 3D sticky stretched lava neck",base_coords,faces,[crimson])
 keys=neck.shape_key_add(name="Basis",from_mix=False)
 for frame,lift,width in stages:
  key=neck.shape_key_add(name="viscous pull %d"%frame,from_mix=False)
  for i,co in enumerate(tendon_coords(lift,width)):key.data[i].co=co
  key.value=0
  key.keyframe_insert(data_path="value",frame=1)
 # Time each actual morph to the exact storyboard and interpolate between successive poses.
 for j,(frame,_,_) in enumerate(stages):
  for jj,(_,_,_) in enumerate(stages):
   block=neck.data.shape_keys.key_blocks[jj+1]
   block.value=1 if jj==j else 0
   block.keyframe_insert(data_path="value",frame=frame)
 # Background saucy strands, subordinate to main neck and preserved attached on both ends.
 for strand in range(3):
  angle=2*math.pi*strand/3+.3
  parent=cyl("fine secondary attached molten filament %d"%strand,
      (.18*math.cos(angle),.12*math.sin(angle),.49),.025,.24,crimson,18)
  # mesh strand is purposely kept subtle; no fake hair or severe geometry flicker.
  set_keys(parent,"scale",[(1,(1,1,.7)),(42,(1,1,1.4)),
                            (74,(.75,.75,2.5)),(120,(.68,.68,4.4))])
 # Real bake before rendering, to preserve traceable solver evidence.
 bpy.context.view_layer.objects.active=pool
 bpy.ops.object.select_all(action="DESELECT");pool.select_set(True)
 mod.point_cache.use_disk_cache=True
 temp=OUT/"lava_core_for_bake.blend"
 bpy.ops.wm.save_as_mainfile(filepath=str(temp))
 result=bpy.ops.ptcache.bake_all(bake=True)
 if "FINISHED" not in result or not mod.point_cache.is_baked:
  raise RuntimeError("Baked soft-body lava-core simulation missing, reject render")
 light("warm red restrained rim",(0,1.4,2.5),(1,.36,.19),110,1.1,1.8,(0,0,.45))
 light("broad cinematic white key",(-2,-2.2,3.5),(1,.88,.80),155,1.7,2.2,(0,0,.7))
 light("cool glancing highlight",(2,-1.2,2.5),(.75,.83,1),125,.65,2.2,(0,0,.9))
 camera((1.45,-3.5,2.3),(0,0,.88),48)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/("premium_"+CONCEPT+"_editable.blend")))
if os.environ.get("ASMR_PREVIEW","1")=="1":
 frames=[1,55,100]
else:
 st=int(os.environ.get("ASMR_FRAME_START","1"));en=int(os.environ.get("ASMR_FRAME_END","120"))
 frames=list(range(st,en+1))
for frame in frames:
 sc.frame_set(frame)
 sc.render.filepath=str(OUT/("frame_%04d.png"%frame))
 bpy.ops.render.render(write_still=True)
 print("ASMR_V2_ACTUAL_RENDERED_FRAME",CONCEPT,frame,flush=True)
(OUT/"result.json").write_text(json.dumps({
 "concept":CONCEPT,"frames":frames,"resolution":[sc.render.resolution_x,sc.render.resolution_y],
 "source":"original editable blender scene, no AI video","human_quality_approved":False,
 "notes":"fruit cut uses directed rigid mesh separation, lava uses real baked softbody core plus directed secondary sticky neck; not approved as complete viscous simulation"}))
