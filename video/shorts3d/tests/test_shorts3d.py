import copy,json,sys,tempfile,unittest,wave,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from shotlist import load_and_validate,validate
from download_assets import chosen_ids,asset_url,fetch
from qwen_audio import cache_key,mix_authored_timeline
from render_short import commands
CAT=json.loads((ROOT/'assets.json').read_text())
class Tests(unittest.TestCase):
    def setUp(self):self.spec=load_and_validate(ROOT/'short.json')
    def test_3d_9_16_fixture(self):
        self.assertEqual((self.spec['width'],self.spec['height'],len(self.spec['shots'])),(720,1280,7))
        self.assertFalse(validate(self.spec,CAT))
    def test_gap_and_release_fail_closed(self):
        changed=copy.deepcopy(self.spec);changed['shots'][1]['start']=8.1
        self.assertTrue(any('gap' in e for e in validate(changed,CAT)))
        self.assertTrue(any('not approved' in e for e in validate(self.spec,CAT,True)))
    def test_licensed_exact_models(self):
        self.assertEqual(chosen_ids(CAT,['wall','wall','tree']),['wall','tree'])
        self.assertTrue(asset_url(CAT['assets']['wall']).endswith('/castle-kit/wall.glb'))
        with self.assertRaises(ValueError):chosen_ids(CAT,['not_in_catalog'])
        with self.assertRaises(ValueError):asset_url({'pack':'..','file':'unsafe.glb'})
    def test_dry_run_does_not_download(self):
        with tempfile.TemporaryDirectory() as path:
            self.assertEqual(len(fetch(['wall'],Path(path),CAT,dry_run=True)),1)
            self.assertFalse(list(Path(path).glob('*.glb')))
    def test_qwen_cache_keys_are_content_sensitive(self):
        self.assertNotEqual(cache_key('a','Ryan','English','','one'),cache_key('a','Ryan','English','','two'))
    def test_movie_preset(self):
        g,f=commands(self.spec,ROOT/'godot',ROOT/'audio.wav',ROOT/'out.mp4',draft=True)
        self.assertIn('--write-movie',g);self.assertIn('scale=720:1280:flags=lanczos',f)
    def test_stereo_mix_exact_authored_offsets(self):
        with tempfile.TemporaryDirectory() as d:
            temp=Path(d);voices=temp/'voices';voices.mkdir()
            spec=copy.deepcopy(self.spec);spec['seconds']=2
            spec['shots']=[dict(self.spec['shots'][0],id='a',start=0,end=1),dict(self.spec['shots'][1],id='b',start=1,end=2)]
            for id in ('a','b'):
                with wave.open(str(voices/(id+'.wav')),'wb') as out:
                    out.setnchannels(1);out.setsampwidth(2);out.setframerate(24000)
                    out.writeframes(struct.pack('<h',1600)*4800)
            name=temp/'stereo.wav'
            self.assertEqual(len(mix_authored_timeline(spec,voices,name)),2)
            with wave.open(str(name),'rb') as wav:
                self.assertEqual(wav.getnchannels(),2)
                self.assertAlmostEqual(wav.getnframes()/wav.getframerate(),2,places=1)
if __name__=='__main__':unittest.main()
