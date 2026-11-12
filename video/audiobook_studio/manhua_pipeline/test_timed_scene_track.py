"""Regression: concat still-image timestamps must not silently skip visual events."""
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from video.audiobook_studio.manhua_pipeline.timed_scene_track import (
    build_timed_scene_track, verify_rendered_scene_frames,
)


class TimedSceneTrackTests(unittest.TestCase):
    def test_decoded_video_matches_each_narration_beat_and_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            scenes = []
            for i, color in enumerate(((185, 42, 32), (32, 157, 72), (42, 66, 185))):
                art = path / f"scene{i}.jpg"
                Image.new("RGB", (896, 504), color).save(art, quality=95)
                scenes.append((art, (0.75, 0.85, 1.05)[i]))
            track = path / "story_track.mp4"
            produced = build_timed_scene_track(scenes, track, preset="ultrafast")
            self.assertEqual(produced["frames"], round(sum(s for _, s in scenes) * 24))
            self.assertEqual(produced["scene_count"], 3)
            checked = verify_rendered_scene_frames(track, scenes)
            self.assertTrue(checked["all_scenes_timed_correctly"])
            self.assertEqual(checked["decoded_midpoint_frames_checked"], 3)
            reused = build_timed_scene_track(scenes, track, preset="ultrafast")
            self.assertEqual(reused["cache_hits"], 3)
            wrong = list(scenes)
            wrong[1] = (scenes[0][0], scenes[1][1])
            with self.assertRaisesRegex(ValueError, "ENCODED_SCENE_MISMATCH"):
                verify_rendered_scene_frames(track, wrong)


if __name__ == "__main__":
    unittest.main()
