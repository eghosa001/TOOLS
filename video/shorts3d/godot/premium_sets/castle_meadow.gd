extends RefCounted
## Reusable photographic-HDRI castle grounds built exclusively from PREBUILT
## artist-made Kenney CC0 GLB meshes. No new castle or character meshes.
## Reusable in many editor-directed shorts; intentionally deterministic.
##
## Godot 4.7.2. Not a video editor and not a quality sign-off.

const GRASS_SOURCE := "res://assets/nature__grass-large.glb"
const WILD_GRASS_SOURCE := "res://assets/nature__grass-leafs.glb"
const BUSH_SOURCE := "res://assets/nature__plant-bushdetailed.glb"
const TREE_SOURCE := "res://assets/nature__tree-detailed.glb"
const TREE_OAK_SOURCE := "res://assets/nature__tree-oak.glb"
const ROCK_SOURCE := "res://assets/nature__rock-largea.glb"
const PATH_SOURCE := "res://assets/nature__ground-pathstraight.glb"
const GROUND_HEIGHT := -0.45

static func _first_mesh(node: Node) -> MeshInstance3D:
    if node is MeshInstance3D and node.mesh != null:
        return node as MeshInstance3D
    for child in node.get_children():
        var result := _first_mesh(child)
        if result != null:
            return result
    return null

static func _read_glb(path: String) -> PackedScene:
    var p = load(path)
    if p == null or not p is PackedScene:
        push_error("MISSING_LICENSED_GROUNDS_MODEL " + path)
        return null
    return p as PackedScene

static func _meadow_ok(x: float,z: float) -> bool:
    # Untrampled castle masonry and the front gate remain clean and walkable.
    if absf(x) < 31.0 and absf(z) < 31.0:
        return false
    if -67.0 < z and z < -29.0 and absf(x) < 10.0:
        return false
    # Keep the camera approach open, avoiding distracting foreground silhouettes.
    if z < -60.0 and absf(x) < 19.0:
        return false
    return true

static func _green_material(original: Material) -> Material:
    if original is BaseMaterial3D:
        var green: BaseMaterial3D = original.duplicate() as BaseMaterial3D
        # Multiply the ORIGINAL licensed texture/vertex colour: retain the
        # detailed imported Kenney mesh, wood trunks and alpha cut-outs.
        green.albedo_color = green.albedo_color * Color(0.82,0.97,0.16)
        return green
    return original

static func _colourize_tree(node: Node) -> void:
    if node is MeshInstance3D:
        var vis: MeshInstance3D = node as MeshInstance3D
        for surface_index in range(vis.mesh.get_surface_count()):
            var original := vis.get_active_material(surface_index)
            if original != null:
                vis.set_surface_override_material(surface_index,_green_material(original))
    for child in node.get_children():
        _colourize_tree(child)

static func _scatter_mesh(stage: Node3D, source: PackedScene, name: String, count: int,seed: int,
        region: Rect2, min_scale: float, max_scale: float) -> int:
    var prototype := source.instantiate()
    stage.add_child(prototype)
    var node := _first_mesh(prototype)
    if node == null:
        push_error("LICENSED_SOURCE_HAS_NO_MESH "+name)
        prototype.queue_free()
        return -1
    var source_mesh: Mesh = node.mesh.duplicate()
    if source_mesh is ArrayMesh:
        for material_index in range(source_mesh.get_surface_count()):
            var original_mat := node.get_active_material(material_index)
            if original_mat != null:
                (source_mesh as ArrayMesh).surface_set_material(material_index,_green_material(original_mat))
    var local_correction: Transform3D = prototype.global_transform.affine_inverse() * node.global_transform
    var rng := RandomNumberGenerator.new()
    rng.seed = seed
    var multimesh := MultiMesh.new()
    multimesh.transform_format = MultiMesh.TRANSFORM_3D
    multimesh.mesh = source_mesh
    multimesh.instance_count = count
    var complete := 0
    var attempts := 0
    while complete < count and attempts < count * 14:
        attempts += 1
        var x := rng.randf_range(region.position.x,region.end.x)
        var z := rng.randf_range(region.position.y,region.end.y)
        if not _meadow_ok(x,z):
            continue
        var size := rng.randf_range(min_scale,max_scale)
        var base := Transform3D(Basis(Vector3.UP,rng.randf_range(0,TAU)).scaled(Vector3.ONE*size),
                                Vector3(x,GROUND_HEIGHT,z))
        multimesh.set_instance_transform(complete,base * local_correction)
        complete += 1
    multimesh.visible_instance_count = complete
    var result := MultiMeshInstance3D.new()
    result.name = name
    result.multimesh = multimesh
    # Individual tiny blades should not produce harsh dark hard shadows.
    result.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    stage.add_child(result)
    prototype.queue_free()
    print("REUSED_LICENSED_FOLIAGE",name,complete,"distinct placements from",source.resource_path)
    return complete

static func _spawn(stage: Node3D, source: PackedScene, name: String,pos: Vector3,
        scale: float,rotation_y: float=0.0) -> void:
    var model := source.instantiate() as Node3D
    model.name = name
    model.position = pos
    model.scale = Vector3.ONE * scale
    model.rotation.y = rotation_y
    stage.add_child(model)
    if name.begins_with("Forest_") or name.begins_with("Side_"):
        _colourize_tree(model)

static func _forest(stage: Node3D, tree: PackedScene, oak: PackedScene) -> int:
    var rng := RandomNumberGenerator.new()
    rng.seed = 12041204
    var placed := 0
    # Three depth bands create recognizable forest beyond both sides of
    # the castle; individual tree models are still authentic Kenney originals.
    for band in range(3):
        for i in range(19):
            var x := -104.0 + float(i)*11.2 + rng.randf_range(-3.8,3.8)
            var z: float = float([38.0,58.0,81.0][band]) + rng.randf_range(-8.0,8.0)
            if absf(x)<32.0 and z<40.0:continue
            var source: PackedScene = oak if (i+band)%3==0 else tree
            _spawn(stage,source,"Forest_%d_%02d" %[band,i],
                Vector3(x,GROUND_HEIGHT,z),rng.randf_range(6.3,10.0),rng.randf_range(-PI,PI))
            placed+=1
    # Visible side grove, in frame without hiding the approach.
    for side in [-1,1]:
        for i in range(13):
            var x: float = float(side) * (37.0 + float(i%4)*7.0+rng.randf_range(-2,2))
            var z := -64.0+float(i)*6.0+rng.randf_range(-4,4)
            _spawn(stage,tree,"Side_%d_%02d" %[side,i],
                Vector3(x,GROUND_HEIGHT,z),rng.randf_range(6.5,10.3),rng.randf_range(-PI,PI))
            placed+=1
    return placed

static func _rocks(stage: Node3D, source: PackedScene) -> int:
    var rng := RandomNumberGenerator.new()
    rng.seed = 10661204
    var placed := 0
    for i in range(48):
        var x := rng.randf_range(-80.0,80.0)
        var z := rng.randf_range(-74.0,66.0)
        if not _meadow_ok(x,z):continue
        _spawn(stage,source,"Stone_%02d" %i,Vector3(x,GROUND_HEIGHT,z),
            rng.randf_range(0.8,2.5),rng.randf_range(0,TAU))
        placed+=1
    return placed

static func _path(stage: Node3D, source: PackedScene) -> int:
    # Readable existing terrain pieces, close to the front gate but NOT inside it.
    for i in range(11):
        _spawn(stage,source,"Path_%02d" %i,
            Vector3(0.0,GROUND_HEIGHT+0.015,-31.0-3.2*float(i)),1.6,0)
    return 11

static func install(parent: Node3D, settings: Dictionary={}) -> Dictionary:
    if str(settings.get("preset","")) != "castle_meadow_v1":
        push_error("Unknown castle grounds preset")
        return {"valid":false}
    var grass := _read_glb(GRASS_SOURCE)
    var wild := _read_glb(WILD_GRASS_SOURCE)
    var bush := _read_glb(BUSH_SOURCE)
    var tree := _read_glb(TREE_SOURCE)
    var oak := _read_glb(TREE_OAK_SOURCE)
    var rock := _read_glb(ROCK_SOURCE)
    var path := _read_glb(PATH_SOURCE)
    if grass==null or wild==null or bush==null or tree==null or oak==null or rock==null or path==null:
        return {"valid":false}
    var stage := Node3D.new()
    stage.name="Reusable_Kenney_CC0_Castle_Meadow_v1"
    parent.add_child(stage)
    var result := {
        "grass":_scatter_mesh(stage,grass,"LicensedGrass",4500,20261103,
                   Rect2(-78,-85,156,180),1.6,3.2),
        "wildgrass":_scatter_mesh(stage,wild,"LicensedWildGrass",1100,20261105,
                   Rect2(-69,-80,138,156),1.5,2.8),
        "bushes":_scatter_mesh(stage,bush,"LicensedBushes",210,20261104,
                   Rect2(-81,-80,162,169),1.3,2.7),
        "trees":_forest(stage,tree,oak),
        "rocks":_rocks(stage,rock),
        "path":0,
        "valid":true,
        "license":"CC0 Kenney original",
        "provenance":"pack_index.json"
    }
    if result["grass"] < 0 or result["wildgrass"] < 0 or result["bushes"] < 0:
        result["valid"]=false
    print("CASTLE_MEADOW_SET_READBACK",JSON.stringify(result))
    return result
