extends Node3D
## Hand-directed physical action stage for original 64s history Shorts.
## Each 5/6 second beat has a specific licensed asset set and a physically visible event.
## All camera and actor paths are human-authored; no narration-to-visual automation.

var studio: Node3D
var topic: String
var stages: Array = []
var cameras: Array = []
var movers: Array = []
var seconds_by_shot: Array = []
var current_index := -1

func setup(parent: Node3D, scene_topic: String, shots: Array) -> void:
    studio = parent
    topic = scene_topic
    for index in range(shots.size()):
        var root := Node3D.new()
        root.name = "HAND_DIRECTED_" + str(shots[index].get("id",index))
        root.position = Vector3(float(index+1)*400.0, 0, 550.0)
        add_child(root)
        stages.append(root)
        seconds_by_shot.append(Vector2(float(shots[index]["start_seconds"]), float(shots[index]["end_seconds"])))
        _build(root,index)
        root.visible=false
    print("PHYSICAL_STORYBOARD_ACTION_STAGES",topic,stages.size(),"props",movers.size())

func _box(root: Node3D,p:Vector3, dimensions:Vector3, material:String) -> MeshInstance3D:
    return studio._box(p,dimensions,material,root)
func _cyl(root: Node3D,p:Vector3,r:float,h:float,m:String,rotation:Vector3=Vector3.ZERO) -> MeshInstance3D:
    return studio._cylinder(p,r,h,m,rotation,root)
func _ball(root:Node3D,p:Vector3,r:float,m:String)->MeshInstance3D:
    return studio._sphere(p,r,m,root)
func _beam(root:Node3D,a:Vector3,b:Vector3,width:float,mat:String)->Node3D:
    return studio._beam(a,b,width,mat,root)
func _roof(root:Node3D,c:Vector3,hx:float,hz:float,rise:float,mat:String)->void:
    studio._gable_roof(c,hx,hz,rise,mat,root)
func _prop(root:Node3D,identity:String,p:Vector3,scale:float=1.0)->Node3D:
    var file:String="res://assets/props/"+identity+".glb"
    var src:PackedScene=load(file) as PackedScene
    if src==null:
        push_error("REQUIRED_LICENSED_CC0_HERO_PROP_MISSING:"+file)
        return Node3D.new()
    var obj:Node3D=src.instantiate()
    obj.position=p
    obj.scale=Vector3.ONE*scale
    root.add_child(obj)
    return obj

func _ground(root:Node3D,material:String="grass") -> void:
    _box(root,Vector3(0,-0.34,0),Vector3(220,0.55,220),material)
func _caption3(root:Node3D,message:String,pos:Vector3,size:int=70) -> void:
    var text3:=Label3D.new()
    text3.text=message
    text3.font_size=size
    text3.pixel_size=0.010
    text3.modulate=Color("#f5efd6")
    text3.outline_size=14
    text3.billboard=BaseMaterial3D.BILLBOARD_ENABLED
    text3.position=pos
    root.add_child(text3)
func _hut(root:Node3D,where:Vector3,wall:String="plaster",roof:String="roof") -> Node3D:
    var house:=Node3D.new()
    house.position=where
    root.add_child(house)
    # Reuse an entire authored CC0 medieval home for recognisable period-like
    # construction instead of a plain plaster box and triangular roof.
    if topic=="london":
        var cottage:PackedScene=load("res://assets/props/forge__models__kaykit-medieval-hexagon__building-home-a-red.glb") as PackedScene
        if cottage!=null:
            var building:Node3D=cottage.instantiate()
            building.scale=Vector3.ONE*4.2
            house.add_child(building)
            return house
    _box(house,Vector3(0,3,0),Vector3(7,6,8),wall)
    _roof(house,Vector3(0,6.15,0),3.85,4.35,2.15,roof)
    for side in [-1.0,1.0]:
        for z in [-3.9,0.0,3.9]:
            _box(house,Vector3(side*3.58,3,z),Vector3(0.27,6.0,0.3),"oak")
        for y in [1.0,4.8]:
            _box(house,Vector3(side*3.65,y,0),Vector3(0.24,0.26,8),"oak")
    _box(house,Vector3(0,1.35,-4.05),Vector3(1.7,2.7,0.12),"boards")
    _box(house,Vector3(2.15,4.4,-4.08),Vector3(0.8,0.95,0.12),"black")
    return house
func _village(root:Node3D,num:int=6) -> void:
    # Dense timber-fronted city with multiple streets, not isolated huts
    # on an empty grass field.
    for i in range(num):
        var col:int=i%4
        var row:int=int(i/4)
        var x:float= -34.0 + float(col)*23.0
        var z:float= -28.0 + float(row)*13.5
        var home:=_hut(root,Vector3(x,0,z),"plaster" if i%3 else "brick","roof" if i%2 else "dark_roof")
        home.rotation.y=(0.06 if col<2 else -0.06)
    _box(root,Vector3(0,0.015,-2),Vector3(11,0.06,75),"street")
func _wall(root:Node3D,broken:bool=false,with_moat:bool=true) -> void:
    # Layered and visibly separate land-wall system. The local breach is genuine open space.
    if with_moat:
        _box(root,Vector3(0,-0.09,-16),Vector3(88,0.19,9),"water")
        _box(root,Vector3(0,0.0,-21),Vector3(88,0.27,1.0),"sandstone")
    if broken:
        for sx in [-1.0,1.0]:
            _box(root,Vector3(sx*23,4.1,11),Vector3(34,8.2,3.8),"castle")
            _box(root,Vector3(sx*23,8.8,24),Vector3(34,17.6,5.2),"stone")
        for i in range(19):
            var x:float=sin(float(i)*1.74)*6
            var z:float=6+cos(float(i)*2.1)*6
            var rubble:=_box(root,Vector3(x,0.33+float(i%3)*0.23,z),Vector3(0.8+float(i%4)*0.35,0.6,1.2),"stone")
            rubble.rotation_degrees.y=float(i*29)
    else:
        _box(root,Vector3(0,4.1,11),Vector3(78,8.2,3.8),"castle")
        _box(root,Vector3(0,8.8,24),Vector3(80,17.6,5.2),"stone")
    for x in [-37.0,-22.0,22.0,37.0]:
        _box(root,Vector3(x,6.2,11),Vector3(7,12.4,6.8),"castle")
        _box(root,Vector3(x,11.1,24),Vector3(8,22.2,8),"stone")
        for j in range(3):
            _box(root,Vector3(x-2.5+float(j)*2.5,22.6,24),Vector3(1.2,1.5,1.5),"stone")
    for x in range(-39,40,5):
        if broken and abs(x)<7:continue
        _box(root,Vector3(float(x),9.0,11),Vector3(2.6,1.4,2.4),"castle")
        _box(root,Vector3(float(x),18.0,24),Vector3(2.7,1.6,2.6),"stone")
    # Relief bricks are pooled in a single multimesh; no thousands of nodes,
    # while the wall actually reads as masonry at 720p instead of a flat panel.
    _surface_masonry(root,11.0,8.2,9.05,broken,"castle")
    _surface_masonry(root,24.0,17.6,21.35,broken,"stone")

func _surface_masonry(root:Node3D,wall_depth:float,height:float,face_z:float,broken:bool,material:String)->void:
    var transforms:Array[Transform3D]=[]
    var rows:int=int(height/0.72)
    var cols:int=71
    for row in range(rows):
        for col in range(cols):
            var x:float=-38.5+float(col)*1.09 + (0.52 if row%2==1 else 0.0)
            if broken and absf(x)<6.5:
                continue
            var y:float=0.32+float(row)*0.72
            var noise:float=sin(float(col)*31.73+float(row)*11.27)
            var p:=Vector3(x,y,face_z-0.16+0.035*noise)
            transforms.append(Transform3D(Basis.IDENTITY,p))
    var block:=BoxMesh.new()
    block.size=Vector3(1.06,0.67,0.22)
    block.material=studio.mats[material] as Material
    var collection:=MultiMesh.new()
    collection.transform_format=MultiMesh.TRANSFORM_3D
    collection.mesh=block
    collection.instance_count=transforms.size()
    for i in range(transforms.size()):
        collection.set_instance_transform(i,transforms[i])
    var surface:=MultiMeshInstance3D.new()
    surface.multimesh=collection
    root.add_child(surface)
func _actor(root:Node3D,at:Vector3,move_to:Vector3=Vector3.INF,style:String="civilian",animation:String="Walking_A",start:float=0.05,end:float=0.96) -> Node3D:
    var key: String="knight" if style=="soldier" else "rogue"
    var pack:PackedScene=load("res://assets/prebuilt/"+key+".glb") as PackedScene
    if pack==null:
        push_error("MISSING_VERIFIED_CC0_ANIMATED_ACTOR:"+key)
        return Node3D.new()
    var rig:=pack.instantiate() as Node3D
    rig.position=at
    rig.scale=Vector3.ONE*(1.6 if style=="soldier" else 1.65)
    root.add_child(rig)
    var player:AnimationPlayer=rig.find_child("AnimationPlayer",true,false) as AnimationPlayer
    if player!=null:
        var candidate:String=animation
        if not player.has_animation(candidate):
            candidate="Idle"
        player.play(candidate)
    if move_to!=Vector3.INF:
        _move(rig,at,move_to,"translate",start,end)
        rig.rotation.y=atan2(move_to.x-at.x,move_to.z-at.z)
    return rig
func _move(node:Node3D,a:Vector3,b:Vector3,kind:String="translate",start:float=0.0,end:float=1.0) -> void:
    movers.append({"node":node,"a":a,"b":b,"kind":kind,"from":start,"to":end,"index":stages.size()-1})
func _fire(root:Node3D,at:Vector3,shot:int,scale:float=1.0,delay:float=0.0)->void:
    # Genuine licensed 64-frame Brackeys flame flipbook; independent visible fire at every actual ignition.
    studio._fire_at(root.position+at, float(shot)*3.0+delay,scale)
func _boat(root:Node3D,pos:Vector3)->Node3D:
    var n:=Node3D.new()
    n.position=pos
    root.add_child(n)
    studio._boat_hull(n)
    _cyl(n,Vector3(0,4.4,0.3),0.12,4.3,"oak")
    _beam(n,Vector3(-2.7,5.7,0.3),Vector3(2.7,5.7,0.3),0.16,"oak")
    _box(n,Vector3(0,6.0,0.4),Vector3(5.2,0.55,0.7),"boards")
    for side in [-1.0,1.0]:
        for j in range(5):
            var dz:float=-3.5+float(j)*1.6
            _beam(n,Vector3(side*1.55,2.0,dz),Vector3(side*4.0,1.35,dz-0.8),0.12,"oak")
    return n
func _spark_arc(root:Node3D,a:Vector3,b:Vector3,count:int,kind:String="embers")->void:
    for i in range(count):
        var dot:=_ball(root,a,0.13 if kind=="water" else 0.09,kind)
        movers.append({"node":dot,"a":a,"b":b,"kind":"arc","phase":float(i)/float(count),"index":stages.size()-1,"from":0.0,"to":1.0})
func _pour_water(root:Node3D,begin:Vector3,hit:Vector3)->void:
    # Translucent continuous water ribbon, replacing the former rigid
    # dotted blue bead chain. Discrete drops exist only at the impact.
    var stream_material:=StandardMaterial3D.new()
    stream_material.albedo_color=Color(0.57,0.85,0.95,0.65)
    stream_material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
    stream_material.roughness=0.13
    stream_material.cull_mode=BaseMaterial3D.CULL_DISABLED
    var surface:=SurfaceTool.new()
    surface.begin(Mesh.PRIMITIVE_TRIANGLES)
    var last_left:=Vector3.ZERO
    var last_right:=Vector3.ZERO
    for i in range(27):
        var t:float=float(i)/26.0
        var p:Vector3=begin.lerp(hit,t)+Vector3(0,2.0*sin(t*PI),0)
        var w:float=0.15*(1.0-0.55*t)
        var left:Vector3=p+Vector3(-w,0,w*0.2)
        var right:Vector3=p+Vector3(w,0,-w*0.2)
        if i>0:
            for vertex in [last_left,last_right,right,last_left,right,left]:
                surface.set_uv(Vector2(t,0))
                surface.add_vertex(vertex)
        last_left=left
        last_right=right
    surface.generate_normals()
    var water_mesh:=MeshInstance3D.new()
    water_mesh.mesh=surface.commit()
    water_mesh.material_override=stream_material
    root.add_child(water_mesh)
    for i in range(12):
        var angle:float=float(i)*2.3999
        var splash:MeshInstance3D=_ball(root,hit+Vector3(0.4*cos(angle),0.25+float(i%3)*0.25,0.5*sin(angle)),0.065,"water")
        var outward:Vector3=splash.position+Vector3(cos(angle)*0.8,0.4+float(i%3)*0.3,sin(angle)*0.8)
        _move(splash,splash.position,outward,"splash",0.35,0.88)

func _add_chain(root:Node3D,from:Vector3,to:Vector3,num:int=24)->void:
    for i in range(num):
        var m:=MeshInstance3D.new()
        var tor:=TorusMesh.new()
        tor.inner_radius=0.25
        tor.outer_radius=0.42
        tor.rings=9
        tor.ring_segments=12
        m.mesh=tor
        m.material_override=studio.mats["bronze_edge"]
        m.position=from.lerp(to,float(i)/float(num-1))
        m.rotation_degrees=Vector3(0,float(i%2)*90,90)
        root.add_child(m)
func _frame_camera(root:Node3D,start:Vector3,finish:Vector3,target:Vector3,far:float=53.0)->void:
    cameras.append({"from":start,"to":finish,"at":target,"fov":far})

func _build(root:Node3D,i:int)->void:
    if topic=="london":
        _london(root,i)
    else:
        _constantinople(root,i)

func _decorate(root:Node3D,index:int)->void:
    # Reference-driven set dressing: actual CC0 3D tree models, not fake billboards.
    # Distant trees/structures leave the featured physical event unobstructed.
    for j in range(15):
        var kind:String="nature__tree-oak" if j%3==0 else "nature__tree-default"
        var pack:PackedScene=load("res://assets/prebuilt/"+kind+".glb") as PackedScene
        if pack==null:
            push_error("MISSING_LICENSED_BACKGROUND_TREE:"+kind)
            continue
        var tree:Node3D=pack.instantiate()
        var x:float=(-46.0-float(j%4)*2.5) if j%2==0 else (44.0+float(j%4)*3.0)
        var z:float=-45.0+float((j*11)%85)
        tree.position=Vector3(x,0,z)
        tree.scale=Vector3.ONE*(7.0+float(j%3)*1.7)
        tree.rotation.y=float(j*43)*PI/180.0
        studio._tint_imported_leaf_materials(tree)
        root.add_child(tree)
    if topic=="london" and index in [1,4,5,6,7,9,11]:
        for j in range(5):
            var a:float=-38.0+float(j)*19.0
            _hut(root,Vector3(a,0,33),"plaster" if j%2 else "brick","dark_roof")
        # A second row adds depth without scattering unrelated buildings across water.
        if index not in [4,7]:
            for j in range(3):
                _hut(root,Vector3(-42+float(j)*40,0,-38),"plaster","roof")
    if topic=="constantinople" and index in [2,3,4,9,10]:
        for j in range(5):
            var ox:float=-46.0+float(j)*23.0
            _box(root,Vector3(ox,0.5,39),Vector3(7,1,9),"sandstone")
            _roof(root,Vector3(ox,1.1,39),3.5,4.5,2.5,"boards")

func _london(root:Node3D,i:int) -> void:
    _ground(root,"grass")
    _decorate(root,i)
    match i:
        0:
            _village(root,28)
            _fire(root,Vector3(14,8,-5),i,1.35,0.9)
            _fire(root,Vector3(16,8,7),i,1.30,1.4)
            _frame_camera(root,Vector3(44,39,-49),Vector3(35,34,-36),Vector3(0,5,-1),55)
        1:
            _village(root,4)
            _box(root,Vector3(0,1.7,-6.0),Vector3(4.8,3.4,2.6),"brick")
            _box(root,Vector3(0,1.0,-7.4),Vector3(2.4,2.0,0.25),"black")
            _box(root,Vector3(0,2.3,-7.6),Vector3(3.1,0.5,0.4),"brick")
            _caption3(root,"PUDDING LANE",Vector3(0,4.5,-7.9),50)
            _prop(root,"forge__models__kaykit-medieval-hexagon__barrel",Vector3(4,0.0,-7.1),2.2)
            _fire(root,Vector3(1,3.2,-6),i,1.20,0.65)
            _frame_camera(root,Vector3(14,8,-19),Vector3(11,7,-14),Vector3(0,3.5,-6),48)
        2:
            _village(root,28)
            _frame_camera(root,Vector3(0,7,-35),Vector3(0,6,-27),Vector3(0,5,7),48)
        3:
            _village(root,24)
            _fire(root,Vector3(-14,8,-12),i,1.25,0.0)
            _fire(root,Vector3(14,8,-4),i,1.3,1.3)
            _spark_arc(root,Vector3(-13,10,-12),Vector3(14,9,-4),24)
            _frame_camera(root,Vector3(27,24,-32),Vector3(23,22,-27),Vector3(0,9,-5),49)
        4:
            _box(root,Vector3(0,0.08,-24),Vector3(120,0.16,36),"water")
            for j in range(3):
                _hut(root,Vector3(-15+float(j)*13,0,12),"brick","dark_roof")
                _cyl(root,Vector3(-17+float(j)*13,0.6,5),0.6,1.2,"boards")
            _boat(root,Vector3(2,-0.15,-19))
            _fire(root,Vector3(0,8,12),i,1.45,0.2)
            _frame_camera(root,Vector3(21,13,-33),Vector3(19,12,-27),Vector3(-4,4,1),51)
        5:
            _hut(root,Vector3(14,0,7))
            _fire(root,Vector3(14,7,7),i,1.35,0)
            for j in range(5):
                _actor(root,Vector3(0.5+float(j)*2.6,0,-5),Vector3(1.8+float(j)*2.6,0,-3),"civilian","Interact")
                _prop(root,"forge__models__kaykit-medieval-hexagon__bucket-water",Vector3(0.5+float(j)*2.6,0.85,-3.5),1.7)
            _pour_water(root,Vector3(10,2.7,-4),Vector3(14,7,6))
            _frame_camera(root,Vector3(22,8,-20),Vector3(18,7,-17),Vector3(9,4,1),51)
        6:
            _village(root,4)
            _fire(root,Vector3(14,8,2),i,1.4)
            for j in range(3):
                _actor(root,Vector3(-12+float(j)*3,0,-5),Vector3(-11+float(j)*3,0,-4),"civilian","Interact")
                _beam(root,Vector3(-10+float(j)*3,1.8,-4),Vector3(0,9,1.5),0.19,"oak")
            var panel:=Node3D.new()
            panel.position=Vector3(0,0.2,1.5)
            root.add_child(panel)
            _box(panel,Vector3(0,5.0,0),Vector3(7.2,10.0,0.45),"boards")
            _move(panel,Vector3(0,0.2,1.5),Vector3(0,0.2,1.5),"collapse",0.28,0.86)
            _frame_camera(root,Vector3(17,11,-19),Vector3(14,9,-16),Vector3(0,5,1),50)
        7:
            _box(root,Vector3(0,0,-20),Vector3(110,0.18,32),"water")
            _boat(root,Vector3(-14,-0.3,-19))
            for j in range(6):
                var start=Vector3(-11+float(j)*3,0,10+float(j%2)*3)
                var ending=Vector3(-12+float(j)*2.5,0,-9)
                _actor(root,start,ending,"civilian","Running_A",0.10,0.92)
                _box(root,start+Vector3(0,1.5,0.8),Vector3(0.65,0.6,0.52),"boards")
            _frame_camera(root,Vector3(18,8,-26),Vector3(14,7,-20),Vector3(-6,2,-8),55)
        8:
            _cathedral(root)
            _fire(root,Vector3(0,23,5),i,2.2,0.6)
            _fire(root,Vector3(10,21,5),i,1.5,0.9)
            _frame_camera(root,Vector3(37,31,-48),Vector3(31,30,-39),Vector3(0,13,3),55)
        9:
            _hut(root,Vector3(-22,0,8))
            _hut(root,Vector3(24,0,8))
            _fire(root,Vector3(-22,7,8),i,1.5)
            for j in range(13):
                var x:float=-9+float(j%5)*4
                _box(root,Vector3(x,0.3,8+float(j%3)*2.3),Vector3(2.6,0.7,1.5),"stone")
            _caption3(root,"FIREBREAK",Vector3(0,4,-1),58)
            _frame_camera(root,Vector3(37,24,-37),Vector3(30,20,-29),Vector3(0,5,5),53)
        10:
            for j in range(18):
                var x:float=-26+float(j%6)*11
                var z:float=-23+float(int(j/6))*13
                _box(root,Vector3(x,0.8,z),Vector3(8.3,1.6,8),"stone")
                for k in range(3):
                    _box(root,Vector3(x-2+float(k)*2,1.7,z+1.2),Vector3(1.3,0.7,1.3),"black")
            _prop(root,"forge__models__kaykit-medieval-hexagon__building-destroyed",Vector3(-24,0,-22),4.5)
            _caption3(root,"13,200 HOUSES  •  87 CHURCHES",Vector3(0,14,6),50)
            _frame_camera(root,Vector3(36,38,-36),Vector3(31,34,-31),Vector3(0,3,3),54)
        11:
            _prop(root,"forge__models__kaykit-medieval-hexagon__building-scaffolding",Vector3(-13,0,8),5.0)
            for j in range(5):
                var x:float=-20+float(j)*10
                _box(root,Vector3(x,4,6),Vector3(7.5,8,7),"brick" if j%2 else "stone")
                for h in range(3):
                    _box(root,Vector3(x-2.1+float(h)*2.0,5.2,2.4),Vector3(1.1,1.6,0.15),"black")
                if j<3:
                    var lift:=_box(root,Vector3(x,0.7,-5),Vector3(1.7,1.2,1.6),"stone")
                    _move(lift,Vector3(x,0.7,-5),Vector3(x,7.9,4.0),"translate",0.16,0.84)
                _actor(root,Vector3(x-2,0,-7),Vector3(x-1.5,0,-5),"civilian","Interact")
            _frame_camera(root,Vector3(23,12,-25),Vector3(18,10,-19),Vector3(0,5,3),50)

func _cathedral(root:Node3D)->void:
    # Broad Gothic nave; not anachronistic present-day dome or spire.
    _box(root,Vector3(0,11,5),Vector3(23,22,42),"stone")
    _roof(root,Vector3(0,22,5),12.5,22.5,8.0,"dark_roof")
    for side in [-1.0,1.0]:
        _box(root,Vector3(side*14,7,4),Vector3(5,14,29),"sandstone")
        _box(root,Vector3(side*9.0,18,-15),Vector3(6,36,8),"stone")
        _box(root,Vector3(side*9.0,37,-15),Vector3(6.5,2,8.3),"sandstone")
        for j in range(3):
            _box(root,Vector3(side*9.0,40,-17+float(j)*2),Vector3(1.5,3,1.5),"stone")
    for x in [-5.0,0.0,5.0]:
        _box(root,Vector3(x,12,-16.5),Vector3(1.5,11.0,0.2),"black")

func _constantinople(root:Node3D,i:int)->void:
    _ground(root,"grass")
    _decorate(root,i)
    match i:
        0:
            _wall(root,false,true)
            _box(root,Vector3(36,0.05,38),Vector3(36,0.10,50),"water")
            for j in range(11):
                _hut(root,Vector3(-24+float(j%5)*13.0,0,35+float(int(j/5))*11),"sandstone","dark_roof")
            _frame_camera(root,Vector3(37,46,-48),Vector3(32,42,-41),Vector3(0,10,12),53)
        1:
            _wall(root,false,true)
            _frame_camera(root,Vector3(16,24,-35),Vector3(12,20,-27),Vector3(0,8,13),51)
        2:
            _wall(root,false,false)
            _prop(root,"forge__models__kaykit-medieval-hexagon__building-scaffolding",Vector3(-34,0,-25),3.5)
            for j in range(7):
                var x:float=-29+float(j)*10
                var tent:=_hut(root,Vector3(x,0,-38),"boards","boards")
                tent.scale=Vector3.ONE*0.55
                _actor(root,Vector3(x+3,0,-27),Vector3(x+3,0,-24),"soldier","Walking_A")
            _cannon(root,Vector3(-4,0,-23))
            _frame_camera(root,Vector3(25,13,-46),Vector3(19,12,-35),Vector3(0,5,-15),50)
        3:
            _wall(root,true,false)
            _cannon(root,Vector3(1,0,-18))
            _fire(root,Vector3(1,2,-21),i,0.75,0.1)
            # The central slab hides the breach until the cannonball impact.
            var slab:MeshInstance3D=_box(root,Vector3(0,5.7,10.5),Vector3(11.3,11.4,3.9),"castle")
            _move(slab,slab.position,slab.position,"shatter",0.0,1.0)
            var ball: MeshInstance3D=_ball(root,Vector3(0,3,-14),0.92,"black")
            _move(ball,Vector3(0,3,-14),Vector3(0,11,10),"projectile",0.28,0.68)
            _spark_arc(root,Vector3(0,2.7,-20),Vector3(0,6,-14),15)
            for j in range(5):
                var rock:=_box(root,Vector3(-4+float(j)*2,5,11),Vector3(1.6,1.25,1.9),"stone")
                _move(rock,rock.position,Vector3(-8+float(j)*4,0.5,0),"translate",0.55,0.86)
            _frame_camera(root,Vector3(12,8,-28),Vector3(9,7,-24),Vector3(0,4,-10),53)
        4:
            _wall(root,true,false)
            _prop(root,"forge__models__kaykit-medieval-hexagon__building-scaffolding",Vector3(0,0,9),4.8)
            for j in range(5):
                _actor(root,Vector3(-7+float(j)*3,0,4),Vector3(-6+float(j)*3,0,8),"soldier","Interact")
                _beam(root,Vector3(-10+float(j)*5,0.2,15),Vector3(-10+float(j)*5,7,16),0.26,"boards")
            var stone: MeshInstance3D=_box(root,Vector3(0,0.7,12),Vector3(6,1.5,2),"sandstone")
            _move(stone,Vector3(0,0.7,12),Vector3(0,5.5,12),"translate",0.18,0.85)
            _frame_camera(root,Vector3(17,12,-19),Vector3(13,10,-14),Vector3(0,5,10),51)
        5:
            _harbor(root)
            _add_chain(root,Vector3(-26,1.7,0),Vector3(26,1.7,0),80)
            _boat(root,Vector3(-14,0,-20))
            _boat(root,Vector3(16,0,-21))
            _frame_camera(root,Vector3(18,13,-27),Vector3(15,11,-22),Vector3(0,1,-3),53)
        6:
            _harbor(root)
            _box(root,Vector3(0,1.25,0),Vector3(20,2.8,50),"grass")
            _boat(root,Vector3(-16,3,0))
            var land_boat:=_boat(root,Vector3(0,3,3))
            _move(land_boat,Vector3(0,3,3),Vector3(0,3,-8),"translate",0.10,0.95)
            _frame_camera(root,Vector3(38,33,-38),Vector3(29,25,-29),Vector3(0,2,0),51)
        7:
            _box(root,Vector3(0,1,0),Vector3(115,2.2,120),"grass")
            for j in range(8):
                _cyl(root,Vector3(0,2.3,-21+float(j)*5),0.55,6,"boards",Vector3(0,0,90))
            var galley:=_boat(root,Vector3(0,3.1,-10))
            _move(galley,Vector3(0,3.1,-10),Vector3(0,3.1,7),"translate",0.07,0.96)
            for j in range(6):
                _actor(root,Vector3(-10+float(j%2)*20,0.9,-16+float(int(j/2))*7),Vector3(-10+float(j%2)*20,0.9,-8+float(int(j/2))*7),"soldier","Walking_A")
                _beam(root,Vector3(-9+float(j%2)*18,2,-11+float(int(j/2))*7),Vector3(-2+float(j%2)*4,4,-11+float(int(j/2))*7),0.11,"oak")
            _frame_camera(root,Vector3(18,9,-24),Vector3(14,8,-19),Vector3(0,3,-3),52)
        8:
            _harbor(root)
            var boat: Node3D=_boat(root,Vector3(0,0,-16))
            _move(boat,Vector3(0,0,-16),Vector3(0,0,11),"translate",0.08,0.92)
            for j in range(3):
                _actor(root,Vector3(-23+float(j)*7,0,25),Vector3(-22+float(j)*7,0,22),"soldier","Cheer")
            _frame_camera(root,Vector3(18,10,-28),Vector3(15,9,-21),Vector3(0,2,-2),52)
        9:
            _wall(root,true,false)
            for j in range(9):
                _actor(root,Vector3(-9+float(j%3)*7,0,-23+float(int(j/3))*5),Vector3(-7+float(j%3)*7,0,7+float(int(j/3))*4),"soldier","Running_A",0.02,0.97)
            _frame_camera(root,Vector3(13,10,-25),Vector3(10,9,-19),Vector3(0,5,7),50)
        10:
            _wall(root,true,false)
            for j in range(12):
                _actor(root,Vector3(-11+float(j%4)*6,0,-25+float(int(j/4))*4),Vector3(-7+float(j%4)*4,0,13),"soldier","Running_A",0.08,0.92)
            _frame_camera(root,Vector3(12,8,-23),Vector3(8,7,-17),Vector3(0,3,8),48)
        11:
            _wall(root,false,false)
            _box(root,Vector3(35,0.10,43),Vector3(35,0.2,39),"water")
            for j in range(13):
                _hut(root,Vector3(-32+float(j%6)*11,0,32+float(int(j/6))*11),"stone","dark_roof")
            _caption3(root,"29 MAY 1453",Vector3(0,29,12),64)
            _frame_camera(root,Vector3(37,43,-44),Vector3(33,39,-36),Vector3(0,8,17),54)

func _cannon(root:Node3D,at:Vector3)->void:
    var pivot:=Node3D.new()
    pivot.position=at
    root.add_child(pivot)
    _box(pivot,Vector3(0,0.7,0),Vector3(3.1,1,4.8),"boards")
    for side in [-1.0,1.0]:
        _cyl(pivot,Vector3(side*1.65,0.85,1.2),0.8,0.3,"oak",Vector3(0,0,90))
    _cyl(pivot,Vector3(0,1.9,0),0.78,5.6,"bronze",Vector3(90,0,0))
    _cyl(pivot,Vector3(0,1.9,-3.0),0.83,0.40,"bronze_edge",Vector3(90,0,0))
func _harbor(root:Node3D)->void:
    _box(root,Vector3(0,0.08,0),Vector3(115,0.19,85),"water")
    for x in [-30.0,30.0]:
        _box(root,Vector3(x,0.32,22),Vector3(5,0.8,47),"sandstone")
        for j in range(5):
            _box(root,Vector3(x,1.9,float(j)*8),Vector3(2.6,2.4,1.1),"castle")

func update_at(t:float)->void:
    var which:int=-1
    for i in range(seconds_by_shot.size()):
        var bounds:Vector2=seconds_by_shot[i]
        if t>=bounds.x and t<bounds.y:
            which=i
            break
    if which<0:
        return
    if which!=current_index:
        for i in range(stages.size()):
            stages[i].visible=(i==which)
        current_index=which
    var shot_bounds:Vector2=seconds_by_shot[which]
    var a:float=clampf((t-shot_bounds.x)/(shot_bounds.y-shot_bounds.x),0.0,1.0)
    for m in movers:
        if int(m["index"])!=which:
            continue
        var n:Node3D=m["node"]
        var k:String=m["kind"]
        var first:Vector3=m["a"]
        var last:Vector3=m["b"]
        var p:float=clampf((a-float(m["from"]))/maxf(0.001,float(m["to"])-float(m["from"])),0.0,1.0)
        if k=="translate":
            n.position=first.lerp(last,p)
        elif k=="collapse":
            n.rotation_degrees.x=87.0*p
        elif k=="projectile":
            n.visible=a>=float(m["from"]) and a<=float(m["to"])
            n.position=first.lerp(last,p)+Vector3(0,5.0*sin(p*PI),0)
        elif k=="splash":
            n.visible=a>=float(m["from"]) and a<=float(m["to"])
            n.position=first.lerp(last,p)+Vector3(0,0.6*sin(p*PI),0)
        elif k=="shatter":
            n.visible=a<0.55
        elif k=="arc":
            var flight:float=fposmod(a*5.0-float(m["phase"]),1.0)
            n.position=first.lerp(last,flight)+Vector3(0,2.0*sin(flight*PI),0)

func camera_at(t:float,camera:Camera3D,caption:Label,shots:Array)->void:
    update_at(t)
    var idx:int=maxi(0,current_index)
    if idx>=cameras.size():return
    var view:Dictionary=cameras[idx]
    var bounds:Vector2=seconds_by_shot[idx]
    var a:float=clampf((t-bounds.x)/(bounds.y-bounds.x),0.0,1.0)
    camera.global_position=stages[idx].global_position+((view["from"] as Vector3).lerp(view["to"],a))
    camera.fov=float(view["fov"])
    camera.look_at(stages[idx].global_position+(view["at"] as Vector3),Vector3.UP)
    caption.text=str(shots[idx]["caption"])
