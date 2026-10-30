"""Check the standalone private Kaggle job before consuming any GPU credits."""
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
NOTEBOOK=ROOT/"audio"/"kaggle_voice_auto_batch.ipynb"
LAUNCHER=ROOT/"ops"/"launch_kaggle_voice.py"

class KaggleVoiceJobTest(unittest.TestCase):
    def test_gpu_job_notebook_compiles(self):
        data=json.loads(NOTEBOOK.read_text(encoding="utf8"))
        cells=[x for x in data["cells"] if x["cell_type"]=="code"]
        self.assertEqual(1,len(cells))
        compile("".join(cells[0]["source"]),"kaggle-voice-batch","exec")

    def test_voice_job_protects_audio_and_uses_temporary_weights(self):
        source="".join(json.loads(NOTEBOOK.read_text())["cells"][1]["source"])
        self.assertIn("/kaggle/temp/ninefold_hf_cache",source)
        self.assertIn("--takes-per-line"," ".join(source.split()))
        self.assertIn("three original voice references",source)
        self.assertIn("UNAPPROVED",source)
        self.assertIn("references",source)
        self.assertIn("takes",source)

    def test_launch_is_private_and_never_deletes_other_kernels(self):
        script=LAUNCHER.read_text()
        self.assertIn('"is_private": True',script)
        self.assertIn('"enable_gpu": True',script)
        self.assertIn('"enable_internet": True',script)
        self.assertNotIn('"delete"',script)
        self.assertIn("if any(x.get(\"ref\") == handle",script)

if __name__=="__main__":
    unittest.main()
