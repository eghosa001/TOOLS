extends Node3D
## Everything visible is imported from existing CC0 assets. No generated meshes.
## Camera and captions follow an editor-authored shot list, never auto-select media.

var shots: Array = []
var total_seconds := 0.0
var current_shot := -1
var elapsed := 0.0
var camera_3d: Camera3D
var caption: Label

func _ready() -> void:
    var source := OS.get_environment("SHORTS3D_SHOTLIST")
    if source.is_empty():
        push_error("SHORTS3D_SHOTLIST must point to the editor's shotlist JSON")
        get_tree().quit(2)
        return
    var file := FileAccess.open(source, FileAccess.READ)
    if file == null:
        push_error("Authored 3D timeline missing")
        get_tree().quit(2)
        return
    var json = JSON.parse_string(file.get_as_text())
    if not json is Dictionary or not json.has("shots"):
        push_error("Invalid authored scene data")
        get_tree().quit(2)
        return
    shots = json["shots"]
    total_seconds = float(json["seconds"])
    var sky_id: String = str(json.get("world",{}).get("hdri_asset","cloud_layers_2k"))
    if not _imported_world(sky_id):
        get_tree().quit(2)
        return
    _camera_and_overlay()
    for part in json.get("set", []):
        var asset_file: String = "res://assets/" + str(part["asset"]) + ".glb"
        var source_model = load(asset_file)
        if source_model == null or not source_model is PackedScene:
            push_error("Missing required imported CC0 model: " + asset_file)
            get_tree().quit(2)
            return
        var instance: Node3D = source_model.instantiate()
        instance.name = str(part["id"])
        instance.position = _vec(part.get("position", [0,0,0]))
        instance.rotation_degrees = _vec(part.get("rotation", [0,0,0]))
        instance.scale = Vector3.ONE * float(part.get("scale", 1))
        add_child(instance)
        if str(part["asset"]) == "nature__ground-grass":
            var grass_texture = load("res://assets/leafy_grass_diff_1k.jpg")
            if grass_texture == null or not grass_texture is Texture2D:
                push_error("Imported CC0 green grass photograph missing; no colored replacement")
                get_tree().quit(2)
                return
            if _apply_existing_grass_image(instance,grass_texture) == 0:
                push_error("Imported floor asset has no compatible mesh to texture")
                get_tree().quit(2)
                return
        if part.has("animation"):
            var player := _find_player(instance)
            if player != null:
                var name: String = str(part["animation"])
                if player.has_animation(name):
                    player.play(name)
                else:
                    push_warning("Imported character has no clip " + name + "; leaving original pose")
            else:
                push_warning("Imported character has no AnimationPlayer; no synthetic rig substituted")
    _direct_shot(0.0)

func _apply_existing_grass_image(node: Node, photograph: Texture2D) -> int:
    var changed := 0
    if node is MeshInstance3D:
        var surface: MeshInstance3D = node as MeshInstance3D
        if surface.mesh != null:
            var existing_image_material := StandardMaterial3D.new()
            existing_image_material.albedo_texture = photograph
            existing_image_material.roughness = 0.95
            existing_image_material.albedo_color = Color(0.65,0.96,0.62)
            existing_image_material.uv1_scale = Vector3(60,60,1)
            for n in range(surface.mesh.get_surface_count()):
                surface.set_surface_override_material(n,existing_image_material)
                changed += 1
    for child in node.get_children():
        changed += _apply_existing_grass_image(child,photograph)
    return changed

func _find_player(node: Node) -> AnimationPlayer:
    if node is AnimationPlayer:
        return node as AnimationPlayer
    for child in node.get_children():
        var candidate := _find_player(child)
        if candidate != null:
            return candidate
    return null

func _vec(coords: Array) -> Vector3:
    return Vector3(float(coords[0]),float(coords[1]),float(coords[2]))

func _imported_world(hdri_id: String) -> bool:
    if hdri_id.is_empty() or hdri_id.contains("/") or hdri_id.contains(".") or hdri_id.contains("\\"):
        push_error("Unsafe director-selected HDRI asset name")
        return false
    var hdri = load("res://assets/" + hdri_id + ".hdr")
    if hdri == null or not hdri is Texture2D:
        push_error("Required licensed Poly Haven HDRI missing; refusing plain generated replacement")
        return false
    var env_node := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_SKY
    var sky := Sky.new()
    var panoramic := PanoramaSkyMaterial.new()
    panoramic.panorama = hdri
    sky.sky_material = panoramic
    env.sky = sky
    env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
    env.ambient_light_energy = 0.35
    env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
    env.tonemap_exposure = 0.65
    env_node.environment = env
    add_child(env_node)
    var daylight := DirectionalLight3D.new()
    daylight.name = "LightForImportedModels"
    daylight.rotation_degrees = Vector3(-53,35,-9)
    daylight.light_energy = 0.8
    daylight.shadow_enabled = true
    add_child(daylight)
    return true

func _camera_and_overlay() -> void:
    camera_3d = Camera3D.new()
    camera_3d.fov = 46
    camera_3d.near = 0.05
    camera_3d.far = 400
    camera_3d.current = true
    add_child(camera_3d)
    var layer := CanvasLayer.new()
    add_child(layer)
    caption = Label.new()
    caption.position = Vector2(24,915)
    caption.size = Vector2(672,132)
    caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    caption.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    caption.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    caption.add_theme_font_size_override("font_size", 42)
    caption.add_theme_color_override("font_color", Color("fff2b0"))
    caption.add_theme_color_override("font_outline_color", Color.BLACK)
    caption.add_theme_constant_override("outline_size", 12)
    layer.add_child(caption)

func _process(delta: float) -> void:
    elapsed += delta
    if elapsed >= total_seconds:
        get_tree().quit()
        return
    _direct_shot(elapsed)

func _direct_shot(t: float) -> void:
    for i in range(shots.size()):
        var shot: Dictionary = shots[i]
        var a := float(shot["start"])
        var b := float(shot["end"])
        if t >= a and t < b:
            var alpha := clampf((t-a)/(b-a),0,1)
            var smooth := alpha*alpha*(3-2*alpha)
            camera_3d.position = _vec(shot["camera_from"]).lerp(_vec(shot["camera_to"]),smooth)
            camera_3d.look_at(_vec(shot["look_at"]),Vector3.UP)
            if current_shot != i:
                current_shot = i
                caption.text = str(shot["caption"])
            return
