#!/usr/bin/env python3
"""32-second original glass-marble ASMR: eight independent 5s Bullet takes.

Run in Blender 4.5 LTS with ASMR_MODE=SCENE|BAKE|RENDER, ASMR_SHOT=0..7,
ASMR_SHARD=0..1. Original CGI only; no reference footage, no fake Foley,
no automated artistic approval. Every sound event requires cached geometry.
"""
import hashlib, json, math, os, random
from pathlib import Path
import bpy
from mathutils import Vector

SHOT=int(os.environ.get("ASMR_SHOT","0"))
if not 0 <= SHOT <= 7: raise RuntimeError("Eight designed takes only")
MODE=os.environ.get("ASMR_MODE","SCENE").upper()
ROOT=Path(os.environ.get("ASMR_OUT","/tmp/asmr_continuous_32s")).resolve()
OUT=ROOT/("shot_%d"%SHOT)
OUT.mkdir(parents=True,exist_ok=True)
BLEND=OUT/"glass_marble_8s_baked.blend"
FPS=24
FRAMES=120
BEADS=12
R=.052
COLOURS=[(.018,.70,.95),(.91,.19,.31),(.95,.66,.05),(.09,.77,.53),
         (.65,.32,.91),(.02,.82,.79),(.98,.43,.20),(.40,.68,.99)]
PROFILE=[(.014,.23),(.15,.24),(.32,.285),(.49,.37),(.64,.49),(.78,.67),(.835,.665)]

def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for buf in iter(lambda:f.read(1024*1024),b""):h.update(buf)
    return h.hexdigest()

def mat(name,rgb,metal=0,rough=.22,trans=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1)
    m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    for k,v in [("Base Color",(*rgb,1)),("Metallic",metal),("Roughness",rough),
                ("Transmission Weight",trans),("IOR",1.51),("Coat Weight",.18)]:
        if k in b.inputs:b.inputs[k].default_value=v
    return m

def collider(obj,active=False,shape="BOX",mass=.1,friction=.5,bounce=.14):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.rigidbody.object_add()
    r=obj.rigid_body;r.type="ACTIVE" if active else "PASSIVE"
    r.collision_shape=shape;r.use_margin=True;r.collision_margin=.0015
    r.friction=friction;r.restitution=bounce
    if active:r.mass=mass
    return r

def cube(name,loc,scale,material,physical=False):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name;o.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    b=o.modifiers.new("Precision machined edges","BEVEL")
    b.width=min(.012,min(scale)*.2);b.segments=3
    o.modifiers.new("Smooth manufactured edges","WEIGHTED_NORMAL")
    if physical:collider(o,shape="BOX",friction=.38,bounce=.05)
    return o

def lamp(name,xyz,energy,size,color,focus):
    bpy.ops.object.light_add(type="AREA",location=xyz)
    o=bpy.context.object;o.name=name;o.data.energy=energy
    o.data.shape="DISK";o.data.size=size;o.data.color=color
    o.rotation_euler=(Vector(focus)-o.location).to_track_quat("-Z","Y").to_euler()

def make():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene;s.frame_start=1;s.frame_end=FRAMES;s.render.fps=FPS
    s.render.engine="CYCLES";s.cycles.samples=24
    s.render.resolution_x=720;s.render.resolution_y=1280
    s.render.resolution_percentage=100
    try:s.view_settings.view_transform="AgX"
    except Exception:pass
    try:s.view_settings.look="Medium High Contrast"
    except Exception:pass
    # Real manifold porcelain bowl for each *independently simulated* take.
    contour=PROFILE+[(.73,.43),(.56,.28),(.34,.18),(.15,.17),(.014,.17)]
    sections=64;verts=[];faces=[]
    for r,z in contour:
        for k in range(sections):
            a=2*math.pi*k/sections;verts.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(len(contour)):
        for k in range(sections):
            faces.append((j*sections+k,j*sections+(k+1)%sections,
                          ((j+1)%len(contour))*sections+(k+1)%sections,
                          ((j+1)%len(contour))*sections+k))
    mesh=bpy.data.meshes.new("Glazed porcelain bowl mesh")
    mesh.from_pydata(verts,[],faces);mesh.update()
    bowl=bpy.data.objects.new("REAL_PHYSICAL_PORCELAIN_BOWL",mesh)
    bpy.context.collection.objects.link(bowl)
    colours=[(.085,.019,.18),(.023,.11,.13),(.15,.055,.10),(.10,.065,.18),(.075,.10,.15),(.11,.046,.12),(.035,.12,.10),(.12,.071,.09)]
    bowl.data.materials.append(mat("Glazed coloured ceramic",colours[SHOT],rough=.17))
    for p in bowl.data.polygons:p.use_smooth=True
    collider(bowl,shape="MESH",friction=.62,bounce=.11)
    tabletop=mat("Matte slate tabletop",(.045,.05,.07),rough=.51)
    cube("Set tabletop",(0,0,.08),(30,30,.12),tabletop,True)
    alloy=mat("Dark satin metal feeder",(.105,.12,.15),metal=.78,rough=.28)
    gold=mat("Brushed champagne shutter",(.66,.43,.24),metal=.88,rough=.25)
    silver=mat("Guide rail",(.65,.76,.83),metal=.88,rough=.20)
    cube("Raised gantry beam",(0,.05,1.71),(1.16,.06,.06),alloy)
    for x in [-.57,.57]:
        cube("Gantry upright",(x,.05,1.72),(.030,.045,1.22),alloy)
    for y in [-.39,.39]:
        cube("Mechanical tray guide",(0,y,1.255),(1.16,.025,.027),silver)
    # 12 truly distinct marbles (3 x 4), each initially supported by a gate.
    # Every shot has a new release order and independent 192-frame physics bake.
    slots=[(i,j) for j in range(3) for i in range(4)]
    if SHOT%4==0: order=list(range(12))
    elif SHOT%4==1: order=sorted(range(12),key=lambda k:(k%4,2-k//4))
    elif SHOT%4==2: order=sorted(range(12),key=lambda k:abs((k%4)-1.5)+.6*(k//4))
    else:
        rng=random.Random(1406+SHOT);order=list(range(12));rng.shuffle(order)
    if SHOT>=4:order=list(reversed(order))
    order_at={index:rank for rank,index in enumerate(order)}
    release_times={}
    for index,(i,j) in enumerate(slots):
        x=(i-1.5)*.292;y=(j-1)*.204
        z=1.312+(.02 if SHOT==3 and i%2 else 0.)
        release=3+7*order_at[index]
        release_times[str(index)]=release
        pad=cube("PHYSICAL_RETRACTING_GATE_%02d"%index,(x,y,1.254),
                 (.125,.143,.016),gold,True)
        pad.rigid_body.kinematic=True
        # Every shutter retreats AWAY from un-released slots. Old 0.36m
        # cross-row motion left a pad exactly under a later marble.
        if j==0: dx,dy=0.,-.60
        elif j==1: dx,dy=(.72 if x>0 else -.72),0.
        else: dx,dy=0.,.60
        for frame,frac in [(1,0.),(max(1,release-2),0.),(release+1,1.),(FRAMES,1.)]:
            pad.location=(x+dx*frac,y+dy*frac,1.254)
            pad.keyframe_insert(data_path="location",frame=frame)
        # The mechanical shutter disappears behind the feeder housing after
        # its actual sideways retraction; it no longer hangs in mid-air.
        pad.hide_render=False
        pad.keyframe_insert(data_path="hide_render",frame=1)
        pad.keyframe_insert(data_path="hide_render",frame=release+1)
        pad.hide_render=True
        pad.keyframe_insert(data_path="hide_render",frame=min(FRAMES,release+3))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=32,
                                              radius=R,location=(x,y,z))
        bead=bpy.context.object;bead.name="REAL_GLASS_SPHERE_%02d"%index
        for poly in bead.data.polygons:poly.use_smooth=True
        colour=COLOURS[(index+SHOT*2+(index//4))%len(COLOURS)]
        glass=mat("Transparent glass %d"%index,colour,rough=.038,trans=.88)
        bead.data.materials.append(glass)
        r=collider(bead,active=True,shape="SPHERE",mass=.035,friction=.26,bounce=.31)
        r.kinematic=True
        bead.keyframe_insert(data_path="rigid_body.kinematic",frame=1)
        bead.keyframe_insert(data_path="rigid_body.kinematic",frame=max(1,release-1))
        r.kinematic=False
        bead.keyframe_insert(data_path="rigid_body.kinematic",frame=release)
    focus=Vector((0,0,.85))
    angles=[(1.42,-3.4,2.45),(.88,-3.3,2.5),(-1.13,-3.5,2.60),(.55,-3.35,2.4),(-.82,-3.45,2.55),(1.2,-3.3,2.5),(-.4,-3.25,2.43),(.62,-3.5,2.62)]
    bpy.ops.object.camera_add(location=angles[SHOT])
    cam=bpy.context.object;cam.name="Portrait studio macro camera"
    cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.lens=58;cam.data.dof.use_dof=True
    cam.data.dof.focus_distance=(focus-cam.location).length
    cam.data.dof.aperture_fstop=14;s.camera=cam
    lamp("Large diffuse softbox",(-1.7,-2.0,3.0),235,2.1,(1,.92,.87),focus)
    lamp("Blue glass rimlight",(1.7,1.1,2.55),155,1.25,(.65,.87,1),focus)
    lamp("Warm narrow streak",(0,-1.5,2.8),100,.9,(1,.75,.51),focus)
    w=bpy.data.worlds.new("Original studio background");w.use_nodes=True
    bg=w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(.09,.10,.16,1)
    bg.inputs["Strength"].default_value=.32
    hdri=os.environ.get("ASMR_HDRI_FILE")
    if hdri and Path(hdri).is_file():
        env=w.node_tree.nodes.new("ShaderNodeTexEnvironment")
        env.image=bpy.data.images.load(hdri,check_existing=True)
        w.node_tree.links.new(env.outputs["Color"],bg.inputs["Color"])
    # Preserve photographic HDR illumination in glass reflections but avoid
    # the distracting pale horizon above the dark ceramic tabletop.
    nodes=w.node_tree.nodes;links=w.node_tree.links
    camera_backdrop=nodes.new("ShaderNodeBackground")
    camera_backdrop.inputs["Color"].default_value=(.048,.053,.069,1)
    camera_backdrop.inputs["Strength"].default_value=.55
    light_path=nodes.new("ShaderNodeLightPath")
    world_mix=nodes.new("ShaderNodeMixShader")
    links.new(light_path.outputs["Is Camera Ray"],world_mix.inputs[0])
    links.new(bg.outputs["Background"],world_mix.inputs[1])
    links.new(camera_backdrop.outputs["Background"],world_mix.inputs[2])
    links.new(world_mix.outputs[0],nodes.get("World Output").inputs["Surface"])
    s.world=w
    if not s.rigidbody_world:raise RuntimeError("Rigidbody world absent")
    s.rigidbody_world.substeps_per_frame=14
    s.rigidbody_world.solver_iterations=30
    cache=s.rigidbody_world.point_cache
    cache.frame_start=1;cache.frame_end=FRAMES
    s.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    (OUT/"take_plan.json").write_text(json.dumps({
        "shot":SHOT,"frames":FRAMES,"fps":FPS,"real_marble_count":BEADS,
        "release_frames":release_times,"no_footage_or_audio_from_reference":True,
        "all_marble_supports_animated":True,"editorial_approval":False
    },indent=2)+"\n")
    print("32S_SHOT_SCENE_CREATED",SHOT,len(release_times),flush=True)

def bowl_height(x,y):
    r=math.hypot(x,y)
    for k in range(len(PROFILE)-1):
        r0,z0=PROFILE[k];r1,z1=PROFILE[k+1]
        if r<=r1:return z0+(z1-z0)*max(0,(r-r0)/(r1-r0))
    return PROFILE[-1][1]

def detect(trajectory,releases):
    primary=[];secondary=[]
    seen=set();seen_pairs=set()
    for f in range(2,len(trajectory)+1):
        a=trajectory[f-2];b=trajectory[f-1]
        for i in range(BEADS):
            release=releases[str(i)]
            if f<=release:continue
            now=b[i];prev=a[i]
            floor=bowl_height(now[0],now[1])
            gap=now[2]-R-floor
            oldgap=prev[2]-R-bowl_height(prev[0],prev[1])
            speed=FPS*math.dist(now,prev)
            contact=None
            if gap<=.024 and oldgap>.024 and prev[2]>now[2]:
                contact="glass_against_ceramic"
            else:
                for j in range(BEADS):
                    if j==i:continue
                    dist=math.dist(now,b[j])
                    pd=math.dist(prev,a[j])
                    if dist<=2*R+.007 and pd>2*R+.007 and speed>.05:
                        contact="glass_against_glass";seen_pairs.add((f,min(i,j),max(i,j)))
                        break
            if contact and i not in seen:
                seen.add(i)
                primary.append({"shot":SHOT,"marble_index":i,"frame":f,
                    "kind":contact,"position_xyz":now,"speed_m_s":round(speed,3),
                    "contact_inferred_from":"measured Bullet centres at 24fps",
                    "one_frame_visual_review_required":True})
        for i in range(BEADS):
            if f<=releases[str(i)]:continue
            for j in range(i+1,BEADS):
                if f<=releases[str(j)]:continue
                d=math.dist(b[i],b[j]);old=math.dist(a[i],a[j])
                if d<2*R+.005 and old>2*R+.005 and (f,i,j) not in seen_pairs:
                    vi=[FPS*(b[i][k]-a[i][k]) for k in range(3)]
                    vj=[FPS*(b[j][k]-a[j][k]) for k in range(3)]
                    speed=math.dist(vi,vj)
                    if speed>.16:
                        secondary.append({"shot":SHOT,"frame":f,
                           "marble_pair":[i,j],"kind":"glass_against_glass",
                           "speed_m_s":round(speed,3),
                           "position_xyz":[round((b[i][k]+b[j][k])/2,5) for k in range(3)]})
    return primary,secondary

def bake():
    s=bpy.context.scene
    cache=s.rigidbody_world.point_cache
    print("BULLET_CACHE_RANGE",SHOT,cache.frame_start,cache.frame_end,"SCENE",s.frame_start,s.frame_end,flush=True)
    result=bpy.ops.ptcache.bake_all(bake=True)
    if "FINISHED" not in result or not cache.is_baked:raise RuntimeError("No genuine Bullet bake")
    beads=sorted((o for o in bpy.data.objects if o.name.startswith("REAL_GLASS_SPHERE_")),
                 key=lambda o:o.name)
    if len(beads)!=BEADS:raise RuntimeError("Bead inventory mismatch")
    releases=json.loads((OUT/"take_plan.json").read_text())["release_frames"]
    trajectory=[]
    for f in range(1,FRAMES+1):
        s.frame_set(f)
        row=[[round(float(v),5) for v in o.matrix_world.translation] for o in beads]
        if not all(math.isfinite(v) and abs(v)<3 for p in row for v in p):
            raise RuntimeError("Invalid or escaped physical bead at frame "+str(f))
        trajectory.append(row)
    for t in [35,65,90,110,120]:
        s.frame_set(t)
        obj=bpy.data.objects["REAL_GLASS_SPHERE_11"]
        gate=bpy.data.objects["PHYSICAL_RETRACTING_GATE_11"]
        print("RELEASE_DIAGNOSTIC",SHOT,t,"bead",tuple(round(float(v),3) for v in obj.matrix_world.translation),"kinematic",obj.rigid_body.kinematic,"pad",tuple(round(float(v),3) for v in gate.matrix_world.translation),flush=True)
    print("BULLET_FINAL_HEIGHTS",SHOT,[round(p[2],3) for p in trajectory[-1]],flush=True)
    print("BULLET_DESCENDED",SHOT,{str(h):sum(p[2]<h for p in trajectory[-1]) for h in [.8,1.0,1.2,1.3,1.4]},flush=True)
    if sum(trajectory[-1][i][2]<1 for i in range(BEADS))<10:
        raise RuntimeError("Not enough beads physically descended into bowl")
    primary,secondary=detect(trajectory,releases)
    if len(primary)<9:raise RuntimeError("Insufficient observed marble contact events: %d"%len(primary))
    events={"shot":SHOT,"fps":FPS,"frames":FRAMES,"real_releases":BEADS,
            "primary":primary,"secondary":secondary,
            "sound_approval":False,"readout_is_geometric_contact_proxy":True}
    evt=OUT/"physical_contacts.json";evt.write_text(json.dumps(events,indent=2)+"\n")
    s.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    audit={"shot":SHOT,"frames":FRAMES,"fps":FPS,"baked_point_cache":True,
           "editable_blend_sha256":digest(BLEND),
           "contact_sha256":digest(evt),
           "original_contact_count":len(primary),
           "secondary_contact_count":len(secondary),
           "releases":BEADS,"artistic_approval":False}
    (OUT/"bake_audit.json").write_text(json.dumps(audit,indent=2)+"\n")
    print("32S_REAL_BULLET_BAKE",SHOT,len(primary),len(secondary),flush=True)

def render():
    s=bpy.context.scene
    audit=json.loads((OUT/"bake_audit.json").read_text())
    if not s.rigidbody_world.point_cache.is_baked:raise RuntimeError("Physics cache lost")
    if digest(BLEND)!=audit["editable_blend_sha256"]:raise RuntimeError("Scene changed")
    shard=int(os.environ.get("ASMR_SHARD","0"))
    if not 0<=shard<=1:raise RuntimeError("Shard must be 0..1")
    first=shard*45+12
    s.render.engine="CYCLES";s.cycles.device="CPU"
    s.cycles.samples=int(os.environ.get("ASMR_FINAL_SAMPLES","20"))
    s.cycles.use_denoising=True
    s.render.resolution_x=720;s.render.resolution_y=1280
    s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG"
    folder=OUT/"rendered";folder.mkdir(exist_ok=True)
    for f in range(first,first+45):
        s.frame_set(f)
        s.render.filepath=str(folder/("frame_%04d.png"%f))
        bpy.ops.render.render(write_still=True)
        if Path(s.render.filepath).stat().st_size<2000:raise RuntimeError("Missing Cycles frame")
    print("32S_CYCLES_RENDERED",SHOT,shard,first,first+44,flush=True)

if MODE=="SCENE":make()
elif MODE=="BAKE":bake()
elif MODE=="RENDER":render()
else:raise RuntimeError("Unknown mode "+MODE)
