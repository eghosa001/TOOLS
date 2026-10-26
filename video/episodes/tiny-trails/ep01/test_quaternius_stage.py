#!/usr/bin/env python3
"""Offline safety tests: synthetic glTF files, never downloaded/relabelled as production art."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from quaternius_stage import select_and_extract

NAMES = (
    [f"Tree_{i:02}.gltf" for i in range(5)]
    + [f"Fern_{i:02}.gltf" for i in range(4)]
    + [f"Flower_{i:02}.gltf" for i in range(4)]
    + [f"Mushroom_{i:02}.gltf" for i in range(2)]
)


def make_archive(path, *, missing=False, unsafe=False, license_text="CC0 1.0 Universal"):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("License_Standard.txt", license_text)
        if unsafe:
            z.writestr("../evil.txt", "x")
        for name in NAMES:
            payload = {"asset": {"version": "2.0"},
                       "buffers": [{"uri": "mesh.bin"}],
                       "images": [{"uri": "../textures/palette.png"}]}
            z.writestr("gltf/" + name, json.dumps(payload))
        if not missing:
            z.writestr("gltf/mesh.bin", b"abc123")
        z.writestr("textures/palette.png", b"png123")
    return hashlib.sha256(path.read_bytes()).hexdigest()


class QuaterniusStageTests(unittest.TestCase):
    def test_select_original_dependencies_and_license(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p = d / "pack.zip"
            sha = make_archive(p)
            report = select_and_extract(p, d / "out", sha)
            self.assertEqual(len(report["selected_models"]), 15)
            self.assertEqual(report["dependency_file_count"], 17)
            self.assertTrue((d / "out/textures/palette.png").is_file())
            self.assertTrue((d / "out/gltf/mesh.bin").is_file())

    def test_refuse_unsafe_archive(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p = d / "pack.zip"
            sha = make_archive(p, unsafe=True)
            with self.assertRaises(ValueError):
                select_and_extract(p, d / "out", sha)
            self.assertFalse((d / "evil.txt").exists())

    def test_refuse_unlicensed_archive(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p = d / "pack.zip"
            sha = make_archive(p, license_text="restricted")
            with self.assertRaises(RuntimeError):
                select_and_extract(p, d / "out", sha)

    def test_refuse_missing_texture_or_buffer(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p = d / "pack.zip"
            sha = make_archive(p, missing=True)
            with self.assertRaises(FileNotFoundError):
                select_and_extract(p, d / "out", sha)

    def test_refuse_checksum_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p = d / "pack.zip"
            make_archive(p)
            with self.assertRaises(RuntimeError):
                select_and_extract(p, d / "out", "0" * 64)


if __name__ == "__main__":
    unittest.main()
