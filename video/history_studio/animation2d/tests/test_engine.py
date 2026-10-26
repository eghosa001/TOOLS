import importlib.util
import json
import unittest
from pathlib import Path
here=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('engine',here/'engine.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class TestRig(unittest.TestCase):
 def data(self):return json.loads((here/'examples/episode.json').read_text())
 def test_example_schema(self):self.assertEqual(mod.verify_episode(self.data(),here/'examples'),[])
 def test_missing_voice_rejected(self):
  d=self.data();d['scenes'][0]['audio_file']='missing.wav'
  self.assertTrue(mod.verify_episode(d,here/'examples'))
 def test_invalid_actor_rejected(self):
  d=self.data();d['scenes'][0]['actors'][0]['id']='not_here'
  self.assertTrue(mod.verify_episode(d,here/'examples'))
 def test_frame_changes_on_walk(self):
  from PIL import Image
  a=Image.new('RGB',(640,360));b=Image.new('RGB',(640,360));c={'coat':'#443333'}
  person={'x':0.4,'ground':0.9,'action':'walk'}
  mod.render_actor(a,c,person,0,1);mod.render_actor(b,c,person,0.35,1)
  self.assertNotEqual(a.tobytes(),b.tobytes())
 def test_source_label_on_unapproved_background(self):
  scene=self.data()['scenes'][0]
  bg=mod.scene_background((640,360),scene,here/'examples')
  self.assertEqual(bg.size,(640,360))
if __name__=='__main__':unittest.main()