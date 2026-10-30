"""Manually directed multiformat take-assembly tests, no paid API or video downloads."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import studio_formats as formats
from production import assemble_reviewed as assembler


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = formats.init_project("domino-marble", self.root / "episode")
        self.dir = self.manifest.parent
        self.data = json.loads(self.manifest.read_text())
        kind = formats.get_format("domino-marble")
        self.data["manual_timeline_approved"] = True
        for role, file in (("scene", "original.blend"), ("foley", "real_foley.wav")):
            path=self.dir / file
            path.write_bytes(b"test fixture: original content")
            item = {
                "role":role, "file":file, "sha256":formats.sha256(path),
                "license":"original", "asset_owner":"studio", "source_url":"https://example.com/studio-recording",
                "material":kind["material"], "gesture":kind["action"], "reviewed":True,
            }
            if role=="foley":
                item["auditioned_against_picture"]=True
            self.data["asset_inventory"].append(item)
        take=self.dir / "approved_take.mp4"
        take.write_bytes(b"unit test fake take; no claim of real video")
        self.data["manually_directed_shots"][0].update({
            "cgi_source_blend": "original.blend",
            "cgi_source_blend_sha256": formats.sha256(self.dir/"original.blend"),
            "rendered_from_cgi": True,
            "edited_take":take.name,
            "edited_take_sha256":formats.sha256(take),
            "take_visual_audio_reviewed":True,
            "take_review_notes":"Unit test fixture only: editor watches unique picture and listens to every matching physical contact cue",
            "source_license":"original",
            "source_url":"studio://blender/unique-original-take",
        })
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.data),encoding="utf-8")

    def test_no_automatic_timeline_or_media_selection(self):
        data, root, takes=assembler.validate(self.manifest,probe=False)
        self.assertEqual(len(takes),1)
        self.assertEqual(data["duration_seconds"],5)

    def test_missing_manual_approval_fails(self):
        self.data["manual_timeline_approved"]=False
        self.save()
        with self.assertRaisesRegex(assembler.AssemblyBlocked, "Editor must explicitly approve"):
            assembler.validate(self.manifest,probe=False)

    def test_original_blender_source_hash_is_required(self):
        self.data["manually_directed_shots"][0]["cgi_source_blend_sha256"] = "not-real"
        self.save()
        with self.assertRaisesRegex(assembler.AssemblyBlocked, "actual CGI scene"):
            assembler.validate(self.manifest, probe=False)

    def test_external_footage_source_is_rejected(self):
        self.data["manually_directed_shots"][0]["source_url"] = "https://stock.example/footage.mp4"
        self.save()
        with self.assertRaisesRegex(assembler.AssemblyBlocked, "studio-authored original CGI"):
            assembler.validate(self.manifest, probe=False)

    def test_stale_take_rejected(self):
        self.data["manually_directed_shots"][0]["edited_take_sha256"]="wrong"
        self.save()
        with self.assertRaisesRegex(assembler.AssemblyBlocked, "hash mismatch"):
            assembler.validate(self.manifest,probe=False)

    def test_same_clip_duplicate_is_not_silent_filler(self):
        self.data["duration_seconds"]=10
        first=self.data["manually_directed_shots"][0]
        second=dict(first)
        second["start_seconds"]=5
        second["end_seconds"]=10
        second["transition_intent"]="Same object deserves a distinct second take"
        self.data["manually_directed_shots"]=[first,second]
        self.save()
        with self.assertRaisesRegex(assembler.AssemblyBlocked, "exact duplicate take"):
            assembler.validate(self.manifest,probe=False)

    def test_no_source_audio_review_fails(self):
        self.data["manually_directed_shots"][0]["take_visual_audio_reviewed"]=False
        self.save()
        with self.assertRaisesRegex(assembler.AssemblyBlocked, "watch/listen"):
            assembler.validate(self.manifest,probe=False)

    def test_no_auto_crop_of_wide_takes(self):
        with patch.object(assembler.subprocess, "run") as mocked:
            mocked.return_value.stdout=json.dumps({
                "format":{"duration":"5.0"},
                "streams":[
                    {"codec_type":"video","codec_name":"h264",
                     "width":1920,"height":1080,"avg_frame_rate":"24/1","nb_read_frames":"120"},
                    {"codec_type":"audio","sample_rate":"48000","channels":2},
                ]
            })
            with self.assertRaisesRegex(assembler.AssemblyBlocked, "No auto crop"):
                assembler.inspect_take(self.dir/"approved_take.mp4",120,"9:16")

    def test_check_only_does_not_render_or_approve(self):
        with patch.object(assembler, "validate", return_value=(
                 self.data, self.dir, [self.dir / "approved_take.mp4"])):
            result=assembler.assemble(self.manifest,check_only=True)
        self.assertEqual(result["status"],"source_takes_validated_not_rendered")


if __name__=="__main__":
    unittest.main()
