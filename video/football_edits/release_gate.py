#!/usr/bin/env python3
"""Fail-closed editorial, footage-rights and technical release gate for football edits.

The gate is an internal quality control, NOT a prediction of YouTube approval.
Usage: python video/football_edits/release_gate.py --manifest path.json --phase plan
       python video/football_edits/release_gate.py --manifest path.json --phase release --assets-root .
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


class GateError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise GateError(message)


def url(value):
    return isinstance(value, str) and urlparse(value).scheme == "https" and bool(urlparse(value).netloc)


def sha_file(path: Path, algo: str):
    h = hashlib.new(algo)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(2 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def valid_date(value):
    try:
        date.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def media_probe(file):
    return json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(file)],
        timeout=30,
    ))


def validate_plan(m):
    require(isinstance(m, dict), "Manifest must be a JSON object")
    require(m.get("schema_version") == 1, "Unsupported schema_version")
    require(m.get("workflow") == "football_real_footage", "Wrong workflow")
    require(isinstance(m.get("title"), str) and len(m["title"].strip()) >= 12, "Missing meaningful title")
    require(m.get("visual_policy") == "REAL_FOOTAGE_ONLY", "AI, CGI and generated football images are forbidden")
    require(m.get("footage_mode") in ("curated_segments", "source_unabridged"), "Invalid footage_mode")
    sources = m.get("sources")
    require(isinstance(sources, list) and sources, "No source rights ledger")
    ids = set()
    for s in sources:
        sid = s.get("id")
        require(isinstance(sid, str) and sid and sid not in ids, "Missing or duplicate source ID")
        ids.add(sid)
        require(url(s.get("source_page")), f"{sid}: exact source page required")
        require(url(s.get("license_evidence")), f"{sid}: reviewable licence evidence required")
        require(url(s.get("license_url")), f"{sid}: licence URL required")
        require(isinstance(s.get("creator"), str) and len(s["creator"].strip()) >= 3, f"{sid}: creator required")
        require(s.get("license") in ("CC BY 3.0", "CC BY 4.0", "CC0 1.0", "Public Domain", "Written Permission"),
                f"{sid}: unapproved licence or unreviewed licence terms")
        require(s.get("commercial_use") is True and s.get("derivatives_allowed") is True,
                f"{sid}: commercial reuse and editing must both be permitted")
        require(valid_date(s.get("license_checked_on")), f"{sid}: dated rights check required")
        require(isinstance(s.get("file"), str) and s["file"].strip() and not Path(s["file"]).is_absolute()
                and ".." not in Path(s["file"]).parts, f"{sid}: relative source path required")
        digest = s.get("sha1")
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{40}", digest),
                f"{sid}: verified original-file SHA1 required")
    segments = m.get("segments")
    require(isinstance(segments, list) and segments, "No edit segments")
    goal_count = 0
    for i, seg in enumerate(segments, 1):
        require(seg.get("source_id") in ids, f"Segment {i}: unapproved source")
        start, end = seg.get("start_sec"), seg.get("end_sec")
        require(isinstance(start, (int, float)) and isinstance(end, (int, float))
                and 0 <= start < end, f"Segment {i}: invalid timing")
        require(seg.get("kind") in ("goal", "context", "source_unabridged"), f"Segment {i}: invalid kind")
        if seg["kind"] == "goal":
            goal_count += 1
            require(end - start >= 3.0, f"Segment {i}: potentially truncated goal (under 3 seconds)")
            require(seg.get("pre_goal_action_verified") is True
                    and seg.get("ball_crossing_line_verified") is True
                    and seg.get("post_goal_resolution_verified") is True,
                    f"Segment {i}: full goal action and resolution must be watched and confirmed")
            require(isinstance(seg.get("scene_notes"), str) and len(seg["scene_notes"].strip()) >= 25,
                    f"Segment {i}: individual observed scene notes required")
        if seg["kind"] == "source_unabridged":
            require(m["footage_mode"] == "source_unabridged", "Unabridged segment requires source_unabridged mode")
    if m["footage_mode"] == "source_unabridged":
        require(len(segments) == 1 and segments[0]["kind"] == "source_unabridged"
                and segments[0]["start_sec"] == 0, "Preserve source from time zero without cut points")
    else:
        require(all(s["kind"] != "source_unabridged" for s in segments), "Mixed unabridged/curated mode")
    claim = m.get("coverage_claim", {})
    require(claim.get("type") in ("selected_highlights", "entire_source", "every_goal"), "Coverage claim undefined")
    if re.search(r"\b(?:all|every)\s+\d+\s+goals?\b", m["title"], flags=re.I):
        require(claim["type"] == "every_goal", "A title claiming every goal needs an independently verified every-goal ledger")
    if claim["type"] == "every_goal":
        require(isinstance(claim.get("goal_count"), int) and claim["goal_count"] > 0,
                "Every-goal claim must specify count")
        require(m["footage_mode"] == "source_unabridged" or goal_count == claim["goal_count"],
                "Not every claimed goal has a complete reviewed scene")
        require(claim.get("goal_by_goal_human_count_verified") is True,
                "Claim of every goal blocked until a human counted every goal in the export")
    if claim["type"] == "entire_source":
        require(m["footage_mode"] == "source_unabridged", "Entire-source title requires unabridged video")
    editorial = m.get("original_editorial", {})
    require(isinstance(editorial.get("angle"), str) and len(editorial["angle"].split()) >= 8,
            "Missing unique thesis/storyline for this video")
    commentary = editorial.get("commentary")
    require(isinstance(commentary, list) and len(commentary) >= 3, "At least 3 individually authored analysis beats required")
    for i, beat in enumerate(commentary, 1):
        require(isinstance(beat.get("text"), str) and len(beat["text"].split()) >= 7,
                f"Analysis beat {i}: needs a substantive sentence")
        require(isinstance(beat.get("specific_observation"), str)
                and len(beat["specific_observation"].split()) >= 6,
                f"Analysis beat {i}: explain what footage supports")
        require(url(beat.get("factual_source")), f"Analysis beat {i}: cite factual context")
    require(editorial.get("narration_origin") in ("original_recorded_voice", "generated_from_original_script"),
            "Narration must be independently authored and recorded (AI voice is permitted; visuals are not)")
    require(editorial.get("narration_in_video") is True, "Original commentary must actually be in the final audio")
    narrator_file = editorial.get("narration_file")
    require(isinstance(narrator_file, str) and narrator_file.strip()
            and not Path(narrator_file).is_absolute() and ".." not in Path(narrator_file).parts,
            "Provide a recorded original narration file path; music alone is not sufficient")
    require(len({beat["text"].strip().lower() for beat in commentary}) == len(commentary)
            and len({beat["specific_observation"].strip().lower() for beat in commentary}) == len(commentary),
            "Repeated generic commentary lines or duplicate observations are not substantive analysis")
    require(len(editorial.get("visual_storytelling", [])) >= 2,
            "Substantive editor-designed explanatory visuals, annotations or structure required")
    music = m.get("music", {})
    require(music.get("origin") in ("original_composition", "licensed_commercial"), "Music rights missing")
    require(music.get("commercial_use") is True, "Music must permit commercial reuse")
    if music["origin"] == "licensed_commercial":
        require(url(music.get("license_evidence")) and isinstance(music.get("file"), str)
                and music["file"].strip(), "Third-party music needs an exact licence and file record")
    out = m.get("output", {})
    require(isinstance(out.get("file"), str) and out["file"].endswith(".mp4")
            and not Path(out["file"]).is_absolute() and ".." not in Path(out["file"]).parts,
            "Expected final MP4 file path required")
    require(m.get("attribution_text", "").strip().count("http") >= 2
            and all(s["creator"] in m["attribution_text"] for s in sources),
            "Attribution must credit authors and link exact footage and licence")
    if m.get("editorial_review", {}).get("approved") is True:
        require(m["editorial_review"].get("goals_complete") is True
                and m["editorial_review"].get("transformation_reviewed") is True
                and m["editorial_review"].get("rights_reviewed") is True,
                "Editorial approval must include all three checks")
        require(len(m["editorial_review"].get("reviewer", "").strip()) >= 3
                and valid_date(m["editorial_review"].get("reviewed_on")),
                "Human editorial sign-off must identify reviewer and date")
    return {"sources": len(sources), "segments": len(segments), "complete_goals_recorded": goal_count,
            "coverage": claim["type"], "human_approved": m.get("editorial_review", {}).get("approved") is True}


def validate_release(m, assets_root):
    plan = validate_plan(m)
    require(plan["human_approved"], "Human editorial viewing and rights approval pending: publication blocked")
    root = Path(assets_root).resolve()
    checks = []
    for s in m["sources"]:
        path = (root / s["file"]).resolve()
        require(root == path or root in path.parents, f"Source {s['id']}: illegal file path")
        require(path.is_file(), f"Source {s['id']}: media missing")
        actual = sha_file(path, "sha1")
        require(actual == s["sha1"], f"Source {s['id']}: source-file SHA1 mismatch")
        info = media_probe(path)
        require(any(x["codec_type"] == "video" for x in info["streams"]), f"Source {s['id']}: no video")
        checks.append({"id": s["id"], "source_sha256": sha_file(path, "sha256"),
                       "source_duration": float(info["format"]["duration"])})
    by_id = {s["id"]: check for s, check in zip(m["sources"], checks)}
    for i, seg in enumerate(m["segments"], 1):
        require(seg["end_sec"] <= by_id[seg["source_id"]]["source_duration"] + 0.3,
                f"Segment {i}: outside source")
        if m["footage_mode"] == "source_unabridged":
            src_len = by_id[seg["source_id"]]["source_duration"]
            require(abs(seg["end_sec"] - src_len) <= 0.3, "Unabridged mode must not remove the end")
    narration = (root / m["original_editorial"]["narration_file"]).resolve()
    require(root in narration.parents and narration.is_file(), "Narration file not found at release")
    narration_streams = media_probe(narration)["streams"]
    require(any(s["codec_type"] == "audio" for s in narration_streams), "Original narration file has no audio")
    output = m.get("output", {})
    name = output.get("file")
    require(isinstance(name, str) and name.endswith(".mp4") and not Path(name).is_absolute()
            and ".." not in Path(name).parts, "Output MP4 relative path required")
    file = (root / name).resolve()
    require(root in file.parents and file.is_file(), "Output MP4 missing")
    result = media_probe(file)
    video = next((s for s in result["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in result["streams"] if s["codec_type"] == "audio"), None)
    require(video is not None and audio is not None, "Output needs both video and original commentary audio")
    require((video.get("width"), video.get("height")) == (1080, 1920), "Output must be 1080x1920 vertical")
    seconds = float(result["format"]["duration"])
    require(seconds >= 12, "Output too short for verified commentary and goal action")
    require(url(output.get("human_review_reference")), "Provide final export review evidence URL")
    require(output.get("narration_audibly_verified") is True, "Someone must confirm audible original commentary")
    if m["footage_mode"] == "source_unabridged":
        require(seconds >= by_id[m["segments"][0]["source_id"]]["source_duration"] - 0.5,
                "Output is shorter than unabridged source")
    return {"status": "TECHNICAL_AND_MANIFEST_GATE_PASSED_NOT_YOUTUBE_APPROVAL",
            "video_sha256": sha_file(file, "sha256"), "duration_sec": seconds,
            "verified_sources": checks, **plan}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--phase", choices=["plan", "release"], required=True)
    parser.add_argument("--assets-root", default=".")
    parser.add_argument("--evidence-output", type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.manifest.read_text())
        output = validate_release(data, args.assets_root) if args.phase == "release" else validate_plan(data)
    except (GateError, ValueError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print("FOOTBALL_EDITORIAL_GATE_BLOCKED:", exc, file=sys.stderr)
        return 2
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if args.evidence_output:
        args.evidence_output.parent.mkdir(parents=True, exist_ok=True)
        args.evidence_output.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
