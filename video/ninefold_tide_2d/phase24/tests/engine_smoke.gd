extends SceneTree
## Load the exact staged MIT third-party addon without private artwork.
func _initialize() -> void:
    var script_resource: Script = load("res://addons/easyik/nodes/easy_ik_manager.gd") as Script
    if script_resource == null:
        push_error("Missing EasyIK runtime script")
        quit(1)
        return
    var instance: Variant = script_resource.new()
    if not (instance is Node2D):
        push_error("EasyIKManager must extend Node2D")
        quit(1)
        return
    (instance as Node2D).free()
    print("PASS Godot native optional EasyIK intake (mock only, no production)")
    quit(0)
