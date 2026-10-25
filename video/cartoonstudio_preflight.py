#!/usr/bin/env python3
"""Offline preflight of CartoonStudio's exact embedded story parser and render input."""
from __future__ import annotations

import ast
import base64
import hashlib
import io
import json
import subprocess
import types
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from kaggle_actions_runner import update_notebook, validate_story

HERE = Path(__file__).resolve().parent


def embedded_source_archive(notebook: dict) -> bytes:
    source_cells = [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code" and "SOURCE_ARCHIVE_B64 =" in "".join(cell.get("source", []))
    ]
    if len(source_cells) != 1:
        raise ValueError(f"Expected one source archive cell, got {len(source_cells)}")
    for node in ast.parse(source_cells[0]).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SOURCE_ARCHIVE_B64" for t in node.targets):
            encoded = ast.literal_eval(node.value)
            return base64.b64decode(encoded, validate=True)
    raise ValueError("SOURCE_ARCHIVE_B64 assignment not found")


def main() -> None:
    original = json.loads((HERE / "story.json").read_text(encoding="utf-8"))
    story = validate_story(original)
    notebook_path = HERE / "CartoonStudio-Kaggle-HighQuality.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="cartoonstudio-preflight-") as d:
        root = Path(d)
        patched = root / "test.ipynb"
        shutil.copy2(notebook_path, patched)
        update_notebook(patched, story, "preview")
        patched_data = json.loads(patched.read_text(encoding="utf-8"))
        source_data = embedded_source_archive(patched_data)
        archive_code = next(
            "".join(cell.get("source", []))
            for cell in patched_data["cells"]
            if cell.get("cell_type") == "code" and "SOURCE_ARCHIVE_B64 =" in "".join(cell.get("source", []))
        )
        checksum_value = None
        for node in ast.parse(archive_code).body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "expected_sha256" for t in node.targets
            ):
                checksum_value = ast.literal_eval(node.value)
        if hashlib.sha256(source_data).hexdigest() != checksum_value:
            raise ValueError("Updated embedded ZIP checksum does not match notebook extraction guard")
        print("PASS: upgraded source archive checksum matches notebook guard")
        with zipfile.ZipFile(io.BytesIO(source_data)) as archive:
            for member in archive.namelist():
                parts = Path(member).parts
                if Path(member).is_absolute() or ".." in parts:
                    raise ValueError("Unsafe entry in embedded source archive")
            archive.extractall(root)
        source_roots = list(root.glob("*/cartoon_studio/story.py"))
        if len(source_roots) != 1:
            raise ValueError(f"Expected one embedded renderer story.py, found {len(source_roots)}")
        source_root = source_roots[0].parent.parent
        sys.path.insert(0, str(source_root))
        for relative in ("cartoon_studio/story.py", "cartoon_studio/cli.py", "renderer/blender_scene.py"):
            candidate = source_root / relative
            compile(candidate.read_text(encoding="utf-8"), str(candidate), "exec")
        renderer_source = (source_root / "renderer/blender_scene.py").read_text(encoding="utf-8")
        for name in ("def open_mouth(", "def ball(", "def pivot(", "def material(", "def box(", "def set_smooth_keys("):
            pos = renderer_source.find(name)
            if pos < 0:
                raise RuntimeError("Cannot inspect Blender helper " + name)
            next_def = renderer_source.find("\\ndef ", pos+len(name))
            print("ENGINE_HELPER " + name + "\\n" + renderer_source[pos:next_def if next_def >= 0 else pos+2500][:5000], flush=True)
        if "rgba(color_name)" not in renderer_source:
            raise RuntimeError("Renderer is not using unrestricted RGB/hex character materials")
        if "render_scene_sequence" not in (source_root / "cartoon_studio/cli.py").read_text(encoding="utf-8"):
            raise RuntimeError("Scene composition is not connected to the Blender CLI")
        from cartoon_studio.story import read_story

        story_path = root / "input.json"
        story_path.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
        read_story(story_path)
        from studio_contract import rgba, validate_scene_contract
        assert rgba("#12abef")[:3] == (18/255, 171/255, 239/255)
        assert rgba("rgb(255, 128, 0)")[0] == 1.0
        assert rgba([0.1, 0.3, 0.8])[2] == 0.8
        test_story = json.loads(json.dumps(story))
        test_story["visual_prompt"] = "Original stage with detailed camera direction. " * 55
        test_story["characters"]["lelli"]["color"] = "#17abcf"
        for index, action in enumerate(("point", "walk", "hop", "turn", "clap")):
            test_story["dialogue"][index]["action"] = action
        half = len(test_story["dialogue"]) // 2
        test_story["scenes"] = [
            {"title": "Garden wide", "start_line": 1, "end_line": half,
             "stage": "forest", "camera": "wide", "background_color": "#e9d8ae"},
            {"title": "Garden dialogue", "start_line": half+1,
             "end_line": len(test_story["dialogue"]),
             "stage": "forest", "camera": "close", "background_color": "#aabbcc"},
        ]
        validate_story(test_story)
        validate_scene_contract(test_story)
        test_input = root / "complex.json"
        test_input.write_text(json.dumps(test_story), encoding="utf-8")
        read_story(test_input)
        complex_path = root / "complex.ipynb"
        shutil.copy2(notebook_path, complex_path)
        update_notebook(complex_path, test_story, "preview")
        complex_data = json.loads(complex_path.read_text(encoding="utf-8"))
        complex_cells = [
            "".join(c.get("source", [])) for c in complex_data["cells"]
            if c.get("cell_type") == "code" and "STORY_TITLE =" in "".join(c.get("source", []))
        ]
        if len(complex_cells) != 1 or "'scenes':" not in complex_cells[0] and "SCENES = " not in complex_cells[0]:
            raise RuntimeError("Detailed scene input was dropped from notebook")
        compile(complex_cells[0], "complex_story_input", "exec")
        print("PASS: unrestricted RGB, long prompt, and two scene cuts accepted")
        # Exercise the real scene composer using tiny, synthetic FFmpeg clips.
        # This deliberately never runs Blender or submits a Kaggle render.
        from cartoon_studio.studio_scenes import render_scene_sequence
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise RuntimeError("Offline scene composition requires FFmpeg and ffprobe")
        seen_dialogue = []
        def synthetic_scene_render(part_args):
            source = json.loads(Path(part_args.story).read_text(encoding="utf-8"))
            seen_dialogue.extend(source["dialogue"])
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=blue:s=160x90:r=24",
                "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
                "-t", "1.1", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", str(part_args.output),
            ], check=True, timeout=90)
        render_args = types.SimpleNamespace(
            work=str(root / "synthetic_work"), output=str(root / "joined.mp4"),
            preview_seconds=0,
        )
        render_scene_sequence(test_story, render_args, synthetic_scene_render)
        if seen_dialogue != test_story["dialogue"] or not Path(render_args.output).is_file():
            raise RuntimeError("Scene composer changed dialogue or failed to join video")
        print("PASS: two synthetic MP4 scenes joined with all dialogue data intact")
        prepared_cell = [
            "".join(c.get("source", []))
            for c in patched_data["cells"]
            if c.get("cell_type") == "code" and "STORY_TITLE =" in "".join(c.get("source", []))
        ]
        if len(prepared_cell) != 1 or story["title"] not in prepared_cell[0]:
            raise ValueError("Notebook story cell was not populated")
        render_cell = [
            "".join(c.get("source", []))
            for c in patched_data["cells"]
            if c.get("cell_type") == "code" and "'--preview-seconds'" in "".join(c.get("source", []))
        ]
        if len(render_cell) != 1 or "'--preview-seconds','3'" not in render_cell[0].replace(" ", ""):
            raise ValueError("Notebook preview setting is missing or not 3 seconds")
    print(f"PASS: embedded renderer accepted '{story['title']}'")
    print(f"PASS: {len(story['dialogue'])} original dialogue entries preserved")
    print("PASS: notebook updated for preview without starting Kaggle")


if __name__ == "__main__":
    main()
