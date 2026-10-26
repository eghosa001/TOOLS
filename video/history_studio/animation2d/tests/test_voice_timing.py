import importlib.util,json,tempfile,unittest,wave
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('voices',root/'voices.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def make_wav(path,samples=4800,rate=24000):
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(b'\x00\x00'*samples)

class TimingTest(unittest.TestCase):
    def test_per_speaker_accurate_intervals(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);make_wav(p/'a.wav');make_wav(p/'b.wav',7200)
            dur,intervals=mod.assemble_speech([('worker',p/'a.wav'),('historian',p/'b.wav')],p/'total.wav',pause=.1)
            self.assertAlmostEqual(dur,.7,places=2)
            self.assertEqual(intervals[0]['speaker'],'worker')
            self.assertAlmostEqual(intervals[1]['start'],.3,places=3)
            self.assertAlmostEqual(intervals[1]['end'],.6,places=3)
    def test_subtitle_timing_across_scenes(self):
        e={"scenes":[
            {"duration":4.0,"lines":[{"speaker":"king","text":"Hello, court."}],
             "speech_timing":[{"speaker":"king","start":0.1,"end":1.4}]},
            {"duration":3.0,"lines":[{"speaker":"worker","text":"A second scene."}],
             "speech_timing":[{"speaker":"worker","start":0.2,"end":1.3}]},
        ]}
        text=mod.subtitle_text(e)
        self.assertIn("00:00:00,100 --> 00:00:01,400",text)
        self.assertIn("00:00:04,200 --> 00:00:05,300",text)
        self.assertEqual(text.count('-->'),2)
    def test_rebase_preserves_art(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);src=base/'src';dest=base/'build';src.mkdir();dest.mkdir()
            Image.new('RGBA',(12,12)).save(src/'head.png')
            data={'characters':{'king':{'sprites':{'head':'head.png'}}},'scenes':[{'background_image':'head.png'}]}
            mod.rebase_media(data,src,dest)
            rel=data['characters']['king']['sprites']['head']
            self.assertEqual(data['scenes'][0]['background_image'],rel)
            self.assertTrue((dest/rel).is_file())
    def test_rebase_blocks_path_escape(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'source').mkdir()
            (root/'hidden.png').write_bytes(b'not an image')
            data={'characters':{'x':{'sprites':{'head':'../hidden.png'}}},'scenes':[{}]}
            with self.assertRaises(ValueError):mod.rebase_media(data,root/'source',root/'out')
if __name__=='__main__':unittest.main()