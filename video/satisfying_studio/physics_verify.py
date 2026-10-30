#!/usr/bin/env python3
"""Checks real physics-cache evidence; never judges aesthetic quality."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ALLOWED = {
    "blender_softbody", "SPlisHSPlasH",
    "blender_rigidbody", "blender_cloth", "blender_animation"
}


class PhysicsEvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise PhysicsEvidenceError(message)


def sha256(file: Path) -> str:
    h = hashlib.sha256()
    with file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def in_root(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and relative.strip(), "Missing physics cache file path")
    p = Path(relative)
    require(not p.is_absolute() and ".." not in p.parts, "Unsafe physics evidence path")
    result = (root / p).resolve()
    require(result.is_relative_to(root.resolve()), "Physics evidence escapes project")
    return result


def verify(data: dict, root: Path) -> dict:
    rel = data.get("physics_cache_manifest")
    manifest_file = in_root(root, rel)
    require(manifest_file.is_file(), "Missing actual physics cache manifest")
    try:
        info = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PhysicsEvidenceError("Invalid physics cache JSON") from exc
    require(isinstance(info, dict), "Invalid physics cache data")
    solver = info.get("solver")
    require(solver in ALLOWED, "Unsupported physics solver: %r" % solver)
    fps = data.get("fps", 24)
    duration = data.get("duration_seconds", 5)
    require(isinstance(fps, int) and fps > 0, "Invalid physics FPS")
    frames = int(round(duration * fps))
    require(frames > 1, "Invalid physics duration")
    if solver in ("blender_softbody", "blender_rigidbody", "blender_cloth"):
        require(info.get("baked_point_cache") is True,
                "No verified baked Blender physics cache")
        require(info.get("cached_frames", 0) >= frames,
                "Blender physics cache does not cover the entire video")
        source = in_root(manifest_file.parent, info.get("source_blend"))
        require(source.is_file() and source.suffix == ".blend",
                "Editable Blender physics source is missing")
        require(sha256(source) == info.get("source_blend_sha256"),
                "Editable Blender physics asset changed since bake")
        if solver == "blender_softbody":
            # An actual Director preflight is now compulsory, not a
            # suggestion that can be forgotten when a preview is exported.
            require(info.get("director_floating_risk") is False,
                    "ASMR Production Director: jelly floating check missing or failed")
            require(isinstance(info.get("director_camera"), dict),
                    "ASMR Production Director: camera decision not recorded")
            evidence = manifest_file.parent / "actual_physics_camera_framing.json"
            require(evidence.is_file(),
                    "ASMR Production Director: baked camera evidence missing")
            try:
                frames_on_camera = json.loads(evidence.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise PhysicsEvidenceError("Invalid Director framing evidence") from exc
            require(isinstance(frames_on_camera, list) and len(frames_on_camera) >= 7,
                    "ASMR Director must inspect at least 7 physical checkpoints")
            for f in frames_on_camera:
                require(all(isinstance(f.get(k), (int, float)) for k in
                            ("min_x", "max_x", "min_y", "max_y")),
                        "Invalid physical camera geometry in Director proof")
                require(f["min_x"] >= .025 and f["max_x"] <= .975 and
                        f["min_y"] >= .025 and f["max_y"] <= .975,
                        "ASMR Director detected physically cropped jelly in final proof")
    elif solver == "SPlisHSPlasH":
        require(info.get("surface_mesh_files", 0) >= frames,
                "Incomplete SPH reconstructed mesh sequence")
        require(info.get("simulated_frames", 0) >= frames,
                "Incomplete SPH particle cache")
        require(isinstance(info.get("source_scene_sha256"), str)
                and len(info["source_scene_sha256"]) == 64,
                "Missing originating SPH scene hash")
        meshdir = manifest_file.parent / "meshes"
        meshes = sorted(meshdir.glob("fluid_*.obj"))
        require(len(meshes) >= frames, "Missing physical SPH OBJ mesh frames")
        require(sha256(meshes[0]) == info.get("first_mesh_sha256"),
                "SPH first mesh changed after simulation")
        require(sha256(meshes[frames - 1]) == info.get("last_mesh_sha256"),
                "SPH last mesh changed after simulation")
    else:
        # Non-physical actions (e.g. rigged face, atmosphere, carefully authored
        # mechanical layout) may use genuine 3D animation, NEVER video-footage.
        source = in_root(manifest_file.parent, info.get("source_blend"))
        require(source.is_file() and source.suffix.lower() == ".blend",
                "CGI animation requires editable Blender .blend source")
        require(sha256(source) == info.get("source_blend_sha256"),
                "Animated Blender source changed since 3D scene verification")
        require(info.get("animated_frames_verified", 0) >= frames,
                "CGI animation must cover the complete shot frame count")
        require(info.get("actual_3d_animation") is True,
                "CGI scene must contain genuine evaluated 3D animation")
        require(info.get("review_status") == "unapproved",
                "Automated CGI scene validation must not self-approve artistic quality")
    return info


def verify_shots(data: dict, root: Path) -> list[dict]:
    """Evidence for each manually directed shot in a mixed-material ASMR film.

    For a single 5-second pilot, the existing physics_cache_manifest path works.
    Longer or multi-shot masters must bind physical source evidence to each shot;
    one successful five-second bake is NOT proof of a 10-minute film.
    """
    from studio_formats import get_format, StudioFormatError
    try:
        fmt = get_format(data["format_id"])
    except (KeyError, StudioFormatError) as exc:
        raise PhysicsEvidenceError("Invalid registered ASMR format") from exc
    route = data.get("selected_asset_route")
    require(route == "scene", "Registered ASMR formats require actual Blender CGI, not filming")
    expected = fmt["required_evidence_solver"]
    shots = data.get("manually_directed_shots", [])
    require(isinstance(shots, list) and len(shots) > 0,
            "Missing authored shot list for per-shot material verification")
    result = []
    for i, shot in enumerate(shots, 1):
        require(isinstance(shot, dict), "Invalid authored shot")
        rel = shot.get("physics_cache_manifest")
        if not rel and len(shots) == 1:
            rel = data.get("physics_cache_manifest")
        require(isinstance(rel, str) and rel.strip(),
                f"Shot {i}: missing independent physics/footage evidence path")
        duration = shot["end_seconds"] - shot["start_seconds"]
        # IMPORTANT: shot-level cache frame count (not full film fake evidence).
        info = verify({
            "physics_cache_manifest": rel,
            "fps": data.get("fps", 24),
            "duration_seconds": duration,
        }, root)
        require(info["solver"] == expected,
                f"Shot {i}: evidence solver {info['solver']} does not match "
                f"selected {route} format solver {expected}")
        result.append({"shot_index": i, "solver": info["solver"], "evidence_path": rel})
    return result
