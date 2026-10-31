@tool
extends Node2D
## Six ordered 2D set layers; missing artwork intentionally leaves an empty scene.
## All 15 instances are staging plans, NOT registered approved backgrounds.
@export var set_id: String = ""
const PATH := "res://data/production_inventory.json"
const Z_LEVELS := [-100,-60,-30,0,5,90]
var set_record: Dictionary = {}
var bound_images := 0
var missing_layers: PackedStringArray = []
func _ready() -> void:
    var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
    if not (doc is Dictionary):
        push_error("Missing world structure manifest")
        return
    for candidate in doc.get("set_staging_slots",[]):
        if str(candidate.get("id","")) == set_id:
            set_record = candidate
            break
    if set_record.is_empty():
        push_error("Unrecognized world staging slot: "+set_id)
        return
    for idx in range(set_record.get("layer_slots",[]).size()):
        var label := str(set_record["layer_slots"][idx])
        var node := Sprite2D.new()
        node.name = label
        node.centered = false
        node.z_as_relative = false
        node.z_index = Z_LEVELS[idx]
        add_child(node)
        var candidate_path := "res://private_art/sets/%s/%s.png" % [set_id,label]
        if ResourceLoader.exists(candidate_path):
            node.texture = load(candidate_path)
            bound_images += 1
        else:
            missing_layers.append(label)
func get_art_status() -> Dictionary:
    return {"set_id":set_id,"bound_layers":bound_images,"missing_layers":missing_layers.size(),
        "artist_approved":false,"production_ready":false}