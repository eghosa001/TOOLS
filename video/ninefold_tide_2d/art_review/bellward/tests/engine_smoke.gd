extends SceneTree

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var scene: PackedScene = load("res://scenes/bellward_original.tscn")
    if scene == null:
        push_error("Bellward scene failed to load")
        quit(1)
        return
    var instance: Node2D = scene.instantiate()
    get_root().add_child(instance)
    var actor: Sprite2D = instance.get_node("Master") as Sprite2D
    if actor == null or actor.texture == null:
        push_error("Bellward scene missing artwork texture")
        quit(2)
        return
    if actor.texture.get_size() != Vector2(2688, 1520):
        push_error("Bellward artwork changed dimensions")
        quit(3)
        return
    if actor.centered or actor.position != Vector2.ZERO or actor.scale != Vector2.ONE or abs(actor.rotation) > 0.000001:
        push_error("Bellward painting transformed instead of preserving source geometry")
        quit(4)
        return
    var sha: String = FileAccess.get_sha256("res://assets/bellward_original_2688.png")
    if sha != "267cd029e3b9382a7b5202e518586f2fe85f5374871f821144444770785d0d54":
        push_error("Bellward image hash mismatch: " + sha)
        quit(5)
        return
    print("PASS Bellward: actual Godot 4 scene imports unchanged 2688x1520 full-resolution painting; no transform")
    quit(0)
