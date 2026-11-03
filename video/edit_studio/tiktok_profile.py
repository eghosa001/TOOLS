#!/usr/bin/env python3
"""TikTok review profile for the Universal Edit Studio.

This is not an eligibility, monetization, copyright or Content ID approval.
Distinguishes TikTok publishing checks from Creator Rewards eligibility.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import sys
from pathlib import Path

GATE_FILE = Path(__file__).with_name("release_gate.py")
spec = importlib.util.spec_from_file_location("universal_edit_gate", GATE_FILE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class TikTokProfileError(ValueError):
    pass


def evaluate(m, *, objective, duration_sec, account=None, phase="plan", assets_root="."):
    if objective not in ("publish", "creator_rewards"):
        raise TikTokProfileError("objective must be publish or creator_rewards")
    if isinstance(duration_sec, bool) or not isinstance(duration_sec, (int, float)) or duration_sec <= 0:
        raise TikTokProfileError("Valid actual/planned duration in seconds is required")
    if phase == "release":
        baseline = gate.validate_release(m, assets_root)
    elif phase == "plan":
        baseline = gate.validate_plan(m)
    else:
        raise TikTokProfileError("phase must be plan or release")
    if objective == "publish":
        issues = list(baseline.get("risk_flags", []))
        if issues:
            status = "REVIEW_REQUIRED_NO_AUTOMATIC_PUBLICATION"
        else:
            status = "PLAN_CHECKS_ONLY" if phase == "plan" else "INTERNAL_RELEASE_GATE_PASSED"
        return {
            "platform": "tiktok", "objective": objective, "status": status,
            "duration_sec": duration_sec,
            "rights_or_exception_risk": issues,
            "rights_review_status": "not_yet_human_approved" if phase == "plan" else "signed_review_present",
            "tiktok_account_and_video_eligible": None, "monetization_guaranteed": False,
            "notes": [
                "Use exact rights evidence for movie/anime/sport clips and music; TikTok posts can still be removed or muted.",
                "Audio selected within TikTok's app is not automatically cross-platform licensed.",
                "Check the platform's content policies and actual account before posting."
            ]
        }
    account = account or {}
    failures = []
    risks = list(baseline.get("risk_flags", []))
    if duration_sec < 60:
        failures.append("Video is under TikTok Creator Rewards 60-second minimum.")
    if account.get("creator_rewards_available_in_tiktok_studio") is not True:
        failures.append("TikTok Studio does not confirm Creator Rewards access for this actual account.")
    if account.get("personal_account") is not True:
        failures.append("Creator Rewards requires an eligible Personal account.")
    if account.get("account_in_good_standing") is not True:
        failures.append("Account good standing is not established.")
    if account.get("age_at_least_18") is not True:
        failures.append("Age eligibility is not established.")
    if account.get("followers", 0) < 10000:
        failures.append("Creator Rewards account needs at least 10,000 followers.")
    if account.get("views_last_30_days", 0) < 100000:
        failures.append("Creator Rewards account needs at least 100,000 views over the last 30 days.")
    if account.get("sponsored_or_paid_promotion") is True:
        failures.append("Paid promotional/sponsored posts are not eligible for Creator Rewards.")
    if account.get("is_duet_or_stitch") is True:
        failures.append("Duets and Stitches are not eligible for Creator Rewards.")
    if account.get("country") in ("NG", "Nigeria"):
        failures.append("Nigeria is not on TikTok's published Creator Rewards country list as of 2026-11-03.")
    if not account.get("country"):
        failures.append("Account country not verified.")
    if m.get("originality", {}).get("editorial_significance_human_review_required") is not True:
        failures.append("Originality must be editorially verified.")
    external_categories = {"anime","movie","tv","football","sports","celebrity","music","history"}
    if m.get("category") in external_categories:
        risks.append("Existing third-party character/broadcast/film clips may be rejected as unoriginal even when licensed.")
    if m.get("media_sources"):
        if any(src.get("rights_status") != "owned" for src in m["media_sources"]):
            risks.append("Creator Rewards originality not established for reused or licensed third-party footage.")
    if objective == "creator_rewards" and phase == "release" and (risks or failures):
        status = "NOT_ELIGIBLE_OR_UNVERIFIED"
    elif failures:
        status = "NOT_ELIGIBLE_OR_UNVERIFIED"
    elif risks:
        status = "ORIGINALITY_REVIEW_RISK"
    else:
        status = "POTENTIAL_ACCOUNT_VIDEO_MATCH_TIKTOK_DECIDES"
    return {
        "platform": "tiktok", "objective": objective, "status": status,
        "duration_sec": duration_sec, "eligibility_blocks": failures,
        "additional_originality_risk": sorted(set(risks)),
        "monetization_guaranteed": False,
        "notes": [
            "Creator Rewards requires qualified views and content meeting TikTok's originality standards.",
            "Platform review and actual TikTok Studio access control eligibility; no guarantee from this report.",
            "Country availability is time-sensitive; the TikTok Studio entitlement is required even if a public country list changes."
        ]
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--objective", choices=["publish", "creator_rewards"], required=True)
    p.add_argument("--phase", choices=["plan", "release"], default="plan")
    p.add_argument("--duration-sec", required=True, type=float)
    p.add_argument("--account-json", type=Path)
    p.add_argument("--assets-root", default=".")
    p.add_argument("--json-out", type=Path)
    a = p.parse_args(argv)
    try:
        m = json.loads(a.manifest.read_text())
        account = json.loads(a.account_json.read_text()) if a.account_json else None
        out = evaluate(m, objective=a.objective, duration_sec=a.duration_sec,
                       account=account, phase=a.phase, assets_root=a.assets_root)
        print(json.dumps(out, indent=2))
        if a.json_out:
            a.json_out.parent.mkdir(parents=True, exist_ok=True)
            a.json_out.write_text(json.dumps(out, indent=2))
        if a.objective == "creator_rewards" and out["status"] != "POTENTIAL_ACCOUNT_VIDEO_MATCH_TIKTOK_DECIDES":
            return 2
        if a.objective == "publish" and out["status"] == "REVIEW_REQUIRED_NO_AUTOMATIC_PUBLICATION":
            return 2
        return 0
    except (TikTokProfileError, gate.GateError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"TIKTOK_PROFILE_BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
