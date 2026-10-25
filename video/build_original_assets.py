#!/usr/bin/env python3
"""Offline build of reusable GLB/BLEND/PNG assets, no Kaggle or render token."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from cartoonstudio_preflight import embedded_source_archive
from kaggle_actions_runner import update_notebook, validate_story


def build(destination: Path):
    here=Path(__file__).resolve().parent
    destination=destination.resolve()
    destination.mkdir(parents=True,exist_ok=True)
    story=validate_story(json.loads((here/"story.json").read_text(encoding="utf-8")))
    with tempfile.TemporaryDirectory(prefix="cartoonstudio-original-assets-") as directory:
        temp=Path(directory)
        notebook=temp/"asset_source.ipynb"
        shutil.copy2(here/"CartoonStudio-Kaggle-HighQuality.ipynb",notebook)
        update_notebook(notebook,story,"preview")
        archive=embedded_source_archive(json.loads(notebook.read_text(encoding="utf-8")))
        with zipfile.ZipFile(__import__("io").BytesIO(archive)) as source:
            members=source.namelist()
            if any(Path(p).is_absolute() or ".." in Path(p).parts for p in members):
                raise RuntimeError("Embedded archive contains an unsafe path")
            source.extractall(temp)
        root=temp/"CartoonStudio"
        if not (root/"cartoon_studio"/"studio_world.py").is_file():
            raise RuntimeError("Bundled character and environment generator missing")
        subprocess.run([
            "blender","-b","--python-exit-code","1","-t","2","--python",
            str(here/"blender_asset_export.py"),"--",str(root),str(destination)
        ],check=True,timeout=1800)
    for filename in (
        "lelli_original_clay.glb","brin_original_clay.glb",
        "odo_original_clay.glb","sunpatch_court.glb",
        "sunpatch_court_cast.blend","sunpatch_court_lookdev.png",
        "asset_manifest.json",
    ):
        filepath=destination/filename
        if not filepath.is_file() or filepath.stat().st_size<=100:
            raise RuntimeError(f"Missing reusable Blender asset: {filepath}")
    print("ALL ORIGINAL ASSETS VALIDATED",flush=True)


if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python video/build_original_assets.py OUTPUT_DIRECTORY")
    build(Path(sys.argv[1]))
