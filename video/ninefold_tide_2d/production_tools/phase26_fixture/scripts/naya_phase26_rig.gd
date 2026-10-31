@tool
extends Node2D
## Phase 26: source-faithful joint pivots, constrained hand/rail contact and mirror-invariant IK.
## External licensed/approved 2D artwork is kept in separate alpha PNGs.
## Engine motion tests are distinct from the artist's quality approval.
@export_enum("rest", "hear", "reach", "brace", "look", "rail_grip") var preview_pose: String = "rest"
@export_enum("neutral", "focused", "startled", "worried", "determined", "surprised", "warm", "laugh", "doubt", "uncertain") var preview_expression: String = "neutral"
@export var auto_motion_review: bool = false
@export var preview_rail_grip: bool = false
@export var show_source_warning: bool = true

const RIG_PATH := "res://assets/naya/rig.json"
const HIDDEN_BY_DEFAULT := ["shoulder_tape", "braid_left", "braid_right", "belt", "back_hair", "reading_disc", "notebook"]
const MOTION_BEATS := [
    {"time": 0.0, "pose": "rest", "expression": "neutral"},
    {"time": 0.55, "pose": "hear", "expression": "startled"},
    {"time": 1.20, "pose": "reach", "expression": "focused"},
    {"time": 2.00, "pose": "brace", "expression": "worried"},
    {"time": 2.80, "pose": "look", "expression": "determined"},
    {"time": 3.30, "pose": "rest", "expression": "neutral"}
]

var rig_data: Dictionary = {}
var joints: Dictionary = {}
var art_nodes: Dictionary = {}
var last_pose: String = "rest"
var elapsed: float = 0.0
var missing: PackedStringArray = []
var rail_grip_active := false
var grip_unreachable := false
var rail_bg: Sprite2D
var rail_fg: Sprite2D
var grip_hand: Sprite2D
var original_right_forearm: Sprite2D

func _ready() -> void:
    if not FileAccess.file_exists(RIG_PATH):
        push_error("Missing Phase 20 rig data")
        return
    var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(RIG_PATH))
    if not (parsed is Dictionary):
        push_error("Invalid Phase 20 rig data")
        return
    rig_data = parsed
    build_rig()
    set_pose(preview_pose)
    set_expression(preview_expression)
    _build_grip_scene()
    if preview_rail_grip or preview_pose == "rail_grip":
        set_rail_grip(true)
    if show_source_warning:
        push_warning("Phase20 source-study art: paint-behind, articulation and rig motion not art approved")

func _source_asset_path(entry: Dictionary) -> String:
    # Manifest paths are relative to project root; do not create URLs or remote file requests.
    return "res://" + str(entry["texture"])

func build_rig() -> void:
    for child in get_children():
        if child.has_meta("phase19_generated"):
            child.free()
    joints.clear()
    art_nodes.clear()
    missing.clear()
    var parts: Dictionary = rig_data.get("parts", {})
    var root_pivot: Array = rig_data.get("root_world_pivot", [0, 0])
    var root_world := Vector2(float(root_pivot[0]), float(root_pivot[1]))
    for name in parts.keys():
        _add_joint_recursive(str(name), parts, root_world)
    # Attach rail after the articulated rig is built. The grip sprites are handled separately.

func _add_joint_recursive(part: String, parts: Dictionary, root_pivot: Vector2) -> Node2D:
    if joints.has(part):
        return joints[part] as Node2D
    var entry: Dictionary = parts[part]
    var parent_name: String = str(entry.get("parent", "root"))
    var parent_joint: Node2D = self
    var parent_pivot := root_pivot
    if parent_name != "root":
        if not parts.has(parent_name):
            missing.append("parent:" + part)
            return self
        parent_joint = _add_joint_recursive(parent_name, parts, root_pivot)
        var parent_entry: Dictionary = parts[parent_name]
        parent_pivot = Vector2(float(parent_entry["pivot_world"][0]), float(parent_entry["pivot_world"][1]))
    var absolute_pivot := Vector2(float(entry["pivot_world"][0]), float(entry["pivot_world"][1]))
    var joint := Node2D.new()
    joint.name = part
    joint.position = absolute_pivot - parent_pivot
    joint.set_meta("phase19_generated", true)
    parent_joint.add_child(joint)
    joints[part] = joint
    var spr := Sprite2D.new()
    spr.name = "Artwork"
    spr.centered = false
    spr.z_as_relative = false
    spr.z_index = int(entry.get("z",0))
    spr.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
    spr.scale = Vector2.ONE * float(entry.get("scale",1.0))
    var top_left := Vector2(float(entry["position"][0]),float(entry["position"][1]))
    spr.position = top_left - absolute_pivot
    var path := _source_asset_path(entry)
    if ResourceLoader.exists(path):
        spr.texture = load(path)
    else:
        missing.append("texture:" + part)
    spr.visible = not (part in HIDDEN_BY_DEFAULT)
    joint.add_child(spr)
    art_nodes[part] = spr
    return joint

func set_pose(pose_name: String) -> void:
    if rig_data.is_empty():
        return
    var poses: Dictionary = rig_data.get("poses", {})
    if not poses.has(pose_name):
        push_warning("Missing pose: " + pose_name)
        return
    if pose_name != "rail_grip" and rail_grip_active:
        set_rail_grip(false)
    last_pose = pose_name
    var target: Dictionary = poses[pose_name]
    for key in joints.keys():
        var joint: Node2D = joints[key] as Node2D
        # Angles are authored in degrees. Limit rotations to small review poses.
        joint.rotation_degrees = clampf(float(target.get(key, 0.0)), -45.0, 45.0)
        joint.scale = Vector2.ONE

func set_expression(expression_name: String) -> bool:
    if not rig_data.get("expressions",[]).has(expression_name):
        return false
    if not art_nodes.has("head"):
        return false
    var path: String = "res://assets/naya/expressions/%s.png" % expression_name
    if not ResourceLoader.exists(path):
        return false
    var sprite: Sprite2D = art_nodes["head"] as Sprite2D
    sprite.texture = load(path)
    # All expression sprites share one pivot. No scaling distortions and no false viseme overlay.
    sprite.scale = Vector2.ONE * float(rig_data["parts"]["head"]["scale"])
    preview_expression = expression_name
    return true

func reset_face_to_source() -> void:
    if not art_nodes.has("head"):
        return
    var sprite: Sprite2D = art_nodes["head"] as Sprite2D
    var original: String = str(rig_data["parts"]["head"]["texture"])
    if ResourceLoader.exists("res://" + original):
        sprite.texture = load("res://" + original)

func _make_rail_sprite(texture_path: String, name_label: String, depth: int) -> Sprite2D:
    var sprite := Sprite2D.new()
    sprite.name = name_label
    sprite.centered = false
    sprite.z_as_relative = false
    sprite.z_index = depth
    var rail: Dictionary = rig_data["rail_grip"]
    var origin: Array = rig_data["root_world_pivot"]
    sprite.position = Vector2(float(rail["rail_x_start"]) - float(origin[0]), float(rail["rail_y_top"]) - float(origin[1]))
    if ResourceLoader.exists(texture_path):
        sprite.texture = load(texture_path)
    else:
        missing.append("texture:" + name_label)
    sprite.visible = false
    sprite.set_meta("phase19_generated", true)
    add_child(sprite)
    return sprite

func _build_grip_scene() -> void:
    if not rig_data.has("rail_grip"):
        return
    rail_bg = _make_rail_sprite("res://assets/naya/rail/steel_rail_background.png", "RailBehind", -80)
    rail_fg = _make_rail_sprite("res://assets/naya/rail/steel_rail_foreground_lip.png", "RailForemostLip", 85)
    grip_hand = Sprite2D.new()
    grip_hand.name = "RightRailGripForearm"
    grip_hand.z_as_relative = false
    grip_hand.z_index = 22
    grip_hand.centered = false
    var grip_data: Dictionary = rig_data["rail_grip"]
    var rel: Array = grip_data["hand_sprite_position"]
    grip_hand.position = Vector2(float(rel[0]), float(rel[1]))
    grip_hand.scale = Vector2.ONE * float(grip_data["hand_scale"])
    var source: String = "res://" + str(grip_data["hand_texture"])
    if ResourceLoader.exists(source):
        grip_hand.texture = load(source)
    else:
        missing.append("texture:right_grip_hand")
    grip_hand.visible = false
    grip_hand.set_meta("phase19_generated", true)
    if joints.has("right_forearm"):
        (joints["right_forearm"] as Node2D).add_child(grip_hand)
    original_right_forearm = art_nodes.get("right_forearm", null)

func get_grip_target_global() -> Vector2:
    var c: Array = rig_data["rail_grip"]["target_canvas"]
    var o: Array = rig_data["root_world_pivot"]
    return to_global(Vector2(float(c[0])-float(o[0]),float(c[1])-float(o[1])))

func get_grip_contact_global() -> Vector2:
    if grip_hand == null:
        return Vector2.INF
    var anchor: Array = rig_data["rail_grip"]["hand_pivot_local"]
    return (joints["right_forearm"] as Node2D).to_global(Vector2(float(anchor[0]),float(anchor[1])))

func grip_contact_error_px() -> float:
    return get_grip_contact_global().distance_to(get_grip_target_global()) / maxf(absf(global_scale.x), 0.00001)

func solve_grip_ik() -> void:
    # Phase26: solve in the *shoulder parent local coordinate system*, where
    # mirrored actors, parent rotation and nonuniform scale do not invert the
    # bend or change the length of the original 2D paintings.
    if not (joints.has("right_upper_arm") and joints.has("right_forearm") and joints.has("torso")):
        grip_unreachable = true
        if grip_hand != null:
            grip_hand.visible = false
        return
    var shoulder := joints["right_upper_arm"] as Node2D
    var elbow := joints["right_forearm"] as Node2D
    var parent := shoulder.get_parent() as Node2D
    var grip_data: Dictionary = rig_data["rail_grip"]
    var hand_xy: Array = grip_data["hand_pivot_local"]
    var hand_local := Vector2(float(hand_xy[0]), float(hand_xy[1]))
    var target_world := get_grip_target_global()
    # This rig's Node2D pivots are specifically calibrated to scale (1,1).
    # Deforming a limb would invalidate the painting's dimensions.
    if not shoulder.scale.is_equal_approx(Vector2.ONE) or not elbow.scale.is_equal_approx(Vector2.ONE):
        grip_unreachable = true
        grip_hand.visible = false
        push_warning("Art joint scale changed: refusing to stretch an approved painting")
        return
    var original_shoulder := shoulder.rotation
    var original_elbow := elbow.rotation
    var solved := _solve_grip_angles_local(parent, shoulder, elbow, hand_local, target_world)
    if not bool(solved.get("reachable", false)):
        # Respect the canonical bracing torso pose for unreachable postures;
        # this is an explicit, reversible body staging correction.
        (joints["torso"] as Node2D).rotation_degrees = 2.0
        solved = _solve_grip_angles_local(parent, shoulder, elbow, hand_local, target_world)
    if not bool(solved.get("reachable", false)):
        shoulder.rotation = original_shoulder
        elbow.rotation = original_elbow
        grip_unreachable = true
        grip_hand.visible = false
        push_warning("Rail target outside right-arm reach or joint rotation limits")
        return
    shoulder.rotation = float(solved["shoulder"])
    elbow.rotation = float(solved["elbow"])
    var canvas_error := grip_contact_error_px()
    if is_nan(canvas_error) or is_inf(canvas_error) or canvas_error > 2.0:
        shoulder.rotation = original_shoulder
        elbow.rotation = original_elbow
        grip_unreachable = true
        grip_hand.visible = false
        push_warning("Rail hand missed target: refusing a fake contact")
        return
    grip_unreachable = false
    grip_hand.visible = true

func _solve_grip_angles_local(parent: Node2D, shoulder: Node2D, elbow: Node2D, hand_local: Vector2, target_world: Vector2) -> Dictionary:
    var upper_local := elbow.position
    var l1 := upper_local.length()
    var l2 := hand_local.length()
    var displacement := parent.to_local(target_world) - shoulder.position
    var dist := displacement.length()
    if l1 <= 0.001 or l2 <= 0.001 or dist <= 0.001:
        return {"reachable": false, "reason": "degenerate"}
    if dist >= l1 + l2 - 0.0001 or dist <= absf(l1 - l2) + 0.0001:
        return {"reachable": false, "reason": "out_of_reach"}
    var base_angle := displacement.angle()
    var opening := acos(clampf((l1*l1 + dist*dist - l2*l2)/(2.0*l1*dist), -1.0, 1.0))
    var max_shoulder := deg_to_rad(45.0)
    var max_elbow := deg_to_rad(135.0)
    var best := {}
    var best_score := INF
    for side in [-1.0, 1.0]:
        var shoulder_angle := wrapf(base_angle + side*opening - upper_local.angle(), -PI, PI)
        var rotated_upper := upper_local.rotated(shoulder_angle)
        var to_hand := displacement - rotated_upper
        var elbow_angle := wrapf(to_hand.angle() - shoulder_angle - hand_local.angle(), -PI, PI)
        if absf(shoulder_angle) > max_shoulder + 0.0001 or absf(elbow_angle) > max_elbow + 0.0001:
            continue
        var score := absf(wrapf(shoulder_angle - shoulder.rotation, -PI, PI)) + 0.5*absf(wrapf(elbow_angle - elbow.rotation, -PI, PI))
        if score < best_score:
            best_score = score
            best = {"reachable": true, "shoulder": shoulder_angle, "elbow": elbow_angle}
    if best.is_empty():
        return {"reachable": false, "reason": "joint_limit"}
    return best

func set_rail_grip(enabled: bool) -> void:
    if grip_hand == null or rail_bg == null or rail_fg == null:
        return
    rail_grip_active = enabled
    if enabled:
        # This is a fixed-contact stage check, not a timeline export.
        auto_motion_review = false
        elapsed = 0.0
    grip_hand.visible = enabled
    rail_bg.visible = enabled
    rail_fg.visible = enabled
    if original_right_forearm:
        original_right_forearm.visible = not enabled
    if enabled:
        if last_pose != "rail_grip":
            set_pose("rail_grip")
        # Prevent persistent drift when the actor was previously posed.
        solve_grip_ik()
    else:
        # Return to the ordinary illustrated forearm without leaving the grip overlay visible.
        if last_pose == "rail_grip":
            set_pose("rest")

func get_asset_counts() -> Dictionary:
    return {"joints": joints.size(), "missing": missing.size(), "art_sprites": art_nodes.size(), "expression_count": rig_data.get("expressions",[]).size()}

func _process(delta: float) -> void:
    if not auto_motion_review or rig_data.is_empty() or Engine.is_editor_hint():
        return
    elapsed = fmod(elapsed + delta, 3.3)
    var before: Dictionary = MOTION_BEATS[0]
    var after: Dictionary = MOTION_BEATS[MOTION_BEATS.size() - 1]
    for i in range(MOTION_BEATS.size() - 1):
        if elapsed >= float(MOTION_BEATS[i]["time"]) and elapsed < float(MOTION_BEATS[i + 1]["time"]):
            before = MOTION_BEATS[i]
            after = MOTION_BEATS[i+1]
            break
    var timespan := maxf(float(after["time"]) - float(before["time"]), 0.001)
    var interpolation := clampf((elapsed - float(before["time"])) / timespan,0.0,1.0)
    var pose_a: Dictionary = rig_data["poses"][before["pose"]]
    var pose_b: Dictionary = rig_data["poses"][after["pose"]]
    for key in joints.keys():
        var a := float(pose_a.get(key,0.0))
        var b := float(pose_b.get(key,0.0))
        var joint: Node2D = joints[key] as Node2D
        joint.rotation_degrees = clampf(lerpf(a,b,interpolation),-45.0,45.0)
        joint.scale = Vector2.ONE
    if rail_grip_active:
        solve_grip_ik()
    # Expression changes use keyed drawings and never claim intermediate lip animation.
    var expression_name: String = str(before["expression"])
    if expression_name != preview_expression:
        set_expression(expression_name)

func _unhandled_key_input(event: InputEvent) -> void:
    if not (event is InputEventKey) or not event.pressed or event.echo:
        return
    match (event as InputEventKey).keycode:
        KEY_G: set_rail_grip(not rail_grip_active)
        KEY_1: set_pose("rest")
        KEY_2: set_pose("hear")
        KEY_3: set_pose("reach")
        KEY_4: set_pose("brace")
        KEY_5: set_pose("look")
        KEY_SPACE: auto_motion_review = not auto_motion_review
        KEY_ESCAPE:
            if ResourceLoader.exists("res://scenes/production_dashboard.tscn"):
                get_tree().change_scene_to_file("res://scenes/production_dashboard.tscn")
        KEY_E: set_expression("startled")
        KEY_Q: set_expression("neutral")