"""Offline source/geometry preflight checks. No Blender or GPU required."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ops"))
import art_preflight as p


class NinefoldArtIntakeTests(unittest.TestCase):
    def test_missing_private_sources_fail_closed(self):
        report = p.audit()
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["creative_release_approval"])
        self.assertEqual(len(report["issues"]), 4)

    def test_reject_zip_path_escape(self):
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "escape.zip"
            with zipfile.ZipFile(file, "w") as archive:
                archive.writestr("../escape.txt", "NO")
            details, issues = p.inspect_transfer(file)
            self.assertFalse(details["validated"])
            self.assertTrue(any("unsafe" in issue for issue in issues))

    def test_reject_visible_temp_actor_in_ora(self):
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "template.ora"
            items = [
                ("TEMP Naya proxy", "data/0.png", "visible"),
                ("paint", "data/1.png", "visible"),
                ("shadow", "data/2.png", "visible"),
                ("foreground", "data/3.png", "visible"),
            ]
            xml = '<image w="1280" h="720"><stack>'
            xml += "".join(
                '<layer name="%s" src="%s" visibility="%s"/>' % row
                for row in items
            )
            xml += "</stack></image>"
            with zipfile.ZipFile(file, "w") as archive:
                archive.writestr("mimetype", "image/openraster")
                archive.writestr("stack.xml", xml)
                for index in range(4):
                    archive.writestr("data/%d.png" % index, b"a")
            details, issues = p.inspect_ora(file)
            self.assertFalse(details["layered"])
            self.assertTrue(any("VISIBLE" in issue for issue in issues))

    def test_enforce_gp_layers_and_canonical_dimensions(self):
        evidence = {
            "blender_version": [4, 5, 15],
            "active_camera": p.CANON["cam_name"],
            "cam_xyz": p.CANON["cam_xyz"],
            "look_at": p.CANON["look_at"],
            "naya_root": p.CANON["naya_root"],
            "hand_target": p.CANON["hand_target"],
            "resolution": [1280, 720], "fps": 24,
            "temporary_actor_planes_visible": False,
            "distinct_rope_systems": 3,
            "actors": {
                name: {"height_m": height, "grease_pencil_layers": 9, "is_2d": True}
                for name, height in p.CANON["model_heights_m"].items()
            },
        }
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "probe.json"
            file.write_text(json.dumps(evidence), encoding="utf-8")
            _, issues = p.inspect_blender(file)
            self.assertEqual(issues, [])
            evidence["actors"]["iri"]["grease_pencil_layers"] = 8
            file.write_text(json.dumps(evidence), encoding="utf-8")
            _, issues = p.inspect_blender(file)
            self.assertTrue(any("iri has fewer" in issue for issue in issues))

    def test_never_auto_approve_release(self):
        self.assertFalse(p.audit()["creative_release_approval"])


    def test_blank_final_artist_layers_cannot_pass(self):
        from io import BytesIO
        from PIL import Image
        def png(alpha):
            image = Image.new("RGBA", (1280, 720), (44, 82, 91, alpha))
            buf = BytesIO()
            image.save(buf, format="PNG")
            return buf.getvalue()
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "blank.ora"
            entries = [
                ("NAYA original flat TEMP guide", "data/temp.png", "hidden", 255),
                ("NAYA FINAL INK + SHADOW", "data/ink.png", "visible", 0),
                ("BG PAINT OVER", "data/paint.png", "visible", 0),
                ("3D world colours", "data/guide.png", "visible", 255),
            ]
            xml = '<image w="1280" h="720"><stack>'
            xml += "".join(
                '<layer name="%s" src="%s" visibility="%s"/>' % row[:3]
                for row in entries
            )
            xml += "</stack></image>"
            with zipfile.ZipFile(file, "w") as archive:
                archive.writestr("mimetype", "image/openraster")
                archive.writestr("stack.xml", xml)
                for _, src, _, alpha in entries:
                    archive.writestr(src, png(alpha))
            report, issues = p.inspect_ora(file)
            self.assertTrue(report["layered"])
            self.assertFalse(report["artist_paint_present"])
            self.assertTrue(any("Naya FINAL INK layer" in issue for issue in issues))
            self.assertTrue(any("BG PAINT layer" in issue for issue in issues))

    def test_real_paint_pixels_meet_metadata_only_not_creative_review(self):
        from io import BytesIO
        from PIL import Image
        def png(alpha):
            img = Image.new("RGBA", (1280, 720), (52, 96, 118, alpha))
            buf = BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "inked.ora"
            lines = [
                ("NAYA FINAL INK + SHADOW", "data/ink.png", 255),
                ("BG PAINT OVER", "data/bg.png", 255),
                ("FOREGROUND corrected occlusion", "data/foreground.png", 255),
                ("CONTACT SHADOW", "data/shadow.png", 255),
            ]
            xml = '<image w="1280" h="720"><stack>'
            xml += "".join(
                '<layer name="%s" src="%s" visibility="visible"/>' % (name, src)
                for name, src, _ in lines
            ) + "</stack></image>"
            with zipfile.ZipFile(file, "w") as archive:
                archive.writestr("mimetype", "image/openraster")
                archive.writestr("stack.xml", xml)
                for _, src, alpha in lines:
                    archive.writestr(src, png(alpha))
            report, issues = p.inspect_ora(file)
            self.assertEqual(issues, [])
            self.assertTrue(report["artist_paint_present"])
            self.assertEqual(p.audit(ora=file)["status"], "BLOCKED")
            self.assertFalse(p.audit(ora=file)["creative_release_approval"])


if __name__ == "__main__":
    unittest.main()
