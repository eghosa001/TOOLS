#!/usr/bin/env python3
"""Story-FIRST gate for every NEW Facts Uncovered 3D historical Short.

Checks evidence structure, authored stakes and exact shot continuity. A machine
cannot decide whether a story is captivating: actual human editorial ratings
still determine the render greenlight. Structural PASS is NOT art approval.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

REQUIRED_ARC = {
    "hook", "central_question", "focal_subject", "goal",
    "obstacle", "escalation", "reversal", "payoff",
    "opening_action", "reveal_seconds",
    "ending_subscription_duration_seconds",
}
STORY_RATINGS = ("story_retention_score", "narrative_coherence_score",
                 "emotional_stakes_score", "payoff_score")
PREVIOUS_LEGACY = frozenset({
    "great-fire-london-64s.json",
    "constantinople-64s.json",
})


def require(valid: bool, why: str):
    if not valid:
        raise ValueError("STORY_FIRST_BLOCKED: " + why)


def substantial(value, min_length=38):
    return isinstance(value, str) and len(value.strip()) >= min_length


def check_story(source: dict, *, require_editor_approval=False,
                filename: str = "") -> dict:
    """Return STRUCTURAL checks; never issue artistic approval automatically."""
    arc = source.get("story_arc")
    if arc is None:
        require(filename in PREVIOUS_LEGACY and not require_editor_approval,
                "Every NEW 3D Short needs a researched, human-authored story_arc.")
        return {"status": "LEGACY_STORY_NOT_APPROVED_FOR_RENDER",
                "story_pass": False, "editorial_approved": False,
                "reason": "Old recaps lack the new hook/stakes/reversal/payoff brief"}
    require(isinstance(arc, dict), "story_arc must be a dictionary")
    missing = REQUIRED_ARC.difference(arc)
    require(not missing, "Missing story beats: " + ", ".join(sorted(missing)))
    for key in ("hook", "central_question", "focal_subject",
                "goal", "obstacle", "escalation", "reversal", "payoff",
                "opening_action"):
        require(substantial(arc[key], 23), key + " must be a specific historical fact/action")
    seconds = source.get("seconds")
    require(seconds == 64, "Storyboard must keep the 64-second narration budget")
    reveal = arc.get("reveal_seconds")
    require(isinstance(reveal, int) and 25 <= reveal <= 54,
            "Central story reversal must occur between 25s and 54s")
    ending = arc.get("ending_subscription_duration_seconds")
    require(isinstance(ending, int) and 1 <= ending <= 3,
            "Short ends with a brief, manually directed channel CTA")
    shots = source.get("shots")
    require(isinstance(shots, list) and len(shots) == 12,
            "Story needs twelve independently authored camera/action beats")
    require(shots[0].get("start_seconds") == 0,
            "The hook and visible physical action must begin at frame 1")
    require(substantial(shots[0].get("required_visible_action"), 68),
            "The first shot must depict a physical hook, not a title card")
    require(shots[-1].get("end_seconds") == 64,
            "Payoff and closing cannot be truncated")
    spoken = " ".join(s.get("spoken", "") for s in shots)
    require("subscribe to facts uncovered" in spoken.lower(),
            "Finish the story with a brief spoken Facts Uncovered subscription invitation")
    require("subscribe to facts uncovered" in shots[-1].get("spoken", "").lower(),
            "Closing CTA must be in the manually authored FINAL shot")
    require(len(source.get("history_sources", [])) >= 2,
            "Historical claims need at least two traceable research sources")
    require(not source.get("publication_approved", False),
            "A storyboard must not claim YouTube publication approval")
    review = source.get("story_editorial_approval")
    require(isinstance(review, dict), "Missing independent story-editor review block")
    review_approved = review.get("human_story_approved") is True
    if require_editor_approval:
        require(review_approved, "Story not personally reviewed and approved")
        require(source.get("render_authorized") is True,
                "No render authorization until separate quality and licensing gates pass")
        require(substantial(review.get("editor_name"), 4),
                "Identify the real story editor")
        require(substantial(review.get("review_notes"), 70),
                "Provide real evidence of engagement, tension and payoff")
        for dimension in STORY_RATINGS:
            score = review.get(dimension)
            require(type(score) in (float, int) and 8.5 <= score <= 10.0,
                    dimension + ": reviewer score must independently meet 8.5/10")
    return {
        "status": ("STRUCTURAL_STORY_READY_NOT_ART_APPROVED"
                   if not require_editor_approval else "HUMAN_STORY_REVIEW_PASS"),
        "story_pass": True,
        "editorial_approved": review_approved,
        "render_authorized": bool(source.get("render_authorized", False)),
        "opening_hook": shots[0]["spoken"],
        "reveal_seconds": reveal,
        "independent_story_editorial_review_still_required": not review_approved,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("storyboards", nargs="+", type=Path)
    p.add_argument("--require-editor-approval", action="store_true",
                   help="Mandatory before costly full-length 3D rendering")
    args = p.parse_args()
    for path in args.storyboards:
        report = check_story(json.loads(path.read_text(encoding="utf8")),
                             require_editor_approval=args.require_editor_approval,
                             filename=path.name)
        print(json.dumps({"path": str(path), **report}))


if __name__ == "__main__":
    main()
