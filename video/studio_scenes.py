"""Actual per-scene Blender renders, joined with FFmpeg without rewriting dialogue."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path

from .studio_contract import validate_scene_contract


def render_scene_sequence(story, args, render_one_scene):
    """Render each shot group with independent stage, lighting and camera.

    This is deterministic staging from prepared assets and fallback sets,
    NOT generation of a new 3D world from a visual prompt.
    """
    scenes = validate_scene_contract(story)
    if not scenes:
        raise ValueError("No scenes to render")
    preview = bool(args.preview_seconds)
    chosen = scenes[:1] if preview else scenes
    root = Path(args.work).expanduser().resolve() / "scene_renders"
    root.mkdir(parents=True, exist_ok=True)
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    clips = []
    for index, scene in enumerate(chosen, 1):
        current = {key: copy.deepcopy(value) for key, value in story.items() if key != "scenes"}
        current["scene"] = scene.get("stage", "auto")
        current["visual_prompt"] = scene.get("visual_prompt", story.get("visual_prompt", ""))
        current["dialogue"] = copy.deepcopy(story["dialogue"][scene["start_line"]-1:scene["end_line"]])
        current["scene_options"] = {
            key: scene[key] for key in ("camera", "background_color", "environment_file")
            if key in scene
        }
        work = root / f"scene_{index:03d}"
        work.mkdir(exist_ok=True)
        input_json = work / "story.json"
        input_json.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        part_output = work / "clip.mp4"
        part_args = copy.copy(args)
        part_args.story = str(input_json)
        part_args.work = str(work / "work")
        part_args.output = str(part_output)
        part_args.preview_seconds = args.preview_seconds if preview else 0
        print(f"SCENE {index}/{len(chosen)}: {scene.get('title','Untitled')}; "
              f"lines {scene['start_line']}..{scene['end_line']} / stage {current['scene']}",
              flush=True)
        render_one_scene(part_args)
        if not part_output.is_file() or part_output.stat().st_size <= 1024:
            raise RuntimeError(f"Scene {index} produced no valid MP4")
        clips.append(part_output)
    if len(clips) == 1:
        shutil.copy2(clips[0], output)
    else:
        concat_file = root / "scene_list.txt"
        concat_file.write_text(
            "".join("file '" + str(p.resolve()).replace("'", "'\\''") + "'\n" for p in clips),
            encoding="utf-8",
        )
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c", "copy", "-movflags", "+faststart", str(output),
        ], check=True)
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-of", "json", str(output),
    ], capture_output=True, text=True, check=True)
    metadata = json.loads(probe.stdout)["format"]
    if float(metadata["duration"]) < 1 or int(metadata["size"]) <= 1024:
        raise RuntimeError("Merged scene MP4 is missing or too short")
    print(f"SCENE-BASED MP4 SUCCESS: {output} ({len(clips)} scenes, "
          f"{float(metadata['duration']):.2f} seconds)", flush=True)
