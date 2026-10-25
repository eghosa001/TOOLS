extends Node3D
## Reusable CC0 asset and original-cast look-development scene.
## The pipeline does not automatically convert arbitrary prose into a 3D animation.

var cast_roots: Dictionary = {}
var timeline_seconds := 0.0
var captions: Label
const CAST = ["lelli", "brin", "odo"]
const COLORS = [Color("#16b2ba"), Color("#bf7f30"), Color("#e76579")]

func _ready() -> void:
    _configure_world()
    _load_garden()
    _load_cast()
    _place_imported_props()
    _load_background_rigs()
    _make_caption()
    set_process(true)
    print("GODOT_LIBRARY_READY characters=", cast_roots.size())

func _configure_world() -> void:
    var environment := Environment.new()
    environment.background_mode = Environment.BG_SKY
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
    environment.reflected_light_source = Environment.REFLECTION_SOURCE_BG
    environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
    var sky := Sky.new()
    var pano_path := _find_file("res://assets/quality/hdris/studio_garden", "hdr")
    if pano_path != "":
        var sky_material := PanoramaSkyMaterial.new()
        sky_material.panorama = load(pano_path)
        sky.sky_material = sky_material
        print("GODOT_HDRI_LOADED ", pano_path)
    else:
        var procedural := ProceduralSkyMaterial.new()
        procedural.sky_top_color = Color("#84b9e5")
        procedural.ground_bottom_color = Color("#91ae85")
        sky.sky_material = procedural
    environment.sky = sky
    var world := WorldEnvironment.new()
    world.environment = environment
    add_child(world)
    var key := DirectionalLight3D.new()
    key.name = "Soft sun"
    key.rotation_degrees = Vector3(-49, -25, 0)
    key.light_energy = 1.1
    key.shadow_enabled = true
    add_child(key)
    var fill := OmniLight3D.new()
    fill.name = "Warm fill"
    fill.position = Vector3(-3.5, 1.5, 3.0)
    fill.light_energy = 0.6
    fill.omni_range = 12
    add_child(fill)
    var camera := Camera3D.new()
    camera.name = "Camera"
    camera.position = Vector3(0, 3.05, 8.5)
    camera.fov = 48
    add_child(camera)
    camera.look_at(Vector3(0, 1.5, 0), Vector3.UP)
    camera.current = true

func _find_file(directory: String, extension: String) -> String:
    if not DirAccess.dir_exists_absolute(directory):
        return ""
    for file in DirAccess.get_files_at(directory):
        if file.get_extension().to_lower() == extension:
            return directory.path_join(file)
    return ""

func _load_garden() -> void:
    var garden := _load_glb("res://assets/original/sunpatch_court.glb", Vector3.ZERO, 1.0, "Garden")
    if garden != null:
        _apply_pbr_materials(garden)

func _apply_pbr_materials(garden: Node3D) -> void:
    var manifest_path := "res://assets/quality/quality_manifest.json"
    if not FileAccess.file_exists(manifest_path):
        return
    var source := FileAccess.get_file_as_string(manifest_path)
    var parsed = JSON.parse_string(source)
    if not (parsed is Dictionary):
        return
    var materials = parsed.get("materials", [])
    if materials.size() < 2:
        return
    for obj in garden.find_children("*", "MeshInstance3D", true, false):
        var mesh_instance := obj as MeshInstance3D
        var node_name := String(obj.name).to_lower()
        var index := -1
        if node_name.contains("court_grass"):
            index = 0
        elif node_name.contains("court_path") or node_name.contains("stepping_stone"):
            index = mini(2, materials.size() - 1)
        if index < 0:
            continue
        var maps = materials[index].get("maps", {})
        var pbr := StandardMaterial3D.new()
        var base := "res://assets/quality/"
        for kind in ["color", "normal", "roughness"]:
            var path := base + String(maps.get(kind, ""))
            if not ResourceLoader.exists(path):
                continue
            var texture := load(path) as Texture2D
            if texture == null:
                continue
            match kind:
                "color":
                    pbr.albedo_texture = texture
                "normal":
                    pbr.normal_enabled = true
                    pbr.normal_texture = texture
                    pbr.normal_scale = 0.55
                "roughness":
                    pbr.roughness_texture = texture
                    pbr.roughness = 1.0
        pbr.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
        if mesh_instance.mesh != null:
            for surface in range(mesh_instance.mesh.get_surface_count()):
                mesh_instance.set_surface_override_material(surface, pbr)
    print("GODOT_PBR_READY")

func _load_cast() -> void:
    for i in range(CAST.size()):
        var path := "res://assets/original/%s_original_clay.glb" % CAST[i]
        var position := Vector3((i - 1) * 1.7, 0.0, 0.0)
        var item := _load_glb(path, position, 1.0, CAST[i])
        if item != null:
            cast_roots[CAST[i]] = item
        else:
            push_warning("Missing reusable GLB for " + CAST[i])

func _load_glb(path: String, location: Vector3, size: float, label: String) -> Node3D:
    if not ResourceLoader.exists(path):
        return null
    var scene_resource := load(path) as PackedScene
    if scene_resource == null:
        return null
    var item := scene_resource.instantiate() as Node3D
    if item == null:
        return null
    item.name = label
    item.position = location
    item.scale = Vector3.ONE * size
    add_child(item)
    return item

func _place_imported_props() -> void:
    var root := "res://assets/imported/imports/kenney_platformer_4/Models/GLB format"
    for entry in [
        {"name": "tree.glb", "pos": Vector3(-4, 0, -1)},
        {"name": "flowers.glb", "pos": Vector3(3.6, 0, 1.4)},
        {"name": "plant.glb", "pos": Vector3(-3.6, 0, 1.8)},
    ]:
        _load_glb(root.path_join(entry["name"]), entry["pos"], 0.65, "CC0_" + entry["name"])

func _load_background_rigs() -> void:
    var manifest_path := "res://assets/imported/import_manifest.json"
    if not FileAccess.file_exists(manifest_path):
        return
    var catalog = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
    if not (catalog is Dictionary):
        return
    var entries = catalog.get("background_characters", [])
    for index in range(mini(2, entries.size())):
        var path := "res://assets/imported/" + String(entries[index].get("file", ""))
        var x := -3.6 if index == 0 else 3.6
        var figure := _load_glb(path, Vector3(x, 0, -1.4), 0.9, "CC0_Extra_" + str(index))
        if figure == null:
            push_warning("Godot could not load imported rig: " + path)
            continue
        var animator = figure.find_children("*", "AnimationPlayer", true, false)
        if animator.size() > 0:
            var player := animator[0] as AnimationPlayer
            var clips := player.get_animation_list()
            if clips.size() > 0:
                var idle := String(clips[0])
                for candidate in clips:
                    if String(candidate).to_lower().contains("idle"):
                        idle = String(candidate)
                player.play(idle)
        print("GODOT_RIG_LOADED ", path)

func _make_caption() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    captions = Label.new()
    captions.text = "CartoonStudio • reusable imported 3D assets"
    captions.add_theme_color_override("font_color", Color("#29364d"))
    captions.position = Vector2(25, 25)
    layer.add_child(captions)

func _process(delta: float) -> void:
    timeline_seconds += delta
    for idx in range(CAST.size()):
        var name: String = CAST[idx]
        if cast_roots.has(name):
            var puppet: Node3D = cast_roots[name]
            puppet.position.y = 0.018 * sin(timeline_seconds * 2.2 + idx)
            puppet.rotation.y = 0.045 * sin(timeline_seconds * 1.1 + idx * 0.7)
