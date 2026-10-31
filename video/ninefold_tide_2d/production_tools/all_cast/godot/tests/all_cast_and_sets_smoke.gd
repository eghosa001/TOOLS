extends SceneTree
## Fail-closed Godot 4.7.2 test of ALL 20 actual scene instances + ALL 15 layer trees.
## Structural motion under non-canon pivots only; no approval of final artwork.
func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var errors: PackedStringArray = []
    var doc = JSON.parse_string(FileAccess.get_file_as_string("res://data/production_inventory.json"))
    if not (doc is Dictionary):
        push_error("No production manifest")
        quit(1)
        return
    var character_tests := 0
    for person in doc["characters"]:
        var id := str(person["id"])
        var packed: PackedScene = load("res://scenes/cast/%s.tscn" % id)
        if packed == null:
            errors.append("No cast scene: " + id)
            continue
        var actor := packed.instantiate() as Node2D
        if actor == null:
            errors.append("Bad cast scene root: " + id)
            continue
        root.add_child(actor)
        if str(actor.get("character_id")) != id:
            errors.append("Wrong cast binding: " + id)
        if not actor.has_method("get_art_status"):
            errors.append("Character controller did not load: " + id)
            actor.free()
            continue
        var status: Dictionary = actor.call("get_art_status")
        if status.get("part_slots",0) != 15:
            errors.append("Missing joint pivot slots: " + id)
        if status.get("human_art_approved",true) or status.get("production_ready",true):
            errors.append("Danger: prototype falsely approved: " + id)
        if status.get("missing_in_current_view",0) != 15:
            errors.append("Missing private art was not detected: " + id)
        for pose in ["rest","brace","reach","point","walk_left","walk_right"]:
            if not bool(actor.call("apply_pose",pose)):
                errors.append("Pose blocked for " + id + ": " + pose)
        if bool(actor.call("apply_pose","nonexistent")):
            errors.append("Unknown pose accepted: " + id)
        if not bool(actor.call("set_joint_angle","upper_arm_right",999.0)):
            errors.append("Right upper-arm joint missing: " + id)
        var upper := actor.get_node_or_null("pelvis/torso/upper_arm_right") as Node2D
        if upper == null or absf(upper.rotation_degrees) > 115.001:
            errors.append("Shoulder safety limit failure: " + id)
        if bool(actor.call("set_joint_angle","unknown",100.0)):
            errors.append("Unknown joint accepted: " + id)
        actor.scale = Vector2(-1.0,1.0)
        if not bool(actor.call("apply_pose","reach")):
            errors.append("Mirrored pose failure: " + id)
        actor.free()
        character_tests += 1
    var world_tests := 0
    for site in doc["set_staging_slots"]:
        var id := str(site["id"])
        var packed: PackedScene = load("res://scenes/sets/%s.tscn" % id)
        if packed == null:
            errors.append("No set scene: " + id)
            continue
        var world := packed.instantiate() as Node2D
        if world == null:
            errors.append("Bad world scene: " + id)
            continue
        root.add_child(world)
        if not world.has_method("get_art_status"):
            errors.append("Set-layer controller did not load: " + id)
            world.free()
            continue
        var status: Dictionary = world.call("get_art_status")
        if world.get_child_count() != 6 or status.get("missing_layers",0) != 6:
            errors.append("Missing set parallax/occlusion layers: " + id)
        if status.get("production_ready",true) or status.get("artist_approved",true):
            errors.append("Danger: unpainted world falsely approved: " + id)
        world.free()
        world_tests += 1
    if character_tests != 20 or world_tests != 15:
        errors.append("Expected 20 cast and 15 world instances, not %d/%d" % [character_tests,world_tests])
    if errors.is_empty():
        print("PASS ALL-CAST native Godot: %d cast scenes, %d environment scenes, poses, safety limits and private-art release gate" % [character_tests,world_tests])
        quit(0)
    else:
        for error in errors:
            push_error(error)
        quit(1)