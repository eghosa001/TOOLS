"""ASMR silence gate must reject unintentional prolonged near-silence."""
import math
import tempfile
import unittest
import wave
from array import array
from pathlib import Path
from audio_continuity_gate import check_audio


class ContinuityGateTests(unittest.TestCase):
    def make_file(self, folder, gaps=()):
        file = Path(folder) / "sample.wav"
        audio = array("h")
        for sample in range(8000*3):
            t=sample/8000
            quiet=any(start <= t < end for start,end in gaps)
            audio.append(0 if quiet else round(800*math.sin(2*math.pi*220*t)))
        with wave.open(str(file),"wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(8000)
            f.writeframes(audio.tobytes())
        return file

    def test_continuous_audio_passes(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertTrue(check_audio(self.make_file(root))["passed"])

    def test_real_silent_gap_blocks_export(self):
        with tempfile.TemporaryDirectory() as root:
            report=check_audio(self.make_file(root,[(1.05,1.9)]))
            self.assertFalse(report["passed"])
            self.assertGreaterEqual(report["gaps"][0]["duration_s"],0.7)

    def test_very_brief_pause_allowed(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertTrue(check_audio(self.make_file(root,[(1.1,1.3)]))["passed"])


if __name__=="__main__":
    unittest.main()
