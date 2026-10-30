"""Offline tests for the selected supporting voice bank's file naming contract."""
import importlib.util
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
FILE=ROOT/"ops/select_supporting_cast_voices.py"
spec=importlib.util.spec_from_file_location("selected_voice",FILE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class CorrectVoiceBankNames(unittest.TestCase):
    def test_original_voice_output_names_are_playable_wavs(self):
        entries=[{"id":"fara","name":"Captain Fara","take":2},
                 {"id":"mari","name":"Mari","take":1},
                 {"id":"calen","name":"Lieutenant Calen Oris","take":1}]
        names=[mod.selected_output_name(x) for x in entries]
        self.assertEqual(len(names),len(set(names)))
        self.assertTrue(all(x.endswith(".wav") for x in names))
        self.assertEqual("FARA_BEST_AVAILABLE_UNAPPROVED.wav",names[0])
    def test_unsafe_file_paths_rejected(self):
        with self.assertRaises(ValueError):
            mod.selected_output_name({"id":"../secret"})
if __name__=="__main__":
    unittest.main()
