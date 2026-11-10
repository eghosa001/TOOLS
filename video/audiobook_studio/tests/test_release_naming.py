#!/usr/bin/env python3
"""Regression checks for the mandatory Mythveil episode identity gate."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_naming import canonical_identity, validate_manifest


def valid_manifest():
    series = "The Villain's Second Son"
    title = "The Blue Thread"
    obj = canonical_identity(series, 2, title)
    obj.pop("narration_filename_prefix")
    return {
        "series_title": series, "episode_number": 2, "episode_title": title,
        **obj,
        "narration_filename": "The_Villains_Second_Son_E02_The_Blue_Thread_NARRATION_KokoroMichael.mp3",
        "channel_id": "UC9gPFT64nrou4TMSxu1NZKg",
        "owner_public_release_approved": True,
    }


class NamingTests(unittest.TestCase):
    def test_valid(self):
        info = validate_manifest(valid_manifest())
        self.assertEqual(info["youtube_title"], "The Villain's Second Son | Episode 02: The Blue Thread | Audiobook")

    def test_consistent_file_slugs(self):
        info = canonical_identity("Eternal Dao of the Lost Epoch", 12, "The Wrong Sky")
        self.assertEqual(info["master_filename"],
                         "Eternal_Dao_of_the_Lost_Epoch_E12_The_Wrong_Sky_MASTER_1080p.mp4")

    def test_reject_unnatural_youtube_label(self):
        value = valid_manifest()
        value["youtube_title"] += " | Epic Dark Fantasy 4K!!!"
        with self.assertRaisesRegex(ValueError, "youtube_title"):
            validate_manifest(value)

    def test_reject_wrong_episode_number(self):
        value = valid_manifest()
        value["thumbnail_episode_number"] = "EP 03"
        with self.assertRaisesRegex(ValueError, "thumbnail_episode_number"):
            validate_manifest(value)

    def test_reject_wrong_filename(self):
        value = valid_manifest()
        value["master_filename"] = "EPISODE_2_FINAL_FINAL.mp4"
        with self.assertRaisesRegex(ValueError, "master_filename"):
            validate_manifest(value)

    def test_reject_wrong_thumbnail_story(self):
        value = valid_manifest()
        value["thumbnail_episode_title"] = "A Theft in the Stable Yard"
        with self.assertRaisesRegex(ValueError, "thumbnail_episode_title"):
            validate_manifest(value)

    def test_reject_wrong_channel(self):
        value = valid_manifest()
        value["channel_id"] = "UC_other"
        with self.assertRaisesRegex(ValueError, "channel identity mismatch"):
            validate_manifest(value)

    def test_reject_unapproved_release(self):
        value = valid_manifest()
        value["owner_public_release_approved"] = False
        with self.assertRaisesRegex(ValueError, "approval"):
            validate_manifest(value)

    def test_reject_duplicate_upload(self):
        value = valid_manifest()
        value["already_published_video_id"] = "VCoQWeMCgE0"
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_manifest(value)

    def test_reject_missing_fields(self):
        value = valid_manifest()
        value.pop("thumbnail_filename")
        with self.assertRaisesRegex(ValueError, "missing"):
            validate_manifest(value)

    def test_reject_poisoned_series_and_bool_episode(self):
        with self.assertRaises(ValueError):
            canonical_identity("Mythveil | New Series", 2, "Opening")
        with self.assertRaises(ValueError):
            canonical_identity("Mythveil", True, "Opening")


if __name__ == "__main__":
    unittest.main()
