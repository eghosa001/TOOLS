extends Node3D
## Review scene for optional characters only. The 12 prototypes are NOT canon.

const NAMES = ["tavi", "miko", "pippa", "nori", "kolo", "suri",
               "marn", "fen", "rumi", "bex", "luma", "zaza"]

func _ready() -> void:
    var world := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color("#b9d4e5")
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color("#fff0db")
    env.ambient_light_energy = 0.9
    world.environment = env
    add_child(world)
    var light := DirectionalLight3D.new()
    light.rotation_degrees = Vector3(-45, -22, 0)
    light.light_energy = 1.2
    light.shadow_enabled = true
    add_child(light)
    var camera := Camera3D.new()
    camera.position = Vector3(0, 8.0, 19.5)
    camera.fov = 59
    add_child(camera)
    camera.look_at(Vector3(0, 1.2, 0), Vector3.UP)
    camera.current = true
    var loaded := 0
    for i in range(NAMES.size()):
        var name: String = NAMES[i]
        var file_path := "res://assets/proposed/%s_proposed_clay.glb" % name
        if not ResourceLoader.exists(file_path):
            push_error("Missing proposed character model: " + file_path)
            return
        var res := load(file_path) as PackedScene
        if res == null:
            push_error("Unable to load cast candidate: " + name)
            return
        var actor := res.instantiate() as Node3D
        if actor == null:
            push_error("Imported GLB is not a Node3D: " + name)
            return
        actor.name = name
        actor.position = Vector3((i % 4 - 1.5) * 2.75, 0, (i / 4 - 1) * 3.3)
        add_child(actor)
        loaded += 1
    var layer := CanvasLayer.new()
    add_child(layer)
    var text_label := Label.new()
    text_label.text = "CartoonStudio — 12 PROPOSED supporting characters (NOT canon)"
    text_label.position = Vector2(20, 18)
    text_label.add_theme_color_override("font_color", Color("#20354c"))
    layer.add_child(text_label)
    print("GODOT_CAST_GALLERY_READY count=", loaded, " canon=false")
