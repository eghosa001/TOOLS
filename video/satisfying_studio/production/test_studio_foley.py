"""CGI studio Foley sourcing from existing sound archives; no user uploads or network."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from production import studio_foley


class StudioCC0Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.cache=self.root/"studio_cache"
        self.cache.mkdir()
        self.project=self.root/"cg_project"
        self.project.mkdir()
        with zipfile.ZipFile(self.cache/"rubberduck_water_slime.zip","w") as z:
            z.writestr("slime_03.ogg",b"fixture sound only, not real recorded audio")
            z.writestr("non_sound.txt",b"text")
            z.writestr("../evil.wav",b"bad entry not selected")
        with zipfile.ZipFile(self.cache/"rubberduck_breaking_falling.zip","w") as z:
            z.writestr("glass_crack_02.ogg",b"small fake fixture")

    def test_uses_studio_cache_and_marks_every_candidate_unapproved(self):
        result=studio_foley.stage(self.cache,self.project,"slime")
        self.assertFalse(result["user_media_required"])
        self.assertGreaterEqual(result["candidates_staged"],1)
        for item in result["studio_owned_asset_inventory_candidates"]:
            self.assertEqual(item["asset_owner"],"studio")
            self.assertEqual(item["license"],"CC0")
            self.assertFalse(item["reviewed"])
            self.assertFalse(item["auditioned_against_picture"])
            self.assertFalse(item["artistic_approval"])
            self.assertTrue((self.project/item["file"]).is_file())
        self.assertTrue((self.project/"foley_candidates_unapproved.json").is_file())

    def test_broken_paths_cannot_escape_project(self):
        result=studio_foley.stage(self.cache,self.project,"glass-fruit",limit=3)
        self.assertTrue(all(not any(part==".." for part in Path(item["file"]).parts)
                       for item in result["studio_owned_asset_inventory_candidates"]))

    def test_missing_library_never_demands_user_recordings(self):
        missing=self.root/"new_cache"
        self.assertEqual(studio_foley.candidates(missing,"soap-cutting"),[])
        result=studio_foley.stage(missing,self.project,"soap-cutting",limit=4)
        self.assertEqual(result["candidates_staged"],0)
        self.assertFalse(result["user_media_required"])
        self.assertTrue(result["missing_packs"])

    def test_no_candidate_is_pretended_as_matching_material(self):
        candidates=studio_foley.candidates(self.cache,"soap-cutting")
        self.assertTrue(all(item["approved"] is False and
                            item["material_action_match"] is False
                            for item in candidates))


if __name__=="__main__":
    unittest.main()
