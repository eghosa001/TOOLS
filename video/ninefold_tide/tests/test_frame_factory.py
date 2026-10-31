"""Offline technical tests for the Ninefold 2D frame renderer (Pillow only)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from frame_factory import FrameSpecError, render, validate_spec


def png(path: Path, color, size=(8, 8)):
    Image.new("RGBA", size, color).save(path)


class FrameFactoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        png(self.root / "bg.png", (255, 255, 255, 255), (32, 24))
        png(self.root / "red.png", (220, 10, 20, 255))
        png(self.root / "blue.png", (10, 20, 230, 255))
        png(self.root / "rail.png", (0, 180, 0, 255), (2, 2))
        self.data = {
            "version": 1, "shot_id": "E101_CAM03B_TEST",
            "width": 32, "height": 24, "fps": 24, "frames": 6,
            "layers": [
                {"id": "painted_bg", "z": 0, "image": "bg.png", "parallax": 0},
                {"id": "naya", "z": 10, "on_twos": True,
                 "drawings": [
                     {"frame": 1, "image": "red.png"},
                     {"frame": 3, "image": "blue.png"}
                 ],
                 "motion": [{"frame": 1, "x": 0, "y": 0, "scale": 1}]},
                {"id": "foreground_rail", "z": 20, "image": "rail.png"},
            ],
        }
        self.spec = self.root / "test_shot.json"

    def write(self):
        self.spec.write_text(json.dumps(self.data), encoding="utf-8")

    def readpixel(self, f, pos):
        with Image.open(self.root / "frames" / f"frame_{f:06d}.png") as im:
            return im.convert("RGB").getpixel(pos)

    def test_all_frames_exposed_with_no_frame_morphing(self):
        self.write()
        result = render(self.spec, self.root / "frames")
        self.assertEqual(6, result["rendered_frames"])
        self.assertEqual(4, result["held_frames_reused_without_recompositing"])
        self.assertEqual((220, 10, 20), self.readpixel(1, (5, 5)))
        self.assertEqual(self.readpixel(1, (5, 5)), self.readpixel(2, (5, 5)))
        self.assertEqual((10, 20, 230), self.readpixel(3, (5, 5)))
        self.assertEqual((10, 20, 230), self.readpixel(4, (5, 5)))
        self.assertFalse(result["artistic_approval"])
        self.assertFalse(result["release_authorized"])
        self.assertEqual(24, result["fps"])
        self.assertEqual((0, 180, 0), self.readpixel(1, (1, 1)))
        self.assertTrue((self.root / "frames" / "technical_report_000001_000006.json").is_file())

    def test_camera_parallax_only_when_requested(self):
        self.data["camera"] = [{"frame": 1, "x": 0}, {"frame": 3, "x": 4, "ease": "linear"}]
        self.write()
        render(self.spec, self.root / "frames")
        # foreground/actor move, background stays still since parallax 0
        self.assertEqual((255, 255, 255), self.readpixel(3, (30, 20)))
        self.assertEqual((0, 180, 0), self.readpixel(1, (1, 1)))
        self.assertEqual((10, 20, 230), self.readpixel(3, (1, 5)))

    def test_chunk_and_half_res(self):
        self.write()
        report = render(self.spec, self.root / "frames", scale=0.5, start=2, end=4)
        self.assertEqual([2, 4], report["frame_range"])
        self.assertEqual((16, 12), (report["width"], report["height"]))
        self.assertFalse((self.root / "frames" / "frame_000001.png").exists())
        self.assertTrue((self.root / "frames" / "frame_000004.png").exists())

    def test_missing_blank_or_escaping_art_is_blocked(self):
        self.data["layers"][1]["drawings"][0]["image"] = "../secrets.png"
        self.write()
        with self.assertRaises(FrameSpecError):
            render(self.spec, self.root / "frames")
        self.data["layers"][1]["drawings"][0]["image"] = "empty.png"
        png(self.root / "empty.png", (0, 0, 0, 0))
        self.write()
        with self.assertRaisesRegex(FrameSpecError, "Empty artwork"):
            render(self.spec, self.root / "frames")
        self.data["layers"][1]["drawings"][0]["image"] = "not_found.png"
        self.write()
        with self.assertRaises(FrameSpecError):
            render(self.spec, self.root / "frames")

    def test_invalid_exposure_and_invalid_depth_are_blocked(self):
        self.data["layers"][1]["drawings"] = [{"frame": 2, "image": "red.png"}]
        self.write()
        with self.assertRaises(FrameSpecError):
            validate_spec(self.data, self.root)
        self.data["layers"][1]["drawings"] = [{"frame": 1, "image": "red.png"}]
        self.data["layers"][1]["parallax"] = 1.5
        with self.assertRaises(FrameSpecError):
            validate_spec(self.data, self.root)
        self.data["layers"][1]["parallax"] = 1
        self.data["layers"][1]["motion"] = [{"frame": 1, "scale": 0}]
        with self.assertRaises(FrameSpecError):
            validate_spec(self.data, self.root)


if __name__ == "__main__":
    unittest.main()
