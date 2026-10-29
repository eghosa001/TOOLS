#!/usr/bin/env python3
"""MANDATORY SPlisHSPlasH -> splashsurf cache for authored flowing-fluid shots.

Requires two real installed binaries: SPHSimulator (SPlisHSPlasH/MIT) and
splashsurf (MIT). No made-up fluid movement, no silent shape-key substitute.
Scene inputs must be original, approved authored SPlisHSPlasH JSON files.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha256(file):
    result = hashlib.sha256()
    with file.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def find_binary(value, name):
    path = shutil.which(value)
    require(path, "%s binary not installed or not in PATH: %s" % (name, value))
    return path


def particle_sequence(files):
    require(files, "SPlisHSPlasH produced no supported VTK/BGEO particle cache")
    files = sorted(files)
    # A numerical suffix must exist to create an actual contiguous mesh sequence.
    parts = [re.search(r"(\d+)(?=\.(?:bgeo|vtk)$)", f.name, re.I) for f in files]
    require(all(parts), "Fluid cache files need numbered frames")
    numbers = [int(p.group(1)) for p in parts]
    require(len(set(numbers)) == len(numbers), "Duplicate fluid simulation frame numbers")
    require(numbers == list(range(numbers[0], numbers[0] + len(numbers))),
            "Missing frames in simulated fluid cache")
    first = files[0]
    pattern = first.name[:parts[0].start()] + "{}" + first.name[parts[0].end():]
    require(all(f.name[:p.start()] + "{}" + f.name[p.end():] == pattern
                for f, p in zip(files, parts)),
            "Particle outputs belong to multiple fluid bodies; select one numbered series")
    return first.parent / pattern


def run(scene, output, seconds, frames, particle_radius, simulator, surface):
    require(scene.is_file() and scene.suffix.lower() == ".json",
            "An existing authored SPlisHSPlasH JSON fluid scene is required")
    require(seconds > 0 and frames >= 2 and particle_radius > 0,
            "Invalid simulation duration, frames or particle radius")
    sim = find_binary(simulator, "SPlisHSPlasH SPHSimulator")
    recon = find_binary(surface, "splashsurf surface reconstruction")
    output.mkdir(parents=True, exist_ok=True)
    particles = output / "particles"
    meshes = output / "meshes"
    particles.mkdir(exist_ok=True)
    meshes.mkdir(exist_ok=True)
    simcmd = [sim, str(scene.resolve()), "--no-gui", "--stopAt", str(seconds),
              "--output-dir", str(particles)]
    subprocess.run(simcmd, check=True, timeout=1500)
    files = list(particles.rglob("*.bgeo")) + list(particles.rglob("*.vtk"))
    files = [f for f in files if f.stat().st_size > 128]
    require(len(files) >= frames,
            "Fluid simulation output incomplete (%d cached files; %d frames required)"
            % (len(files), frames))
    # Include exactly the requested frame count, without retiming by duplicate frames.
    selected = sorted(files)[:frames]
    seq = particle_sequence(selected)
    cmd = [recon, "reconstruct", str(seq), "-r", str(particle_radius),
           "-l", "2.0", "-c", "0.65", "-t", "0.6",
           "--mesh-smoothing-weights=on", "--mesh-smoothing-iters", "15",
           "--mesh-cleanup=on", "--normals=on",
           "-o", str(meshes / "fluid_{}.obj")]
    subprocess.run(cmd, check=True, timeout=600)
    objs = sorted(meshes.glob("fluid_*.obj"))
    require(len(objs) >= frames and all(f.stat().st_size > 128 for f in objs[:frames]),
            "Surface reconstruction did not produce complete nonempty 3D mesh cache")
    report = {
        "solver": "SPlisHSPlasH", "reconstruction": "splashsurf",
        "source_scene_sha256": sha256(scene), "simulated_frames": frames,
        "duration_seconds": seconds, "particle_radius": particle_radius,
        "particle_files": len(selected), "surface_mesh_files": len(objs),
        "first_mesh_sha256": sha256(objs[0]), "last_mesh_sha256": sha256(objs[frames - 1]),
        "render_import": "Blender Sequence Loader (install/verify separately)",
        "editorial_approval": False,
    }
    (output / "physics_bake_manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description="Real SPH liquid simulation + usable OBJ frame sequence")
    p.add_argument("--scene", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--seconds", type=float, default=5.0)
    p.add_argument("--frames", type=int, default=120)
    p.add_argument("--particle-radius", type=float, required=True)
    p.add_argument("--simulator", default="SPHSimulator")
    p.add_argument("--surface", default="splashsurf")
    args = p.parse_args()
    print(json.dumps(run(args.scene, args.output, args.seconds, args.frames,
                         args.particle_radius, args.simulator, args.surface), indent=2))


if __name__ == "__main__":
    main()
