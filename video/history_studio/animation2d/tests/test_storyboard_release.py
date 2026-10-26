import importlib.util, tempfile, unittest, json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,root/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
storyboard=load('storyboard');release2d=load('release2d')
class StoryboardReleaseTest(unittest.TestCase):
    def test_original_text_preserved_across_chunks(self):
        original=('A small sentence. A second recorded event happened. '*80).strip()
        parts=storyboard.sentence_groups(original,65)
        self.assertEqual(' '.join(parts),original)
    def test_long_form_12_minutes_below_engine_clip_limit(self):
        narration='This is test narration about a hypothetical event, not history. '*140
        ep=storyboard.build({'title':'Development test','characters':{},'chapters':[{'narration':narration}]})
        self.assertTrue(9*60<ep['estimated_duration_seconds']<15*60)
        self.assertTrue(len(ep['scenes'])>=20)
    def test_not_an_approved_video(self):
        sample=json.loads((root/'examples/episode.json').read_text())
        failures=release2d.validate(sample,root/'examples')
        self.assertTrue(any('human review' in s for s in failures))
        self.assertTrue(any('Placeholder' in s for s in failures))
if __name__=='__main__':unittest.main()