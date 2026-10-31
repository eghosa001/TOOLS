extends Node3D
## Everything visible is imported from existing CC0 assets. No generated meshes.
## Camera and captions follow an editor-authored shot list, never auto-select media.

var shots: Array = []
var total_seconds := 0.0
var current_shot := -1
var elapsed := 0.0
var camera_3d: Camera3D
var caption: Label
var historical_title: Label
var subscribe_note: Label
var current_world: Dictionary = {}
var scene_parts: Array = []
var historical_effects: Array = []

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
    current_world = json.get("world", {})
    total_seconds = float(json["seconds"])
    var sky_id: String = str(json.get("world",{}).get("hdri_asset","cloud_layers_2k"))
    if not _imported_world(sky_id):
        get_tree().quit(2)
        return
    _camera_and_overlay()
    if json.has("title"):
        historical_title.text = str(json["title"])
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
        scene_parts.append({"node":instance, "data":part, "origin":instance.position})
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
    _build_imported_effects(json.get("effects", []))
    _move_imported_assets(0.0)
    _animate_imported_effects(0.0)
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
    env.tonemap_exposure = float(current_world.get("exposure",0.65))
    var daylight := DirectionalLight3D.new()
    daylight.name = "LightForImportedModels"
    daylight.rotation_degrees = Vector3(-53,35,-9)
    daylight.light_energy = float(current_world.get("light_energy",0.8))
    daylight.light_color = Color(str(current_world.get("light_tint","#ffffff")))

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
    historical_title = Label.new()
    historical_title.text = "HISTORY • 3D RECONSTRUCTION"
    historical_title.position = Vector2(24,93)
    historical_title.size = Vector2(672,76)
    historical_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    historical_title.add_theme_font_size_override("font_size", 34)
    historical_title.add_theme_color_override("font_color",Color("fff2d3"))
    historical_title.add_theme_color_override("font_outline_color",Color.BLACK)
    historical_title.add_theme_constant_override("outline_size",9)
    layer.add_child(historical_title)
    subscribe_note = Label.new()
    subscribe_note.text = "FACTS UNCOVERED  •  FOLLOW FOR MORE"
    subscribe_note.position = Vector2(30,1104)
    subscribe_note.size = Vector2(660,62)
    subscribe_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    subscribe_note.add_theme_font_size_override("font_size",25)
    subscribe_note.add_theme_color_override("font_color",Color("fff2d3"))
    subscribe_note.add_theme_color_override("font_outline_color",Color.BLACK)
    subscribe_note.add_theme_constant_override("outline_size",7)
    subscribe_note.visible = false
    layer.add_child(subscribe_note)

func _process(delta: float) -> void:
    elapsed += delta
    _move_imported_assets(elapsed)
    _animate_imported_effects(elapsed)
    subscribe_note.visible = elapsed >= total_seconds - 4.0
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

# These are entirely original imported Kenney CC0 art sprites placed in real 3D.
# Sprite3D is a rendering node, not a procedurally generated environment mesh.
func _build_imported_effects(definitions: Array) -> void:
    for fx in definitions:
        var kind: String = str(fx.get("kind",""))
        if not (kind == "fire" or kind == "smoke"):
            push_error("Unknown manually directed historical effect: "+kind)
            get_tree().quit(2)
            return
        var texture_path: String = "res://assets/historical_" + kind + "_01.png"
        var texture = load(texture_path)
        if texture == null or not texture is Texture2D:
            push_error("Original licensed Kenney FX texture missing: "+texture_path)
            get_tree().quit(2)
            return
        var sprite := Sprite3D.new()
        sprite.name = str(fx["id"])
        sprite.texture = texture
        sprite.position = _vec(fx.get("position",[0,4,0]))
        sprite.pixel_size = 0.0018
        sprite.scale = Vector3.ONE * float(fx.get("scale",4))
        sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
        sprite.shaded = false
        sprite.no_depth_test = false
        sprite.transparent = true
        sprite.visible = false
        add_child(sprite)
        var entry = {"node":sprite, "base":sprite.position,
                     "start":float(fx.get("start",0)),
                     "end":float(fx.get("end",999999)), "kind":kind,
                     "scale":float(fx.get("scale",4))}
        if kind == "fire":
            var flare := OmniLight3D.new()
            flare.name = str(fx["id"]) + "_glow"
            flare.position = sprite.position
            flare.light_color = Color("ff692a")
            flare.light_energy = 0.0
            flare.omni_range = 24.0
            flare.shadow_enabled = false
            add_child(flare)
            entry["glow"] = flare
        historical_effects.append(entry)

func _animate_imported_effects(t: float) -> void:
    for entry in historical_effects:
        var sprite: Sprite3D = entry["node"]
        var begin: float = entry["start"]
        var finish: float = entry["end"]
        var active: bool = t >= begin and t < finish
        sprite.visible = active
        if entry.has("glow"):
            var firelight: OmniLight3D = entry["glow"]
            firelight.light_energy = (0.55 + 0.12*sin(t*10.0 + float(entry["scale"]))) if active else 0.0
        if not active:
            continue
        var local_time: float = t - begin
        var prefix: String = str(entry["kind"])
        var variant: int = 1 + int(floor(local_time*7.0))%2
        var image = load("res://assets/historical_"+prefix+"_0"+str(variant)+".png")
        if image is Texture2D:
            sprite.texture = image
        var baseline: Vector3 = entry["base"]
        if prefix == "smoke":
            sprite.position = baseline + Vector3(0,local_time*0.18,sin(local_time*.7)*0.35)
        else:
            sprite.position = baseline + Vector3(sin(t*7.0)*0.14,cos(t*9.0)*0.16,0)
        sprite.modulate.a = clampf((local_time+0.1)*0.8,0.0,0.92)

func _move_imported_assets(t: float) -> void:
    for entry in scene_parts:
        var model: Node3D = entry["node"]
        var part: Dictionary = entry["data"]
        model.visible = t >= float(part.get("appear_at",0)) and t < float(part.get("hide_at",999999))
        if part.has("motion"):
            var motion: Dictionary = part["motion"]
            var start: float = float(motion["start"])
            var finish: float = float(motion["end"])
            var alpha := clampf((t-start)/maxf(0.01,finish-start),0.0,1.0)
            var smooth := alpha*alpha*(3.0-2.0*alpha)
            model.position = _vec(motion["from"]).lerp(_vec(motion["to"]),smooth)
