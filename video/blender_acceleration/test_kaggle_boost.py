"""Safety and resume logic tests that run without Blender or Kaggle access."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import kaggle_boost as boost

class BlenderBoostTests(unittest.TestCase):
    def test_explicit_frames_and_ranges(self):
        self.assertEqual(boost.parse_frames("4-6,1,5"),[1,4,5,6])
        self.assertEqual(boost.ranges([1,4,5,6]),[(1,1),(4,6)])
        for invalid in ("","0","8-2","2-99999","1;rm -rf /"):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                boost.parse_frames(invalid)

    def test_asset_index_does_not_approve_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/"asset.glb").write_bytes(b"approved? no")
            (root/"ignored.exe").write_bytes(b"untracked")
            dest=root/"assets.json"
            self.assertEqual(boost.index_assets(root,dest)["count"],1)
            data=json.loads(dest.read_text())
            self.assertFalse(data["assets"][0]["license_verified"])
            self.assertFalse(data["assets"][0]["art_approved"])

    def test_dry_run_and_prohibit_mixed_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            scene=root/"test.blend";scene.write_bytes(b"blend scene")
            output=root/"render"
            plan=boost.render(scene,output,[1,2],"cycles","CPU",12,35,60,True)
            self.assertEqual(plan["pending"],2)
            self.assertFalse(output.exists())
            output.mkdir()
            (output/"render_manifest.json").write_text(json.dumps({"fingerprint":"other"}))
            with self.assertRaisesRegex(ValueError,"changed"):
                boost.render(scene,output,[1,2],"cycles","CPU",12,35,60,True)

    def test_incomplete_png_is_not_cached(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/"frame_0001.png"
            file.write_bytes(b"not a png")
            self.assertFalse(boost.valid_png(file))

    def test_install_never_runs_apt_without_explicit_option(self):
        with patch.object(boost,"doctor",return_value={"blender":None,"ffmpeg":None,"ffprobe":None}):
            with patch("subprocess.run") as run:
                result=boost.install(False)
                self.assertEqual(result["status"],"missing_tools")
                run.assert_not_called()

if __name__=="__main__":
    unittest.main()
