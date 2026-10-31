"""AI/artist/Drive image import is local-only and never confers art approval."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import art_intake


class ArtIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.private = self.root / 'private'
        self.private.mkdir()
        self.source = self.root / 'generated.png'
        Image.new('RGB', (1280,720), (73, 104, 116)).save(self.source)
        self.shot = self.root / 'repo_shot.json'
        data = {'schema_version': 1, 'episode': 'E101', 'camera':'CAM03B', 'fps':24,
                'frame_count':72,'resolution':[1280,720],
                'drawings': {stage:[] for stage in art_intake.DRAWING_STAGES},
                'approvals':{'canon':{'approved':False,'reviewer':None},
                             'character_model':{'approved':False,'reviewer':None}}}
        self.shot.write_text(json.dumps(data))

    def add(self, **kwargs):
        params = dict(shot=self.shot,root=self.private,source=self.source,
                      stage='keys',origin='chatgpt_image',source_ref='ChatGPT conversation image',
                      frame=1)
        params.update(kwargs)
        return art_intake.add_asset(**params)

    def test_stage_image_keeps_origin_and_pending_review(self):
        row=self.add()
        self.assertEqual(row['review_status'],art_intake.STATUS)
        self.assertEqual(row['origin'],'chatgpt_image')
        self.assertTrue((self.private/row['path']).is_file())
        self.assertEqual(art_intake.digest(self.private/row['path']),row['sha256'])
        self.assertEqual(len(json.loads((self.private/art_intake.REGISTER).read_text())['assets']),1)

    def test_bridge_does_not_mark_approvals_true(self):
        self.add()
        output=self.private/'shot.json'
        report=art_intake.bind_manifest(shot=self.shot,root=self.private,output=output)
        self.assertEqual(report['status'],'BOUND_BUT_UNAPPROVED')
        spec=json.loads(output.read_text())
        self.assertEqual(len(spec['drawings']['keys']),1)
        self.assertFalse(spec['approvals']['character_model']['approved'])
        self.assertFalse(spec['approvals']['canon']['approved'])

    def test_drive_input_requires_genuine_drive_url(self):
        with self.assertRaisesRegex(art_intake.IntakeError,'Google Drive'):
            self.add(origin='google_drive',source_ref='https://example.com/test.png')

    def test_reference_sheet_not_assumed_keyframe(self):
        row=self.add(stage='character_model',frame=None,origin='artist',source_ref='artist created model sheet')
        self.assertTrue(row['path'].startswith('references/'))
        output=self.private/'shot.json'
        art_intake.bind_manifest(shot=self.shot,root=self.private,output=output)
        spec=json.loads(output.read_text())
        self.assertEqual(spec['drawings']['keys'],[])

    def test_duplicate_and_ambiguous_key_are_blocked(self):
        self.add()
        with self.assertRaisesRegex(art_intake.IntakeError,'already registered'):
            self.add()
        new_source=self.root/'alt.png'
        Image.new('RGB',(1280,720),(73,103,116)).save(new_source)
        self.add(source=new_source)
        with self.assertRaisesRegex(art_intake.IntakeError,'competing drawings'):
            art_intake.bind_manifest(shot=self.shot,root=self.private,output=self.private/'shot.json')

    def test_wrong_size_cannot_be_silently_cropped(self):
        Image.new('RGB',(600,600),'blue').save(self.source)
        with self.assertRaisesRegex(art_intake.IntakeError,'locked resolution'):
            self.add()

    def test_contact_sheet_is_review_only(self):
        self.add()
        preview=self.private/'review/contact.png'
        report=art_intake.contact_sheet(shot=self.shot,root=self.private,output=preview)
        self.assertEqual(report['status'],'REVIEW_ONLY')
        with Image.open(preview) as im:
            self.assertEqual(im.format,'PNG')
            self.assertEqual(im.width,1120)

    def test_source_tampering_is_detected(self):
        row=self.add()
        (self.private/row['path']).write_bytes(b'tampered')
        with self.assertRaisesRegex(art_intake.IntakeError,'checksum changed'):
            art_intake.bind_manifest(shot=self.shot,root=self.private,output=self.private/'shot.json')

    def test_corrupt_register_cannot_read_outside_private_root(self):
        row=self.add()
        record=self.private/art_intake.REGISTER
        obj=json.loads(record.read_text())
        obj["assets"][0]["path"]="../generated.png"
        record.write_text(json.dumps(obj))
        with self.assertRaisesRegex(art_intake.IntakeError, "unsafe relative path"):
            art_intake.contact_sheet(shot=self.shot,root=self.private,output=self.private/'review/corrupt.png')

    def test_previz_origin_keeps_technical_not_artist_status(self):
        row=self.add(origin='technical_previz',source_ref='local v13 vector experiment')
        self.assertEqual(row['origin'],'technical_previz')
        self.assertEqual(row['review_status'],art_intake.STATUS)

    def test_cannot_overwrite_public_manifest(self):
        self.add()
        with self.assertRaisesRegex(art_intake.IntakeError,'Cannot overwrite'):
            art_intake.bind_manifest(shot=self.shot,root=self.private,output=self.shot)


if __name__=='__main__':
    unittest.main()
