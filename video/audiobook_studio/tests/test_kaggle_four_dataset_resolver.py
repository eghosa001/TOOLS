"""Tests for exact private Kaggle source discovery (no Kaggle calls)."""
from __future__ import annotations
import subprocess
import unittest

from video.audiobook_studio import kaggle_four_dataset_resolver as m


def response(stdout: str = "", rc: int = 0):
    return subprocess.CompletedProcess(["kaggle"], rc, stdout=stdout, stderr="")

DATASETS = "ref,title\nowner/legacy-audiobook,Legacy\nowner/fiction-long-novels,Private\nowner/other,Other\n"
SOURCE_FILE = "name,size\nFICTION_FOUR_NOVELS_PRIVATE_SOURCE.zip,850000\n"
LEGACY_FILE = "name,size\nAUDIOBOOK_STUDIO_QWEN_VIDEO_PIPELINE_2026-11-06.zip,900000\n"


class KaggleMappingTests(unittest.TestCase):
    def test_autodiscovery_only_unique_exact_zip(self):
        calls = []
        def fake(cmd):
            calls.append(cmd)
            if cmd[:3] == ["kaggle", "datasets", "list"]:
                return response(DATASETS)
            if "legacy-audiobook" in cmd:
                return response(LEGACY_FILE)
            if "fiction-long-novels" in cmd:
                return response(SOURCE_FILE)
            return response("name,size\nrandom.txt,123\n")
        r = m.resolve("", "owner", call=fake)
        self.assertEqual(r.ref, "owner/fiction-long-novels")
        self.assertEqual(r.matching_datasets, 1)
        self.assertEqual(r.origin, "discovered")
        self.assertFalse(any("download" in v for c in calls for v in c))

    def test_explicit_approved_dataset_does_not_enumerate(self):
        calls = []
        def fake(cmd):
            calls.append(cmd)
            return response(SOURCE_FILE)
        r = m.resolve("owner/fiction-long-novels", "owner", call=fake)
        self.assertEqual(r.ref, "owner/fiction-long-novels")
        self.assertEqual(len(calls), 1)
        self.assertIn("files", calls[0])

    def test_explicit_legacy_bundle_rejected(self):
        with self.assertRaises(m.MappingError):
            m.resolve("owner/legacy-audiobook", "owner", call=lambda _: response(LEGACY_FILE))

    def test_missing_source_returns_no_ref_in_diagnostic_mode(self):
        def fake(cmd):
            if "list" in cmd:
                return response("ref,title\nowner/legacy-audiobook,Legacy\n")
            return response(LEGACY_FILE)
        r = m.resolve("", "owner", call=fake, allow_missing=True)
        self.assertIsNone(r.ref)
        self.assertEqual(r.reason, "long_novel_source_zip_not_found")

    def test_multiple_identical_source_zip_names_rejected(self):
        def fake(cmd):
            if "list" in cmd:
                return response("ref,title\nowner/source-a,Source A\nowner/source-b,Source B\n")
            return response(SOURCE_FILE)
        with self.assertRaisesRegex(m.MappingError, "Multiple Kaggle datasets"):
            m.resolve("", "owner", call=fake)

    def test_inaccessible_candidates_fail_closed(self):
        def fake(cmd):
            if "list" in cmd:
                return response("ref,title\nowner/private-a,Private\n")
            return response("", rc=1)
        with self.assertRaises(m.MappingError):
            m.resolve("", "owner", call=fake)

    def test_malformed_config_is_rejected(self):
        with self.assertRaises(m.MappingError):
            m.resolve("owner/../bad", "owner", call=lambda _: response(SOURCE_FILE))
        with self.assertRaises(m.MappingError):
            m.resolve("", "owner/bad", call=lambda _: response(DATASETS))

    def test_csv_bom_and_alt_headers(self):
        self.assertEqual(m.csv_rows("\ufeffref,title\nowner/data,Data")[0]["ref"], "owner/data")
        self.assertEqual(m.csv_rows("name,size\nFICTION_FOUR_NOVELS_PRIVATE_SOURCE.zip,99")[0]["name"],
                         m.SOURCE_FILE)


if __name__ == "__main__":
    unittest.main()
