import importlib.util
import sys
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from render2d import validate
from art_director import draw_plate
from broll import _text_style

class FastIllustrationTest(unittest.TestCase):
    def test_matte_plate_is_deterministic_and_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a.png';b=Path(tmp)/'b.png'
            r1=draw_plate('sahel_market',a,960,540,17)
            r2=draw_plate('sahel_market',b,960,540,17)
            self.assertEqual(r1['sha256'],r2['sha256'])
            self.assertEqual(r1['rights'],'original-owned')
    def test_broll_has_no_actors_and_requires_real_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'voice.wav').write_bytes(b'test')
            bg=root/'scene.png'; Image.new('RGB',(960,540)).save(bg)
            episode={'kind':'historical_2d_animation','characters':{'scholar':{'skin':'#8d5b46','tunic':'#453e59','hair':'#2c2d39','sash':'#e5c189'}},
                'scenes':[{'chapter':'Trade routes','visual_label':'ILLUSTRATED RECONSTRUCTION',
                           'audio':'voice.wav','shot_type':'illustrated_broll','background':'scene.png','actors':[]}]}
            self.assertTrue(validate(episode,root))
            episode['scenes'][0]['actors']=[{'id':'scholar'}]
            with self.assertRaises(ValueError):validate(episode,root)
            episode['scenes'][0]['actors']=[]
            del episode['scenes'][0]['background']
            with self.assertRaises(ValueError):validate(episode,root)
    def test_overlay_uses_alpha_and_correct_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'overlay.png'
            _text_style({'chapter':'Historical context','visual_label':'ILLUSTRATED NOT ARCHIVAL'},(960,540),out)
            with Image.open(out) as img:
                self.assertEqual(img.size,(960,540))
                self.assertEqual(img.mode,'RGBA')
                self.assertEqual(img.getpixel((20,20))[3],0)
if __name__=='__main__':unittest.main()