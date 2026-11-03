extends SceneTree

func _initialize() -> void:
    call_deferred("_inspect")

func _inspect() -> void:
    var files := ["res://assets/knight.glb", "res://assets/kaykit_modern_movement.glb", "res://assets/kaykit_modern_general.glb", "res://assets/kaykit_modern_combat.glb", "res://assets/castle.glb"]
    for file in files:
        var source = load(file)
        if source == null or not source is PackedScene:
            push_error("MISSING_OR_UNIMPORTABLE_MODEL " + file)
            quit(3)
            return
        var model: Node3D = source.instantiate()
        root.add_child(model)
        var skeletons: Array = []
        var players: Array = []
        _scan(model, skeletons, players)
        var full: Array = []
        for skel in skeletons:
            var bones: Array = []
            for i in range(skel.get_bone_count()):
                bones.append(skel.get_bone_name(i))
            full.append({"path": str(model.get_path_to(skel)), "bones": bones})
        var clips: Array = []
        for player in players:
            var names: Array = []
            for lib_name in player.get_animation_library_list():
                var lib = player.get_animation_library(lib_name)
                for anim_name in lib.get_animation_list():
                    var anim = lib.get_animation(anim_name)
                    var sample_tracks: Array = []
                    for i in range(min(anim.get_track_count(), 4)):
                        sample_tracks.append(str(anim.track_get_path(i)))
                    names.append({"name": anim_name, "tracks": anim.get_track_count(), "examples": sample_tracks})
            clips.append({"path": str(model.get_path_to(player)), "root": str(player.root_node), "clips": names})
        print("NATIVE_RIG_READBACK ", JSON.stringify({"source": file, "skeletons": full, "players": clips}))
        model.queue_free()
    quit(0)

func _scan(n: Node, skeletons: Array, players: Array) -> void:
    if n is Skeleton3D:
        skeletons.append(n)
    if n is AnimationPlayer:
        players.append(n)
    for child in n.get_children():
        _scan(child, skeletons, players)
