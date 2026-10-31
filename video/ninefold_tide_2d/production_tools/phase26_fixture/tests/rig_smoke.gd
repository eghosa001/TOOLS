extends SceneTree
# No character art is included; tests only the private Naya rig controller
# against fake, non-canon geometry and targets under Godot 4.7.2.
func _initialize() -> void:
    call_deferred("_run")

func _expect(ok: bool, reason: String, errors: PackedStringArray) -> void:
    if not ok:
        errors.append(reason)

func _run() -> void:
    var errors := PackedStringArray()
    var script_resource := load("res://scripts/naya_phase26_rig.gd") as Script
    if script_resource == null:
        push_error("Cannot load Phase26 Naya rig controller")
        quit(1)
        return
    var naya := script_resource.new() as Node2D
    if naya == null:
        push_error("Controller is not a Node2D")
        quit(1)
        return
    naya.set("show_source_warning", false)
    root.add_child(naya)
    await process_frame
    naya.call("set_rail_grip", true)
    _expect(bool(naya.get("rail_grip_active")), "rail grip activation", errors)
    _expect(not bool(naya.get("grip_unreachable")), "reachable target not solved", errors)
    _expect(float(naya.call("grip_contact_error_px")) <= 2.0, "reachable contact error > 2px", errors)
    var shoulder := (naya.get("joints") as Dictionary)["right_upper_arm"] as Node2D
    var elbow := (naya.get("joints") as Dictionary)["right_forearm"] as Node2D
    _expect(absf(shoulder.rotation_degrees) <= 45.01, "shoulder exceeded angular limit", errors)
    _expect(absf(elbow.rotation_degrees) <= 135.01, "elbow exceeded angular limit", errors)
    for pose in [Vector2(-1.0, 1.0), Vector2(0.65, 0.9), Vector2(-0.75, 0.8)]:
        naya.scale = pose
        naya.rotation_degrees = 19.0
        naya.call("solve_grip_ik")
        _expect(not bool(naya.get("grip_unreachable")), "mirror or affine transformation rejected", errors)
        _expect(float(naya.call("grip_contact_error_px")) <= 2.0, "mirror or affine contact drift", errors)
        _expect(absf(shoulder.rotation_degrees) <= 45.01, "mirrored shoulder limit failure", errors)
        _expect(absf(elbow.rotation_degrees) <= 135.01, "mirrored elbow limit failure", errors)
    naya.scale = Vector2.ONE
    naya.rotation = 0.0
    var grip_config := naya.get("rig_data") as Dictionary
    var grip_params := grip_config["rail_grip"] as Dictionary
    var original_target: Array = grip_params["target_canvas"]
    grip_params["target_canvas"] = [800, 1200]
    grip_config["rail_grip"] = grip_params
    naya.call("solve_grip_ik")
    _expect(bool(naya.get("grip_unreachable")), "distant rail not flagged", errors)
    var hand := naya.get("grip_hand") as Sprite2D
    _expect(not hand.visible, "unreachable hand incorrectly visible", errors)
    grip_params["target_canvas"] = original_target
    grip_config["rail_grip"] = grip_params
    naya.call("set_pose", "rail_grip")
    naya.call("solve_grip_ik")
    _expect(not bool(naya.get("grip_unreachable")), "recovery after unreachable target failed", errors)
    _expect(float(naya.call("grip_contact_error_px")) <= 2.0, "recovery contact drift", errors)
    naya.call("set_rail_grip", false)
    _expect(not bool(naya.get("rail_grip_active")), "grip did not switch off", errors)
    if errors.is_empty():
        print("PASS: Phase26 Naya Node2D controller — contact, mirror, scaling, limits, unreachable, recovery")
        quit(0)
    else:
        for e in errors:
            push_error(e)
        quit(1)