extends SceneTree
## Headless regression: an unfinished 2D shot MUST NOT play.
func _initialize() -> void:
    call_deferred("_check")

func _check() -> void:
    var packed: PackedScene = load("res://scenes/shots/e101_cam03b_5s.tscn") as PackedScene
    if packed == null:
        push_error("Phase4 shot scene cannot be imported")
        quit(1)
        return
    var shot: Node2D = packed.instantiate()
    root.add_child(shot)
    if shot.play_if_approved():
        push_error("UNSAFE: an unapproved image sequence was allowed to play")
        quit(1)
        return
    if shot.display_sprite.texture != null:
        push_error("UNSAFE: the engine displayed unapproved drawing content")
        quit(1)
        return
    if not shot.status_label.text.begins_with("SHOT BLOCKED"):
        push_error("UNSAFE: visible production-blocking warning is missing")
        quit(1)
        return
    print("PASS Godot Phase4: unapproved source art blocked; no frames displayed")
    quit(0)
