extends Node
## Silent animatic unless measured dialogue WAV clips were supplied in episode/.
## Original character GLB meshes are NOT skeletal rigs. Body gestures are pivots.

var actors: Dictionary = {}
var faces: Dictionary = {}
var motion: Dictionary = {}
var caption: Label
var events: Array = []
var elapsed := 0.0
var active := -1
var audio_player: AudioStreamPlayer

func _ready() -> void:
    set_process(false)

func configure(cast: Dictionary, subtitle: Label) -> void:
    actors = cast
    caption = subtitle
    audio_player = AudioStreamPlayer.new()
    add_child(audio_player)
    for key in actors:
        var mesh_blends: Array = []
        var limbs: Array = []
        var head: Node3D = null
        var root: Node3D = actors[key]
        for node in root.find_children("*", "Node3D", true, false):
            var label := String(node.name).to_lower()
            if label.contains("_arm_pivot_"):
                limbs.append(node)
            elif label.ends_with("_head_pivot"):
                head = node as Node3D
        for node in root.find_children("*", "MeshInstance3D", true, false):
            var mesh_node := node as MeshInstance3D
            if mesh_node.mesh == null:
                continue
            for idx in range(mesh_node.mesh.get_blend_shape_count()):
                mesh_blends.append({"node": mesh_node, "idx": idx,
                    "name": String(mesh_node.mesh.get_blend_shape_name(idx)).to_lower()})
        faces[key] = mesh_blends
        motion[key] = {"limbs": limbs, "head": head}
    var file := "res://episode/timeline.json"
    if not FileAccess.file_exists(file):
        push_warning("Godot episode cue sheet absent; displaying assets only")
        return
    var data = JSON.parse_string(FileAccess.get_file_as_string(file))
    if not (data is Dictionary) or not (data.get("events") is Array):
        push_error("Malformed episode timeline")
        return
    events = data["events"]
    for entry in events:
        if not (entry is Dictionary) or not actors.has(entry.get("speaker", "")):
            push_error("Episode contains an unknown speaker")
            events.clear()
            return
    if events.is_empty():
        push_error("Episode timeline empty")
        return
    print("GODOT_EPISODE_READY lines=", events.size(), " timing=", data.get("timing_source", "unknown"))
    set_process(true)

func _process(delta: float) -> void:
    if events.is_empty():
        return
    elapsed += delta
    while active + 1 < events.size() and elapsed >= float(events[active + 1]["start"]):
        active += 1
        _activate(events[active])
    if active < 0:
        return
    var line: Dictionary = events[active]
    var duration := float(line["end"]) - float(line["start"])
    var t := elapsed - float(line["start"])
    if t < duration:
        _act(line, t, duration)
    else:
        caption.text = ""
        _reset(String(line["speaker"]))
        if active == events.size() - 1:
            set_process(false)
            print("GODOT_EPISODE_ANIMATIC_COMPLETE")

func _activate(line: Dictionary) -> void:
    for key in actors:
        _reset(String(key))
    caption.text = String(line["speaker"]).capitalize() + ": " + String(line["text"])
    audio_player.stop()
    var path := String(line.get("audio_path", ""))
    if path.is_empty():
        return
    if not ResourceLoader.exists(path):
        push_error("Dialogue audio missing: " + path)
        return
    var stream := load(path) as AudioStream
    if stream == null:
        push_error("Dialogue audio invalid: " + path)
        return
    audio_player.stop()
    audio_player.stream = stream
    audio_player.play()

func _reset(key: String) -> void:
    if not motion.has(key):
        return
    var part: Dictionary = motion[key]
    for limb in part["limbs"]:
        (limb as Node3D).rotation = Vector3.ZERO
    if part["head"] != null:
        (part["head"] as Node3D).rotation = Vector3.ZERO
    for blend in faces[key]:
        (blend["node"] as MeshInstance3D).set_blend_shape_value(int(blend["idx"]), 0.0)

func _act(line: Dictionary, t: float, length: float) -> void:
    var speaker := String(line["speaker"])
    var part: Dictionary = motion[speaker]
    var action := String(line.get("action", "none"))
    var emotion := String(line.get("emotion", "neutral"))
    var lift := sin(PI * clampf(t / maxf(.1, length), 0.0, 1.0))
    if part["head"] != null:
        var head := part["head"] as Node3D
        if action == "nod":
            head.rotation.x = lift * .14 * sin(t * 7.0)
        elif emotion == "sad":
            head.rotation.x = lift * .08
        elif emotion == "surprised":
            head.rotation.x = -lift * .08
    for limb in part["limbs"]:
        var arm := limb as Node3D
        if action == "wave":
            arm.rotation.z = -.65 * lift
            arm.rotation.x = .20 * lift * sin(t * 9.0)
        elif action == "point":
            arm.rotation.x = -.38 * lift
    var phrase := String(line["text"]).to_lower()
    var letter := ""
    if not phrase.is_empty():
        letter = phrase.substr(mini(phrase.length() - 1, int(t * 9.0)), 1)
    var mouth := "viseme_aa"
    if letter == "o":
        mouth = "viseme_o"
    elif letter in ["u", "w"]:
        mouth = "viseme_u"
    elif letter in ["e", "i", "y"]:
        mouth = "viseme_e"
    elif letter in ["m", "b", "p"]:
        mouth = "viseme_pp"
    elif letter in ["f", "v"]:
        mouth = "viseme_ff"
    elif letter == "n":
        mouth = "viseme_nn"
    var rhubarb_active := false
    if String(line.get("lip_sync_source", "")) == "rhubarb":
        rhubarb_active = true
        mouth = ""
        var cues: Array = line.get("mouth_cues", [])
        for cue in cues:
            if t >= float(cue["start"]) and t < float(cue["end"]):
                var mouth_code := String(cue["value"])
                match mouth_code:
                    "A": mouth = "viseme_pp"
                    "B": mouth = "viseme_kk"
                    "C": mouth = "viseme_e"
                    "D": mouth = "viseme_aa"
                    "E": mouth = "viseme_o"
                    "F": mouth = "viseme_u"
                    "G": mouth = "viseme_ff"
                    "H": mouth = "viseme_nn"
                    _: mouth = ""
                break
    var strength := (.30 + .42 * absf(sin(t * 12.0))) * lift
    for blend in faces[speaker]:
        var blend_name := String(blend["name"])
        var value := 0.0
        if not mouth.is_empty() and blend_name == mouth and (letter != " " or rhubarb_active):
            value = strength
        elif blend_name == "mouthsmile" and emotion in ["happy", "excited"]:
            value = .55 * lift
        elif blend_name.begins_with("eyeblink") and fmod(t, 3.7) > 3.59:
            value = 1.0
        (blend["node"] as MeshInstance3D).set_blend_shape_value(int(blend["idx"]), value)
