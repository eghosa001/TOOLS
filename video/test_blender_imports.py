#!/usr/bin/env python3
"""Unpack the exact patched render-source into Blender's CPU smoke test."""
import argparse
import io
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from cartoonstudio_preflight import embedded_source_archive
from kaggle_actions_runner import update_notebook,validate_story


def extract_safe(zip_ref, target):
    with zipfile.ZipFile(zip_ref) as z:
        for member in z.namelist():
            p=Path(member)
            if p.is_absolute() or ".." in p.parts:
                raise RuntimeError("Unsafe asset path")
        z.extractall(target)


def main(kenney,quality):
    here=Path(__file__).resolve().parent
    story=validate_story(json.loads((here/"story.json").read_text()))
    with tempfile.TemporaryDirectory(prefix="cc0-blender-smoke-") as temp:
        root=Path(temp)
        notebook=root/"source.ipynb"
        shutil.copy2(here/"CartoonStudio-Kaggle-HighQuality.ipynb",notebook)
        update_notebook(notebook,story,"preview")
        source=embedded_source_archive(json.loads(notebook.read_text()))
        extracted=root/"src"
        extracted.mkdir()
        extract_safe(io.BytesIO(source),extracted)
        imported=root/"imported"
        imported.mkdir()
        extract_safe(kenney,imported)
        env=os.environ.copy()
        env.update(CARTOON_IMPORT_LIBRARY=str(imported),
                   CARTOON_QUALITY_LIBRARY=str(Path(quality).resolve()),
                   CARTOON_EPISODE_KEY=story["title"])
        subprocess.run(["blender","-b","--python-exit-code","1","-t","2",
                        "--python",str(here/"blender_import_smoke.py"),
                        "--",str(extracted/"CartoonStudio")],
                       check=True,timeout=300,env=env)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--kenney",required=True)
    parser.add_argument("--quality",required=True)
    opts=parser.parse_args()
    main(opts.kenney,opts.quality)
