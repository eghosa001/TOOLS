@tool
extends Node2D
## Shared *engineering-only* 2D cutout rig for 20 different canon characters.
## No generated art is painted. Named Sprite2D slots remain empty until authentic
## independently reviewed source artwork is supplied. Naya's Phase26 working rig
## is preserved separately; this generic rig is not a replacement for it.
@export var character_id: String = ""
@export_enum("front", "front_three_quarter", "profile", "rear_three_quarter", "rear") var art_view: String = "front"
@export_enum("rest", "brace", "reach", "point", "walk_left", "walk_right") var preview_pose: String = "rest"
@export var missing_art_warning := false

const INVENTORY_PATH := "res://data/production_inventory.json"
const PARENT: Dictionary = {
    "pelvis": "", "torso":"pelvis", "head":"torso",
    "upper_arm_left":"torso", "forearm_left":"upper_arm_left", "hand_left":"forearm_left",
    "upper_arm_right":"torso", "forearm_right":"upper_arm_right", "hand_right":"forearm_right",
    "thigh_left":"pelvis", "shin_left":"thigh_left", "foot_left":"shin_left",
    "thigh_right":"pelvis", "shin_right":"thigh_right", "foot_right":"shin_right"
}
# Named pivots are deliberately SYNTHETIC and normalized, not the anatomical
# measurements of any particular character's completed five-view art.
const LOCAL_PIVOTS: Dictionary = {
    "pelvis": Vector2.ZERO, "torso":Vector2(0,-42), "head":Vector2(0,-74),
    "upper_arm_left":Vector2(-22,-55),"forearm_left":Vector2(-42,0),"hand_left":Vector2(-33,0),
    "upper_arm_right":Vector2(22,-55),"forearm_right":Vector2(42,0),"hand_right":Vector2(33,0),
    "thigh_left":Vector2(-12,10),"shin_left":Vector2(-5,58),"foot_left":Vector2(-3,55),
    "thigh_right":Vector2(12,10),"shin_right":Vector2(5,58),"foot_right":Vector2(3,55)
}
const Z: Dictionary = {
    "thigh_left":-4,"shin_left":-4,"foot_left":-4,
    "upper_arm_left":-2,"forearm_left":-2,"hand_left":-2,
    "pelvis":0,"torso":1,"thigh_right":2,"shin_right":2,"foot_right":2,
    "head":3,"upper_arm_right":4,"forearm_right":4,"hand_right":4
}
const ANGLE_LIMITS: Dictionary = {
    "head":22.0,"torso":18.0,"upper_arm_left":115.0,"upper_arm_right":115.0,
    "forearm_left":135.0,"forearm_right":135.0,"thigh_left":85.0,"thigh_right":85.0,
    "shin_left":110.0,"shin_right":110.0,"foot_left":40.0,"foot_right":40.0,
    "hand_left":50.0,"hand_right":50.0,"pelvis":15.0
}
var record: Dictionary = {}
var joints: Dictionary = {}
var art_slots: Dictionary = {}
var missing_art: PackedStringArray = []
var art_approved := false
var review_pose := "rest"

func _ready() -> void:
    if character_id.is_empty():
        push_error("Cast ID required; this is not a generic background person")
        return
    var parsed = JSON.parse_string(FileAccess.get_file_as_string(INVENTORY_PATH))
    if not (parsed is Dictionary):
        push_error("Unreadable canon cast manifest")
        return
    for item in parsed.get("characters", []):
        if str(item.get("id", "")) == character_id:
            record = item
            break
    if record.is_empty():
        push_error("Unknown character ID in canon source: " + character_id)
        return
    build_engineering_rig()
    apply_pose(preview_pose)
    bind_art_view(art_view)
    if missing_art_warning and not missing_art.is_empty():
        push_warning("No final layered art for %s; engineering only" % character_id)

func build_engineering_rig() -> void:
    for n in get_children():
        if n.has_meta("engineering_generated"):
            n.free()
    joints.clear()
    art_slots.clear()
    missing_art.clear()
    # Do NOT rescale final character art from a generic height. These are abstract,
    # normalized movement pivots; final anatomical pivots must be art-calibrated.
    for key in PARENT.keys():
        _make_joint(str(key))

func _make_joint(part: String) -> Node2D:
    if joints.has(part):
        return joints[part]
    var parent_id := str(PARENT[part])
    var owner: Node2D = self
    if not parent_id.is_empty():
        owner = _make_joint(parent_id)
    var pivot := Node2D.new()
    pivot.name = part
    pivot.position = LOCAL_PIVOTS[part]
    pivot.set_meta("engineering_generated", true)
    owner.add_child(pivot)
    joints[part] = pivot
    var sprite := Sprite2D.new()
    sprite.name = "ApprovedArtwork"
    sprite.centered = false
    sprite.z_as_relative = false
    sprite.z_index = int(Z.get(part,0))
    pivot.add_child(sprite)
    art_slots[part] = sprite
    return pivot

func bind_art_view(view: String) -> void:
    missing_art.clear()
    if not record.get("views_required", []).has(view):
        push_error("Unapproved or unknown viewpoint: " + view)
        return
    art_view = view
    for key in art_slots.keys():
        var part := str(key)
        var candidate := "res://private_art/characters/%s/%s/%s.png" % [character_id, view, part]
        var sprite: Sprite2D = art_slots[part]
        sprite.texture = null
        if ResourceLoader.exists(candidate):
            sprite.texture = load(candidate)
        else:
            missing_art.append("%s/%s" % [view,part])
    art_approved = bool(record.get("rig_art_approved", false)) and missing_art.is_empty()

func expression_ready(expression_name: String) -> bool:
    if not record.get("expression_slots", []).has(expression_name):
        return false
    return ResourceLoader.exists("res://private_art/characters/%s/expressions/%s.png" % [character_id,expression_name])

func mouth_ready(mouth_name: String) -> bool:
    if not record.get("mouth_slots", []).has(mouth_name):
        return false
    return ResourceLoader.exists("res://private_art/characters/%s/mouths/%s.png" % [character_id,mouth_name])

func apply_pose(pose: String) -> bool:
    if not ["rest", "brace", "reach", "point", "walk_left", "walk_right"].has(pose):
        return false
    reset_joints()
    if joints.is_empty():
        return false
    review_pose = pose
    match pose:
        "brace":
            set_joint_angle("torso",8.0)
            set_joint_angle("upper_arm_left",25.0)
            set_joint_angle("upper_arm_right",-25.0)
            set_joint_angle("shin_left",-13.0)
        "reach":
            set_joint_angle("torso",-6.0)
            set_joint_angle("upper_arm_right",-85.0)
            set_joint_angle("forearm_right",50.0)
        "point":
            set_joint_angle("upper_arm_left",60.0)
            set_joint_angle("forearm_left",-38.0)
        "walk_left":
            set_joint_angle("thigh_left",-22.0)
            set_joint_angle("thigh_right",22.0)
            set_joint_angle("upper_arm_left",14.0)
            set_joint_angle("upper_arm_right",-14.0)
        "walk_right":
            set_joint_angle("thigh_left",22.0)
            set_joint_angle("thigh_right",-22.0)
            set_joint_angle("upper_arm_left",-14.0)
            set_joint_angle("upper_arm_right",14.0)
    return true

func reset_joints() -> void:
    for key in joints.keys():
        var pivot: Node2D = joints[key]
        pivot.rotation = 0.0
        pivot.scale = Vector2.ONE

func set_joint_angle(part: String, degrees: float) -> bool:
    if not joints.has(part):
        return false
    if not is_finite(degrees):
        return false
    var range_deg := float(ANGLE_LIMITS.get(part,0))
    (joints[part] as Node2D).rotation_degrees = clampf(degrees,-range_deg,range_deg)
    return true

func get_art_status() -> Dictionary:
    return {"character_id": character_id,"view":art_view,
        "part_slots":art_slots.size(),"missing_in_current_view":missing_art.size(),
        "full_five_views_verified":false,"human_art_approved":art_approved,
        "production_ready":false}