#!/usr/bin/env python3
"""Titanic class-survival exact photo choice regression, no speculative film approval."""
import pathlib,json,unittest
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
class TestSurvivalChapter(unittest.TestCase):
    def test_exact_22_original_narrated_scene_ids(self):
        a=json.loads((HERE/'CHAPTER10_EXPLICIT_HISTORICAL_PICTURE_EDIT.json').read_text())
        old=json.loads((ROOT/'MANUAL_SCENE_LEDGER_DRAFT.json').read_text())['scenes']
        self.assertEqual(a['chapter'],10)
        self.assertEqual([z['scene_id'] for z in a['shots']],[z['scene_id'] for z in old if z['chapter']==10])
        self.assertEqual(len(a['shots']),22)
    def test_fifteen_genuine_historical_items_and_only_necessary_diagrams(self):
        a=json.loads((HERE/'CHAPTER10_EXPLICIT_HISTORICAL_PICTURE_EDIT.json').read_text())
        photos=[z for z in a['shots'] if z['visual_kind']=='photo']
        diagrams=[z for z in a['shots'] if z['visual_kind']=='graphic']
        self.assertEqual((len(photos),len(diagrams)),(15,7))
        self.assertGreaterEqual(len(set(z['source_asset_id'] for z in photos)),10)
        styles=json.loads((ROOT/'REMAINING_11_CHAPTERS_DIRECTED_ART_TYPES.json').read_text())
        allowed=set(styles['expected_approved_graphics_per_chapter']['10'])
        for z in diagrams:self.assertIn(z['source_asset_id'],allowed)
        for z in a['shots']:
            self.assertFalse(z['publication_approved'])
            self.assertFalse(z['licensing_and_identification_editor_approved'])
            self.assertFalse(z['complete_audiovisual_playback_editor_approved'])
    def test_no_photo_mislabeled_as_british_inquiry_or_actual_sinking(self):
        a=json.loads((HERE/'CHAPTER10_EXPLICIT_HISTORICAL_PICTURE_EDIT.json').read_text())
        photos={z['source_asset_id']:z for z in a['shots'] if z['visual_kind']=='photo'}
        self.assertIn('U.S.',photos['loc_senate_hearing_1383']['onscreen_label'])
        self.assertIn('AFTER',photos['lifeboats']['onscreen_label'])
        self.assertTrue(a['editorial_status'].startswith('BLOCKED'))
if __name__=='__main__':unittest.main()
