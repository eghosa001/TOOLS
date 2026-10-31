import hashlib,importlib.util,io,json,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'library'))
from asset_library import catalog,chosen,PACK_GENRES,git_blob_sha,validate_media
from import_extra_cc0 import gobkit_manifest,glb,safe_id
class LibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.items=catalog()
    def test_large_catalog_not_just_castles(self):
        self.assertEqual(len(self.items),5252)
        kinds={x['kind'] for x in self.items.values()}
        self.assertEqual(kinds,{'model','audio','hdr','texture'})
        self.assertTrue(any(x['pack']=='city-kit-commercial' for x in self.items.values()))
        self.assertTrue(any(x['pack']=='models/kaykit-skeletons' for x in self.items.values()))
    def test_license_cannot_be_assumed_cc0_for_mit(self):
        mit=[x for x in self.items.values() if x['license']=='MIT']
        self.assertEqual(len(mit),34)
        selected=chosen(self.items,[],['forge:models/rocketbox'],[],[],None,False)
        self.assertFalse(selected)
        self.assertEqual(len(chosen(self.items,[],['forge:models/rocketbox'],[],[],None,True)),34)
    def test_editor_selects_packs_not_random_shots(self):
        r=chosen(self.items,[],['kenney:castle-kit'],[],[],None,False)
        self.assertEqual(len(r),76)
        self.assertTrue(all(x['kind']=='model' for x in r))
        self.assertGreater(len(chosen(self.items,[],[],['city'],[],None,False)),100)
        with self.assertRaises(ValueError):chosen(self.items,[],['notvalid:bad'],[],[],None,False)
    def test_git_blob_integrity_rejects_tampering(self):
        binary=b'glTF'+(2).to_bytes(4,'little')+(20).to_bytes(4,'little')+b'12345678'
        row={'size':20,'blob_sha':git_blob_sha(binary),'path':'any.glb'}
        validate_media(binary,row)
        with self.assertRaises(ValueError):validate_media(binary[:-1]+b'X',row)
        with self.assertRaises(ValueError):validate_media(b'no',row)
    def test_url_pinned_and_no_arbitrary_host(self):
        for item in list(self.items.values())[::155]:
            self.assertTrue(item['url'].startswith('https://raw.githubusercontent.com/'))
            self.assertGreater(len(item['blob_sha']),20)
    def test_gobkit_license_and_free_url_guard(self):
        row={'packs':[{'id':'animals','license':'CC0 1.0','models':[{'id':'Bee','url':'https://gobkit.com/freebies/animal/Bee.glb','license':'CC0'}]}]}
        self.assertIn('animals__bee',gobkit_manifest(row))
        row['packs'][0]['models'][0]['url']='https://gobkit.com/pricing/paid.glb'
        with self.assertRaises(ValueError):gobkit_manifest(row)
        row['packs'][0]['models'][0]['url']='https://evil.example/freebies/model.glb'
        with self.assertRaises(ValueError):gobkit_manifest(row)
    def test_external_models_require_known_license(self):
        source={'packs':[{'id':'x','license':'unknown','models':[]}]}
        with self.assertRaises(ValueError):gobkit_manifest(source)
if __name__=='__main__':unittest.main()
