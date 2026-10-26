import importlib.util,json,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('engine_pan',root/'engine.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
class PanzoomContract(unittest.TestCase):
    def test_panzoom_without_image_rejected(self):
        sample=json.loads((root/'examples/episode.json').read_text())
        sample['scenes'][0]={'id':'pan','duration':2,'mode':'panzoom','actors':[]}
        self.assertTrue(any('panzoom' in x for x in engine.verify_episode(sample,root/'examples')))
    def test_panzoom_with_actor_rejected(self):
        sample=json.loads((root/'examples/episode.json').read_text())
        sample['scenes'][0]['mode']='panzoom'
        sample['scenes'][0]['background_image']='missing.png'
        self.assertTrue(any('panzoom' in x for x in engine.verify_episode(sample,root/'examples')))
if __name__=='__main__':unittest.main()