extends Node3D
## Film-direction prototype: the sets are new authored 3D constructions built from
## procedural architectural parts with licensed CC0 photograph textures.
## Original third-party boats are props only; neither historical environment
## is an untouched prefab. Nothing here claims archaeological precision.

const DURATION := 36.0
var mode := "london"
var camera: Camera3D
var caption: Label
var time_now := 0.0
var shots: Array = []
var people: Array = []
var fire_nodes: Array = []
var fragments: Array = []
var boats: Array = []
var siege_dust: Array = []
var cannonball: Node3D
var mats: Dictionary = {}
var total_nodes := 0
var rng := RandomNumberGenerator.new()

func _ready() -> void:
    rng.seed = 1666
    mode = OS.get_environment("HISTORY_SCENE")
    if mode != "london" and mode != "constantinople":
        push_error("HISTORY_SCENE must be london or constantinople")
        get_tree().quit(2)
        return
    _materials()
    _world()
    _overlays()
    if mode == "london":
        _london()
        _shots_london()
    else:
        _constantinople()
        _shots_constantinople()
    _animate(0.0)
    _direct(0.0)
    print("REBUILT_HISTORICAL_3D_SCENE",mode,"nodes",total_nodes,"shots",shots.size())

func _materials() -> void:
    _mat("plaster","grey_plaster",Color("#d8c4a1"),1.5)
    _mat("oak","rough_wood",Color("#4b3025"),1.4)
    _mat("roof","clay_roof_tiles_02",Color("#b05f4c"),2.0)
    _mat("dark_roof","roof_slates_03",Color("#514c4a"),2.0)
    _mat("street","cobblestone_01",Color("#b3aba0"),12.0)
    _mat("stone","stone_brick_wall_001",Color("#b4a68f"),2.4)
    _mat("sandstone","sandstone_blocks_05",Color("#cec09d"),3.1)
    _mat("brick","medieval_red_brick",Color("#a75642"),2.4)
    _mat("grass","mossy_cobblestone",Color("#969a7e"),20.0)
    _mat("soil","dirt_floor",Color("#7e6a52"),20.0)
    _mat("boards","planks_brown_10",Color("#7a5942"),1.5)
    _mat("castle","castle_brick_07",Color("#c2b5a4"),2.2)
    _plain("glass",Color("#54483b"),0.18,0.10)
    _plain("black",Color("#171c20"),0.7)
    _plain("bronze",Color("#655642"),0.47,0.0)
    (mats["bronze"] as StandardMaterial3D).metallic=0.40
    _plain("bronze_edge",Color("#af9563"),0.45)
    _plain("water",Color("#284e64"),0.28)
    _plain("embers",Color("#ff842e"),0.4,1.0)
    _plain("smoke",Color(0.38,0.37,0.36,0.16),1.0)
    (mats["smoke"] as StandardMaterial3D).transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
    _plain("banner_red",Color("#923f32"),0.94)
    _plain("banner_ochre",Color("#b19d60"),0.94)
    _plain("shirt",Color("#5c4941"),0.85)
    _plain("shirt2",Color("#797769"),0.85)
    _plain("skin",Color("#aa8063"),0.86)
    _plain("hair",Color("#38281f"),0.90)

func _mat(key: String, file: String, tint: Color, repeat: float) -> void:
    var m := StandardMaterial3D.new()
    m.albedo_color = tint
    m.metallic = 0.0
    m.roughness = 0.95
    m.uv1_scale = Vector3(repeat, repeat, 1)
    m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
    var tex = load("res://assets/"+file+".jpg")
    if tex == null:
        push_error("Missing CC0 photographed construction material "+file)
        get_tree().quit(2)
        return
    m.albedo_texture = tex
    if key=="roof" or key=="dark_roof":m.cull_mode=BaseMaterial3D.CULL_DISABLED
    mats[key]=m

func _plain(key:String, c:Color, rough:float=0.9, emission:float=0.0) -> void:
    var m := StandardMaterial3D.new()
    m.albedo_color=c
    m.roughness=rough
    if emission>0:
        m.emission_enabled=true
        m.emission=c
        m.emission_energy_multiplier=emission
    mats[key]=m

func _world() -> void:
    var e := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode=Environment.BG_SKY
    var sky := Sky.new()
    var s := ProceduralSkyMaterial.new()
    if mode=="london":
        s.sky_top_color=Color("#4a718d")
        s.sky_horizon_color=Color("#b2bbc0")
        s.ground_bottom_color=Color("#27272a")
        s.sun_angle_max=30.0
        env.tonemap_exposure=0.85
        env.ambient_light_energy=0.52
        env.fog_enabled=false
        env.fog_light_color=Color("#858279")
        env.fog_density=0.009
    else:
        s.sky_top_color=Color("#356b95")
        s.sky_horizon_color=Color("#d1dce0")
        s.ground_bottom_color=Color("#736f5f")
        env.tonemap_exposure=1.23
        env.ambient_light_energy=0.95
        env.fog_enabled=false
        env.fog_light_color=Color("#a9a19a")
        env.fog_density=0.003
    var sky_tex = load("res://assets/daylight_sky.hdr")
    if sky_tex is Texture2D and mode=="london":
        var panorama:=PanoramaSkyMaterial.new()
        panorama.panorama=sky_tex
        sky.sky_material=panorama
    else:
        sky.sky_material=s
    env.sky=sky
    env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY
    env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
    e.environment=env
    add_child(e)
    var sun := DirectionalLight3D.new()
    sun.rotation_degrees=Vector3(-48, -36, -15)
    sun.light_color=Color("#ffbf89") if mode=="london" else Color("#fff3d6")
    sun.light_energy=1.1 if mode=="london" else 1.65
    sun.shadow_enabled=true
    add_child(sun)
    var bounce:=DirectionalLight3D.new()
    bounce.rotation_degrees=Vector3(-37,149,0)
    bounce.light_color=Color("#e3e9e6")
    bounce.light_energy=0.40 if mode=="london" else 0.95
    bounce.shadow_enabled=false
    add_child(bounce)
    camera=Camera3D.new()
    camera.fov=55.0
    camera.near=0.08
    camera.far=450.0
    camera.current=true
    add_child(camera)

func _box(at: Vector3, dims: Vector3, material_name: String, parent: Node3D=null) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    var mesh := BoxMesh.new()
    mesh.size=dims
    node.mesh=mesh
    node.material_override=mats[material_name]
    node.position=at
    if parent!=null:
        parent.add_child(node)
    else:
        add_child(node)
    total_nodes+=1
    return node

func _cylinder(at:Vector3,rad:float,height:float,mat:String,rotation:Vector3=Vector3.ZERO,parent:Node3D=null) -> MeshInstance3D:
    var node:=MeshInstance3D.new()
    var m:=CylinderMesh.new()
    m.top_radius=rad
    m.bottom_radius=rad
    m.height=height
    m.radial_segments=12
    node.mesh=m
    node.material_override=mats[mat]
    node.position=at
    node.rotation_degrees=rotation
    if parent!=null:parent.add_child(node)
    else:add_child(node)
    total_nodes+=1
    return node

func _sphere(at:Vector3,rad:float,mat:String,parent:Node3D=null) -> MeshInstance3D:
    var node:=MeshInstance3D.new()
    var m:=SphereMesh.new()
    m.radius=rad
    m.height=rad*2.0
    m.radial_segments=12
    m.rings=8
    node.mesh=m
    node.material_override=mats[mat]
    node.position=at
    if parent!=null:parent.add_child(node)
    else:add_child(node)
    total_nodes+=1
    return node

func _beam(a:Vector3,b:Vector3,width:float,mat:String,parent:Node3D=null) -> Node3D:
    var mid:Vector3=(a+b)*0.5
    var mesh:=_box(mid,Vector3(width,a.distance_to(b),width),mat,parent)
    mesh.quaternion=Quaternion(Vector3.UP,(b-a).normalized())
    return mesh

func _gable_roof(center:Vector3,half_x:float,half_z:float,rise:float,mat:String,parent:Node3D=null) -> void:
    # Every triangle is built to a coherent roof plan; the tile texture is a
    # licensed real surface, rather than an entire stock house dropped in.
    var v: Array[Vector3]=[
        center+Vector3(-half_x,0,-half_z),
        center+Vector3(0,rise,-half_z),
        center+Vector3(half_x,0,-half_z),
        center+Vector3(-half_x,0,half_z),
        center+Vector3(0,rise,half_z),
        center+Vector3(half_x,0,half_z),
    ]
    var triangles=[[4,1,0],[3,4,0],[5,2,1],[4,5,1]]
    var uv:Array[Vector2]=[Vector2(0,0),Vector2(0.5,0.5),Vector2(1,0),Vector2(0,1),Vector2(0.5,1.5),Vector2(1,1)]
    var st:=SurfaceTool.new()
    st.begin(Mesh.PRIMITIVE_TRIANGLES)
    for face in triangles:
        for k in face:
            st.set_uv(uv[k])
            st.add_vertex(v[k])
    st.generate_normals()
    var node:=MeshInstance3D.new()
    node.mesh=st.commit()
    node.material_override=mats[mat]
    if parent!=null:parent.add_child(node)
    else:add_child(node)
    total_nodes+=1

func _overlays() -> void:
    var layer:=CanvasLayer.new()
    add_child(layer)
    var kicker:=Label.new()
    kicker.position=Vector2(30,99)
    kicker.size=Vector2(660,62)
    kicker.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
    kicker.text="STYLISED HISTORICAL RECONSTRUCTION"
    kicker.add_theme_font_size_override("font_size",19)
    kicker.add_theme_color_override("font_color",Color("#f6eed9"))
    kicker.add_theme_color_override("font_outline_color",Color("#15212d"))
    kicker.add_theme_constant_override("outline_size",7)
    layer.add_child(kicker)
    caption=Label.new()
    caption.position=Vector2(26,1012)
    caption.size=Vector2(668,142)
    caption.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
    caption.vertical_alignment=VERTICAL_ALIGNMENT_CENTER
    caption.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
    caption.add_theme_font_size_override("font_size",33)
    caption.add_theme_color_override("font_color",Color("#fff7e9"))
    caption.add_theme_color_override("font_outline_color",Color("#171b20"))
    caption.add_theme_constant_override("outline_size",10)
    layer.add_child(caption)

func _window(face_x:float,y:float,z:float,side:float) -> void:
    # Lit leaded-glass panes with real timber mullions, in correct scale.
    _box(Vector3(face_x,y,z),Vector3(0.14,1.1,0.82),"glass")
    _box(Vector3(face_x+side*0.1,y,z),Vector3(0.22,0.11,1.10),"oak")
    _box(Vector3(face_x+side*0.1,y+0.64,z),Vector3(0.22,0.10,1.10),"oak")
    _box(Vector3(face_x+side*0.1,y-0.64,z),Vector3(0.22,0.10,1.10),"oak")
    _box(Vector3(face_x+side*0.1,y,z),Vector3(0.22,1.28,0.10),"oak")

func _house(side:float,z:float,index:int) -> void:
    var x:=side*(6.2+0.4*(index%3))
    var h:=8.1+float(index%3)*0.6
    var w:=6.7
    var length:=7.9
    var root:=Node3D.new()
    root.name="Timbered_street_house_"+str(index)+"_"+str(side)
    add_child(root)
    var front:=x-side*3.4
    var upper_x:=x-side*0.55
    var trim_name: String="oak"
    var plaster_name: String="plaster"
    _box(Vector3(x,1.55,z),Vector3(w,3.1,length),plaster_name,root)
    _box(Vector3(upper_x,5.7,z),Vector3(w+0.65,5.1,length+0.25),plaster_name,root)
    for elevation in [3.2,4.5,6.8,8.15]:
        _box(Vector3(upper_x-side*3.82,elevation,z),Vector3(0.31,0.27,8.15),trim_name,root)
    for longitudinal in [-3.95,-1.85,0.0,1.85,3.95]:
        _box(Vector3(upper_x-side*3.82,5.75,z+longitudinal),Vector3(0.31,5.0,0.28),trim_name,root)
    for offset in [-2.0,2.0]:
        _window(front,2.15,z+offset,side)
        _window(upper_x-side*3.95,6.6,z+offset,side)
    _box(Vector3(front-side*0.08,1.14,z),Vector3(0.16,2.2,1.23),"boards",root)
    _box(Vector3(front-side*0.25,0.25,z+1.4),Vector3(1.0,0.42,2.0),"stone",root)
    # Tiled pitched roofs (not historical-accuracy-breaking thatch).
    _gable_roof(Vector3(upper_x,h+0.25,z),3.95,4.15,2.35,"roof" if index%4!=2 else "dark_roof",root)
    _box(Vector3(upper_x+1.3,h+1.6,z+0.9),Vector3(0.95,2.2,1.05),"brick",root)
    var ignite:float=0.0 if side>0.0 and index==6 else 1.8+float(abs(index-6))*1.65+ (6.5 if side<0.0 else 0.0)
    if index>=1 and index<=13 and (index%3 != 1 or index==6):
        _fire_at(Vector3(upper_x,h+1.55,z),ignite,1.20 if index==6 else 0.88)
    for bay in [-2.1,1.6]:
        var facade:float=upper_x-side*3.91
        _beam(Vector3(facade,4.35,z+bay-0.92),Vector3(facade,6.44,z+bay+0.92),0.14,"oak",root)
    if index%3==0:
        _box(Vector3(front-side*0.35,2.9,z+1.9),Vector3(0.4,0.75,1.2),"boards",root)
    if index%5==0:
        _barrel(Vector3(side*2.9,0.58,z+1.8))

func _barrel(p:Vector3) -> void:
    _cylinder(p,0.35,1.05,"boards")
    for y in [-0.31,0.31]:
        _cylinder(p+Vector3(0,y,0),0.36,0.09,"bronze")

func _person(p:Vector3, direction:Vector3, variation:int, start:float) -> void:
    var root:=Node3D.new()
    root.position=p
    add_child(root)
    _sphere(Vector3(0,1.56,0),0.19,"skin",root)
    _sphere(Vector3(0,1.75,0),0.20,"hair",root)
    _cylinder(Vector3(0,1.03,0),0.34,0.93,"shirt" if variation%2==0 else "shirt2",Vector3.ZERO,root)
    _box(Vector3(0,0.76,0),Vector3(0.63,0.12,0.44),"oak",root)
    _cylinder(Vector3(-0.36,1.03,0),0.12,0.70,"shirt",Vector3(0,0,12),root)
    _cylinder(Vector3(0.36,1.03,0),0.12,0.70,"shirt",Vector3(0,0,-12),root)
    var l:=_cylinder(Vector3(-0.17,0.34,0),0.14,0.70,"oak",Vector3.ZERO,root)
    var r:=_cylinder(Vector3(0.17,0.34,0),0.14,0.70,"oak",Vector3.ZERO,root)
    _cylinder(Vector3(0,1.88,0),0.27,0.18,"oak",Vector3.ZERO,root)
    _cylinder(Vector3(0,1.81,0),0.34,0.04,"oak",Vector3.ZERO,root)
    root.rotation.y=atan2(direction.x,direction.z)
    people.append({"root":root,"home":p,"direction":direction.normalized(),"start":start,"left":l,"right":r,"offset":float(variation)})

func _fire_at(position:Vector3,ignite:float,scale:float) -> void:
    # Three-dimensional wind-animated flame surface, split across multiple
    # crossing planes so the camera can orbit it. Not a static 2D flame icon.
    # Physically motivated staging: source burns at the roof, luminous tongues
    # rise through the air, smoke rolls upwind, and nearby walls receive light.
    var fire:=Node3D.new()
    fire.name="Animated_roof_fire_"+str(ignite)
    fire.position=position
    add_child(fire)
    var lit:=OmniLight3D.new()
    lit.light_color=Color("#ff6e2c")
    lit.light_energy=0.0
    lit.omni_range=18.0
    lit.shadow_enabled=false
    fire.add_child(lit)
    var animated_flames:Array=[]
    var shared:Shader=load("res://real_fire_flipbook.gdshader")
    var baked_texture:Texture2D=load("res://assets/brackeys_fire_01_8x8.tga")
    if shared==null or baked_texture==null:
        push_error("Missing CC0 Brackeys 64-frame photographic fire effect")
        return
    for j in range(7):
        var node:=MeshInstance3D.new()
        var quad:=QuadMesh.new()
        quad.size=Vector2(2.55+float(j%3)*0.5,3.8+float(j%4)*0.34)
        node.mesh=quad
        var mat:=ShaderMaterial.new()
        mat.shader=shared
        mat.set_shader_parameter("flipbook",baked_texture)
        mat.set_shader_parameter("offset",float(j)*9.15+ignite*0.19)
        mat.set_shader_parameter("speed",22.0+float(j%3)*1.5)
        mat.set_shader_parameter("opacity",1.0)
        mat.set_shader_parameter("brightness",1.8)
        node.material_override=mat
        var ring:float=float(j)*2.399963
        var radius:float=0.23+float(j%4)*0.44
        node.position=Vector3(cos(ring)*radius,1.62+float(j%3)*0.31,sin(ring)*radius)
        node.rotation_degrees.y=float((j*39)%180)
        fire.add_child(node)
        animated_flames.append({"mesh":node,"base_x":node.position.x,"base_y":node.position.y})
    var smoke:Array=_smoke_sprites(fire)
    var embers:Array=[]
    for k in range(11):
        var piece:=_sphere(Vector3.ZERO,0.055+float(k%3)*0.015,"embers",fire)
        embers.append({"mesh":piece,"seed":float(k)*1.37})
    # High intensity lights make the fire interact with the historical roofs.
    fire_nodes.append({"root":fire,"light":lit,"flames":animated_flames,
        "smoke_sprites":smoke,"embers":embers,"start":ignite,"scale":scale})

func _london() -> void:
    # 1666 street reconstruction: contiguous, extremely close timber houses
    # with overhanging upper storeys; connected street, not grassy demo tiles.
    _box(Vector3(0,-0.4,0),Vector3(175,0.7,190),"soil")
    _box(Vector3(0,0.02,0),Vector3(8.0,0.12,160.0),"street")
    _street_details()
    _neighborhood()
    _rebuilt_stone_quarter()
    for side in [-1.0,1.0]:
        _box(Vector3(side*4.19,0.13,0),Vector3(0.29,0.27,160.0),"stone")
        for i in range(15):
            _house(side,-57.5+float(i)*8.2,i)
    # Build a broad Gothic stone cathedral outline instead of a generic
    # blocky tower. A stylised medieval Old St Paul's, not an exact replica.
    _gothic_cathedral()
    _fire_at(Vector3(29,29.7,65),25.0,1.12)
    _fire_at(Vector3(34,26.6,73),26.0,0.98)
    for j in range(10):
        var dz:float=0.0+float(j)*7.6
        _person(Vector3(-1.2 if j%2==0 else 1.25,0.0,dz),Vector3(0,0,-1),j,float(j)*1.05)
    for i in range(9):
        _barrel(Vector3((-1 if i%2==0 else 1)*3.4,0.55,-46+float(i)*13.3))

func _crenels(z:float,top:float,half_width:float,mat:String) -> void:
    for k in range(-17,18):
        var x:float=float(k)*4.0
        if absf(x)>half_width-0.6:continue
        _box(Vector3(x,top+0.46,z),Vector3(2.1,0.94,2.7),mat)

func _tower(x:float,z:float,height:float,mat:String) -> void:
    _box(Vector3(x,height*0.5,z),Vector3(7.5,height,7.0),mat)
    _box(Vector3(x,height*0.43,z-3.6),Vector3(7.55,0.34,0.20),"brick")
    _box(Vector3(x,height*0.75,z-3.62),Vector3(7.55,0.32,0.2),"brick")
    for dx in [-3.0,3.0]:
        _box(Vector3(x+dx,height+0.58,z-2.95),Vector3(1.1,1.15,1.1),mat)
        _box(Vector3(x+dx,height+0.58,z+2.95),Vector3(1.1,1.15,1.1),mat)
    for dz in [-2.95,0,2.95]:
        _box(Vector3(x,height+0.58,z+dz),Vector3(1.12,1.15,1.05),mat)
    _box(Vector3(x,10.2,z-3.55),Vector3(0.38,1.45,0.1),"black")

func _cannon(p:Vector3,index:int) -> void:
    var root:=Node3D.new()
    root.position=p
    root.rotation_degrees.y=7.5*float(index-1)
    root.name="Ottoman_bombard_custom_assembly"
    add_child(root)
    # Period-motivated long muzzle and wooden transport carriage, not little
    # 18th-century pirate cannon pointed at a generic fantasy castle.
    _box(Vector3(0,0.65,0),Vector3(2.6,0.85,5.0),"boards",root)
    for x in [-1.32,1.32]:
        for z in [-1.6,1.6]:
            _cylinder(Vector3(x,0.53,z),0.67,0.25,"boards",Vector3(0,0,90),root)
            _cylinder(Vector3(x+(0.15 if x>0 else -0.15),0.53,z),0.20,0.07,"bronze",Vector3(0,0,90),root)
    var barrel:=_cylinder(Vector3(0,1.65,-0.4),0.56,5.4,"bronze",Vector3(90,0,0),root)
    _cylinder(Vector3(0,1.65,2.30),0.62,0.45,"bronze_edge",Vector3(90,0,0),root)
    _cylinder(Vector3(0,1.65,-2.85),0.63,0.25,"bronze_edge",Vector3(90,0,0),root)

func _rowboat_overland(i:int) -> void:
    var carriage:=Node3D.new()
    carriage.name="Historically_staged_wooden_galley_and_rollers_"+str(i)
    carriage.position=Vector3(-33+float(i)*12.0,0,-48-float(i)*9.0)
    add_child(carriage)
    _boat_hull(carriage)
    _box(Vector3(0,0.95,0),Vector3(3.5,0.24,7.5),"boards",carriage)
    for z in [-3.6,-2.1,-0.6,0.9,2.4,3.9]:
        _cylinder(Vector3(0,0.54,z),0.48,4.9,"oak",Vector3(0,0,90),carriage)
    _beam(Vector3(-1.3,2.5,3.8),Vector3(-1.4,0.85,7.2),0.09,"oak",carriage)
    _beam(Vector3(1.3,2.5,3.8),Vector3(1.4,0.85,7.2),0.09,"oak",carriage)
    boats.append({"node":carriage,"origin":carriage.position,"offset":float(i)})
    for k in range(3):
        _person(Vector3(carriage.position.x+4.3+float(k),0,carriage.position.z+5.0),Vector3(0,0,1),k+7,17.0)

func _boat_hull(parent:Node3D) -> void:
    # Purpose-built timber galley silhouette with tapered bow, ribs, benches and oars.
    # Imported white untextured boats are deliberately removed from final staging.
    var top:Array[Vector3]=[
      Vector3(-0.65,2.15,-5.2),Vector3(-1.7,2.15,-3.3),Vector3(-1.7,2.15,2.9),
      Vector3(-0.16,2.15,5.0),Vector3(0.16,2.15,5.0),
      Vector3(1.7,2.15,2.9),Vector3(1.7,2.15,-3.3),Vector3(0.65,2.15,-5.2)]
    var surf:=SurfaceTool.new()
    surf.begin(Mesh.PRIMITIVE_TRIANGLES)
    for k in range(8):
        var nxt:int=(k+1)%8
        var a:Vector3=top[k]
        var b:Vector3=top[nxt]
        var low_a:=Vector3(a.x*0.57,1.18,a.z*0.85)
        var low_b:=Vector3(b.x*0.57,1.18,b.z*0.85)
        for v in [a,b,low_b,a,low_b,low_a]:
            surf.set_uv(Vector2(v.z*0.34,v.y*0.44))
            surf.add_vertex(v)
    surf.generate_normals()
    var hull:=MeshInstance3D.new()
    hull.mesh=surf.commit()
    var plank_material:StandardMaterial3D=mats["boards"].duplicate()
    plank_material.cull_mode=BaseMaterial3D.CULL_DISABLED
    hull.material_override=plank_material
    parent.add_child(hull)
    total_nodes+=1
    _box(Vector3(0,1.27,0),Vector3(2.6,0.16,7.8),"oak",parent)
    for z in [-3.6,-2.0,-0.4,1.2,2.8]:
        _box(Vector3(0,1.89,z),Vector3(3.05,0.14,0.55),"boards",parent)
        for side in [-1.0,1.0]:
            _beam(Vector3(side*1.28,2.05,z),Vector3(side*3.3,1.52,z-1.2),0.13,"oak",parent)
    _box(Vector3(0,2.23,-4.1),Vector3(1.05,0.26,1.35),"boards",parent)
    _box(Vector3(0,2.22,4.1),Vector3(0.54,0.3,1.0),"boards",parent)

func _constantinople() -> void:
    # The Theodosian defensive layers: a deep forward ditch, low outer wall,
    # higher inner wall, frequent square towers, distinctive brick courses.
    _box(Vector3(0,-0.5,0),Vector3(230,0.95,220),"soil")
    _city_beyond_walls()
    _siege_camp()
    _custom_vegetation()
    _box(Vector3(0,-0.16,35),Vector3(170,0.25,78),"grass")
    _box(Vector3(0,-1.15,-17),Vector3(170,0.2,12),"soil")
    _box(Vector3(0,-0.56,-24),Vector3(172,0.7,1.7),"sandstone")
    _box(Vector3(0,-0.56,-10),Vector3(172,0.7,1.7),"sandstone")
    _box(Vector3(0,3.95,4.0),Vector3(151,7.9,3.0),"castle")
    _box(Vector3(0,9.05,20.5),Vector3(160,18.1,4.2),"stone")
    for wall in [[4.0,7.9],[20.5,18.1]]:
        var z:float=wall[0]
        var h:float=wall[1]
        for yy in [h*0.31,h*0.67]:
            _box(Vector3(0,yy,z-2.20),Vector3(152,0.46,0.27),"brick")
        _crenels(z,h,75.0,"castle" if z<10 else "stone")
    for x in [-65.0,-39.0,-13.0,13.0,39.0,65.0]:
        _tower(x,4.0,11.0,"castle")
        _tower(x,20.5,23.0,"stone")
    # Explicit gate under construction at the breached central sector:
    _box(Vector3(0,3.1,1.5),Vector3(6.8,6.2,0.5),"black")
    _gate_details()
    _make_siege_dust()
    _box(Vector3(0,7.0,1.6),Vector3(8.4,1.8,1.3),"castle")
    for i in range(3):
        _cannon(Vector3(-24+24.0*i,0,-44.0-float(i%2)*3.0),i)
    for i in range(9):
        _person(Vector3(-36.0+float(i)*8.0,0,-36.0-float(i%2)*4.0),Vector3(0,0,1),i,5.0+float(i)*1.1)
    for i in range(2):
        _rowboat_overland(i)
    cannonball=_sphere(Vector3(0,-100,0),0.56,"black")
    for i in range(24):
        var b:=_box(Vector3(-6+float(i%8)*1.5,0.8+float(i/8),4.4+float(i%4)),Vector3(0.6,0.42,0.8),"castle")
        b.visible=false
        fragments.append(b)

func _shots_london() -> void:
    shots=[
        [0.0,3.0,Vector3(-17,33,-40),Vector3(-14,30,-32),Vector3(3,10,-8),"LONDON 1666 • THE FIRST FLAMES"],
        [3.0,6.0,Vector3(-10,25,-32),Vector3(-8,22,-26),Vector3(5,11,-8),"A FIRE BEGINS IN PUDDING LANE"],
        [6.0,9.0,Vector3(0,3.3,-30),Vector3(0,3.8,-21),Vector3(0,4.5,15),"TIMBER BUILDINGS STOOD CLOSE"],
        [9.0,12.0,Vector3(-30,30,-18),Vector3(-27,28,-8),Vector3(0,7,13),"NARROW STREETS, TILED ROOFS"],
        [12.0,15.0,Vector3(0,16,-20),Vector3(0,17,-8),Vector3(0,7,30),"WIND CARRIED FIRE DOWN THE STREET"],
        [15.0,18.0,Vector3(16,25,0),Vector3(12,22,13),Vector3(3,9,15),"FLAMES SPREAD FROM HOUSE TO HOUSE"],
        [18.0,21.0,Vector3(-17,25,-4),Vector3(-13,23,10),Vector3(0,9,20),"THE FIRE SPREADS THROUGH LONDON"],
        [21.0,24.0,Vector3(0,4.0,5),Vector3(0,4.0,20),Vector3(0,5,35),"PEOPLE FLEE AS BUILDINGS BURN"],
        [24.0,27.0,Vector3(-15,45,10),Vector3(-10,44,22),Vector3(30,24,70),"THE OLD ST PAUL'S CATHEDRAL"],
        [27.0,30.0,Vector3(59,49,15),Vector3(58,47,27),Vector3(30,25,70),"EVEN THE CATHEDRAL WAS LOST"],
        [30.0,33.0,Vector3(2,70,5),Vector3(2,68,20),Vector3(0,10,4),"13,200 HOUSES WERE DESTROYED"],
        [33.0,36.0,Vector3(103,29,-49),Vector3(97,26,-38),Vector3(71,10,-16),"LONDON REBUILT AFTER THE FIRE"],
    ]

func _shots_constantinople() -> void:
    shots=[
        [0.0,3.0,Vector3(-34,9,-61),Vector3(-29,9,-55),Vector3(-21,4,-36),"THE OTTOMAN SIEGE • 1453"],
        [3.0,6.0,Vector3(12,26,-57),Vector3(4,25,-48),Vector3(0,13,18),"CONSTANTINOPLE'S FORTIFICATIONS"],
        [6.0,9.0,Vector3(-28,39,-34),Vector3(-23,35,-27),Vector3(-12,14,40),"OUTER WALL • DEEP MOAT"],
        [9.0,12.0,Vector3(6,55,-27),Vector3(8,51,-14),Vector3(7,18,76),"THE TALLER INNER DEFENSE"],
        [12.0,15.0,Vector3(-29,7,-57),Vector3(-24,7,-52),Vector3(-20,3,-39),"MEHMED'S HEAVY ARTILLERY"],
        [15.0,18.0,Vector3(-18,17,-45),Vector3(-14,20,-35),Vector3(0,11,9),"CANNON SHOTS STRIKE THE WALLS"],
        [18.0,21.0,Vector3(-46,9,-78),Vector3(-38,9,-65),Vector3(-26,2,-49),"GALLEY BOATS ON TIMBER ROLLERS"],
        [21.0,24.0,Vector3(-34,8,-64),Vector3(-27,8,-53),Vector3(-22,2,-43),"SHIPS WERE MOVED OVER LAND"],
        [24.0,27.0,Vector3(7,10,-36),Vector3(5,12,-24),Vector3(0,7,4),"THE ASSAULT REACHES THE GATE"],
        [27.0,30.0,Vector3(-15,17,-33),Vector3(-13,17,-26),Vector3(0,10,8),"THE DEFENSES ARE OVERRUN"],
        [30.0,33.0,Vector3(60,50,-46),Vector3(65,53,-55),Vector3(0,14,24),"29 MAY 1453 • THE CITY FALLS"],
        [33.0,36.0,Vector3(30,70,-34),Vector3(40,77,-50),Vector3(7,22,86),"BYZANTINE RULE COMES TO AN END"],
    ]

func _process(delta:float) -> void:
    time_now+=delta
    if time_now>=DURATION:
        get_tree().quit()
        return
    _animate(time_now)
    _direct(time_now)

func _direct(t:float) -> void:
    for sh in shots:
        if t>=float(sh[0]) and t<float(sh[1]):
            var a:float=clampf((t-float(sh[0]))/(float(sh[1])-float(sh[0])),0.0,1.0)
            # Constant, purposeful dolly motion: no stopping at every cut.
            a=clampf(a,0.0,1.0)
            camera.position=(sh[2] as Vector3).lerp(sh[3],a)
            camera.fov=51.0+2.5*sin(t*0.5)
            camera.look_at(sh[4],Vector3.UP)
            caption.text=sh[5]
            return

func _animate(t:float) -> void:
    for p in people:
        var person:Node3D=p["root"]
        var a:float=clampf((t-float(p["start"]))*0.7,0.0,1.0)
        person.position=p["home"]+p["direction"]*maxf(0.0,t-float(p["start"]))*0.95
        person.position.y=0.025*sin(t*13.0+float(p["offset"]))*a
        p["left"].rotation.x=0.40*sin(t*9.0+float(p["offset"]))*a
        p["right"].rotation.x=-0.40*sin(t*9.0+float(p["offset"]))*a
    for fire in fire_nodes:
        var root:Node3D=fire["root"]
        var age:float=t-float(fire["start"])
        root.visible=age>=0
        if age<0:continue
        var brightness:float=clampf(age/1.4,0.0,1.0)
        var flicker:float=0.94+0.13*sin(t*13.7+float(fire["scale"])*2.3)
        root.scale=Vector3.ONE*float(fire["scale"])*0.88*flicker*maxf(brightness,0.015)
        fire["light"].light_energy=5.2*brightness*(0.85+0.23*sin(t*14.0))
        for i in range(fire["flames"].size()):
            var flame=fire["flames"][i]
            var mesh:MeshInstance3D=flame["mesh"]
            var mat:ShaderMaterial=mesh.material_override
            mat.set_shader_parameter("opacity",brightness*0.92)
            mesh.position.x=float(flame["base_x"])+0.12*sin(t*4.9+float(i)*1.6)
            mesh.position.y=float(flame["base_y"])+0.12*sin(t*6.4+float(i)*2.2)
        for i in range(fire["smoke_sprites"].size()):
            var puff:MeshInstance3D=fire["smoke_sprites"][i]
            puff.position.y=3.1+float(i)*0.75+fmod(maxf(age,0.0)*0.47,1.9)
            puff.position.x=-0.33+float(i)*0.45+sin(t*0.7+float(i))*0.60
            var sm:ShaderMaterial=puff.material_override
            sm.set_shader_parameter("opacity",0.12+0.25*clampf(age/4.0,0.0,1.0))
        for ember in fire["embers"]:
            var dot:Node3D=ember["mesh"]
            var seed:float=ember["seed"]
            dot.position=Vector3(1.0*sin(t*2.1+seed)+0.13*seed,
                0.8+fmod(maxf(age,0.0)*1.9+seed,4.8),0.8*cos(t*1.7+seed))
            dot.visible=age>0.5 and fmod(t*2.3+seed,3.1)<1.8
    for dust in siege_dust:
        var node:Sprite3D=dust["node"]
        var onset:float=float(dust["time"])
        var elapsed:float=t-onset
        node.visible=elapsed>=0.0 and elapsed<3.5
        if node.visible:
            node.position=dust["base"]+Vector3(sin(t*0.7)*0.3,elapsed*0.65,0)
            node.modulate.a=0.45*(1.0-clampf(elapsed/3.5,0.0,1.0))
            node.scale=Vector3.ONE*(1.0+elapsed*0.22)
    for boat in boats:
        var n:Node3D=boat["node"]
        var start:float=18.0+float(boat["offset"])*1.3
        var a:float=clampf((t-start)/9.0,0.0,1.0)
        n.position=boat["origin"]+Vector3(4.3*a,0.025*sin(t*6)*a,5.3*a)
    if cannonball!=null:
        var k:=fmod(t-12.0,12.0)
        var is_flying:=t>=12.0 and t<31.0 and k<2.5
        cannonball.visible=is_flying
        if is_flying:
            var a:float=k/2.5
            cannonball.position=Vector3(-13.0+13.0*a,2.3+18.0*a*(1.0-a),-44.0+49.0*a)
        for i in range(fragments.size()):
            var frag:Node3D=fragments[i]
            frag.visible=t>27.5
            if frag.visible:
                var age:float=minf(t-27.5,4.0)
                frag.position.y=maxf(0.28,frag.position.y-age*0.35)
                frag.rotation_degrees=Vector3(age*float(i%5)*8.0,age*13.0,0)


# Scene detail is purpose-built for the reconstructed geography, not placed
# as a copied asset-pack environment.
func _street_details() -> void:
    for k in range(15):
        var z:float=-52.0+float(k)*8.15
        var side:float=-1.0 if k%2==0 else 1.0
        _box(Vector3(side*3.85,0.09,z),Vector3(0.08,0.06,2.3),"stone")
        _cylinder(Vector3(side*3.67,1.04,z+0.7),0.07,2.08,"oak")
        _beam(Vector3(side*3.70,1.80,z+0.7),Vector3(side*3.1,1.80,z+0.7),0.07,"bronze")
        _box(Vector3(side*3.08,1.49,z+0.7),Vector3(0.42,0.46,0.36),"bronze")
        if k%4==1:
            for n in range(3):
                _box(Vector3(side*(3.35+0.26*float(n)),0.21,z+1.0+float(n)*0.5),Vector3(0.55,0.42,0.62),"boards")
    for side in [-1.0,1.0]:
        _box(Vector3(side*3.91,0.17,0),Vector3(0.34,0.27,149),"stone")
        for k in range(14):
            _box(Vector3(side*3.06,0.23,-54.0+float(k)*9.4),Vector3(1.1,0.29,0.67),"boards")

func _city_beyond_walls() -> void:
    for i in range(24):
        var column:int=i%12
        var row:int=int(i/12)
        var x:float=-73.0+float(column)*13.1
        var z:float=49.0+float(row)*23.5
        var h:float=6.0+float((i*5)%6)*1.0
        _box(Vector3(x,h*0.5,z),Vector3(8.6,h,10.2),"plaster")
        _gable_roof(Vector3(x,h+0.15,z),5.0,5.6,3.5,"dark_roof" if i%3==0 else "roof")
        _box(Vector3(x+2.1,h+1.1,z),Vector3(1.2,2.2,1.2),"brick")
    # Generic Byzantine civic building. Not represented as exact Hagia Sophia.
    _box(Vector3(7,6.0,86),Vector3(25,12,27),"castle")
    _box(Vector3(7,15.0,86),Vector3(18,6.0,19),"sandstone")
    var dome:=MeshInstance3D.new()
    var mesh:=SphereMesh.new()
    mesh.radius=9.0
    mesh.height=11.0
    mesh.is_hemisphere=true
    mesh.radial_segments=24
    mesh.rings=12
    dome.mesh=mesh
    dome.material_override=mats["dark_roof"]
    dome.position=Vector3(7,18.0,86)
    add_child(dome)
    total_nodes+=1
    for side in [-1.0,1.0]:
        _cylinder(Vector3(7+side*16.0,12.0,86),3.4,24,"stone")
    for j in range(5):
        var bx:float=-43.0+float(j)*19.0
        _box(Vector3(bx,3.8,6.4),Vector3(1.0,7.6,0.25),"banner_red" if j%2==0 else "banner_ochre")
        _box(Vector3(bx,8.7,6.4),Vector3(0.14,3.6,0.15),"oak")

func _siege_camp() -> void:
    for j in range(7):
        var x:float=-72.0+float(j)*22.0
        var z:float=-66.0-float(j%3)*8.0
        _box(Vector3(x,0.4,z),Vector3(5.8,0.8,7.0),"boards")
        _gable_roof(Vector3(x,2.1,z),3.1,3.8,2.7,"boards")
        _box(Vector3(x+5.0,0.7,z),Vector3(1.0,1.4,2.4),"boards")
        _cylinder(Vector3(x+8.0,1.1,z),0.42,2.2,"boards")
    for j in range(14):
        var x:float=-68.0+float(j%7)*20.0
        var z:float=-83.0+float(int(j/7))*12.0
        _box(Vector3(x,0.7,z),Vector3(2.2,1.4,1.7),"stone")

func _dynamic_fx_assets(parent:Node3D) -> Array:
    var results:Array=[]
    for i in range(2):
        var texture = load("res://assets/kenney_flame_0"+str(i+1)+".png")
        if texture is Texture2D:
            var sprite:=Sprite3D.new()
            sprite.texture=texture
            sprite.billboard=BaseMaterial3D.BILLBOARD_ENABLED
            sprite.shaded=false
            sprite.pixel_size=0.0250
            sprite.position=Vector3(-0.36+float(i)*0.7,0.9,0.1+float(i)*0.21)
            sprite.scale=Vector3.ONE*(0.74+float(i)*0.18)
            sprite.transparent=true
            sprite.modulate=Color(1.0,0.65,0.28,0.92)
            parent.add_child(sprite)
            results.append(sprite)
    return results

func _custom_vegetation() -> void:
    # Existing CC0 trees are repeating ingredients only. Position, density,
    # size and vegetation zoning are authored for the city approach.
    for i in range(26):
        var old:bool=i%3==0
        var packed=load("res://assets/tree_oak.glb" if old else "res://assets/tree_default.glb")
        if packed == null or not packed is PackedScene:continue
        var tree:Node3D=packed.instantiate()
        var edge:float=-1.0 if i%2==0 else 1.0
        var x:float=edge*(82.0+float(i%5)*2.9)
        var z:float=-37.0+float(i%13)*13.2
        tree.position=Vector3(x,0,z)
        var sc:float=3.3+float((i*7)%6)*0.31
        tree.scale=Vector3.ONE*sc
        tree.rotation_degrees.y=float((i*37)%360)
        add_child(tree)
    for i in range(13):
        var packed=load("res://assets/tree_oak.glb")
        if packed == null or not packed is PackedScene:continue
        var tree:Node3D=packed.instantiate()
        tree.position=Vector3(-65.0+float(i)*10.7,0,100.0+float(i%3)*6.0)
        tree.rotation_degrees.y=float((i*51)%360)
        tree.scale=Vector3.ONE*(3.0+float(i%4)*0.28)
        add_child(tree)


func _gate_details() -> void:
    # The gateway is a three-dimensional timber-and-metal defensive structure,
    # rather than the blank black square from the rejected test.
    for side in [-1.0,1.0]:
        _box(Vector3(side*3.75,3.28,1.36),Vector3(0.80,7.2,1.2),"stone")
        _box(Vector3(side*3.3,6.89,1.26),Vector3(1.18,0.73,1.36),"stone")
    _box(Vector3(0,7.18,1.35),Vector3(7.6,1.25,1.15),"stone")
    for j in range(11):
        var x:float=-2.95+float(j)*0.57
        _box(Vector3(x,3.05,1.12),Vector3(0.49,5.93,0.21),"boards")
        if j%2==0:
            for level in [1.55,3.25,4.80]:
                _sphere(Vector3(x,level,0.93),0.10,"bronze")
    for level in [1.55,3.25,4.8]:
        _box(Vector3(0,level,0.94),Vector3(6.4,0.21,0.17),"bronze")
    _cylinder(Vector3(0,3.3,0.82),0.32,0.38,"bronze",Vector3(90,0,0))

func _neighborhood() -> void:
    # A built-out metropolis must read as a whole city; the first version had
    # one isolated toy street in a barren square. These authored rear quarters
    # are simpler than hero buildings but use the same historic materials.
    for i in range(13):
        var z:float=-54.0+float(i)*9.4
        for band in [-2.0,-1.0,1.0,2.0]:
            var x:float=band*16.8+float(i%3)*0.65
            if z>45.0 and x>13.0 and x<48.0:continue
            var h:float=7.1+float((i*3+int(absf(band)))%5)*0.7
            var brick:bool=(i+int(absf(band)))%4==0
            _box(Vector3(x,h*0.5,z),Vector3(9.6,h,9.0),"brick" if brick else "plaster")
            var roofing:String="dark_roof" if (i+int(absf(band)))%3==0 else "roof"
            _gable_roof(Vector3(x,h+0.15,z),5.2,4.9,2.9,roofing)
            _box(Vector3(x-1.4,h+1.2,z+0.8),Vector3(0.66,2.0,0.8),"brick")
            if i%4==0:
                _box(Vector3(x,h*0.50,z-4.56),Vector3(1.1,1.3,0.16),"glass")
            if i in [7,8,10] and absf(band)<2.0:
                _fire_at(Vector3(x,h+2.5,z),14.0+float(i-7)*2.0,0.88)

func _smoke_sprites(parent:Node3D) -> Array:
    var out:Array=[]
    var tex:Texture2D=load("res://assets/brackeys_smoke_01_8x8.tga")
    var shader:Shader=load("res://real_smoke_flipbook.gdshader")
    if tex==null or shader==null:return out
    for i in range(4):
        var node:=MeshInstance3D.new()
        var q:=QuadMesh.new()
        q.size=Vector2(4.5+float(i)*0.8,5.5+float(i)*0.9)
        node.mesh=q
        var m:=ShaderMaterial.new()
        m.shader=shader
        m.set_shader_parameter("flipbook",tex)
        m.set_shader_parameter("offset",float(i)*14.33)
        m.set_shader_parameter("opacity",0.12)
        m.set_shader_parameter("speed",12.0+float(i%2)*4.0)
        node.material_override=m
        node.position=Vector3(-0.5+float(i)*0.34,3.8+float(i)*0.5,0.25*float(i))
        node.rotation_degrees.y=float(i)*51.0
        parent.add_child(node)
        out.append(node)
    return out

func _make_siege_dust() -> void:
    var image=load("res://assets/kenney_smoke_01.png")
    if image==null or not image is Texture2D:return
    for i in range(3):
        var puff:=Sprite3D.new()
        puff.texture=image
        puff.billboard=BaseMaterial3D.BILLBOARD_ENABLED
        puff.shaded=false
        puff.pixel_size=0.052
        puff.scale=Vector3.ONE*(1.45+float(i)*0.22)
        puff.modulate=Color(0.72,0.66,0.57,0.38)
        puff.position=Vector3(-3.5+float(i)*3.5,8.1+float(i)*1.3,1.1)
        puff.visible=false
        add_child(puff)
        siege_dust.append({"node":puff,"base":puff.position,"time":15.1+float(i)*0.18})

func _gothic_cathedral() -> void:
    # Reference Old St Paul's was a long medieval Gothic building, not
    # the tower/chimney icon present in earlier rejected drafts.
    var x:=30.0
    var z:=70.0
    var nave_height:=19.0
    _box(Vector3(x,nave_height*0.5,z),Vector3(20.0,nave_height,42.0),"stone")
    for side in [-1.0,1.0]:
        _box(Vector3(x+side*12.9,6.0,z),Vector3(6.0,12.0,39.5),"stone")
        for j in range(6):
            var zz:float=z-16.8+float(j)*6.55
            # Gothic buttresses with a stepped profile, integrated into wall.
            _box(Vector3(x+side*10.5,7.0,zz),Vector3(2.8,14.0,1.45),"sandstone")
            _box(Vector3(x+side*11.2,10.1,zz),Vector3(2.9,2.3,1.80),"castle")
            _box(Vector3(x+side*10.2,15.0,zz+3.2),Vector3(0.19,4.9,1.55),"black")
            for yy in [13.1,16.8]:
                _box(Vector3(x+side*10.4,yy,zz+3.2),Vector3(0.22,0.20,1.8),"stone")
        _gable_roof(Vector3(x+side*12.6,12.0,z),3.35,21.2,4.0,"dark_roof")
    _gable_roof(Vector3(x,20.0,z),10.8,22.0,7.3,"dark_roof")
    # Central stone bell tower: broad and crenellated; 1561 fire had removed
    # the historically earlier tall spire, so never show a 1666 spire.
    _box(Vector3(x,26.0,z+2.8),Vector3(14.0,22.0,13.0),"castle")
    for yy in [21.0,28.2,35.3]:
        _box(Vector3(x,yy,z-3.8),Vector3(14.7,0.42,0.42),"sandstone")
    for side in [-1.0,1.0]:
        _box(Vector3(x+side*7.0,29.0,z+2.8),Vector3(0.45,5.7,13.0),"sandstone")
        for zz in [z-0.8,z+4.3]:
            _box(Vector3(x+side*7.27,29.1,zz),Vector3(0.14,5.0,1.65),"black")
    for i in range(5):
        var offset:float=-5.6+float(i)*2.8
        _box(Vector3(x+offset,38.2,z-2.7),Vector3(1.7,2.2,1.4),"castle")
        _box(Vector3(x+offset,38.2,z+8.3),Vector3(1.7,2.2,1.4),"castle")

func _rebuilt_stone_quarter() -> void:
    # Visually communicate the rebuilding in stone instead of showing the
    # still-burning timber streets under narration about reconstruction.
    # These houses are custom geometry, not an exact map of 1670s London.
    _box(Vector3(72,-0.42,-16),Vector3(73,0.80,85),"soil")
    _box(Vector3(72,0.05,-18),Vector3(10.0,0.16,76.0),"street")
    for side in [-1.0,1.0]:
        for i in range(8):
            var x:float=72.0+side*11.4
            var z:float=-48.0+float(i)*8.5
            var h:float=10.3+float(i%3)*1.4
            var tone:String="sandstone" if i%3==0 else "stone"
            _box(Vector3(x,h*0.5,z),Vector3(10.4,h,8.3),tone)
            _gable_roof(Vector3(x,h+0.12,z),5.4,4.5,2.65,"dark_roof")
            _box(Vector3(x,h+0.7,z+1.2),Vector3(0.75,1.5,1.0),"brick")
            var face:float=x-side*5.3
            for level in [3.5,7.2]:
                for bay in [-2.4,1.8]:
                    _box(Vector3(face-side*0.12,level,z+bay),Vector3(0.16,2.1,1.4),"glass")
                    _box(Vector3(face-side*0.24,level,z+bay),Vector3(0.18,0.15,1.6),"sandstone")
            _box(Vector3(face-side*0.18,1.42,z),Vector3(0.15,2.82,1.4),"boards")
    for i in range(10):
        var z:float=-45.0+float(i)*7.7
        _cylinder(Vector3(76.3,1.3,z),0.09,2.55,"bronze")
        _box(Vector3(76.3,2.65,z),Vector3(0.48,0.56,0.50),"bronze")
