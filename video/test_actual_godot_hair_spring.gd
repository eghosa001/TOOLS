extends SceneTree
# Engineering QA: load original external GLBs + original MIT-licensed hair spring.
# No generated character mesh, no episode scene, no story or canon alteration.

func _find_class(node: Node, classname: String) -> Node:
    if node.get_class() == classname:
        return node
    for child in node.get_children():
        var found = _find_class(child, classname)
        if found != null:
            return found
    return null

func _finish_error(message: String) -> void:
    push_error(message)
    print("HAIR_SPRING_ORIGINAL_SOURCE_QA_FAIL ", message)
    quit(1)

func _initialize() -> void:
    call_deferred("_audit")

func _audit() -> void:
    var root_node = get_root()
    var body_scene = load("res://vitruvian_body.glb")
    var hair_scene = load("res://vitruvian_hair_rigged.glb")
    var face_scene = load("res://vitruvian_head.glb")
    if body_scene == null or hair_scene == null or face_scene == null:
        _finish_error("Published original three GLBs unavailable or not imported")
        return
    var body: Node3D = body_scene.instantiate()
    body.name = "OriginalBody"
    root_node.add_child(body)
    var body_skel: Skeleton3D = _find_class(body, "Skeleton3D") as Skeleton3D
    var action_player: AnimationPlayer = _find_class(body, "AnimationPlayer") as AnimationPlayer
    if body_skel == null or action_player == null:
        _finish_error("Original 52-bone skinned human body or animation player absent")
        return
    var head_index = body_skel.find_bone("mixamorig_Head")
    if head_index < 0 or body_skel.get_bone_count() < 50:
        _finish_error("Original Godot body Head bone not found")
        return
    if not action_player.has_animation("Idle") or not action_player.has_animation("Walk"):
        _finish_error("Publisher's original body idle/walk clips did not import")
        return
    var attach := BoneAttachment3D.new()
    attach.name = "OriginalHeadBoneAttachment"
    body_skel.add_child(attach)
    attach.bone_idx = head_index
    var head := face_scene.instantiate() as Node3D
    var hair := hair_scene.instantiate() as Node3D
    attach.add_child(head)
    attach.add_child(hair)
    head.global_transform = Transform3D.IDENTITY
    hair.global_transform = Transform3D.IDENTITY
    var hair_skel: Skeleton3D = _find_class(hair, "Skeleton3D") as Skeleton3D
    if hair_skel == null or hair_skel.get_bone_count() < 5:
        _finish_error("Original multi-bone rigged Hair Tool hair was not imported")
        return
    var spring = load("res://hair_spring.gd").new()
    hair.add_child(spring)
    spring.setup(hair_skel)
    spring.set_body_colliders(body_skel)
    if not spring._ready_ok or spring.joints.size() < 3:
        _finish_error("Original HairSpring failed to build a 3+ bone joint chain")
        return
    if spring.colliders.size() < 6:
        _finish_error("Original hair collision spheres missing or disconnected from body")
        return

    var hair_bones: Array[int] = []
    for j in spring.joints:
        hair_bones.append(int(j["idx"]))
    var baseline_rotations: Dictionary = {}
    for bone_id in hair_bones:
        baseline_rotations[bone_id] = hair_skel.get_bone_pose_rotation(bone_id)
    var original_head_quat = body_skel.get_bone_pose_rotation(head_index)
    var head_motion: float = 0.0
    var max_hair_spring_rotation: float = 0.0
    var max_tail_displacement: float = 0.0
    var tail_initial: Array = []
    for j in spring.joints:
        tail_initial.append(j["tail"])
    for frame in range(100):
        # Exercise both directions and abrupt motion, then let source spring settle.
        var angle = 0.28 * sin(float(frame) * 0.13)
        body_skel.set_bone_pose_rotation(head_index, original_head_quat * Quaternion(Vector3.UP, angle))
        body_skel.force_update_all_bone_transforms()
        hair_skel.force_update_all_bone_transforms()
        spring.step(1.0 / 60.0)
        hair_skel.force_update_all_bone_transforms()
        head_motion = maxf(head_motion, absf(angle))
        for bone_id in hair_bones:
            var q: Quaternion = hair_skel.get_bone_pose_rotation(bone_id)
            var angle_delta: float = q.angle_to(baseline_rotations[bone_id])
            if not is_finite(angle_delta):
                _finish_error("Source original hair simulation produced NaN bone rotation")
                return
            max_hair_spring_rotation = maxf(max_hair_spring_rotation, angle_delta)
        for n in range(spring.joints.size()):
            var tail: Vector3 = spring.joints[n]["tail"]
            if not tail.is_finite():
                _finish_error("Source original hair strand simulation produced nonfinite position")
                return
            max_tail_displacement = maxf(max_tail_displacement,tail.distance_to(tail_initial[n]))
    body_skel.set_bone_pose_rotation(head_index, original_head_quat)
    if head_motion < 0.20 or max_hair_spring_rotation < 0.003:
        _finish_error("Source HairSpring did not actually rotate skinned hair bones on moving head")
        return
    if max_tail_displacement < 0.003:
        _finish_error("Source HairSpring tail vertices did not physically move")
        return
    var report := {
        "source": "Pinned original ibrews/VitruvianGodot body+head+hair.glb and scenes/hair_spring.gd",
        "body_bones": body_skel.get_bone_count(),
        "hair_bones": hair_skel.get_bone_count(),
        "simulated_hair_joints": spring.joints.size(),
        "real_body_head_bone": body_skel.get_bone_name(head_index),
        "collision_spheres_attached_to_body": spring.colliders.size(),
        "original_idle_animation_available": action_player.has_animation("Idle"),
        "original_walk_animation_available": action_player.has_animation("Walk"),
        "physics_steps_executed": 100,
        "max_head_rotation_radians": head_motion,
        "max_simulated_hair_bone_rotation_radians": max_hair_spring_rotation,
        "max_original_hair_tail_motion_world_units": max_tail_displacement,
        "actual_source_spring_physics_tested": true,
        "pixel_perfect_hair_render_quality_verified": false,
        "artist_style_approved_by_user": false,
        "canon_mapping_changed": false,
        "rendered_episode_mp4": false
    }
    var file = FileAccess.open("res://hair-spring-qa.json", FileAccess.WRITE)
    if file == null:
        _finish_error("Could not write genuine source physics report")
        return
    file.store_string(JSON.stringify(report, "\t"))
    file.close()
    print("ACTUAL_ORIGINAL_GODOT_HAIR_SPRING_PHYSICS_PASS ", JSON.stringify(report))
    quit(0)
