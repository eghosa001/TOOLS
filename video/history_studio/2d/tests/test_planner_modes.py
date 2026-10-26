import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from plan_episode import make_plan
class PlanModeTest(unittest.TestCase):
 def doc(self):
  return {'title':'Commercial historical pilot planning','sources':[{'url':'https://example.com/a'},{'url':'https://example.org/b'}],
          'characters':{'presenter':{}},'chapters':[{'title':'Historical context','narration':('Archives describe long-distance trade. ' * 300),'visual_mode':'illustrated_broll','backgrounds':['art1.webp','art2.webp']}]}
 def test_broll_authored_art_only(self):
  x=make_plan(self.doc());self.assertTrue(len(x['scenes'])>=1)
  for shot in x['scenes']:
   self.assertEqual(shot['shot_type'],'illustrated_broll')
   self.assertEqual(shot['actors'],[])
   self.assertIn(shot['background'],('art1.webp','art2.webp'))
 def test_no_background_fails_closed(self):
  x=self.doc();del x['chapters'][0]['backgrounds']
  with self.assertRaises(ValueError):make_plan(x)
if __name__=='__main__': unittest.main()