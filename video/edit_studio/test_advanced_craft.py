#!/usr/bin/env python3
"""Real FFmpeg smoke and anti-overzoom regression tests; not publication assets."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from advanced_craft import visual_filter

class AdvancedCraftTests(unittest.TestCase):
    def shot(self, **additional):
        x = {"start_sec": 0., "end_sec": 2.4}
        x.update(additional)
        return x

    def test_rejects_unverified_extreme_portrait_crop(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Aggressive cover crop"):
                visual_filter(self.shot(), 240, 426, 1920, 1080, 15, 1, "cover", tmp, 0)
            s = self.shot(framing={"mode":"cover","visually_verified":True,"focus_x":.38})
            filt,meta = visual_filter(s, 240, 426, 1920, 1080, 15, 1, "contain", tmp, 0)
            self.assertIn("crop=240:426", filt)
            self.assertLess(meta["source_visible_fraction"], .4)

    def test_preserves_subject_and_has_explicit_caption_timing(self):
        with tempfile.TemporaryDirectory() as tmp:
            s = self.shot(framing={"mode":"soft_background"}, grade={"contrast":1.07},
                caption_events=[{"text":"THE REVEAL","at_sec":.65,"until_sec":1.4,"color":"pink"}])
            f,meta = visual_filter(s, 240, 426, 1080, 1080, 15, 1, "contain", tmp, 1)
            self.assertIn("split=2[back][front]", f)
            self.assertIn("between(t,0.650,1.400)", f)
            self.assertEqual(meta["caption_events"], 1)
            self.assertEqual(meta["source_visible_fraction"], 1)

    def test_invalid_caption_color_and_grade_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "approved readable palette"):
                visual_filter(self.shot(caption_events=[
                    {"text":"X","at_sec":0,"until_sec":1,"color":"neon_fake"}
                ]),240,426,1080,1080,15,1,"contain",tmp,0)
            with self.assertRaisesRegex(ValueError, "contrast"):
                visual_filter(self.shot(grade={"contrast":1.8}),240,426,1080,1080,15,1,"contain",tmp,0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg unavailable")
    def test_filter_encodes_real_mp4(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=self.shot(framing={"mode":"soft_background"},
                caption_events=[{"text":"ORIGINAL STORY","at_sec":.3,
                                 "until_sec":1.6,"color":"cyan","size":36}])
            vf,_=visual_filter(s,240,426,320,180,15,1,"contain",tmp,1)
            out=Path(tmp)/"smoke.mp4"
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                "-f","lavfi","-i","testsrc2=size=320x180:rate=15","-t","2.4",
                "-vf",vf,"-c:v","libx264","-preset","ultrafast",
                "-pix_fmt","yuv420p",str(out)],check=True,timeout=45)
            self.assertGreater(out.stat().st_size,2500)
            subprocess.run(["ffmpeg","-hide_banner","-v","error","-i",str(out),
                            "-f","null","-"],check=True,timeout=35)

if __name__=="__main__":unittest.main()
