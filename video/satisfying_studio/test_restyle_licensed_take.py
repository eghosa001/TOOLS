"""Offline technical tests; synthetic chart never constitutes publishable footage."""
from __future__ import annotations
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from production.restyle_licensed_take import validate, transform, ShotBlocked, probe

class EditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=tempfile.TemporaryDirectory()
        cls.root=Path(cls.d.name)
        cls.video=cls.root/'synthetic.mp4'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi',
                        '-i','testsrc2=s=720x1280:r=30000/1001:d=1.2','-c:v','libx264',
                        '-preset','ultrafast','-pix_fmt','yuv420p',str(cls.video)],check=True,timeout=30)
        h=hashlib.sha256(cls.video.read_bytes()).hexdigest()
        cls.base={
            'source_file':'synthetic.mp4','source_sha256':h,
            'source_role':'LICENSED_STOCK','rights_to_modify_verified':True,
            'source_page':'https://www.pexels.com/video/example-12345/',
            'license':'Pexels License','manually_selected_take':True,
            'visual_framing_approved':True,'source_start_seconds':0,
            'source_duration_seconds':0.8,'playback_speed':0.82,
            'target_fps':24,'output_size':[720,1280], 'style':'pastel_soft',
        }
    @classmethod
    def tearDownClass(cls):
        cls.d.cleanup()
    def case(self, **kw):
        a=self.base.copy();a.update(kw);return a
    def test_valid_frames_without_interpolation(self):
        c=validate(self.case(),self.root)
        self.assertAlmostEqual(c['source_fps'],29.97,places=2)
    def test_no_fake_2x_slow_motion(self):
        with self.assertRaisesRegex(ShotBlocked,'duplicate/invent'):
            validate(self.case(playback_speed=0.5),self.root)
    def test_no_reference_reuse(self):
        with self.assertRaisesRegex(ShotBlocked,'reference-only'):
            validate(self.case(source_role='REFERENCE_ONLY'),self.root)
    def test_no_upscale(self):
        with self.assertRaisesRegex(ShotBlocked,'[Uu]pscal'):
            validate(self.case(output_size=[1080,1920]),self.root)
    def test_hue_affects_everything_without_mask(self):
        with self.assertRaisesRegex(ShotBlocked,'everything'):
            validate(self.case(global_hue_degrees=80),self.root)
    def test_license_rights_must_be_documented(self):
        with self.assertRaisesRegex(ShotBlocked,'licence'):
            validate(self.case(rights_to_modify_verified=False),self.root)
    def test_render_is_silent_picture_and_unapproved(self):
        m=self.root/'manifest.json';m.write_text(json.dumps(self.base))
        o=self.root/'restyled.mp4'
        report=transform(m,o)
        self.assertEqual(report['status'],'PICTURE_ONLY_NOT_ASMR_RELEASE_APPROVED')
        self.assertTrue(report['approvals']['premium_quality_approved'] is False)
        self.assertGreater(float(probe(o)['format']['duration']), 0.85)
        self.assertFalse(any(s['codec_type']=='audio' for s in probe(o)['streams']))
        self.assertEqual(report['visual_output_sha256'],hashlib.sha256(o.read_bytes()).hexdigest())
if __name__=='__main__':unittest.main()
