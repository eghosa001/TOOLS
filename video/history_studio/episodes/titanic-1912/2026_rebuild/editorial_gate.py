#!/usr/bin/env python3
"""Non-assembly editorial gate for Titanic. Never chooses or substitutes visuals.

Planning check is safe and read-only. Release check always refuses incomplete
recorded timelines, rights, audio, and full audiovisual sign-off.
"""
from __future__ import annotations
import argparse, json, math, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
EPISODE = HERE.parent
MANIFEST = HERE / "MANUAL_SCENE_LEDGER_DRAFT.json"
SCRIPT_FILES = [EPISODE / "v2" / f"script_{part}.json"
                for part in ("01_05", "06_10", "11_15")]
REQUIRED = ("scene_id", "chapter", "paragraph", "visual_order",
            "narration_paragraph", "asset_type", "asset_id", "source_refs",
            "in_time", "out_time", "asset_verified", "editor_approved",
            "final_render_reviewed", "licence_status")


def inspect(release=False):
    scripts = [chapter for file in SCRIPT_FILES
               for chapter in json.loads(file.read_text(encoding="utf-8"))]
    ledger = json.loads(MANIFEST.read_text(encoding="utf-8"))
    scenes = ledger.get("scenes", [])
    problems = []
    paragraphs = 0
    ids = set()
    for ch, chapter in enumerate(scripts, 1):
        parts = chapter["narration"].split("\n\n")
        for paragraph, transcript in enumerate(parts, 1):
            paragraphs += 1
            matches = [s for s in scenes
                       if s.get("chapter") == ch and s.get("paragraph") == paragraph]
            if len(matches) != 2:
                problems.append(f"chapter {ch} paragraph {paragraph}: expected exactly 2 deliberate visual decisions, got {len(matches)}")
            for s in matches:
                missing = set(REQUIRED) - s.keys()
                if missing:
                    problems.append(f"{s.get('scene_id','?')}: missing {sorted(missing)}")
                if s.get("narration_paragraph") != transcript:
                    problems.append(f"{s.get('scene_id','?')}: passage does not match approved source script")
                if not s.get("asset_id") or not s.get("source_refs"):
                    problems.append(f"{s.get('scene_id','?')}: missing actual chosen asset or source refs")
                ident = s.get("scene_id")
                if ident in ids:
                    problems.append(f"{ident}: duplicate scene ID")
                ids.add(ident)
    if len(scenes) != 2 * paragraphs:
        problems.append(f"scene count {len(scenes)} != expected {2*paragraphs}")
    if len(scripts) != 15:
        problems.append(f"chapter count {len(scripts)} != 15")
    if release:
        for s in scenes:
            ident = s.get("scene_id", "?")
            if not all(s.get(k) is True for k in
                       ("asset_verified", "editor_approved", "audio_reviewed", "final_render_reviewed")):
                problems.append(f"{ident}: source/rights/audio/picture editorial sign-off missing")
            if s.get("licence_status") != "COMMERCIAL_REUSE_VERIFIED":
                problems.append(f"{ident}: commercial asset rights unverified")
            a, b = s.get("in_time"), s.get("out_time")
            if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or not (math.isfinite(a) and math.isfinite(b) and 0 <= a < b):
                problems.append(f"{ident}: invalid or unreviewed audio-based exact timestamps")
        check = HERE / "FINAL_AV_REVIEW.json"
        if not check.exists():
            problems.append("Final audiovisual playback sign-off does not exist")
        else:
            review = json.loads(check.read_text(encoding="utf8"))
            for k in ("master_sha256", "documentary_watched_with_sound", "short_01_watched_with_sound",
                      "short_02_watched_with_sound", "subscribe_cta_visual_and_audible",
                      "captions_checked", "all_sources_approved"):
                if not review.get(k):
                    problems.append(f"Final audiovisual signoff missing: {k}")
    return {
        "mode": "release" if release else "planning",
        "chapters": len(scripts),
        "paragraphs": paragraphs,
        "manually_chosen_visuals": len(scenes),
        "pass": not problems,
        "problems": problems[:60],
        "more_problems": max(0, len(problems) - 60),
        "note": "Planning pass does not imply rights approval, shot approval, locked timing, export or video completion."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    result = inspect(release=args.release)
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
