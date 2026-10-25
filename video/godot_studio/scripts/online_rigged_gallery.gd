extends Node3D
## Uses real stock artist-authored GLB skeletons/clips, not procedural mesh puppets.
## 15 colour/scale variants = 5 distinctive base characters, NOT 15 bespoke sculpts.

func _ready() -> void:
    var path := "res://assets/online_ready/ready_cast_manifest.json"
    if not FileAccess.file_exists(path):
        push_error("Online stock rig library has not been imported")
        return
    var index = JSON.parse_string(FileAccess.get_file_as_string(path))
    if not (index is Dictionary):
        push_error("Online rigged cast index is invalid")
        return
    var world := WorldEnvironment.new()
    var environment := Environment.new()
    environment.background_mode = Environment.BG_COLOR
    environment.background_color = Color("#adcbdf")
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.ambient_light_color = Color("#ffffff")
    environment.ambient_light_energy = 0.65
    world.environment = environment
    add_child(world)
    var light := DirectionalLight3D.new()
    light.light_energy = 1.45
    light.rotation_degrees = Vector3(-47, -28, 0)
    light.shadow_enabled = true
    add_child(light)
    var camera := Camera3D.new()
    camera.position = Vector3(0.0, 8.0, 21.0)
    camera.fov = 59
    add_child(camera)
    camera.look_at(Vector3(0, 1.4, 0), Vector3.UP)
    camera.current = true
    var actors: Dictionary = index.get("variants", {})
    var keys: Array = actors.keys()
    var rigs := 0
    var with_animations := 0
    for i in range(keys.size()):
        var key := String(keys[i])
        var record: Dictionary = actors[key]
        var filename := "res://assets/online_ready/" + String(record.get("model","")) + ".glb"
        if not ResourceLoader.exists(filename):
            push_error("Missing downloaded CC0 rig: " + filename)
            return
        var glb := load(filename) as PackedScene
        if glb == null:
            push_error("GLB is not a scene: " + filename)
            return
        var actor := glb.instantiate() as Node3D
        if actor == null:
            push_error("Not a Node3D: " + filename)
            return
        actor.name = key
        actor.position = Vector3((i % 5 - 2) * 2.75, 0.0, (i / 5 - 1) * 3.35)
        actor.scale = Vector3.ONE * float(record.get("scale", 1.0))
        add_child(actor)
        var skeletons = actor.find_children("*", "Skeleton3D", true, false)
        if skeletons.is_empty():
            push_error("Downloaded GLB lacks Godot Skeleton3D: " + filename)
            return
        rigs += 1
        var players = actor.find_children("*", "AnimationPlayer", true, false)
        var animated := false
        for node in players:
            var player := node as AnimationPlayer
            var clips := player.get_animation_list()
            if clips.size() == 0:
                continue
            var clip: String = String(clips[0])
            for candidate in clips:
                if String(candidate).to_lower().contains("idle"):
                    clip = String(candidate)
                    break
            player.play(clip)
            animated = true
            break
        if animated:
            with_animations += 1
        else:
            push_error("Downloaded rig lacks playable animation clip: " + filename)
            return
        var tint := Color(String(record.get("tint", "#ffffff")))
        for m in actor.find_children("*", "MeshInstance3D", true, false):
            var mesh := m as MeshInstance3D
            if mesh.mesh == null:
                continue
            for surface in range(mesh.mesh.get_surface_count()):
                var original = mesh.get_active_material(surface)
                if original is StandardMaterial3D:
                    var override := (original as StandardMaterial3D).duplicate() as StandardMaterial3D
                    override.albedo_color = override.albedo_color.lerp(tint, 0.11)
                    mesh.set_surface_override_material(surface, override)
    var layer := CanvasLayer.new()
    add_child(layer)
    var label := Label.new()
    label.text = "15 reusable stock-rig CAST VARIANTS from 5 CC0 artist-made animated GLBs (review only)"
    label.add_theme_color_override("font_color", Color("#20314a"))
    label.position = Vector2(14, 14)
    layer.add_child(label)
    if rigs == 15 and with_animations == 15:
        print("ONLINE_GODOT_READY base_models=5 variants=15 skeletons=15 animated=15 canon=false")
