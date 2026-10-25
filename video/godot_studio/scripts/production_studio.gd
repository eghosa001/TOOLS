extends Node3D
## Production scene: only real imported, skeletal, CC0 characters.
## The retired procedural/proposed clay GLBs must NEVER load in this scene.

@export var gallery_mode: bool = false
const ALL_CAST: Array[String] = [
    "lelli", "brin", "odo", "tavi", "miko", "pippa", "nori", "kolo",
    "suri", "marn", "fen", "rumi", "bex", "luma", "zaza"
]
var cast_roots: Dictionary = {}
var animation_players: Dictionary = {}
var elapsed: float = 0.0
var captions: Label

func _ready() -> void:
    _world()
    _stage()
    var validated := 0
    for key in ALL_CAST:
        var file_name := "res://assets/production/" + key + ".gltf"
        if not ResourceLoader.exists(file_name):
            push_error("REAL_CAST_MISSING " + file_name)
            return
        var candidate := load(file_name) as PackedScene
        if candidate == null:
            push_error("REAL_CAST_NOT_SCENE " + key)
            return
        var sample := candidate.instantiate() as Node3D
        if sample == null:
            push_error("REAL_CAST_NOT_3D " + key)
            return
        var bones = sample.find_children("*", "Skeleton3D", true, false)
        var clips = sample.find_children("*", "AnimationPlayer", true, false)
        if bones.size() < 1 or clips.size() < 1:
            push_error("REAL_CAST_UNRIGGED " + key)
            sample.free()
            return
        var found_animation := false
        for clip_node in clips:
            var player := clip_node as AnimationPlayer
            if player.get_animation_list().size() > 0:
                found_animation = true
        if not found_animation:
            push_error("REAL_CAST_HAS_NO_ANIMATIONS " + key)
            sample.free()
            return
        sample.free()
        validated += 1
    var requested := _selected_keys()
    for i in range(requested.size()):
        var key := requested[i]
        var gltf := load("res://assets/production/" + key + ".gltf") as PackedScene
        var character := gltf.instantiate() as Node3D
        character.name = key
        var x := (float(i) - float(requested.size() - 1) * 0.5)
        character.position = Vector3(x * (2.25 if gallery_mode else 2.05), 0.0,
            ((i / 5) * 3.1 - 3.1) if gallery_mode else 0.0)
        add_child(character)
        cast_roots[key] = character
        var animators = character.find_children("*", "AnimationPlayer", true, false)
        for item in animators:
            var player := item as AnimationPlayer
            var names := player.get_animation_list()
            if names.is_empty():
                continue
            animation_players[key] = player
            var idle := ""
            for name in names:
                var lower := String(name).to_lower()
                if lower == "idle" or lower.ends_with("/idle"):
                    idle = String(name)
                elif lower == "flying" or lower.ends_with("/flying"):
                    if idle == "":
                        idle = String(name)
            if idle == "":
                idle = String(names[0])
            player.play(idle)
            player.set_meta("rest_clip", idle)
            break
        if not animation_players.has(key):
            push_error("ACTIVE_CHARACTER_MISSING_ANIMATION " + key)
            return
    _captions()
    if not gallery_mode:
        var cues := preload("res://scripts/production_episode_player.gd").new()
        add_child(cues)
        cues.configure(cast_roots, captions, animation_players)
    set_process(not gallery_mode)
    print("PRODUCTION_CAST_READY models=", validated,
        " selected=", cast_roots.size(),
        " imported_rigs=true old_procedural=false gallery=", gallery_mode)

func _selected_keys() -> Array[String]:
    if gallery_mode:
        return ALL_CAST.duplicate()
    var path := "res://episode/timeline.json"
    if FileAccess.file_exists(path):
        var timeline = JSON.parse_string(FileAccess.get_file_as_string(path))
        if timeline is Dictionary and timeline.get("cast_keys") is Array:
            var selection: Array[String] = []
            for candidate in timeline["cast_keys"]:
                var key := String(candidate)
                if not ALL_CAST.has(key):
                    push_error("UNKNOWN_STORY_CHARACTER " + key)
                    return []
                if not selection.has(key):
                    selection.append(key)
            if selection.size() > 0:
                return selection
    return ["lelli", "brin", "odo"]

func _world() -> void:
    var environment := Environment.new()
    environment.background_mode = Environment.BG_SKY
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
    environment.reflected_light_source = Environment.REFLECTION_SOURCE_BG
    environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
    var sky := Sky.new()
    var procedural := ProceduralSkyMaterial.new()
    procedural.sky_top_color = Color("#82b8e3")
    procedural.ground_bottom_color = Color("#89aa8b")
    sky.sky_material = procedural
    environment.sky = sky
    var world := WorldEnvironment.new()
    world.environment = environment
    add_child(world)
    var key_light := DirectionalLight3D.new()
    key_light.rotation_degrees = Vector3(-48, -30, 0)
    key_light.shadow_enabled = true
    key_light.light_energy = 1.35
    add_child(key_light)
    var camera := Camera3D.new()
    camera.position = Vector3(0, 5.8 if gallery_mode else 3.2,
        19.0 if gallery_mode else 9.8)
    camera.fov = 59 if gallery_mode else 46
    add_child(camera)
    camera.look_at(Vector3(0, 1.4, -0.3), Vector3.UP)
    camera.current = true

func _stage() -> void:
    # Lightweight terrain in the stage scene, not a replacement for a character.
    var mesh := MeshInstance3D.new()
    mesh.name = "Sunpatch Court temporary floor"
    var plane := PlaneMesh.new()
    plane.size = Vector2(25, 25)
    mesh.mesh = plane
    var surface := StandardMaterial3D.new()
    surface.albedo_color = Color("#94b68a")
    surface.roughness = 1.0
    mesh.material_override = surface
    add_child(mesh)

func _captions() -> void:
    var canvas := CanvasLayer.new()
    add_child(canvas)
    captions = Label.new()
    captions.position = Vector2(28, 28)
    captions.size = Vector2(1224, 105)
    captions.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    captions.add_theme_font_size_override("font_size", 28)
    captions.add_theme_color_override("font_color", Color("#20334b"))
    captions.text = "CartoonStudio • imported 3D cast review" if gallery_mode else ""
    canvas.add_child(captions)

func _process(delta: float) -> void:
    elapsed += delta
    for name in cast_roots:
        var actor := cast_roots[name] as Node3D
        actor.rotation.y = 0.035 * sin(elapsed * 1.0 + float(ALL_CAST.find(name)))
