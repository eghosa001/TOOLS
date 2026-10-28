"""Offline safeguards for the isolated Kaggle production bridge.

These tests do not contact Kaggle, download materials, or render footage.
"""
import ast
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
KAGGLE=ROOT/"kaggle"

class KaggleIsolationTests(unittest.TestCase):
    def test_all_kaggle_scripts_parse(self):
        for name in ("asset_pack.py","build_blender_scene.py","kaggle_job.py","kaggle_bridge.py"):
            path=KAGGLE/name
            self.assertTrue(path.is_file(),name)
            ast.parse(path.read_text(encoding="utf-8"),filename=str(path))

    def test_private_and_source_audited(self):
        bridge=(KAGGLE/"kaggle_bridge.py").read_text()
        self.assertIn('"is_private":True',bridge)
        self.assertIn('"dataset_sources":[id_]',bridge)
        self.assertNotIn('["datasets","create","-u"',bridge)
        sounds=(KAGGLE/"asset_pack.py").read_text()
        self.assertIn("ASSET_PROVENANCE.json",sounds)
        self.assertIn("sha256",sounds)
        self.assertIn("opengameart.org",sounds)

    def test_missing_credentials_stop_before_asset_downloads(self):
        env=os.environ.copy()
        env["KAGGLE_USERNAME"]="testonly"
        env.pop("KAGGLE_API_TOKEN",None)
        env.pop("KAGGLE_KEY",None)
        result=subprocess.run([sys.executable,str(KAGGLE/"kaggle_bridge.py"),"--publish"],
                              capture_output=True,text=True,env=env,timeout=15)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("token missing",result.stderr)
        self.assertNotIn("UPLOAD ACCEPTED",result.stdout)

    def test_only_lookdev_not_full_animation(self):
        kaggle=(KAGGLE/"kaggle_job.py").read_text()
        self.assertIn("timeout=180",kaggle)
        self.assertIn("blender_3d_lookdev.png",kaggle)
        self.assertNotIn("generate_video(",kaggle)
        self.assertNotIn("kaggle kernels push",kaggle)

if __name__=="__main__":unittest.main()
