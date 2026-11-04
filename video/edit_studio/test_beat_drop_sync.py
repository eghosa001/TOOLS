#!/usr/bin/env python3
"""Beat-drop timing tests: real frame switches, not a storyboard promise."""
import unittest
from beat_drop_sync import plan_timeline


class BeatDropTests(unittest.TestCase):
    def manifest(self):
        return {
            "render":{"bed_audio_source_id":"licensed_music","music_drop_markers_sec":[3.033333333]},
            "timeline":[
                {"start_sec":0,"end_sec":3,"playback_speed":1,
                 "cut_on_beat_sec":3.033333333},
                {"start_sec":3,"end_sec":6,"playback_speed":1},
            ],
        }

    def test_scene_switch_is_frame_accurate(self):
        x=plan_timeline(self.manifest(),30)
        self.assertEqual(x[0]["frames"],91)
        self.assertEqual(x[0]["end_frame"],x[1]["start_frame"])
        self.assertAlmostEqual(x[0]["actual_cut_sec"],91/30,places=9)
        self.assertEqual(x[0]["beat_error_frames"],0)
        self.assertLess(abs(x[0]["speed"]-1),.02)

    def test_unnatural_beat_correction_is_rejected(self):
        m=self.manifest()
        m["render"]["music_drop_markers_sec"]=[4.]
        m["timeline"][0]["cut_on_beat_sec"]=4.
        with self.assertRaisesRegex(ValueError,"unnatural"):
            plan_timeline(m,30)

    def test_declared_drop_must_match_actual_marked_time(self):
        m=self.manifest()
        m["timeline"][0]["cut_on_beat_sec"]=2.5
        with self.assertRaisesRegex(ValueError,"declared music drop"):
            plan_timeline(m,30)

    def test_no_beat_markers_does_not_require_music(self):
        m=self.manifest()
        del m["timeline"][0]["cut_on_beat_sec"]
        m["render"]={}
        self.assertEqual(len(plan_timeline(m,30)),2)

    def test_last_shot_cannot_be_a_switch_without_following_sequence(self):
        m=self.manifest()
        m["timeline"][1]["cut_on_beat_sec"]=3.033333333
        with self.assertRaisesRegex(ValueError,"Final shot"):
            plan_timeline(m,30)

    def test_marker_must_have_licensed_music_track(self):
        m=self.manifest()
        m["render"]["bed_audio_source_id"]=None
        with self.assertRaisesRegex(ValueError,"rights-tracked"):
            plan_timeline(m,30)


if __name__=="__main__": unittest.main()
