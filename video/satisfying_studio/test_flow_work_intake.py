"""Regression: account isolation, provenance and no automatic release from Work/Flow."""
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from flow_work_intake import CHANNEL_ID, audit_manifest


class WorkFlowIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.media = self.dir / "clip.mp4"
        subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi",
             "-i", "color=c=blue:s=144x256:r=24:d=1",
             "-c:v", "mpeg4", "-y", str(self.media)],
            check=True, timeout=30,
        )
        self.raw = {
            "schema_version": 1,
            "channel": {"title": "Surreal ASMR", "id": CHANNEL_ID},
            "clips": [{
                "path": "clip.mp4", "source_type": "FLOW_GENERATED",
                "account_alias": "account_1",
                "sha256": hashlib.sha256(self.media.read_bytes()).hexdigest(),
                "rights": {"status": "PENDING", "evidence_url": ""},
            }],
        }
        self.manifest = self.dir / "manifest.json"

    def check(self):
        self.manifest.write_text(json.dumps(self.raw))
        return audit_manifest(self.manifest)

    def test_pending_rights_and_audio_still_not_publishable(self):
        result = self.check()
        self.assertEqual(result["results"][0]["status"], "HOLD_RIGHTS")
        self.assertTrue(result["results"][0]["audio_repair_review_needed"])
        self.assertEqual(result["release_authorization"][:4], "NONE")

    def test_rights_verified_only_moves_to_editorial_review(self):
        self.raw["clips"][0]["rights"] = {
            "status": "VERIFIED", "evidence_url": "https://support.google.com/"
        }
        self.assertEqual(self.check()["results"][0]["status"], "EDITORIAL_REVIEW_REQUIRED")

    def test_modified_source_hash_rejected(self):
        self.raw["clips"][0]["sha256"] = "0" * 64
        self.assertEqual(self.check()["counts"]["rejected"], 1)

    def test_wrong_youtube_channel_fails_closed(self):
        self.raw["channel"]["id"] = "wrong"
        with self.assertRaises(ValueError):
            self.check()

    def test_credentials_are_rejected(self):
        self.raw["clips"][0]["refresh_token"] = "never-store-this"
        self.assertEqual(self.check()["counts"]["rejected"], 1)

    def test_path_traversal_rejected(self):
        self.raw["clips"][0]["path"] = "../clip.mp4"
        self.assertEqual(self.check()["counts"]["rejected"], 1)


if __name__ == "__main__":
    unittest.main()
