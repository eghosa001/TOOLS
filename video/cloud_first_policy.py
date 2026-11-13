#!/usr/bin/env python3
"""Cloud-first OpenMontage production-plan guard for NEW videos.

This verifies a private work order, not whether a remote runner actually exists
or whether a human really inspected media. Source media stays outside GitHub.
No generation, billing, upload or publishing occurs in this module.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PIPELINES = {
    "audiobook": frozenset({"animation"}),
    "history": frozenset({"documentary-montage", "hybrid"}),
    "asmr": frozenset({"cinematic", "hybrid", "animation"}),
    "universal_edit": frozenset({"hybrid", "clip-factory"}),
    "animation": frozenset({"animation", "character-animation"}),
    "shorts": frozenset({"clip-factory", "animation", "documentary-montage", "hybrid"}),
    "other": frozenset({"animation", "documentary-montage", "cinematic", "hybrid",
                        "clip-factory", "character-animation", "talking-head", "screen-demo",
                        "podcast-repurpose", "animated-explainer"}),
}
CLOUD_RUNNERS = frozenset({"github_actions", "cloud_vm", "cloud_container",
                           "connected_cloud_runner"})
OPENMONTAGE_REPO = "https://github.com/OpenMontageInc/OpenMontage"
CHANNEL_GATES = {
    "audiobook": "music_first_kokoro_michael_full_color_source_locked_ffmpeg_8plus",
    "history": "real_footage_source_first_no_generated_visuals",
    "asmr": "synchronized_visual_action_and_original_audio",
    "universal_edit": "verified_source_rights_no_generated_replacements",
    "animation": "approved_story_rigs_and_character_continuity",
    "shorts": "channel_specific_source_and_audio_safety",
    "other": "channel_specific_source_and_audio_safety",
}
REVIEW = ("copyright_and_commercial_use", "scene_to_source_alignment",
          "private_human_final_review", "owner_approval_before_publication")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("CLOUD_OPENMONTAGE_BLOCKED: " + message)


def validate_cloud_plan(plan: dict, *, phase: str = "plan") -> dict:
    _require(phase in ("plan", "execute"), "unsupported phase")
    _require(isinstance(plan, dict), "cloud plan must be a JSON object")
    _require(plan.get("schema") == 1 and type(plan.get("schema")) is int,
             "schema must be 1")
    category = plan.get("video_type")
    _require(category in PIPELINES, "unknown video category")
    montage = plan.get("openmontage")
    _require(isinstance(montage, dict)
             and montage.get("repository") == OPENMONTAGE_REPO
             and montage.get("orchestrator") == "OpenMontage",
             "OpenMontage must be the named orchestration system")
    pipeline = montage.get("pipeline")
    _require(pipeline in PIPELINES[category],
             "wrong OpenMontage pipeline for " + str(category))
    execution = plan.get("execution")
    _require(isinstance(execution, dict)
             and execution.get("mode") == "cloud"
             and execution.get("runner") in CLOUD_RUNNERS,
             "remote cloud runner required: no local-only production")
    _require(execution.get("local_production_fallback") is False,
             "no silent laptop fallback")
    storage = plan.get("storage")
    _require(isinstance(storage, dict)
             and storage.get("source") == "private_google_drive"
             and storage.get("destination") == "private_google_drive",
             "private Google Drive source and output required")
    budget = plan.get("budget")
    _require(isinstance(budget, dict), "explicit per-video cost plan required")
    estimated = budget.get("estimated_usd")
    ceiling = budget.get("approved_ceiling_usd")
    _require(type(estimated) in (int, float) and type(ceiling) in (int, float)
             and 0 <= estimated <= ceiling and ceiling <= 100000,
             "estimated cost exceeds approved maximum or budget is invalid")
    if ceiling > 0:
        _require(budget.get("owner_authorized_paid_usage") is True,
                 "paid cloud provider / runner usage needs owner authorization")
    else:
        _require(budget.get("owner_authorized_paid_usage") is False,
                 "free-first plan must explicitly prohibit paid calls")
    _require(plan.get("channel_gate") == CHANNEL_GATES[category],
             "channel-specific existing quality requirements must remain")
    review = plan.get("mandatory_checks")
    _require(isinstance(review, dict)
             and all(review.get(k) is True for k in REVIEW),
             "rights, source alignment, full human review and owner release gates required")
    _require(plan.get("publish_automatically") is False,
             "public publication forbidden from production workflow")
    if phase == "execute":
        for section, evidence in ((execution, "runner_verification_reference"),
                                  (storage, "transfer_verification_reference"),
                                  (montage, "agent_pipeline_preflight_reference")):
            _require(isinstance(section.get(evidence), str)
                     and len(section[evidence].strip()) >= 12,
                     "missing verified " + evidence)
        _require(execution.get("runner_verified") is True,
                 "cloud runner unavailable or not verified")
        _require(storage.get("transfer_verified") is True,
                 "private Drive read/write unverified")
        _require(montage.get("agent_guide_read") is True
                 and montage.get("pipeline_manifest_read") is True
                 and montage.get("stage_directors_read") is True
                 and montage.get("tool_registry_discovered") is True,
                 "OpenMontage contract/preflight not completed")
    return {
        "status": "CLOUD_OPENMONTAGE_PLAN_PASS" if phase == "plan" else
                  "CLOUD_OPENMONTAGE_EXECUTION_PREFLIGHT_PASS",
        "phase": phase, "video_type": category, "pipeline": pipeline,
        "runner": execution["runner"], "approved_ceiling_usd": ceiling,
        "actual_video_generated": False, "actual_cloud_runner_invoked": False,
        "published": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", type=Path, required=True,
                    help="Path to PRIVATE per-video cloud work order (outside public repo)")
    ap.add_argument("--phase", choices=("plan", "execute"), default="plan")
    args = ap.parse_args()
    try:
        filename = args.plan.expanduser().resolve(strict=True)
        data = json.loads(filename.read_text(encoding="utf-8"))
        print(json.dumps(validate_cloud_plan(data, phase=args.phase), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("CLOUD_OPENMONTAGE_PREFLIGHT_FAILED:", str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
