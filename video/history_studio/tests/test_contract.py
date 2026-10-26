import importlib.util, json, unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("episode_spec",p/"episode_spec.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class ContractTest(unittest.TestCase):
    def get(self):return json.loads((p/"examples/molasses_1919.json").read_text())
    def test_storyboard(self):self.assertEqual([],m.validate(self.get(),p))
    def test_no_fictitious_archive(self):
        d=self.get();d["shots"][0]["kind"]="3d"
        self.assertTrue(any("reconstruction label" in e for e in m.validate(d,p)))
    def test_source_independence(self):
        d=self.get();d["research_sources"][1]["url"]=d["research_sources"][0]["url"]
        self.assertTrue(any("independent" in e for e in m.validate(d,p)))
    def test_release_blocked_without_assets_and_approval(self):
        e=m.validate(self.get(),p,True)
        self.assertTrue(any("asset" in z for z in e))
        self.assertTrue(any("visual_qc_approved" in z for z in e))
if __name__=="__main__":unittest.main()
