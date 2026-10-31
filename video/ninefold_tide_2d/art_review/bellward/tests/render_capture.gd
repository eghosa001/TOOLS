extends SceneTree
## Renders the actual unchanged Godot 2D art into an offscreen framebuffer.
## Run with a real rendering driver (for example xvfb-run Godot OpenGL), not --headless.

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var viewport := SubViewport.new()
    viewport.size = Vector2i(2688, 1520)
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    get_root().add_child(viewport)

    var scene: PackedScene = load("res://scenes/bellward_original.tscn")
    if scene == null:
        push_error("Cannot load original Bellward scene")
        quit(1)
        return
    var instance: Node = scene.instantiate()
    viewport.add_child(instance)
    # Allow textures and render targets to update at their native resolution.
    for i in range(8):
        await process_frame
    await RenderingServer.frame_post_draw
    var img: Image = viewport.get_texture().get_image()
    if img == null or img.is_empty() or img.get_width() != 2688 or img.get_height() != 1520:
        push_error("Godot screenshot not present at native resolution")
        quit(2)
        return
    var output: String = "res://bellward_engine_capture.png"
    var result: Error = img.save_png(output)
    if result != OK:
        push_error("Unable to save Godot pixel capture: " + str(result))
        quit(3)
        return
    print("PASS Bellward real 2D rendering: " + output)
    quit(0)
