extends Node3D
## True 3D GLB meshes and moving 3D camera. Every shot is authored by an editor.

var shots: Array = []
var seconds := 0.0
var active_index := -1
var elapsed := 0.0
var camera_3d: Camera3D
var caption: Label

func _ready() -> void:
    var path := OS.get_environment("SHORTS3D_SHOTLIST")
    if path.is_empty():
        push_error("SHORTS3D_SHOTLIST is required")
        get_tree().quit(2)
        return
    var handle := FileAccess.open(path, FileAccess.READ)
    if handle == null:
        push_error("Missing authored shotlist")
        get_tree().quit(2)
        return
    var spec = JSON.parse_string(handle.get_as_text())
    if not (spec is Dictionary) or not spec.has("shots"):
        push_error("Invalid authored shotlist")
        get_tree().quit(2)
        return
    shots = spec["shots"]
    seconds = float(spec["seconds"])
    _world()
    _camera_and_caption()
    for prop in spec.get("set", []):
        var source := "res://assets/" + str(prop["asset"]) + ".glb"
        var packed = load(source)
        if packed == null or not (packed is PackedScene):
            push_error("Missing CC0 GLB (never insert filler): " + source)
            get_tree().quit(2)
            return
        var model: Node3D = packed.instantiate()
        model.name = str(prop["id"])
        model.position = _v3(prop.get("position", [0, 0, 0]))
        model.rotation_degrees = _v3(prop.get("rotation", [0, 0, 0]))
        model.scale = Vector3.ONE * float(prop.get("scale", 1))
        add_child(model)
    _direct_shot(0.0)

func _v3(a: Array) -> Vector3:
    return Vector3(float(a[0]), float(a[1]), float(a[2]))

func _world() -> void:
    var world := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_SKY
    var sky := Sky.new()
    var sky_material := ProceduralSkyMaterial.new()
    sky_material.sky_top_color = Color("78a9d9")
    sky_material.sky_horizon_color = Color("e6e3d0")
    sky.sky_material = sky_material
    env.sky = sky
    env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
    env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
    world.environment = env
    add_child(world)
    var sun := DirectionalLight3D.new()
    sun.rotation_degrees = Vector3(-55, 35, -15)
    sun.light_energy = 1.65
    sun.shadow_enabled = true
    add_child(sun)
    var ground := MeshInstance3D.new()
    var plane := PlaneMesh.new()
    plane.size = Vector2(220, 220)
    ground.mesh = plane
    var mat := StandardMaterial3D.new()
    mat.albedo_color = Color("83aa6c")
    mat.roughness = 0.98
    ground.material_override = mat
    ground.position.y = -0.035
    add_child(ground)

func _camera_and_caption() -> void:
    camera_3d = Camera3D.new()
    camera_3d.fov = 40.0
    camera_3d.near = 0.05
    camera_3d.far = 500
    camera_3d.current = true
    add_child(camera_3d)
    var overlay := CanvasLayer.new()
    add_child(overlay)
    caption = Label.new()
    caption.position = Vector2(30, 900)
    caption.size = Vector2(660, 130)
    caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    caption.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    caption.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    caption.add_theme_font_size_override("font_size", 43)
    caption.add_theme_color_override("font_color", Color("ffe37b"))
    caption.add_theme_color_override("font_outline_color", Color.BLACK)
    caption.add_theme_constant_override("outline_size", 12)
    overlay.add_child(caption)

func _process(delta: float) -> void:
    elapsed += delta
    if elapsed >= seconds:
        get_tree().quit()
        return
    _direct_shot(elapsed)

func _direct_shot(time_seconds: float) -> void:
    for i in range(shots.size()):
        var shot: Dictionary = shots[i]
        var start := float(shot["start"])
        var end := float(shot["end"])
        if time_seconds >= start and time_seconds < end:
            var t := clampf((time_seconds-start)/(end-start), 0.0, 1.0)
            var ease := t*t*(3.0-2.0*t)
            camera_3d.position = _v3(shot["camera_from"]).lerp(_v3(shot["camera_to"]), ease)
            camera_3d.look_at(_v3(shot["look_at"]), Vector3.UP)
            if i != active_index:
                active_index = i
                caption.text = str(shot["caption"])
            return
