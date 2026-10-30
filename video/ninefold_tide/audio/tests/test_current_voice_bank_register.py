"""Ensure the public voice registry never claims approval or invents a missing voice."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class CurrentVoiceBankTest(unittest.TestCase):
    def test_recorded_selection_matches_twenty_cast(self):
        c=json.loads((ROOT/"cast.json").read_text())
        x=json.loads((ROOT/"current_voice_bank_register.json").read_text())
        ids={p["id"] for p in c["characters"]}
        selected=x["original_voice_reference_ids"]
        self.assertEqual(20,len(ids))
        self.assertEqual(19,len(selected))
        self.assertEqual(19,len(set(selected)))
        self.assertEqual(ids,set(selected)|set(x["unselected_ids"]))
        self.assertEqual({"mari"},set(x["unselected_ids"]))
        self.assertFalse(x["all_source_voice_references_human_approved"])
        self.assertFalse(x["full_episode_voice_canon_locked"])
        self.assertIn("drive.google.com",x["provisional_selections_download"])
        self.assertIn("actual production-quality audio",x["approval_gates"])
if __name__=="__main__":
    unittest.main()
