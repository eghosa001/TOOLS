"""The 34-second editor audio-start offsets must be honored in 24fps viseme cues."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHOTS={s["shot_id"]:s for s in json.loads((ROOT/"pilot_34s_proposed_timing.json").read_text())["shots"]}
AUDIO=json.loads((ROOT/"pilot_34s_proposed_timing.json").read_text())["selected_audio_fit"]
EXPECTED_OFFSETS={"ep101_002":1,"ep101_003":4,"ep101_004":1,"ep101_007":3,
                  "ep101_008":4,"ep101_009":4,"ep101_010":1}

class AudioCutVisemeSyncTest(unittest.TestCase):
    def test_all_seven_voice_entries_have_real_guide_offsets(self):
        self.assertEqual(7,len(AUDIO))
        self.assertEqual(set(EXPECTED_OFFSETS),{row["line_id"] for row in AUDIO})
        for line in AUDIO:
            id=line["line_id"]
            shot=SHOTS[id]
            actual_frame=round(line["audio_start_seconds"]*24)
            delay=actual_frame-shot["start_frame"]
            self.assertEqual(EXPECTED_OFFSETS[id],delay,id)
            self.assertGreaterEqual(actual_frame,shot["start_frame"])
            self.assertLess(actual_frame,shot["end_frame"])
            self.assertLessEqual(line["audio_start_seconds"]+line["duration_seconds"],
                                 shot["end_frame"]/24+.011)
            self.assertRegex(line["source_wav_sha256"],r"^[a-f0-9]{64}$")

    def test_audio_cue_generator_uses_inserted_start_not_shot_start(self):
        code=(ROOT/"pilot_lipsync_from_wavs.py").read_text()
        self.assertIn('first_voice_frame=round(actual_audio_start*FPS)',code)
        self.assertIn('first_voice_frame+round(a*FPS)',code)
        self.assertIn('first_voice_frame+round(b*FPS)',code)
        self.assertIn('edit["source_wav_sha256"]!=checksum',code)
        self.assertNotIn('shot["start_frame"]+round(a*FPS)',code)

    def test_original_pilot_is_preserved_unmodified(self):
        original=json.loads((ROOT.parent/"pilot_shots.json").read_text())
        proposal=json.loads((ROOT/"pilot_34s_proposed_timing.json").read_text())
        self.assertEqual(720,original["total_frames"])
        self.assertEqual(816,proposal["total_frames"])
        self.assertEqual(12,len(proposal["shots"]))
        self.assertEqual(12,len(original["shots"]))
        self.assertFalse(original["director_approvals"]["voice_takes"])
        self.assertEqual("PREVIEW_TIMING_ONLY_NOT_ANIMATIC_LOCK",proposal["approval_status"])

if __name__=="__main__":
    unittest.main()
