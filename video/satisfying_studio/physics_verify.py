#!/usr/bin/env python3
"""Checks real physics-cache evidence; never judges aesthetic quality."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ALLOWED = {
    "blender_softbody", "SPlisHSPlasH",
    "blender_rigidbody", "blender_cloth", "physical_footage"
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
        footage = in_root(manifest_file.parent, info.get("original_source"))
        require(footage.is_file(), "Missing original physical camera footage")
        require(sha256(footage) == info.get("original_source_sha256"),
                "Source footage changed after review")
    return info
