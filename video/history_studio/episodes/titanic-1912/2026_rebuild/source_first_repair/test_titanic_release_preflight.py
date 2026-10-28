#!/usr/bin/env python3
"""Only production-relevant negative gates: no rerender or unrelated CI."""
from __future__ import annotations
import importlib.util,json,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("titanic_preflight",HERE/"titanic_release_preflight.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
class Tests(unittest.TestCase):
    def test_without_verified_manifest_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);r=m.check(p/"missing.json",p,p/"film.mp4",p/"signoff.json")
            self.assertFalse(r["release_approved"])
            self.assertIn("MISSING",r["errors"][0])
    def test_legacy_302_unapproved_shots_cannot_pass(self):
        p=HERE.parent/"MANUAL_SCENE_LEDGER_DRAFT.json"
        old=json.loads(p.read_text())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=root/"legacy.json"
            f.write_text(json.dumps({"shots":old["scenes"],"source_first_editorial_approval":"NOT_APPROVED"}))
            (root/"film.mp4").write_bytes(b"not a real film")
            (root/"signoff.json").write_text('{"approved_for_youtube_publication":true}')
            r=m.check(f,root,root/"film.mp4",root/"signoff.json")
            self.assertFalse(r["release_approved"])
            self.assertEqual(r["source_first_status"],"FAIL")
            self.assertTrue(any("editor" in x.lower() or "authentic" in x.lower() for x in r["errors"]))
    def test_no_synthetic_signoff_can_overwrite_real_digest(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"missing.json").write_text("{}")
            r=m.check(p/"missing.json",p,p/"film.mp4",p/"signoff.json")
            self.assertFalse(r["release_approved"])
if __name__=="__main__":unittest.main()
