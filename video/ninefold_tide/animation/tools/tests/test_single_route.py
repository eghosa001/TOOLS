"""Regression: archived Ninefold animation executors cannot return to active workflows."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import enforce_single_route


class SingleRouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        active = self.root / ".github/workflows"
        active.mkdir(parents=True)
        for name in enforce_single_route.ACTIVE_WORKFLOWS:
            (active / name).write_text("name: test\n", encoding="utf8")
        archive = self.root / "video/ninefold_tide/animation/archive/legacy_workflows"
        archive.mkdir(parents=True)
        for name in enforce_single_route.ARCHIVED_WORKFLOWS:
            (archive / name).write_text("name: archived\n", encoding="utf8")
        tools = self.root / "video/ninefold_tide/animation/tools"
        tools.mkdir(parents=True)
        (tools / "shot_gate.py").write_text("pass\n", encoding="utf8")
        pipeline = self.root / "video/ninefold_tide/pipeline.py"
        pipeline.write_text('frame_package_manifest camera_id shot_gate.validate(package, frame_pkg.parent, "export")')
        ops = self.root / "video/ninefold_tide/ops"
        ops.mkdir(parents=True)
        for name in enforce_single_route.LEGACY_LAUNCHERS:
            (ops / name).write_text("NINEFOLD_ENABLE_ARCHIVED_EXPERIMENTS\n")

    def test_compliant_active_layout(self):
        self.assertEqual([], enforce_single_route.audit(self.root))

    def test_legacy_executor_returning_to_workflows_is_blocked(self):
        n = next(iter(enforce_single_route.ARCHIVED_WORKFLOWS))
        (self.root / ".github/workflows" / n).write_text("on: workflow_dispatch\n")
        self.assertTrue(any("Unapproved active" in x for x in enforce_single_route.audit(self.root)))

    def test_unknown_animation_action_is_blocked(self):
        (self.root / ".github/workflows/ninefold-direct-video.yml").write_text("on: workflow_dispatch\n")
        self.assertTrue(enforce_single_route.audit(self.root))

    def test_lost_archive_is_blocked(self):
        n = next(iter(enforce_single_route.ARCHIVED_WORKFLOWS))
        (self.root / "video/ninefold_tide/animation/archive/legacy_workflows" / n).unlink()
        self.assertTrue(any("Archived workflow missing" in x for x in enforce_single_route.audit(self.root)))

    def test_mp4_only_pipeline_rollback_is_blocked(self):
        (self.root / "video/ninefold_tide/pipeline.py").write_text("old MP4-only path")
        self.assertTrue(any("barrier missing" in x for x in enforce_single_route.audit(self.root)))

    def test_launch_without_explicit_archive_opt_in_is_blocked(self):
        n = enforce_single_route.LEGACY_LAUNCHERS[0]
        (self.root / "video/ninefold_tide/ops" / n).write_text("unguarded")
        self.assertTrue(any("Unprotected" in x for x in enforce_single_route.audit(self.root)))


if __name__ == "__main__":
    unittest.main()
