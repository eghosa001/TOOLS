extends Node
## Exact script cue player for imported skeletal GLTF characters.
## A line has audio ONLY if a matching real WAV was provided.
## These stock models DO NOT have verified phoneme/viseme blend shapes.

var cast: Dictionary = {}
var animations: Dictionary = {}
var captions: Label
var stream: AudioStreamPlayer
var lines: Array = []
var seconds: float = 0.0
var active: int = -1

func _ready() -> void:
    set_process(false)

func configure(actors: Dictionary, label: Label, players: Dictionary) -> void:
    cast = actors
    captions = label
    animations = players
    stream = AudioStreamPlayer.new()
    add_child(stream)
    var path := "res://episode/timeline.json"
    if not FileAccess.file_exists(path):
        push_warning("SILENT_GALLERY_ONLY: no episode timeline supplied")
        return
    var timeline = JSON.parse_string(FileAccess.get_file_as_string(path))
    if not (timeline is Dictionary) or not (timeline.get("events") is Array):
        push_error("Malformed episode timeline")
        return
    lines = timeline["events"]
    if lines.is_empty():
        push_error("Empty episode timeline")
        return
    for entry in lines:
        if not (entry is Dictionary) or not cast.has(String(entry.get("speaker", ""))):
            push_error("Unknown episode speaker: " + String(entry.get("speaker", "?")))
            lines.clear()
            return
    print("PRODUCTION_EPISODE_READY lines=", lines.size(),
        " timing=", String(timeline.get("timing_source","unknown")),
        " actual_voices=", int(timeline.get("audio_line_count",0)),
        " facial_visemes=false")
    set_process(true)

func _process(delta: float) -> void:
    if lines.is_empty():
        return
    seconds += delta
    while active + 1 < lines.size() and seconds >= float(lines[active + 1]["start"]):
        active += 1
        _start_line(lines[active])
    if active < 0:
        return
    var event: Dictionary = lines[active]
    if seconds >= float(event["end"]):
        captions.text = ""
        if active == lines.size() - 1:
            stream.stop()
            set_process(false)
            print("PRODUCTION_ANIMATIC_FINISHED lines=", lines.size())

func _start_line(event: Dictionary) -> void:
    stream.stop()
    for actor in cast:
        _play_rest(String(actor))
    var speaker := String(event["speaker"])
    captions.text = speaker.capitalize() + ": " + String(event["text"])
    var action := String(event.get("action","none"))
    var emotion := String(event.get("emotion","neutral"))
    # These are REAL skeletal clips, not fabricated pivot/wave/point acting.
    if action == "nod":
        _play(speaker, "Yes")
    elif emotion == "excited" or emotion == "happy":
        _play(speaker, "Dance")
    elif emotion == "angry":
        _play(speaker, "No")
    # Wave/point require properly authored clips on these rigs: no fake gestures.
    var audio := String(event.get("audio_path",""))
    if audio.is_empty():
        return
    if not ResourceLoader.exists(audio):
        push_error("Voice file declared but missing: " + audio)
        return
    var resource := load(audio) as AudioStream
    if resource == null:
        push_error("Unable to load real spoken audio: " + audio)
        return
    stream.stream = resource
    stream.play()

func _play(key: String, keyword: String) -> void:
    if not animations.has(key):
        return
    var player := animations[key] as AnimationPlayer
    for name in player.get_animation_list():
        if String(name).to_lower() == keyword.to_lower() or String(name).to_lower().ends_with("/" + keyword.to_lower()):
            player.play(String(name))
            return

func _play_rest(key: String) -> void:
    if not animations.has(key):
        return
    var player := animations[key] as AnimationPlayer
    var idle := String(player.get_meta("rest_clip", ""))
    if not idle.is_empty() and player.has_animation(idle):
        player.play(idle)
