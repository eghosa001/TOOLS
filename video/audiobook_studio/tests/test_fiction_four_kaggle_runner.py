"""Zero-network tests: no Kaggle GPU, generation, private uploads or publishing."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

from video.audiobook_studio import fiction_four_kaggle_runner as runner
from video.audiobook_studio import prepare_four_novel_private_bundle as bundler


class FictionFourSafetyTests(unittest.TestCase):
    def test_exact_long_novel_lineup(self):
        self.assertEqual(list(runner.BOOKS), ["disciple", "one-coin", "gatekeeper", "reborn"])
        self.assertNotIn("full", runner.PHASES)

    def test_chunk_boundaries_are_purposeful_and_preserve_words(self):
        text = "\n\n".join(["One person said the truth. Another person went home."] * 84)
        chunks = runner.chunks(text, max_words=105)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(" ".join(" ".join(chunks).split()), " ".join(text.split()))
        self.assertTrue(all(len(c.split()) <= 105 for c in chunks))
        self.assertFalse(any(not c.strip() for c in chunks))

    def test_oversized_sentence_is_not_truncated(self):
        with self.assertRaises(ValueError):
            runner.chunks("word " * 240)

    def test_private_path_rejects_traversal_and_backslash(self):
        with tempfile.TemporaryDirectory() as d:
            for malicious in ("../outside", "/tmp/outside", r"foo\..\outside", ""):
                with self.assertRaises(ValueError):
                    runner.safe_path(Path(d), malicious)
            self.assertTrue(str(runner.safe_path(Path(d), "books/disciple.txt")).startswith(d))

    def test_wrong_collection_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "source").mkdir()
            (root / "source/manifest.json").write_text(
                json.dumps({"schema_version": 1, "collection": "four-audiobook-novellas", "books": []}))
            with mock.patch.object(runner, "ROOT", root):
                with self.assertRaises(ValueError):
                    runner.load_source()

    def test_manifest_hash_integrity_and_all_four_books(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "source"
            (src / "books").mkdir(parents=True)
            books = []
            for slug, title in runner.BOOKS.items():
                p = src / "books" / (slug + ".txt")
                p.write_text("Original spoken words for " + title + ".", encoding="utf-8")
                books.append({"slug": slug, "title": title,
                              "file": "books/" + slug + ".txt",
                              "sha256": runner.sha256(p)})
            (src / "manifest.json").write_text(json.dumps(
                {"schema_version": 1, "collection": runner.COLLECTION, "books": books}))
            with mock.patch.object(runner, "ROOT", root):
                _, m = runner.load_source()
                self.assertEqual(set(m), set(runner.BOOKS))
                (src / "books/disciple.txt").write_text("silently revised")
                with self.assertRaises(RuntimeError):
                    runner.load_source()

    def test_zip_traversal_blocked_without_file_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            inputdir = root / "input"
            inputdir.mkdir()
            archive = inputdir / runner.SOURCE_NAME
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("../escape.txt", "private data")
            with mock.patch.object(runner, "INPUT", inputdir):
                with self.assertRaises(ValueError):
                    runner.unpack_private(runner.SOURCE_NAME, root / "destination", True)
            self.assertFalse((root / "escape.txt").exists())

    def test_renderer_rejects_missing_human_approval(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):
                runner.verify_approvals(Path(d), "disciple", "abc", include_visuals=True)

    def test_private_packager_does_not_upload_or_publish(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            voice = root / "voice"
            voice.mkdir()
            fake = {}
            for filename in bundler.EXPECTED_AUDIO:
                data = ("FAKE REFERENCE FOR UNIT TEST " + filename).encode()
                (voice / filename).write_bytes(data)
                fake[filename] = hashlib.sha256(data).hexdigest()
            (voice / "RYAN_VOICE_STANDARD_APPROVED.json").write_text(json.dumps(
                {"profile_id": runner.VOICE_ID}))
            books = {}
            for slug in bundler.BOOKS:
                path = root / (slug + ".txt")
                path.write_text("Spoken source for " + slug, encoding="utf-8")
                books[slug] = path
            with mock.patch.object(bundler, "EXPECTED_AUDIO", fake):
                bundle = root / "PRIVATE.zip"
                bundler.make_bundle(books, voice, bundle)
                with zipfile.ZipFile(bundle) as z:
                    names = z.namelist()
                    self.assertIn("manifest.json", names)
                    self.assertIn("books/disciple.txt", names)
                    self.assertNotIn("kaggle-metadata.json", names)
                    self.assertEqual(len(json.loads(z.read("manifest.json"))["books"]), 4)


if __name__ == "__main__":
    unittest.main()
