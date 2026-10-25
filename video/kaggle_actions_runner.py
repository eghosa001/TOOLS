#!/usr/bin/env python3
"""Submit CartoonStudio story renders to the existing Kaggle kernel."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from pprint import pformat
from typing import Any
from cartoonstudio_source_patch import upgrade_notebook_embedded_source

KERNEL_ID = "aighewieghosa/cartoonstudio-3d-video-pipeline"
EMOTIONS = {"neutral", "happy", "surprised", "sad", "angry", "excited"}
ACTIONS = {"none", "wave", "nod", "point"}
STYLES = {"auto", "human", "cartoon"}


def run(args: list[str], timeout: int = 1800) -> str:
    print("Running:", " ".join(args[1:]), flush=True)
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    output = (result.stdout + "\n" + result.stderr).strip()
    if output:
        print(output, flush=True)
    if result.returncode:
        raise RuntimeError(f"Command failed with exit code {result.returncode}")
    return output


def validate_story(data: Any) -> dict[str, Any]:
    required = {"title", "visual_prompt", "visual_style", "characters", "dialogue"}
    if not isinstance(data, dict) or required - data.keys():
        missing = required - data.keys() if isinstance(data, dict) else required
        raise ValueError("Story JSON is missing required fields: " + ", ".join(sorted(missing)))
    if not isinstance(data["title"], str) or not data["title"].strip() or "replace" in data["title"].lower():
        raise ValueError("Set a real episode title in video/story.json before running")
    if not isinstance(data["visual_prompt"], str) or not data["visual_prompt"].strip() or "replace" in data["visual_prompt"].lower():
        raise ValueError("Set a real visual_prompt in video/story.json before running")
    if len(data["visual_prompt"]) > 1000:
        raise ValueError(f"visual_prompt exceeds the 1000-character CartoonStudio limit ({len(data['visual_prompt'])} characters)")
    if len(data["visual_prompt"]) > 1000:
        raise ValueError(f"visual_prompt exceeds the renderer 1000-character limit ({len(data['visual_prompt'])} characters)")
    if data["visual_style"] not in STYLES:
        raise ValueError("visual_style must be auto, human, or cartoon")
    chars = data["characters"]
    if not isinstance(chars, dict) or not chars:
        raise ValueError("characters must be a non-empty object")
    for key, character in chars.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", key):
            raise ValueError(f"Invalid character key: {key}")
        if not isinstance(character, dict) or not isinstance(character.get("voice"), str) or not isinstance(character.get("color"), str):
            raise ValueError(f"Character {key} needs string voice and color values")
    dialogue = data["dialogue"]
    if not isinstance(dialogue, list) or not dialogue:
        raise ValueError("dialogue must contain at least one line")
    for index, line in enumerate(dialogue, start=1):
        if not isinstance(line, dict) or line.get("speaker") not in chars:
            raise ValueError(f"Dialogue line {index} has a speaker absent from characters")
        if not isinstance(line.get("text"), str) or not line["text"].strip():
            raise ValueError(f"Dialogue line {index} has empty text")
        if line.get("emotion", "neutral") not in EMOTIONS or line.get("action", "none") not in ACTIONS:
            raise ValueError(f"Dialogue line {index} has an unsupported emotion or action")
    return data


def update_notebook(notebook_path: Path, story: dict[str, Any], mode: str) -> None:
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    upgrade_notebook_embedded_source(notebook)
    cells = notebook.get("cells", [])
    story_cells = [cell for cell in cells if cell.get("cell_type") == "code" and "STORY_TITLE =" in "".join(cell.get("source", []))]
    if len(story_cells) != 1:
        raise RuntimeError(f"Expected one editable story input cell, found {len(story_cells)}")
    cell = story_cells[0]
    source = "".join(cell.get("source", []))
    assignments = "\n".join([
        f"STORY_TITLE = {story['title']!r}",
        f"VISUAL_PROMPT = {story['visual_prompt']!r}",
        f"VISUAL_STYLE = {story['visual_style']!r}  # auto, human, or cartoon",
        f"CHARACTERS = {pformat(story['characters'], sort_dicts=False)}",
        f"DIALOGUE = {pformat(story['dialogue'], sort_dicts=False)}",
    ])
    source, count = re.subn(r"STORY_TITLE\s*=.*?(?=\n# Add dialogue entries)", assignments, source, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("The Kaggle notebook story cell layout changed; refusing to push")
    cell["source"] = source.splitlines(keepends=True)

    render_cells = [cell for cell in cells if cell.get("cell_type") == "code" and "--preview-seconds" in "".join(cell.get("source", []))]
    if len(render_cells) != 1:
        raise RuntimeError(f"Expected one render cell, found {len(render_cells)}")
    render_cell = render_cells[0]
    render_source = "".join(render_cell.get("source", []))
    duration = "0" if mode == "full" else "3"
    updated, matches = re.subn(r"(['\"]--preview-seconds['\"]\s*,\s*['\"])(\d+)(['\"])", lambda match: match.group(1) + duration + match.group(3), render_source, count=1)
    if matches != 1:
        raise RuntimeError("Could not safely set the preview/full duration; refusing to push")
    render_cell["source"] = updated.splitlines(keepends=True)
    notebook_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def get_status() -> str:
    return run(["kaggle", "kernels", "status", KERNEL_ID], timeout=120)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preview", "full"), required=True)
    parser.add_argument("--confirm-full", choices=("true", "false"), default="false")
    parser.add_argument("--notebook", type=Path, required=True)
    parser.add_argument("--story", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not os.getenv("KAGGLE_API_TOKEN"):
        raise RuntimeError("Add the Kaggle API token as the GitHub Actions secret KAGGLE_API_TOKEN")
    if args.mode == "full" and args.confirm_full != "true":
        raise RuntimeError("Full render blocked: choose the full render confirmation checkbox in GitHub Actions")
    if not args.notebook.is_file() or not args.story.is_file():
        raise FileNotFoundError("Notebook or story input file is missing")
    story = validate_story(json.loads(args.story.read_text(encoding="utf-8")))

    with tempfile.TemporaryDirectory(prefix="cartoonstudio-kaggle-") as tmp:
        folder = Path(tmp)
        run(["kaggle", "kernels", "pull", KERNEL_ID, "-p", str(folder), "-m"])
        metadata_path = folder / "kernel-metadata.json"
        if not metadata_path.is_file():
            raise RuntimeError("Kaggle CLI did not download kernel-metadata.json")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        code_file = Path(metadata.get("code_file", ""))
        if code_file.suffix != ".ipynb" or ".." in code_file.parts:
            raise RuntimeError("Unexpected notebook path in Kaggle metadata")
        target_notebook = folder / code_file
        target_notebook.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.notebook, target_notebook)
        update_notebook(target_notebook, story, args.mode)
        metadata["enable_gpu"] = True
        metadata["enable_internet"] = True
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        run(["kaggle", "kernels", "push", "-p", str(folder), "--accelerator", "NvidiaTeslaT4"], timeout=1800)

    print("Waiting for Kaggle render to finish…", flush=True)
    deadline = time.monotonic() + 5 * 60 * 60
    while time.monotonic() < deadline:
        status = get_status()
        normalized = status.upper()
        if "COMPLETE" in normalized or "SUCCESS" in normalized:
            break
        if any(marker in normalized for marker in ("ERROR", "FAILED", "CANCELLED")):
            # Include the Kaggle notebook traceback in GitHub Actions logs.
            # Do not automatically rerun a failed job and spend more GPU quota.
            try:
                diagnostic = subprocess.run(
                    ["kaggle", "kernels", "logs", KERNEL_ID],
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                log_text = (diagnostic.stdout + "\n" + diagnostic.stderr).strip()
                if log_text:
                    print("Kaggle notebook execution log (last 16000 characters):", flush=True)
                    print(log_text[-16000:], flush=True)
            except subprocess.SubprocessError as error:
                print(f"Could not retrieve Kaggle notebook log: {error}", file=sys.stderr)
            raise RuntimeError("Kaggle reports a failed or cancelled notebook run")
        time.sleep(30)
    else:
        raise TimeoutError("Kaggle render did not finish within five hours")

    args.output.mkdir(parents=True, exist_ok=True)
    run(["kaggle", "kernels", "output", KERNEL_ID, "-p", str(args.output), "--file-pattern", r".*\.mp4$"], timeout=900)
    mp4s = list(args.output.rglob("*.mp4"))
    if not mp4s:
        raise RuntimeError("Kaggle run completed but returned no MP4 output")
    print("MP4 ready for GitHub Actions artifact upload:", ", ".join(str(path) for path in mp4s), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, TimeoutError, FileNotFoundError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        raise SystemExit(1)
