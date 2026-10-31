extends SceneTree
## Private-art-free engine-level contact proof for the optional EasyIK Bone2D route.
## This is a QA geometry rig, NOT Naya's approved artwork or her existing Node2D rig.

const EPSILON_PX := 2.0
const UPPER_LENGTH := 120.0
const LOWER_LENGTH := 100.0

func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var errors: PackedStringArray = []
	var rig := Node2D.new()
	rig.name = "SyntheticRailContactRig"
	var skeleton := Skeleton2D.new()
	skeleton.name = "Skeleton2D"
	rig.add_child(skeleton)

	var upper := Bone2D.new()
	upper.name = "Upper"
	skeleton.add_child(upper)
	var lower := Bone2D.new()
	lower.name = "Forearm"
	upper.add_child(lower)

	var target := Node2D.new()
	target.name = "RailHandTarget"
	rig.add_child(target)

	var ik_script := load("res://addons/easyik/nodes/easy_ik_manager.gd") as Script
	if ik_script == null:
		push_error("Failed to load optional EasyIK source")
		quit(1)
		return

	var ik := ik_script.new() as Node2D
	if ik == null:
		push_error("EasyIK script did not instantiate as Node2D")
		quit(1)
		return
	ik.name = "RailIK"
	rig.add_child(ik)
	ik.set("enabled", false)
	ik.set("target", target)
	ik.set("strength", 1.0)
	ik.set("softness", 0.0)
	ik.set("target_tracking_delay", 0.0)
	ik.call("set_joints", [
		{"bone": NodePath("../Skeleton2D/Upper"), "enabled": false},
		{"bone": NodePath("../Skeleton2D/Upper/Forearm"), "enabled": false},
	])

	root.add_child(rig)
	# Set lengths AFTER entering the tree; Godot skeleton rest preparation must
	# not silently change our test dimensions.
	upper.set_length(UPPER_LENGTH)
	lower.position = Vector2(UPPER_LENGTH, 0.0)
	lower.set_length(LOWER_LENGTH)
	if int(ik.call("get_joint_count")) != 2:
		errors.append("The two Bone2D chain entries were not retained")

	ik.set("enabled", true)
	target.position = Vector2(145.0, 65.0)
	ik.call("_solve", 1.0 / 24.0)
	_check_contact("reachable rail", upper, lower, target, errors)

	# Mirroring is important for shot-direction changes. Repeat with the
	# same local target after flipping the ENTIRE actor, not the individual arm.
	rig.scale = Vector2(-1.0, 1.0)
	ik.call("_solve", 1.0 / 24.0)
	_check_contact("mirrored reachable rail", upper, lower, target, errors)

	# An unreachable rail must leave limb lengths unchanged; do not fake
	# contact by elongating the approved body-part drawings.
	rig.scale = Vector2.ONE
	target.position = Vector2(280.0, 35.0)
	ik.call("_solve", 1.0 / 24.0)
	if lower.get_length() != LOWER_LENGTH or upper.get_length() != UPPER_LENGTH:
		errors.append("Unreachable target stretched a Bone2D length")
	var reach := upper.global_position.distance_to(_tip(lower))
	if reach > UPPER_LENGTH + LOWER_LENGTH + EPSILON_PX:
		errors.append("Unreachable target extended beyond total reach")

	rig.queue_free()
	if errors.is_empty():
		print("PASS native EasyIK geometry: rail contact, mirrored target, no stretching")
		quit(0)
	else:
		for message in errors:
			push_error(message)
		quit(1)


func _tip(bone: Bone2D) -> Vector2:
	return bone.to_global(Vector2(bone.get_length(), 0.0).rotated(bone.get_bone_angle()))


func _check_contact(label: String, upper: Bone2D, lower: Bone2D, target: Node2D, errors: PackedStringArray) -> void:
	var error_px := _tip(lower).distance_to(target.global_position)
	if error_px > EPSILON_PX:
		errors.append("%s hand missed target by %.3f px" % [label, error_px])
	if not is_equal_approx(upper.get_length(), UPPER_LENGTH):
		errors.append("%s changed upper-arm length" % label)
	if not is_equal_approx(lower.get_length(), LOWER_LENGTH):
		errors.append("%s changed forearm length" % label)
