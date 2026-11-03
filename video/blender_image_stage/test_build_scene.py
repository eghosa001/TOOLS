"""Offline validation tests for explicit 2.5D shot manifests."""
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_scene import validate

PNG = bytes.fromhex("89504e470d0a1a0a") + bytes.fromhex(
    "0000000d4948445200000020000000200806000000737a7af4"
)  # PNG header is enough for validator; Blender integration smoke uses Pillow.

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/"art.png").write_bytes(PNG)
        self.scene={
            "schema_version":1,"resolution":[720,1280],"fps":24,"frames":120,
            "camera":{"pan_px":[20,0]},
            "layers":[{"name":"Foreground","image":"art.png","role":"foreground",
                       "rights":{"status":"original"},"depth":-1,
                       "position_px":[360,640],"parallax":1,
                       "keys":[{"frame":1,"position_px":[360,640]},
                               {"frame":120,"position_px":[400,640]}]}]
        }
    def load(self):
        path=self.root/"shot.json"
        path.write_text(json.dumps(self.scene),encoding="utf-8")
        return validate(path)
    def test_valid(self):
        self.assertEqual(self.load()["layers"][0]["dimensions"],(32,32))
    def test_unknown_license(self):
        self.scene["layers"][0]["rights"]={"status":"unknown"}
        with self.assertRaisesRegex(ValueError,"explicit commercial-use"):
            self.load()
    def test_missing_origin_for_cc0(self):
        self.scene["layers"][0]["rights"]={"status":"CC0"}
        with self.assertRaisesRegex(ValueError,"author and URL"):
            self.load()
    def test_missing_image(self):
        self.scene["layers"][0]["image"]="missing.png"
        with self.assertRaises(FileNotFoundError):
            self.load()
    def test_path_escape(self):
        self.scene["layers"][0]["image"]="../../protected.png"
        with self.assertRaises(ValueError):
            self.load()
    def test_duplicate_key(self):
        self.scene["layers"][0]["keys"].append({"frame":1})
        with self.assertRaisesRegex(ValueError,"duplicate frame"):
            self.load()
    def test_invalid_parallax(self):
        self.scene["layers"][0]["parallax"]=400
        with self.assertRaisesRegex(ValueError,"parallax"):
            self.load()
    def test_hash_changed(self):
        self.scene["layers"][0]["sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"hash differs"):
            self.load()

if __name__=="__main__":unittest.main()
