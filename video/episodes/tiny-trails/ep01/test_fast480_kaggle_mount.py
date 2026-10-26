#!/usr/bin/env python3
"""Test Kaggle-style read-only extracted input copying without a GPU or video."""
from __future__ import annotations
import importlib.util
import os
import pathlib
import sys
import tempfile

HERE=pathlib.Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("ep01_kaggle_mount_test",HERE/"kaggle_ep01_fast480_preview.py")
assert SPEC and SPEC.loader
runner=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

def test_extracted_readonly_dataset():
    with tempfile.TemporaryDirectory(prefix="ep01_kaggle_mount_") as base:
        base=pathlib.Path(base)
        runner.INPUT=base/"input"
        runner.WORK=base/"work"
        origin=runner.INPUT/"datasets"/"aighewieghosa"/"tiny-trails-ep01-original-gpu-assets"/"episode-pack"
        ep=origin/"video"/"episodes"/"tiny-trails"/"ep01"
        ep.mkdir(parents=True)
        (origin/"assets").mkdir(parents=True)
        (origin/"voices").mkdir()
        (origin/"assets"/"assets-verified.json").write_text("{}")
        (ep/"story.json").write_text("{}")
        (ep/"render_ep01_native.py").write_text("# existing unmodified renderer")
        (ep/"episode_preflight.py").write_text(
            "def check_legacy(): pass\n"
            "def read(p): return {}\n"
            "def validate(story, assets): return []\n"
            "def check_audio(*args): pass\n"
            "def check_assets(*args): pass\n"
            "def write_cues(*args): pass\n")
        # Test the loader with source files marked read-only, the Kaggle input norm.
        for p in origin.rglob("*"):
            if p.is_file():p.chmod(0o444)
        try:
            result_ep,result_root,cues=runner.load_bundle()
            assert result_root==runner.WORK/"ep01_source"
            assert result_ep.is_relative_to(runner.WORK)
            assert result_root.resolve()!=origin.resolve()
            result_renderer=result_ep/"render_ep01_fast480.py"
            result_renderer.write_text("# synthetic writable smoke test")
            assert result_renderer.is_file()
            assert not (ep/"render_ep01_fast480.py").exists()
            assert (ep/"render_ep01_native.py").read_text()=="# existing unmodified renderer"
            print("EP01_PRIVATE_READ_ONLY_KAGGLE_MOUNT_COPIED_TO_WRITABLE_AREA_PASS")
        finally:
            for p in origin.rglob("*"):
                if p.is_file():p.chmod(0o644)

if __name__=="__main__":
    test_extracted_readonly_dataset()
