"""Free commercial ASMR stock-video intake regression tests: no media downloads."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from production.licensed_footage_gate import StockGateError, verify

class LicensedStockGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        video=self.root/"pexels_take.mp4"
        video.write_bytes(b"test recording placeholder\n"*20)
        audio=self.root/"sand.wav"
        audio.write_bytes(b"test CC0 original sand recording\n"*20)
        self.data={
            "source_media_policy":"LICENSED_STOCK_OR_HYBRID",
            "status":"REVIEW_CANDIDATE_NOT_EDITORIAL_APPROVAL",
            "fps":24,"resolution":"720x1280","duration_seconds":5,
            "shot_count":1,"unique_picture_sources":1,
            "user_supplied_media_required":False,
            "creative_work":"Four-dimensional human-authored visual idea with original tactile action and carefully edited registered sound sources and material-specific cuts.",
            "shots":[{
                "path":video.name, "sha256":hashlib.sha256(video.read_bytes()).hexdigest(),
                "src":"https://www.pexels.com/video/flowing-sand-123456/",
                "licence":"Pexels License","start":0,"duration":5,
                "action":"Tiny granules cascading from a scoop into a textured bowl",
                "intent":"The frame keeps the entire hand, pouring vessel, falling stream and destination visible without arbitrary zooming",
                "material_family":"dry sand",
            }],
            "sound_sources":[{
                "file":audio.name,"sha256":hashlib.sha256(audio.read_bytes()).hexdigest(),
                "source_url":"https://freesound.org/people/test/sounds/44444/",
                "license":"CC0",
            }],
            "actual_contact_sound_review":False,
            "full_visual_audio_approval":False,
        }
        self.manifest=self.root/"clip.json"
        self.save()
    def save(self):
        self.manifest.write_text(json.dumps(self.data))
    def check(self,release=False):
        return verify(self.manifest, self.root, probe=False, release=release)

    def test_original_publisher_and_cc0_audio_pass_preflight_not_approval(self):
        x=self.check()
        self.assertEqual(x["rights_and_timing_intake"],"PASS")
        self.assertFalse(x["artistic_approval"])
        self.assertFalse(x["youtube_monetization_guarantee"])

    def test_no_unlicensed_social_video_scrape(self):
        self.data["shots"][0]["src"]="https://youtube.com/watch?v=creator"
        self.save()
        with self.assertRaisesRegex(StockGateError,"licence/source host mismatch"):
            self.check()

    def test_mixkit_restricted_stock_is_rejected(self):
        self.data["shots"][0]["src"]="https://mixkit.co/free-stock-video/pouring-sand/"
        self.data["shots"][0]["licence"]="Mixkit Stock Video Restricted License"
        self.save()
        with self.assertRaisesRegex(StockGateError,"noncommercial"):
            self.check()

    def test_mixkit_free_permitted_only_with_matching_page_and_exact_label(self):
        self.data["shots"][0]["src"]="https://mixkit.co/free-stock-video/pouring-sand/"
        self.data["shots"][0]["licence"]="Mixkit Stock Video Free License"
        self.save()
        self.assertEqual(self.check()["source_assets_checked"],1)

    def test_pixabay_commercial_licence_supported(self):
        self.data["shots"][0]["src"]="https://pixabay.com/videos/beautiful-sand-falling-1234/"
        self.data["shots"][0]["licence"]="Pixabay Content License"
        self.save()
        self.assertEqual(self.check()["source_assets_checked"],1)

    def test_file_hash_modified_blocks(self):
        self.data["shots"][0]["sha256"]="a"*64
        self.save()
        with self.assertRaisesRegex(StockGateError,"SHA256 mismatch"):
            self.check()

    def test_gimmick_edit_without_creative_value_blocks(self):
        self.data["creative_work"]="Just crop stock footage"
        self.save()
        with self.assertRaisesRegex(StockGateError,"original editorial"):
            self.check()

    def test_repeat_original_excerpt_not_allowed_for_padding(self):
        self.data["shots"].append(dict(self.data["shots"][0],start=1,duration=5))
        self.data["duration_seconds"]=10
        self.data["shot_count"]=2
        self.save()
        with self.assertRaisesRegex(StockGateError,"repeated as filler"):
            self.check()

    def test_unsafe_relative_path_blocked(self):
        self.data["shots"][0]["path"]="../secret.mp4"
        self.save()
        with self.assertRaisesRegex(StockGateError,"Unsafe"):
            self.check()

    def test_missing_real_foley_audio_blocks(self):
        self.data["sound_sources"]=[]
        self.save()
        with self.assertRaisesRegex(StockGateError,"Recorded licensed"):
            self.check()

    def test_cc_by_audio_requires_public_attribution(self):
        self.data["sound_sources"][0]["license"]="CC BY 4.0"
        self.save()
        with self.assertRaisesRegex(StockGateError,"attribution"):
            self.check()

    def test_release_without_entire_human_headphone_review_blocks(self):
        with self.assertRaisesRegex(StockGateError,"No release without"):
            self.check(release=True)

if __name__=="__main__":
    unittest.main()
