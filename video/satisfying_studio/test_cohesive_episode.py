"""Fail-closed regression tests for the rejected mixed-theme / looped-Foley ASMR edit."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / "production"))
from build_cohesive_episode import EditorialError, validate


class EpisodeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = self.root = Path(self.tmp.name)
        (root / "takes").mkdir()
        self.material = "translucent jelly"
        self.shots = []
        self.cues = []
        import hashlib
        for i in range(9):
            p = root / "takes" / f"shot{i:02d}.mp4"
            p.write_bytes(("distinct-editor-cut-"+str(i)).encode())
            action = "gel compression" if i % 2 == 0 else "gel release"
            self.shots.append({
                "file": f"takes/shot{i:02d}.mp4",
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "duration_frames": 480,
                "material_family": self.material,
                "interaction": action,
                "source_url": "https://example.org/creator-owned-footage",
                "license": "original",
            })
            for j in range(4):
                frame = i*480+30+j*110
                self.cues.append({
                    "file": f"recorded/audio{(i*4+j)%6}.wav",
                    "sha256": f"approved-recording-{(i*4+j)%6}",
                    "source_url": "https://example.org/creator-owned-foley",
                    "license": "original",
                    "frame": frame,
                    "visual_contact_frame": frame,
                    "material_family": self.material,
                    "interaction": action,
                    "auditioned_in_context": True,
                    "gain_db": -9,
                    "max_length_seconds": 2.5,
                })
        self.foley = {"fps":24, "duration_seconds":180, "cues":self.cues}
        self.episode = {"material_family":self.material, "fps":24,
                        "duration_seconds":180,
                        "manual_timeline_approved":True,
                        "foley_manifest":"foley.json",
                        "shots":self.shots}
        self.save()

    def save(self):
        (self.root/"foley.json").write_text(json.dumps(self.foley))
        self.manifest = self.root/"episode_manifest.json"
        self.manifest.write_text(json.dumps(self.episode))

    def check(self):
        self.save()
        return validate(self.manifest,probe=False)

    def test_coherent_episode_with_individual_contact_sounds(self):
        data, root, shots, foley_file = self.check()
        self.assertEqual(len(shots),9)
        self.assertEqual(data["material_family"],self.material)

    def test_reject_mixed_materials_even_with_valid_assets(self):
        self.shots[4]["material_family"]="watercolour dye"
        with self.assertRaisesRegex(EditorialError,"changes the ASMR material family"):
            self.check()

    def test_reject_reused_exact_same_video_take(self):
        self.shots[7]["file"]=self.shots[0]["file"]
        self.shots[7]["sha256"]=self.shots[0]["sha256"]
        with self.assertRaisesRegex(EditorialError,"exact same take reused"):
            self.check()

    def test_reject_audio_out_of_sync(self):
        self.cues[0]["visual_contact_frame"]+=3
        with self.assertRaisesRegex(EditorialError,"within one frame"):
            self.check()

    def test_reject_wrong_material_audio(self):
        self.cues[0]["material_family"]="crunchy shell"
        with self.assertRaisesRegex(EditorialError,"material mismatch"):
            self.check()

    def test_reject_unheard_foley(self):
        self.cues[0]["auditioned_in_context"]=False
        with self.assertRaisesRegex(EditorialError,"must be auditioned"):
            self.check()

    def test_reject_repetitive_short_foley(self):
        for cue in self.cues:
            cue["sha256"]="same-five-second-foley-loop"
        with self.assertRaisesRegex(EditorialError,"same tiny Foley clips"):
            self.check()

    def test_reject_sparse_five_second_foley_for_long_sequence(self):
        self.foley["cues"] = [cue for j,cue in enumerate(self.cues) if j % 4 == 0]
        with self.assertRaisesRegex(EditorialError,"too few actual contact sounds"):
            self.check()

    def test_reject_incomplete_three_minutes(self):
        self.shots[-1]["duration_frames"]-=1
        with self.assertRaisesRegex(EditorialError,"4,320 unique frames"):
            self.check()

    def test_reject_unapproved_timeline(self):
        self.episode["manual_timeline_approved"]=False
        with self.assertRaisesRegex(EditorialError,"must approve"):
            self.check()


if __name__=="__main__":
    unittest.main()
