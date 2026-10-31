import json
from pathlib import Path
import re
import unittest
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'godot/data/production_inventory.json').read_text())
class TestAllCast(unittest.TestCase):
    def test_exactly_all_twenty_unique_characters(self):
        chars=D['characters']
        self.assertEqual(len(chars),20)
        self.assertEqual([x['number'] for x in chars],list(range(1,21)))
        self.assertEqual(len(set(x['id'] for x in chars)),20)
    def test_exactly_fifteen_layered_world_slots(self):
        worlds=D['set_staging_slots']
        self.assertEqual(len(worlds),15)
        self.assertEqual(len(set(x['id'] for x in worlds)),15)
        self.assertTrue(all(len(w['layer_slots'])==6 for w in worlds))
        self.assertTrue(all(not w['final_painted_set_approved'] for w in worlds))
    def test_canon_ages_height_and_grip_distinction(self):
        people={c['id']:c for c in D['characters']}
        self.assertEqual(people['naya_venn']['height_cm'],164)
        self.assertEqual(people['kito_vale']['age'],12)
        self.assertEqual(people['iri_sol']['height_cm'],172)
        self.assertEqual(people['mari']['age'],6)
        self.assertIsNone(people['supervisor_ren']['age'])
        self.assertIn('thin messenger rope',people['kito_vale']['canon_notes'])
        self.assertIn('bow hawser',people['captain_fara']['canon_notes'])
        self.assertIn('certified safety line',people['iri_sol']['canon_notes'])
    def test_poses_expressions_lips_and_view_slot_count(self):
        for c in D['characters']:
            self.assertEqual(len(c['views_required']),5)
            self.assertEqual(len(c['part_slots']),15)
            self.assertGreaterEqual(len(c['expression_slots']),8)
            self.assertGreaterEqual(len(c['mouth_slots']),9)
    def test_approvals_fail_closed(self):
        self.assertFalse(D['release_ready'])
        self.assertTrue(all(not c['rig_art_approved'] and not c['turnaround_approved'] and not c['audio_performance_approved'] for c in D['characters']))
        self.assertFalse(next(x for x in D['characters'] if x['id']=='supervisor_ren')['reference_design_approved'])
    def test_scene_sources_for_every_cast_and_set(self):
        for c in D['characters']:
            p=R/'godot/scenes/cast'/f'{c["id"]}.tscn'
            self.assertTrue(p.is_file(),p)
            self.assertIn(f'character_id = "{c["id"]}"',p.read_text())
        for w in D['set_staging_slots']:
            p=R/'godot/scenes/sets'/f'{w["id"]}.tscn'
            self.assertTrue(p.is_file(),p)
            self.assertIn(f'set_id = "{w["id"]}"',p.read_text())
    def test_no_production_pngs_or_unsafe_refs(self):
        self.assertFalse(list((R/'godot').rglob('*.png')))
        self.assertFalse(list((R/'godot').rglob('*.wav')))
        self.assertFalse(list((R/'godot').rglob('*.mp4')))
    def test_scripts_gate_missing_art(self):
        rig=(R/'godot/scripts/cast_cutout.gd').read_text()
        self.assertIn('missing_art.append(',rig)
        self.assertIn('art_approved = bool(record.get(',rig)
        self.assertIn('"production_ready":false',rig)
    def test_parent_joints_and_limits_exist(self):
        rig=(R/'godot/scripts/cast_cutout.gd').read_text()
        for name in D['characters'][0]['part_slots']:
            self.assertIn('"'+name+'"',rig)
        self.assertIn('clampf(degrees',rig)
    def test_generation_reproducible(self):
        import subprocess,sys,hashlib
        p=R/'godot/scenes/cast/naya_venn.tscn'
        before=hashlib.sha256(p.read_bytes()).hexdigest()
        subprocess.run([sys.executable,str(R/'tools/generate_scenes.py')],check=True,capture_output=True)
        self.assertEqual(before,hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':unittest.main()