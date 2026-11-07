"""Fastlane regression tests. Pure CPU; no Kaggle, no paid APIs or uploads."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import wave
import zipfile
from video.audiobook_studio import episode_fastlane as f

class FastlaneTests(unittest.TestCase):
    def test_voice_model_settings_alter_cache_key(self):
        a=f.chunk_key('The door opened.')
        self.assertEqual(a,f.chunk_key('The door opened.'))
        self.assertNotEqual(a,f.chunk_key('The door opened.',speaker='Other'))
        self.assertNotEqual(a,f.chunk_key('The door opened.',instruction='Different direction'))
        self.assertNotEqual(a,f.chunk_key('The door was opened.'))
    def test_truncated_wav_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.wav'
            p.write_bytes(b'RIFF1234567')
            self.assertFalse(f.validated_wav(p))
            with wave.open(str(p),'wb') as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\0'*24000)
            self.assertTrue(f.validated_wav(p))
    def test_ledger_rejects_gaps_and_unapproved_art(self):
        valid=[{'start_chunk':0,'end_chunk':2,'scene_key':'S1','approved_visual_file':True},
               {'start_chunk':2,'end_chunk':4,'scene_key':'S2','visual_approved':True}]
        f.validate_scene_ledger(valid,segment_count=4)
        with self.assertRaises(ValueError):
            f.validate_scene_ledger(valid[:1],segment_count=4)
        with self.assertRaises(ValueError):
            f.validate_scene_ledger([dict(valid[0],end_chunk=3),valid[1]],segment_count=4)
        with self.assertRaises(ValueError):
            f.validate_scene_ledger([dict(valid[0],approved_visual_file=False),valid[1]],segment_count=4)
    def test_checkpoint_rejects_changed_source_or_audio(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); folder=root/'output';folder.mkdir()
            (folder/'text.json').write_text('private data')
            (folder/'visual.png').write_bytes(b'\x00'*100)
            s=hashlib.sha256(b'original').hexdigest()
            dest=root/'checkpoint.zip'
            result=f.efficient_checkpoint(folder,dest,source_sha256=s)
            self.assertEqual(result['files'],2)
            f.inspect_checkpoint(dest,source_sha256=s)
            with self.assertRaises(ValueError):
                f.inspect_checkpoint(dest,source_sha256=hashlib.sha256(b'edited').hexdigest())
            with zipfile.ZipFile(dest) as z:
                self.assertEqual(z.getinfo('visual.png').compress_type,zipfile.ZIP_STORED)
    def test_review_gate_does_not_claim_content_approval(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'review.mp4';p.write_bytes(b'0'*110000)
            data={'format':{'duration':'1507.8'},'streams':[
                  {'codec_type':'video','codec_name':'h264','width':1920,'height':1080},
                  {'codec_type':'audio','codec_name':'aac'}]}
            with mock.patch.object(f,'probe_media',return_value=data):
                r=f.validate_review_video(p,expected_audio_seconds=1507.5,expected_hash=f.sha256(p))
                self.assertEqual(r['status'],'TECHNICAL_REVIEW_PASS')
                self.assertFalse(r['ready_for_youtube'])
                with self.assertRaises(ValueError):
                    f.validate_review_video(p,expected_audio_seconds=1600)
                with self.assertRaises(ValueError):
                    f.validate_review_video(p,expected_hash='0'*64)
                data['streams'][0]['width']=640
                with self.assertRaises(ValueError):
                    f.validate_review_video(p)
    def test_atomic_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'nested'/'report.json'
            f.atomic_json(p,{'pass':True})
            self.assertTrue(json.loads(p.read_text())['pass'])
            self.assertEqual(list(p.parent.glob('*.tmp')),[])

if __name__=='__main__':unittest.main()