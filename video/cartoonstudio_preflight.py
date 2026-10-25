#!/usr/bin/env python3
"""Offline preflight of CartoonStudio's exact embedded story parser and render input."""
from __future__ import annotations

import ast
import base64
import hashlib
import io
import json
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
        if not all(color in renderer_source for color in ("'turquoise'", "'ochre'")):
            raise RuntimeError("3-character renderer is missing the requested palette")
        from cartoon_studio.story import read_story

        story_path = root / "input.json"
        story_path.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
        read_story(story_path)
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
    print(f"PASS: {len(story['dialogue'])} dialogue entries, {len(story['visual_prompt'])}/1000 prompt characters")
    print("PASS: notebook updated for preview without starting Kaggle")


if __name__ == "__main__":
    main()
