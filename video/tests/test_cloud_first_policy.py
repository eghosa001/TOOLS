"""Pure offline regression tests: cloud-first all-video plan guard."""
import copy
import unittest
from video.cloud_first_policy import (
    PIPELINES, CHANNEL_GATES, CLOUD_RUNNERS, OPENMONTAGE_REPO, validate_cloud_plan,
)


def sample(kind="audiobook", pipeline=None):
    return {
        "schema": 1, "video_type": kind,
        "openmontage": {
            "repository": OPENMONTAGE_REPO,
            "orchestrator": "OpenMontage",
            "pipeline": pipeline or next(iter(sorted(PIPELINES[kind]))),
            "agent_guide_read": False, "pipeline_manifest_read": False,
            "stage_directors_read": False, "tool_registry_discovered": False,
            "agent_pipeline_preflight_reference": "",
        },
        "execution": {
            "mode": "cloud", "runner": "github_actions",
            "local_production_fallback": False,
            "runner_verified": False, "runner_verification_reference": "",
        },
        "storage": {
            "source": "private_google_drive", "destination": "private_google_drive",
            "transfer_verified": False, "transfer_verification_reference": "",
        },
        "budget": {
            "estimated_usd": 0, "approved_ceiling_usd": 0,
            "owner_authorized_paid_usage": False,
        },
        "channel_gate": CHANNEL_GATES[kind],
        "mandatory_checks": {
            "copyright_and_commercial_use": True,
            "scene_to_source_alignment": True,
            "private_human_final_review": True,
            "owner_approval_before_publication": True,
        },
        "publish_automatically": False,
    }


class CloudFirstPolicyTests(unittest.TestCase):
    def test_all_studios_can_plan_on_cloud(self):
        for studio in PIPELINES:
            with self.subTest(studio=studio):
                result = validate_cloud_plan(sample(studio))
                self.assertEqual(result["status"], "CLOUD_OPENMONTAGE_PLAN_PASS")
                self.assertFalse(result["published"])

    def test_laptop_or_fallback_rejected(self):
        plan = sample()
        plan["execution"]["mode"] = "local"
        with self.assertRaisesRegex(ValueError, "cloud runner required"):
            validate_cloud_plan(plan)
        plan["execution"]["mode"] = "cloud"
        plan["execution"]["local_production_fallback"] = True
        with self.assertRaisesRegex(ValueError, "laptop fallback"):
            validate_cloud_plan(plan)

    def test_paid_providers_blocked_without_approval(self):
        plan = sample()
        plan["budget"]["estimated_usd"] = 1.0
        plan["budget"]["approved_ceiling_usd"] = 2
        with self.assertRaisesRegex(ValueError, "owner authorization"):
            validate_cloud_plan(plan)
        plan["budget"]["owner_authorized_paid_usage"] = True
        self.assertEqual(validate_cloud_plan(plan)["approved_ceiling_usd"], 2)
        plan["budget"]["estimated_usd"] = 3
        with self.assertRaisesRegex(ValueError, "exceeds approved"):
            validate_cloud_plan(plan)

    def test_wrong_pipeline_and_studio_bypasses_rejected(self):
        plan = sample("history", "documentary-montage")
        plan["openmontage"]["pipeline"] = "cinematic"
        with self.assertRaisesRegex(ValueError, "wrong OpenMontage pipeline"):
            validate_cloud_plan(plan)
        plan = sample("history", "documentary-montage")
        plan["channel_gate"] = "made_up"
        with self.assertRaisesRegex(ValueError, "quality requirements"):
            validate_cloud_plan(plan)
        plan["channel_gate"] = CHANNEL_GATES["history"]
        plan["publish_automatically"] = True
        with self.assertRaisesRegex(ValueError, "publication forbidden"):
            validate_cloud_plan(plan)

    def test_execution_requires_evidence_not_just_plan(self):
        plan = sample("audiobook", "animation")
        with self.assertRaisesRegex(ValueError, "runner_verification_reference"):
            validate_cloud_plan(plan, phase="execute")
        plan["execution"].update(runner_verified=True,
                                 runner_verification_reference="signed_runner_check_001")
        plan["storage"].update(transfer_verified=True,
                               transfer_verification_reference="private_drive_check_001")
        with self.assertRaisesRegex(ValueError, "agent_pipeline_preflight_reference"):
            validate_cloud_plan(plan, phase="execute")
        plan["openmontage"].update(agent_pipeline_preflight_reference="pipeline_preflight_001")
        with self.assertRaisesRegex(ValueError, "OpenMontage contract"):
            validate_cloud_plan(plan, phase="execute")
        plan["openmontage"].update(
            agent_guide_read=True, pipeline_manifest_read=True,
            stage_directors_read=True, tool_registry_discovered=True,
        )
        self.assertEqual(validate_cloud_plan(plan, phase="execute")["phase"], "execute")


if __name__ == "__main__":
    unittest.main()
