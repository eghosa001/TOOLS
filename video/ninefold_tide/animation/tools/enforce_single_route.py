#!/usr/bin/env python3
"""Static guard: only frame-first Ninefold production checks and audio support remain active."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ACTIVE_WORKFLOWS = set([
  "ninefold-art-ora-gate.yml",
  "ninefold-art-preflight.yml",
  "ninefold-director-qa.yml",
  "ninefold-kaggle-inventory.yml",
  "ninefold-kaggle-voice-launch.yml",
  "ninefold-kaggle-voice-readback.yml",
  "ninefold-mari-chatterbox-status.yml",
  "ninefold-mari-chatterbox.yml",
  "ninefold-pilot-lipsync-cues.yml",
  "ninefold-pipeline.yml",
  "ninefold-supporting-cast-safe-launch.yml",
  "ninefold-supporting-cast-status.yml",
  "ninefold-supporting-cast-voices.yml",
  "ninefold-supporting-voice-ranking.yml",
  "ninefold-voice-evaluate.yml",
  "ninefold-young-voice-retakes.yml"
])
ARCHIVED_WORKFLOWS = set([
  "ninefold-blender-cpu-probe.yml",
  "ninefold-blender45-real-smoke.yml",
  "ninefold-cache-blender45.yml",
  "ninefold-kaggle-e101-v11-upload.yml",
  "ninefold-private-v09r1-art-bridge.yml",
  "ninefold-v07-dataset-debug.yml",
  "ninefold-v07-dataset-readback.yml",
  "ninefold-v07-drive-access-preflight.yml",
  "ninefold-v07-encrypted-handoff.yml",
  "ninefold-v07-kaggle-source-discovery.yml",
  "ninefold-v07-private-dataset-bootstrap.yml",
  "ninefold-v07-private-kaggle-build.yml",
  "ninefold-v07-private-status.yml",
  "ninefold-v07-source-inventory.yml"
])
LEGACY_LAUNCHERS = ([
  "launch_kaggle_e101_v11.py",
  "launch_kaggle_blender_probe.py",
  "launch_blender_45_cache.py",
  "private_v09r1_dataset_bridge.py",
  "private_v07_kaggle_job.py"
])


def audit(root: Path) -> list[str]:
    root = root.resolve()
    issues = []
    actual = {p.name for p in (root / ".github/workflows").glob("ninefold*.yml")}
    for name in sorted(actual - ACTIVE_WORKFLOWS):
        issues.append("Unapproved active Ninefold workflow: " + name)
    for name in sorted(ACTIVE_WORKFLOWS - actual):
        issues.append("Expected supporting production/audio workflow missing: " + name)
    for name in sorted(ARCHIVED_WORKFLOWS):
        if name in actual:
            issues.append("Legacy workflow reactivated: " + name)
        if not (root / "video/ninefold_tide/animation/archive/legacy_workflows" / name).is_file():
            issues.append("Archived workflow missing: " + name)
    pipeline = root / "video/ninefold_tide/pipeline.py"
    source = pipeline.read_text(encoding="utf8") if pipeline.is_file() else ""
    for marker in ("frame_package_manifest", "camera_id", 'shot_gate.validate(package, frame_pkg.parent, "export")'):
        if marker not in source:
            issues.append("Legacy MP4-only assembly barrier missing: " + marker)
    if not (root / "video/ninefold_tide/animation/tools/shot_gate.py").is_file():
        issues.append("Canonical frame review gate missing")
    for name in LEGACY_LAUNCHERS:
        script = root / "video/ninefold_tide/ops" / name
        if not script.is_file() or 'NINEFOLD_ENABLE_ARCHIVED_EXPERIMENTS' not in script.read_text(encoding="utf8"):
            issues.append("Unprotected archived experiment launcher: " + name)
    return issues


if __name__ == "__main__":
    problems = audit(ROOT)
    print(json.dumps({"status": "BLOCKED" if problems else "PASS",
                      "active_workflows": len(ACTIVE_WORKFLOWS),
                      "archived_workflows": len(ARCHIVED_WORKFLOWS),
                      "issues": problems}, indent=2))
    raise SystemExit(1 if problems else 0)
