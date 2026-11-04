import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

PATH=Path(__file__).resolve().parents[1]/"football_video_score_gate.py"
spec=importlib.util.spec_from_file_location("football_gate",PATH)
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

class FootballScoreGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.video=Path(self.tmp.name)/"test.mp4"
        self.video.write_bytes(b"SHA fixture for unit test only")
        self.scores={k:9.0 for k in gate.WEIGHTS}
        self.card={
            "scores":self.scores,
            "evidence":{k:"Real editor watched this exact test file and noted specific evidence for "+k for k in gate.WEIGHTS},
            "reviewer_name":"Editor",
            "reviewed_at_utc":"2026-11-04T03:00:00Z",
            "fully_watched_with_sound":True,
            "copyright_and_source_clearance_reviewed":True,
            "editorial_clips_rechecked":True,
            "narration_names_checked_by_listening":True,
            "final_video_sha256":hashlib.sha256(self.video.read_bytes()).hexdigest(),
        }
    def tearDown(self):self.tmp.cleanup()
    def test_good_complete_card_passes(self):
        r=gate.check(self.card,self.video,True)
        self.assertEqual(r["status"],"PASS")
        self.assertEqual(r["weighted_overall"],9.0)
    def test_previous_video_rating_is_hold(self):
        self.scores.update({"football_information":7,"narration_pacing_pronunciation":7,"graphic_design":6,"relevant_match_footage":2,"viewer_retention_entertainment":4,"publishing_readiness":4})
        r=gate.check(self.card,self.video,True)
        self.assertEqual(r["status"],"HOLD")
        self.assertEqual(r["weighted_overall"],4.8)
    def test_missing_full_watch_fails(self):
        self.card["fully_watched_with_sound"]=False
        self.assertEqual(gate.check(self.card,self.video,True)["status"],"HOLD")
    def test_sha_tamper_fails(self):
        self.card["final_video_sha256"]="0"*64
        self.assertEqual(gate.check(self.card,self.video,True)["status"],"HOLD")
    def test_missing_evidence_fails(self):
        self.card["evidence"]["graphic_design"]="nice"
        self.assertEqual(gate.check(self.card,self.video,True)["status"],"HOLD")
    def test_boolean_score_is_not_numeric(self):
        self.scores["football_information"]=True
        self.assertEqual(gate.check(self.card,self.video,True)["status"],"HOLD")
if __name__=="__main__":
    unittest.main()
