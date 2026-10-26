import importlib.util
import sys
import json
import unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from rig2d import draw_actor
from render2d import _draw_frame,validate,_encoder,_plate

ACTOR={'skin':'#a76b4d','tunic':'#536d82','hair':'#24212b','sash':'#c4a370'}
class Historical2DTest(unittest.TestCase):
    def test_real_jointed_draw_changes_with_action(self):
        a=Image.new('RGB',(320,180),(255,255,255));b=a.copy()
        draw_actor(a,ACTOR,150,165,130,0,'walk')
        draw_actor(b,ACTOR,150,165,130,.28,'walk')
        self.assertNotEqual(a.tobytes(),b.tobytes())
    def test_speech_mouth_changes_with_audio_level(self):
        a=Image.new('RGB',(320,180),(255,255,255));b=a.copy()
        draw_actor(a,ACTOR,150,165,130,0,'idle',True,.05)
        draw_actor(b,ACTOR,150,165,130,0,'idle',True,.9)
        self.assertNotEqual(a.tobytes(),b.tobytes())
    def test_original_background_generates(self):
        self.assertEqual(_plate(320,180,'medieval').size,(320,180))
    def test_no_missing_narration(self):
        example={'kind':'historical_2d_animation','characters':{'historian':ACTOR},'scenes':[{'chapter':'History','visual_label':'ILLUSTRATED RECONSTRUCTION','audio':'absent.wav','actors':[{'id':'historian','action':'walk'}]}]}
        with self.assertRaises(FileNotFoundError):validate(example,ROOT)
    def test_missing_gpu_refuses_hard_gpu(self):
        self.assertEqual(_encoder('off'),'libx264')
if __name__=='__main__':unittest.main()
