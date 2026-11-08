"""Offline regression tests: no audiobook narration/render before ALL story art is approved."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
MODAL = ROOT / "video/audiobook_studio/manhua_pipeline/modal_production.py"
POLICY = ROOT / "video/audiobook_studio/FULL_STORY_ILLUSTRATIONS_FIRST.md"
WORKFLOW = ROOT / ".github/workflows/manhua-audiobook-private.yml"


class FullStoryIllustrationGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "art"
        self.story_id = "example-story"
        self.meta = {
            "schema": "audiobook-manhua-v1",
            "story_id": self.story_id,
            "full_source_sha256": "f" * 64,
            "style": "cultivation",
            "characters": [],
            "episodes": [
                {"number": 1, "sha256": "a" * 64},
                {"number": 2, "sha256": "b" * 64},
            ],
        }
        self.manifest_path = self.root / self.story_id / "FULL_STORY_ILLUSTRATIONS_APPROVED.json"
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest = {
            "schema": "full-story-illustrations-v1",
            "story_id": self.story_id,
            "full_source_sha256": self.meta["full_source_sha256"],
            "human_visual_review_approved": True,
            "episodes": {},
        }
        for entry in self.meta["episodes"]:
            ep = entry["number"]
            image_dir = self.root / self.story_id / f"ep{ep:03}-{entry['sha256'][:16]}" / "illustrations"
            image_dir.mkdir(parents=True, exist_ok=True)
            data = f"scene image for episode {ep}".encode()
            (image_dir / "scene-0000.png").write_bytes(data)
            self.manifest["episodes"][str(ep)] = {
                "source_sha256": entry["sha256"],
                "scenes": {
                    "0": {
                        "source_sha256": f"scene-sha-{ep}",
                        "file": "illustrations/scene-0000.png",
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                }
            }
        self.write_manifest()
        # Extract pure gate from real Modal source; no Modal install, secrets, network, or GPU.
        tree = ast.parse(MODAL.read_text(encoding="utf-8"))
        f = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == "require_complete_story_illustrations")
        generator = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                         and node.name == "ensure_full_story_illustration_manifest")
        scope = {
            "Path": Path, "json": json, "hashlib": hashlib,
            "validate_slug": lambda story_id: story_id,
            "open_package": lambda archive, expected_story_id, episode:
                (self.meta, f"episode:{episode}", {}),
            "split_chunks": lambda script: script,
            "dense_illustration_plan": lambda parts, **kwargs: [{
                "scene": 0, "source_sha256": f"scene-sha-{parts.split(':')[-1]}",
                "key": f"generatedkey-{parts.split(':')[-1]}"
            }],
            "directory": lambda root, meta, ep: Path(root) / meta["story_id"]
                / f"ep{ep:03}-{meta['episodes'][ep-1]['sha256'][:16]}",
        }
        exec(compile(ast.Module(body=[generator, f], type_ignores=[]), str(MODAL), "exec"), scope)
        self.gate = scope["require_complete_story_illustrations"]
        self.make_manifest = scope["ensure_full_story_illustration_manifest"]

    def write_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def run_gate(self):
        return self.gate(self.meta, self.story_id, Path(self.temp.name) / "source.zip", self.root)

    def test_complete_two_episode_illustration_library_passes(self):
        result = self.run_gate()
        self.assertEqual(result["status"], "FULL_STORY_ILLUSTRATIONS_VERIFIED")
        self.assertEqual(result["episodes"], 2)
        self.assertEqual(result["scenes"], 2)

    def test_auto_approval_creates_manifest_without_user_review(self):
        self.manifest_path.unlink()
        for ep in (1, 2):
            directory = self.root / self.story_id / (
                f"ep{ep:03}-" + ("a" if ep == 1 else "b") * 16
            ) / "illustrations"
            (directory / "scene-0000.png").rename(
                directory / f"scene-0000-generatedkey-{ep}.png")
        created = self.make_manifest(self.meta, self.story_id,
                                     Path(self.temp.name) / "source.zip", self.root)
        data = json.loads(created.read_text())
        self.assertEqual(data["owner_artwork_approval"], "blanket_preapproved")
        self.assertNotIn("human_visual_review_approved", data)
        result = self.run_gate()
        self.assertEqual(result["scenes"], 2)

    def test_explicit_blanket_approval_passes_even_without_manual_review(self):
        self.manifest["human_visual_review_approved"] = False
        self.manifest["owner_artwork_approval"] = "blanket_preapproved"
        self.write_manifest()
        self.assertEqual(self.run_gate()["status"], "FULL_STORY_ILLUSTRATIONS_VERIFIED")

    def test_missing_manifest_blocks(self):
        self.manifest_path.unlink()
        with self.assertRaisesRegex(RuntimeError, "MISSING"):
            self.run_gate()

    def test_missing_other_episode_blocks_even_when_first_episode_complete(self):
        del self.manifest["episodes"]["2"]
        self.write_manifest()
        with self.assertRaisesRegex(RuntimeError, "INCOMPLETE_EPISODES"):
            self.run_gate()

    def test_unreviewed_library_blocks(self):
        self.manifest["human_visual_review_approved"] = False
        self.write_manifest()
        with self.assertRaisesRegex(RuntimeError, "UNAPPROVED"):
            self.run_gate()

    def test_source_version_change_blocks(self):
        self.manifest["full_source_sha256"] = "c" * 64
        self.write_manifest()
        with self.assertRaisesRegex(RuntimeError, "UNAPPROVED_OR_STALE"):
            self.run_gate()

    def test_missing_scene_image_blocks(self):
        self.root.joinpath(self.story_id, "ep002-" + "b"*16,
                           "illustrations", "scene-0000.png").unlink()
        with self.assertRaisesRegex(RuntimeError, "FILE_MISSING"):
            self.run_gate()

    def test_changed_image_bytes_block(self):
        self.root.joinpath(self.story_id, "ep002-" + "b"*16,
                           "illustrations", "scene-0000.png").write_bytes(b"altered")
        with self.assertRaisesRegex(RuntimeError, "IMAGE_HASH_MISMATCH"):
            self.run_gate()

    def test_unsafe_path_blocks(self):
        self.manifest["episodes"]["1"]["scenes"]["0"]["file"] = "../other.png"
        self.write_manifest()
        with self.assertRaisesRegex(RuntimeError, "UNSAFE"):
            self.run_gate()

    def test_all_media_entry_points_apply_gate(self):
        src = MODAL.read_text()
        for name in ("def generate_ryan(", "def assemble_private_review("):
            section = src[src.index(name):]
            section = section[:section.index("\n@app.") if "\n@app." in section else len(section)]
            self.assertIn("require_complete_story_illustrations(", section)
        main = src[src.index("def main("):]
        self.assertLess(main.index("verify_full_story_illustrations.remote"),
                        main.index("generate_ryan.with_options"))
        self.assertLess(main.index("generate_ryan.with_options"),
                        main.index("assemble_private_review.remote"))
        self.assertNotIn("modal.FunctionCall.gather(tts, art)", main)
        self.assertTrue(POLICY.is_file())
        self.assertIn("FULL_STORY_ILLUSTRATIONS_FIRST.md",
                      (ROOT / "video/audiobook_studio/AGENTS.md").read_text())
        self.assertIn("illustrations", WORKFLOW.read_text())


if __name__ == "__main__":
    unittest.main()
