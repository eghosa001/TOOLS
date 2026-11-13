"""Safe, offline OpenMontage handoff tests. No media or release."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from video.audiobook_studio import openmontage_bridge as bridge
from video.tests.test_cloud_first_policy import sample


class OpenMontageAudiobookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        (self.base / "script.txt").write_text("Approved private story text.", encoding="utf-8")
        self.manifest = {
            "series_title": "Example Series", "episode_number": 6,
            "episode_title": "Owner Approved Title", "approved_script": "script.txt",
            "narration_audio": "voice.wav", "timeline": "timeline.json",
            "quality_scorecard": "signed_scorecard.json",
            "visual_qa_report": "visual_qa.json", "master_mp4": "master.mp4",
            "narrator": "am_michael", "publish": False,
            "cloud_plan": "cloud_production_plan.json",
        }
        self.mfile = self.base / "episode.json"
        self.cloud_file = self.base / "cloud_production_plan.json"
        self.cloud_file.write_text(json.dumps(sample("audiobook", "animation")),
                                   encoding="utf-8")

    def load(self):
        self.mfile.write_text(json.dumps(self.manifest), encoding="utf-8")
        return bridge.read_manifest(self.mfile)

    def test_prepare_is_private_and_does_not_render(self):
        data, directory = self.load()
        out = bridge.prepare(data, directory, montage_root=None)
        content = out.read_text(encoding="utf-8")
        self.assertIn("Example Series | Episode 06: Owner Approved Title | Audiobook", content)
        self.assertIn("NEVER upload or publish", content)
        self.assertNotIn("Approved private story text.", content)
        self.assertFalse((directory / "master.mp4").exists())

    def test_wrong_narrator_or_publication_blocked(self):
        self.manifest["narrator"] = "other"
        with self.assertRaisesRegex(ValueError, "Kokoro"):
            self.load()
        self.manifest["narrator"] = "am_michael"
        self.manifest["publish"] = True
        with self.assertRaisesRegex(ValueError, "publication"):
            self.load()

    def test_placeholders_public_output_and_missing_prompt_blocked(self):
        self.manifest["episode_title"] = "REPLACE_WITH_APPROVED_TITLE"
        with self.assertRaisesRegex(ValueError, "owner-approved"):
            self.load()
        self.manifest["episode_title"] = "Owner Approved Title"
        self.manifest["master_mp4"] = str(bridge.ROOT / "private_master.mp4")
        with self.assertRaisesRegex(ValueError, "public repository"):
            self.load()
        self.manifest["master_mp4"] = "master.mp4"
        data, directory = self.load()
        data["scene_prompts"] = "not-present.txt"
        with self.assertRaisesRegex(ValueError, "does not exist locally"):
            bridge.prepare(data, directory, None)

    def test_laptop_run_rejected_even_if_media_exists(self):
        data, directory = self.load()
        cloud = sample("audiobook", "animation")
        cloud["execution"]["mode"] = "local"
        self.cloud_file.write_text(json.dumps(cloud), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cloud runner required"):
            bridge.prepare(data, directory, None)
        with mock.patch.object(bridge.subprocess, "run") as process:
            with self.assertRaisesRegex(ValueError, "cloud runner required"):
                bridge.render(data, directory)
            process.assert_not_called()

    def test_music_rights_and_gain_blocked(self):
        self.manifest["music_file"] = "licensed.wav"
        with self.assertRaisesRegex(ValueError, "rights"):
            self.load()
        self.manifest["music_rights_file"] = "license.txt"
        self.manifest["music_level"] = 0.9
        with self.assertRaisesRegex(ValueError, "gain"):
            self.load()

    def test_render_has_strict_existing_pipeline_flags(self):
        data, directory = self.load()
        music, render = bridge.commands(data, directory)
        self.assertIn("music_bed", music[2])
        for flag in ("--quality-scorecard", "--visual-qa-report",
                     "--require-visual-qa", "--source-text",
                     "--art-policy", "--music-level"):
            self.assertIn(flag, render)
        self.assertIn("full_color_panels", render)
        self.assertNotIn("--draft-preview", render)
        self.assertNotIn("--legacy-no-music", render)

    def test_render_without_real_assets_fails_closed(self):
        data, directory = self.load()
        with mock.patch.object(bridge.subprocess, "run") as process:
            with self.assertRaisesRegex(ValueError, "runner_verification_reference"):
                bridge.render(data, directory)
            process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
