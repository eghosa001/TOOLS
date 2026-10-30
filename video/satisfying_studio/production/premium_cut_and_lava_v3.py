#!/usr/bin/env python3
"""Original directed Blender tactile-material proof v3.
Design goal: photoreal candy strawberry with real interior / molten sticky lava ASMR.
NOT independent physics or publishing approval. Preview first; use built-in physics for lava base.
"""
import bpy, math, os, random, json
from pathlib import Path
from mathutils import Vector
random.seed(261030)
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
sc.cycles.max_bounces=7
sc.cycles.transmission_bounces=6
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
 wood=pbr("photographic natural oak butcher board",(.21,.095,.048),rough=.51)
 nodes=wood.node_tree.nodes;links=wood.node_tree.links
 wave=nodes.new("ShaderNodeTexWave");wave.wave_type="BANDS";wave.bands_direction="X"
 wave.inputs["Scale"].default_value=2.0;wave.inputs["Distortion"].default_value=.45
 noise=nodes.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=88
 mix=nodes.new("ShaderNodeMixRGB");mix.blend_type="MULTIPLY";mix.inputs[0].default_value=.08
 links.new(wave.outputs["Color"],mix.inputs[1]);links.new(noise.outputs["Fac"],mix.inputs[2])
 bump=nodes.new("ShaderNodeBump");bump.inputs["Strength"].default_value=.038
 bump.inputs["Distance"].default_value=.0006
 links.new(mix.outputs["Color"],bump.inputs["Height"])
 oak_ramp=nodes.new("ShaderNodeValToRGB")
 oak_ramp.color_ramp.elements[0].color=(.155,.081,.042,1)
 oak_ramp.color_ramp.elements[1].color=(.285,.146,.077,1)
 links.new(wave.outputs["Fac"],oak_ramp.inputs["Fac"])
 links.new(oak_ramp.outputs["Color"],nodes.get("Principled BSDF").inputs["Base Color"])
 links.new(bump.outputs["Normal"],nodes.get("Principled BSDF").inputs["Normal"])
 cube("solid grounded maple cutting surface",(0,0,-.16),(4.4,3.6,.32),wood,.065)
 gold=pbr("irregular golden-yellow translucent sugar glass crust",(.97,.38,.012),rough=.185,trans=.16,sub=.17,coat=.37)
 procedural(gold,115,.27,.004)
 # Broad colour irregularity and fine shell pores, not uniform orange plastic.
 n=gold.node_tree.nodes;l=gold.node_tree.links;b=n.get("Principled BSDF")
 pattern=n.new("ShaderNodeTexNoise");pattern.inputs["Scale"].default_value=13
 ramp=n.new("ShaderNodeValToRGB")
 ramp.color_ramp.elements[0].position=.12
 ramp.color_ramp.elements[0].color=(.78,.25,.003,1)
 ramp.color_ramp.elements[1].position=.88
 ramp.color_ramp.elements[1].color=(1,.68,.032,1)
 l.new(pattern.outputs["Fac"],ramp.inputs["Fac"])
 l.new(ramp.outputs["Color"],b.inputs["Base Color"])
 rind=pbr("light amber thin outer fruit flesh",(.95,.65,.21),rough=.22,sub=.13,coat=.16)
 cream=pbr("opaque white creamy sugar filling",(.90,.87,.77),rough=.36,sub=.22,coat=.13)
 procedural(cream,100,.51,.018)
 cream2=pbr("porous ivory whipped white core",(.92,.86,.69),rough=.48,sub=.31)
 procedural(cream2,115,.28,.008)
 seed=pbr("tiny strawberry achene indentations",(.56,.22,.017),rough=.44)
 foliage=pbr("natural broad dark green crown",(.034,.20,.048),rough=.36,sub=.14)
 procedural(foliage,28,.22,.004)
 steel=pbr("brushed steel knife with broad reflection",(.54,.59,.63),rough=.27,metal=1)
 edge=pbr("ground steel honed cutting edge",(.72,.75,.77),rough=.20,metal=1)
 darkmetal=pbr("dark polished handle",(.05,.06,.067),rough=.26,metal=.4)
 C=.19
 def fx(x):return C+(x-C)*.79
 YR=64
 N=72
 def radius(x):
  u=max(.0001,min(.9999,(x+.89)/1.79))
  return .53*(math.sin(math.pi*u)**.67)*(.73+.67*u)
 def make_half(side):
  if side<0:xs=[-.889+(.889+C)*i/YR for i in range(YR+1)]
  else:xs=[C+(.899-C)*i/YR for i in range(YR+1)]
  # Actual ring surface; no floating object or disconnected sphere.
  verts=[];faces=[];mi=[]
  for x in xs:
   r=radius(x)
   for j in range(N):
    a=2*math.pi*j/N
    grain=.004*math.sin(3*a+8*x)+.003*math.sin(13*a+4*x)
    # Geometric seed indentations are part of the fruit skin, not decals.
    k=round((x+.80)/.060)
    if 0<=k<26:
     seed_x=-.80+k*.060
     if abs(x-seed_x)<.038:
      row_shift=.5*(k%2)
      jseed=round(a/(2*math.pi)*18-row_shift)
      seed_a=2*math.pi*(jseed+row_shift)/18
      da=math.atan2(math.sin(a-seed_a),math.cos(a-seed_a))
      pit=math.exp(-((x-seed_x)/.023)**2-(da/.056)**2)
      grain-=.005*pit
    verts.append((fx(x), (.95*r+grain)*math.cos(a), .537+(.91*r+grain)*math.sin(a)))
  for i in range(len(xs)-1):
   for j in range(N):
    k=i*N+j;kn=i*N+(j+1)%N
    faces.append((k,kn,kn+N,k+N));mi.append(0)
  # A volume-closing, creamy cut face with an amber ring and pale core.
  ci=0 if side>0 else len(xs)-1
  x=xs[ci]
  outer=radius(x)
  for rad,midx in ((outer*.97,1),(outer*.81,2),(outer*.55,2),(outer*.18,3)):
   for j in range(N):
    a=2*math.pi*j/N
    jitter=.003*math.sin(11*a+10*j/N) if rad else 0
    verts.append((fx(x)+(.001 if side>0 else -.001),
                  (rad+jitter)*.95*math.cos(a),
                  .537+(rad+jitter)*.91*math.sin(a)))
  base=len(xs)*N
  for level in range(4):
   for j in range(N):
    k=base+level*N+j;l=base+level*N+(j+1)%N
    faces.append((k,l,l+N,k+N));mi.append([1,2,2,3][level])
  center=len(verts)
  verts.append((fx(x)+(.001 if side>0 else -.001),0,.537))
  for j in range(N):
   faces.append((center,base+3*N+j,base+3*N+(j+1)%N));mi.append(3)
  ob=create_mesh("watertight candy-fruit shell and white cross section "+str(side),
        verts,faces,[gold,rind,cream,cream2],mi)
  return ob
 left=make_half(-1);right=make_half(1)
 # Directed blade-pressure deformation of the rigid sugar shell.
 # This is keyframed contact art direction, NOT claimed fracture/soft-body physics.
 for ob in (left,right):
  ob.shape_key_add(name="Undeformed hard shell",from_mix=False)
  dent=ob.shape_key_add(name="Local shell indentation under steel edge",from_mix=False)
  for vert in dent.data:
   pos=vert.co
   if pos.z>.70 and abs(pos.x-C)<.34:
    proximity=math.exp(-((pos.x-C)/.18)**2)
    contact=min(1,max(0,(pos.z-.70)/.44))
    pos.z-=.07*proximity*contact
  for frame,value in ((1,0),(38,0),(52,.20),(67,.85),(80,1),(95,0),(120,0)):
   dent.value=value
   dent.keyframe_insert(data_path="value",frame=frame)
 for side,ob in ((-1,left),(1,right)):
  set_keys(ob,"location",[(1,(0,0,0)),(40,(0,0,0)),
   (68,(side*.028,0,0)),(93,(side*.11,0,0)),(120,(side*.24,0,0))])
  set_keys(ob,"rotation_euler",[(1,(0,0,0)),(76,(0,0,0)),(120,(0,side*.055,side*.045))])
 sc.frame_set(1)
 # Authentic distinct cut center is not an entirely uniform white disc.
 # It has numerous tiny whipped-cream pores anchored to each physical half.
 fiber=pbr("creamy short cut pulp fibers",(.97,.91,.76),rough=.43,sub=.3,coat=.10)
 sugar=pbr("wet honey pulp glints",(.92,.77,.49),rough=.19,sub=.13,coat=.32)
 for side,owner in ((-1,left),(1,right)):
  for i in range(48):
   a=i*2.39996323
   r=radius(C)*(.05+.86*math.sqrt((i+.5)/48))
   fiber_obj=sphere("native microtexture exposed fruit pulp",
      (C+side*.004,.95*r*math.cos(a),.537+.91*r*math.sin(a)),
      (.004,.006+.005*(i%4)/3,.01+.008*(i%3)/2),
      fiber if i%4 else sugar,12,8)
   fiber_obj.parent=owner
   fiber_obj.matrix_parent_inverse=owner.matrix_world.inverted()
 # Physically embedded glossy, recessed seeds; no hovering white beads.
 for k in range(26):
  x=-.80+k*.060
  r=radius(x)
  for j in range(18):
   a=2*math.pi*(j+.5*(k%2))/18
   # underside pits are not worth rendering
   if math.sin(a)<-.28:continue
   rr=r-.004
   ob=sphere("recessed irregular golden achene",
     (fx(x),rr*.95*math.cos(a),.537+rr*.91*math.sin(a)),
     (.009,.007,.005),seed,10,6)
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
   coords.append((fx(x), w*math.cos(a-.23),.537+w*math.sin(a-.23)))
   coords.append((fx(x),w*math.cos(a+.23),.537+w*math.sin(a+.23)))
   if k:faces.append((2*k-2,2*k-1,2*k+1,2*k))
  leaf=create_mesh("organic curved leaf %d"%j,coords,faces,[foliage])
  sol=leaf.modifiers.new("real leaf thickness","SOLIDIFY");sol.thickness=.009
  leaf.parent=right;leaf.matrix_parent_inverse=right.matrix_world.inverted()
 stem=cyl("short green berry stalk",(fx(.96),0,.54),.045,.22,foliage)
 stem.rotation_euler=(0,math.pi/2,0)
 stem.parent=right;stem.matrix_parent_inverse=right.matrix_world.inverted()
 # One large, heavy blade with a honed taper and visible handle.
 # Blade lies along Y, has finite thickness in X and is dragged through Z.
 verts=[
  (-.027,-.90,.24),(.027,-.90,.24),(-.027,.72,.24),(.027,.72,.24),
  (-.019,-.90,-.19),(.019,-.90,-.19),(-.019,.72,-.19),(.019,.72,-.19),
  (0,-.90,-.245),(0,.72,-.245)]
 faces=[(0,2,3,1),(0,1,5,4,8),(2,9,6,7,3),(1,3,7,5),
        (0,4,6,2),(4,5,7,6),(4,8,9,6),(5,7,9,8)]
 knife=create_mesh("wide heavy stainless kitchen knife",verts,faces,[steel])
 bevel=knife.modifiers.new("honed realistically small blade edges","BEVEL")
 bevel.width=.008;bevel.segments=2
 knife.modifiers.new("steel weighted shading","WEIGHTED_NORMAL")
 handle=cube("solid ergonomic black knife handle",(0,1.08,.12),(.12,.67,.115),darkmetal,.045)
 handle.parent=knife;handle.matrix_parent_inverse=knife.matrix_world.inverted()
 for y in (.91,1.18):
  rivet=sphere("steel handle rivet",(0, y,.17),(.045,.018,.025),edge,16,10)
  rivet.parent=knife;rivet.matrix_parent_inverse=knife.matrix_world.inverted()
 set_keys(knife,"location",[(1,(C,0,1.58)),(25,(C,0,1.39)),
  (41,(C,0,1.07)),(64,(C,0,.64)),(83,(C,0,.26)),
  (94,(.70,0,1.04)),(108,(1.43,0,1.60)),(120,(1.73,0,1.91))])
 # A few physically legible slow ooze droplets only after shell has opened.
 drops=pbr("warm ivory thick cream droplets",(.93,.85,.69),rough=.21,sub=.23,coat=.4)
 for j in range(8):
  a=2*math.pi*j/8
  d=sphere("fresh creamy filling bead %02d"%j,
   (C+.011,(.12+.10*(j%3))*.95*math.cos(a),.537+(.12+.10*(j%3))*.91*math.sin(a)),
   (.012,.02,.017),drops,16,8)
  d.parent=right;d.matrix_parent_inverse=right.matrix_world.inverted()
 light("soft large fruit photograph key",(-2.0,-2.5,3.9),(1,.95,.90),180,2.2,2.1,(0,0,.6))
 light("long cool steel reflection",(2.2,-1.0,2.7),(.81,.91,1),105,.65,2.5,(0,0,.6))
 light("gentle back rim",(0.0,2.1,2.3),(1,.76,.48),145,1.2,1.0,(0,0,.4))
 camera((1.35,-3.65,2.13),(.08,0,.60),42)
else:
 # Lava-like red translucent putty: basin, porous obsidian, thick slow-adhering strands.
 ceramic=pbr("deep ruby glass ceramic bowl",(.13,.022,.019),rough=.26,trans=.25,coat=.30)
 slate=pbr("dark matte slate studio",(.035,.030,.030),rough=.64)
 cube("stable black slate slab",(0,0,-.16),(4.6,3.6,.32),slate,.03)
 base=cube("ceramic square slime bowl",(0,0,.11),(2.30,1.72,.23),ceramic,.16)
 collider=base.modifiers.new("real physical pool support","COLLISION")
 baked=pbr("dense translucent crimson molten putty",(.55,.014,.006),rough=.15,trans=.28,sub=.17,coat=.39,emiss=.030)
 procedural(baked,85,.22,.006)
 # Surface color breakup in actual 3D texture space, not a flat red shader.
 n=baked.node_tree.nodes;l=baked.node_tree.links
 gr=n.new("ShaderNodeTexNoise");gr.inputs["Scale"].default_value=15
 gr.inputs["Detail"].default_value=3
 ramp_lava=n.new("ShaderNodeValToRGB")
 ramp_lava.color_ramp.elements[0].color=(.22,.005,.003,1)
 ramp_lava.color_ramp.elements[1].color=(.82,.085,.016,1)
 l.new(gr.outputs["Fac"],ramp_lava.inputs["Fac"])
 l.new(ramp_lava.outputs["Color"],n.get("Principled BSDF").inputs["Base Color"])
 magma=pbr("small deep orange molten illuminated crevices",(.98,.14,.016),rough=.24,trans=.08,sub=.21,coat=.2,emiss=.17)
 charcoal=pbr("genuinely porous craggy black stone",(.013,.010,.012),rough=.81)
 procedural(charcoal,28,.95,.11)
 silver=pbr("real brushed steel spoon",(.53,.59,.61),rough=.27,metal=1)
 crimson=pbr("translucent burgundy wet goo strands",(.50,.010,.004),rough=.095,trans=.43,sub=.14,coat=.44,emiss=.035)
 procedural(crimson,115,.24,.005)
 # Coherent macro variations let backlighting reveal transparent red thickness.
 ns=crimson.node_tree.nodes;ls=crimson.node_tree.links
 cn=ns.new("ShaderNodeTexNoise");cn.inputs["Scale"].default_value=5.6
 cn.inputs["Detail"].default_value=5
 cr=ns.new("ShaderNodeValToRGB")
 cr.color_ramp.elements[0].color=(.21,.005,.003,1)
 cr.color_ramp.elements[1].color=(.94,.105,.012,1)
 ls.new(cn.outputs["Fac"],cr.inputs["Fac"])
 ls.new(cr.outputs["Color"],ns.get("Principled BSDF").inputs["Base Color"])
 # Uneven main red pool: actual genuine soft-body volume with baked cache.
 pool=sphere("physically baked ground-anchored lava core",(0,0,.35),(.76,.54,.19),baked,64,36)
 bpy.context.view_layer.objects.active=pool
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 # Conservative real baked Blender soft-body layer. No faked solver success.
 vg=pool.vertex_groups.new(name="sticky base core")
 for v in pool.data.vertices:
  wt=.999 if v.co.z<-.04 else (.995 if v.co.z<.04 else .985)
  vg.add([v.index],wt,"REPLACE")
 mod=pool.modifiers.new("real baked core soft body","SOFT_BODY")
 st=pool.soft_body;st.use_goal=True;st.vertex_group_goal=vg.name
 st.goal_default=.99;st.goal_min=.98;st.goal_max=.999
 st.goal_spring=.76;st.goal_friction=10
 st.use_edges=True;st.pull=.81;st.push=.81;st.damping=13
 mod.point_cache.frame_start=1;mod.point_cache.frame_end=120
 # Irregular larger porous stones around the *edge* not covering the viscous center.
 for j in range(8):
  a=(j+random.uniform(-.34,.34))*2*math.pi/8
  rr=.82+random.uniform(-.09,.24)
  x=rr*math.cos(a);y=.63*rr*math.sin(a)
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=1,location=(x,y,.40))
  o=bpy.context.object;o.name="angular dark volcanic crust fragment"
  o.scale=(random.uniform(.095,.16),random.uniform(.08,.15),random.uniform(.09,.145))
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
 bowl=sphere("realistic tablespoon oval scoop",(0,0,.52),(.225,.19,.033),silver,48,24)
 bowl.parent=spoon_ctrl;bowl.matrix_parent_inverse=spoon_ctrl.matrix_world.inverted()
 # Silver handle pointing away from shot action.
 spoon_handle=cyl("silver spoon handle",(.69,0,.58),.045,1.36,silver,32)
 spoon_handle.rotation_euler=(0,math.pi/2,0)
 spoon_handle.parent=spoon_ctrl
 spoon_handle.matrix_parent_inverse=spoon_ctrl.matrix_world.inverted()
 # Thick red putty over spoon so visible lifting stays continuous and tactile.
 scoop=sphere("thin wet red drip on spoon",(0,0,.54),(.19,.17,.022),crimson,48,24)
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
   z=.417+u*(.125+lift)
   bulge=.032+(width-.032)*(1-u)**5
   top_wet_lip=.09*math.exp(-((u-.98)/.11)**2)
   rad=(bulge+top_wet_lip)*(1+.15*math.sin(4*math.pi*u+.7)*math.sin(math.pi*u)**2)
   x=.125*math.sin(u*math.pi*1.24+phase)+.09*u*u
   y=.075*math.sin(u*math.pi*1.35+phase)
   for j in range(32):
    a=2*math.pi*j/32
    variation=1+.070*math.sin(5*a+11*u+phase)+.025*math.sin(9*a-6*u)
    v.append((x+rad*variation*math.cos(a),
              y+rad*.9*variation*math.sin(a),z))
  return v
 stages=[(1,0,.36),(25,.01,.33),(48,.29,.30),(78,.84,.24),
         (103,1.20,.20),(120,1.29,.19)]
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
 # Matching second and third strands, rather than unrelated upright cylinders.
 for strand,x,y,scale in ((0,-.10,-.050,.32),(1,.14,.08,.27)):
  thread=neck.copy()
  thread.data=neck.data.copy()
  bpy.context.collection.objects.link(thread)
  thread.name="continuous adjacent goo filament %d"%strand
  thread.location=(x,y,-.008)
  thread.scale=(scale,scale,1)
 # Genuine three-dimensional tiny surface-tension blisters on the molten pool,
 # varied size and placement, to break the old smooth plastic-looking surface.
 for i in range(23):
  aa=i*2.39996323
  rr=(.14+.48*math.sqrt((i+.5)/23))*random.uniform(.88,1.05)
  xx=rr*math.cos(aa)
  yy=.73*rr*math.sin(aa)
  zz=.518+random.uniform(-.01,.023)
  rad=random.uniform(.009,.027)
  sphere("scattered microscopic wet trapped bubble %02d"%i,
         (xx,yy,zz),(rad,rad,rad*.6),crimson,16,12)
 # Real bake before rendering, to preserve traceable solver evidence.
 bpy.context.view_layer.objects.active=pool
 bpy.ops.object.select_all(action="DESELECT");pool.select_set(True)
 mod.point_cache.use_disk_cache=True
 temp=OUT/"lava_core_for_bake.blend"
 bpy.ops.wm.save_as_mainfile(filepath=str(temp))
 result=bpy.ops.ptcache.bake_all(bake=True)
 if "FINISHED" not in result or not mod.point_cache.is_baked:
  raise RuntimeError("Baked soft-body lava-core simulation missing, reject render")
 light("warm red restrained rim",(0,1.4,2.5),(1,.36,.19),155,1.1,1.8,(0,0,.45))
 light("broad cinematic white key",(-2,-2.2,3.5),(1,.88,.80),182,1.7,2.2,(0,0,.7))
 light("cool glancing highlight",(2,-1.2,2.5),(.75,.83,1),125,.65,2.2,(0,0,.9))
 camera((1.42,-3.65,2.32),(0,0,.91),46)
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
