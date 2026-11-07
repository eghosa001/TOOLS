"""Offline tests: do not contact Google APIs."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from video.audiobook_studio import drive_review_delivery as d

class FakeReply:
    def __init__(self,status_code=200,data=None,headers=None):
        self.status_code=status_code;self._data=data or {};self.headers=headers or {}
    def json(self):return self._data
    def raise_for_status(self):
        if self.status_code>=400:raise RuntimeError('HTTP failure')

class DriveDeliveryTests(unittest.TestCase):
    def test_reject_youtube_only_scope(self):
        session=mock.Mock()
        session.post.return_value=FakeReply(data={'access_token':'safe','scope':'https://www.googleapis.com/auth/youtube.upload'})
        with self.assertRaises(PermissionError):
            d.authorized_token(refresh_token='dummy',client_json=json.dumps({'installed':{'client_id':'a','client_secret':'b'}}),session=session)
    def test_upload_rejects_bad_folder_before_network(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'fake.mp4';p.write_bytes(b'0'*100000)
            with self.assertRaises(ValueError):
                d.upload_private_review(p,folder_id='../evil',token='t')
    def test_private_resumable_upload_uses_exact_verified_mp4(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'disciple.mp4';p.write_bytes(b'0'*110000)
            session=mock.Mock()
            session.post.return_value=FakeReply(headers={'Location':'https://google.example/approved-session'})
            session.put.return_value=FakeReply(data={'id':'abc123','webViewLink':'https://drive.example/file','size':p.stat().st_size})
            with mock.patch.object(d,'validate_review_video',return_value={'sha256':'1'*64}):
                result=d.upload_private_review(p,folder_id='1J9GLTHs4gz1X9Pa107sc2CglncNIbpHX',token='test',session=session)
            self.assertTrue(result['review_only'])
            self.assertEqual(result['file_id'],'abc123')
            payload=session.post.call_args.kwargs['json']
            self.assertEqual(payload['appProperties']['release_status'],'review_only')
            self.assertEqual(payload['parents'],['1J9GLTHs4gz1X9Pa107sc2CglncNIbpHX'])

if __name__=='__main__':unittest.main()