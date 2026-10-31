"""Public, source-art-free regression tests for Ninefold's private pack assembler."""
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

module_path = Path(__file__).resolve().parents[1] / "bootstrap.py"
spec = importlib.util.spec_from_file_location("ninefold_bootstrap", module_path)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class TestNinefoldBootstrap(unittest.TestCase):
    def test_three_source_archive_hashes_are_full(self):
        self.assertEqual(len(b.SOURCES), 3)
        self.assertTrue(all(len(digest) == 64 for _, digest in b.SOURCES.values()))

    def test_canonical_sources_are_explicit(self):
        self.assertEqual(set(b.CANON), {"series", "cast", "art_index"})
        self.assertIn("Naya_Rail_Grip_Review.tscn", b.PROJECT_FILE)

    def test_safe_zip_extract(self):
        with tempfile.TemporaryDirectory() as root:
            t = Path(root)
            archive = t / "ok.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("package/assets/readme.txt", "safe")
            out = t / "out"
            out.mkdir()
            self.assertEqual(b.safe_unpack(archive, out, prefix="package/"), 1)
            self.assertEqual((out / "assets/readme.txt").read_text(), "safe")

    def test_rejects_parent_escape(self):
        with tempfile.TemporaryDirectory() as root:
            t = Path(root)
            archive = t / "zip-slip.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("../../escape.txt", "no")
            out = t / "out"
            out.mkdir()
            with self.assertRaisesRegex(ValueError, "Unsafe archive path"):
                b.safe_unpack(archive, out)
            self.assertFalse((t.parent / "escape.txt").exists())

    def test_rejects_unknown_project_root(self):
        with tempfile.TemporaryDirectory() as root:
            t = Path(root)
            archive = t / "foreign.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("different/project.godot", "config_version=5")
            out = t / "out"
            out.mkdir()
            with self.assertRaisesRegex(ValueError, "Unexpected project root"):
                b.safe_unpack(archive, out, prefix="package/")

    def test_missing_private_inputs_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            t = Path(root)
            with self.assertRaises(FileNotFoundError):
                b.assemble(t, t / "assembled")
            self.assertFalse((t / "assembled").exists())

    def test_release_is_not_automatically_granted(self):
        self.assertNotIn("movie_writer", b.PROJECT_FILE)
        self.assertNotIn("video", b.PROJECT_FILE.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)