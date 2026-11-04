#!/usr/bin/env python3
"""Genre-neutral source-rights, editorial originality and completed-event release gate.

Not a promise of copyright safety, Content ID immunity or YouTube monetization.
The human reviewer, not code, decides whether the actual edits are substantive.
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

# Import reliably both from CLI and unittest's file-loader path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_quality_gate import ReferenceQualityError, validate_reference_profile

CATEGORIES = {
    "anime", "movie", "tv", "gaming", "football", "sports", "celebrity",
    "music", "history", "documentary", "comedy", "animation", "other",
}
STYLES = {"analysis", "narrative", "character_study", "visual_essay", "music_sync",
          "comparison", "tribute", "tutorial", "comedy", "other"}
RIGHTS = {"owned", "cc0", "public_domain", "cc_by", "cc_by_sa",
          "commercial_license", "written_permission", "exception_claimed", "unclear"}
EXCEPTION_RISK = {"exception_claimed", "unclear"}


class GateError(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise GateError(message)


def https_link(value):
    return isinstance(value, str) and urlparse(value).scheme == "https" and bool(urlparse(value).netloc)


def valid_date(value):
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def hash_file(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(2 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path):
    return json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        timeout=30,
    ))


def local_file(root, relative):
    need(isinstance(relative, str) and relative.strip()
         and not Path(relative).is_absolute() and ".." not in Path(relative).parts,
         "Only relative file paths within assets-root are allowed")
    path = (root / relative).resolve()
    need(root == path or root in path.parents, "File escapes assets-root")
    return path


def _sources(data, label, require_media=True):
    need(isinstance(data, list), f"{label} must be a list")
    if require_media:
        need(bool(data), f"{label}: at least one source required")
    ids = set()
    risks = []
    for item in data:
        need(isinstance(item, dict), f"{label}: invalid entry")
        key = item.get("id")
        need(isinstance(key, str) and key.strip() and key not in ids, f"{label}: missing/duplicate source ID")
        ids.add(key)
        need(item.get("rights_status") in RIGHTS, f"{label}/{key}: invalid rights_status")
        need(isinstance(item.get("creator"), str) and item["creator"].strip(), f"{label}/{key}: creator missing")
        need(https_link(item.get("source_page")), f"{label}/{key}: exact source landing page required")
        need(https_link(item.get("rights_evidence")), f"{label}/{key}: source-specific rights evidence required")
        need(valid_date(item.get("reviewed_on")), f"{label}/{key}: dated rights review required")
        need(re.fullmatch("[0-9a-f]{64}", item.get("sha256", "")) is not None,
             f"{label}/{key}: verified SHA256 required")
        need(isinstance(item.get("file"), str), f"{label}/{key}: source file required")
        local_file(Path("/tmp"), item["file"])
        if item["rights_status"] in EXCEPTION_RISK:
            risks.append(f"{label}/{key}: {item['rights_status']} - commercial clearance not established")
        else:
            need(item.get("commercial_use") is True and item.get("derivatives_allowed") is True,
                 f"{label}/{key}: commercial adaptation rights must be documented")
            if item["rights_status"] in {"cc_by", "cc_by_sa", "commercial_license", "written_permission"}:
                need(https_link(item.get("license_url")), f"{label}/{key}: full licence or permission URL required")
                need(isinstance(item.get("required_credit"), str) and item["required_credit"].strip(),
                     f"{label}/{key}: credit/conditions required")
            if item["rights_status"] == "cc_by_sa":
                need(item.get("share_alike_plan"), f"{label}/{key}: share-alike compliance plan missing")
    return ids, risks


def validate_plan(m):
    need(isinstance(m, dict) and m.get("schema_version") in {1, 2}, "Edit manifest schema_version must be 1 (legacy) or 2 (reference-led)")
    need(m.get("pipeline") == "universal_edit", "Not a universal edit manifest")
    need(m.get("category") in CATEGORIES, "Unknown category (use other where needed)")
    need(m.get("style") in STYLES, "Unknown edit style")
    need(m.get("visual_sources_policy") == "EXISTING_REAL_OR_ORIGINAL_MEDIA_ONLY",
         "No generated or simulated footage to replace real source clips")
    title = m.get("title")
    need(isinstance(title, str) and len(title.strip()) >= 8, "Missing edit title")
    media_ids, media_risks = _sources(m.get("media_sources"), "media_sources")
    audio_ids, audio_risks = _sources(m.get("audio_sources", []), "audio_sources", require_media=False)
    risks = media_risks + audio_risks
    timeline = m.get("timeline")
    need(isinstance(timeline, list) and len(timeline) >= 1, "At least one intentionally timed shot required")
    previous = 0
    for number, shot in enumerate(timeline, 1):
        need(isinstance(shot, dict), f"Shot {number}: missing data")
        need(shot.get("source_id") in media_ids, f"Shot {number}: unknown source")
        a, b = shot.get("start_sec"), shot.get("end_sec")
        need(isinstance(a, (int, float)) and not isinstance(a, bool)
             and isinstance(b, (int, float)) and not isinstance(b, bool)
             and 0 <= a < b, f"Shot {number}: invalid source cut")
        need(isinstance(shot.get("editorial_reason"), str)
             and len(shot["editorial_reason"].strip().split()) >= 6,
             f"Shot {number}: a concrete editorial reason is required")
        moment = shot.get("complete_moment", {})
        need(isinstance(moment, dict) and moment.get("visually_reviewed") is True
             and moment.get("beginning_included") is True
             and moment.get("payoff_included") is True,
             f"Shot {number}: beginning and payoff must be actually reviewed")
        need(isinstance(moment.get("evidence_note"), str)
             and len(moment["evidence_note"].split()) >= 5,
             f"Shot {number}: shot completion evidence note required")
        previous += (b - a)
    claims = m.get("claims", {})
    need(claims.get("coverage") in {"highlight_selection", "all_events", "single_event", "not_applicable"},
         "Coverage type must be explicit")
    if claims["coverage"] == "all_events":
        need(isinstance(claims.get("expected_count"), int) and claims["expected_count"] > 0,
             "All-events claim requires an expected count")
        need(isinstance(claims.get("event_ledger"), list)
             and len(claims["event_ledger"]) == claims["expected_count"],
             "Every event must be individually catalogued")
        need(len(set(claims["event_ledger"])) == claims["expected_count"],
             "Every event must have a unique ID")
        need(claims.get("human_count_verified") is True,
             "Human must verify every event is represented in the final cut")
    claim_words = bool(re.search(r"\b(?:all|every)\s+\d+\s+(?:goals?|scenes?|moments?|kills?|episodes?)\b", title, re.I))
    need(not claim_words or claims["coverage"] == "all_events",
         "All-events claim in title contradicts highlight selection")
    originality = m.get("originality", {})
    need(isinstance(originality.get("creative_thesis"), str)
         and len(originality["creative_thesis"].split()) >= 8,
         "No specific original interpretation or narrative concept")
    need(isinstance(originality.get("source_to_story_map"), list)
         and len(originality["source_to_story_map"]) == len(timeline)
         and all(isinstance(s, str) and len(s.split()) >= 6
                 for s in originality["source_to_story_map"]),
         "Every shot needs an authored source-to-story contribution")
    modes = originality.get("contribution_modes", [])
    permitted = {"original_commentary", "original_critical_analysis",
                 "original_explanatory_graphics", "original_scene_reconstruction",
                 "original_narrative_structure", "original_comedic_recontextualization"}
    need(isinstance(modes, list) and len(set(modes) & permitted) >= 1,
         "Color filters, beat sync, speed ramps and generic captions alone do not establish originality")
    need(originality.get("editorial_significance_human_review_required") is True,
         "Require a real editorial judgment about substantive contribution")
    if originality.get("uses_voice"):
        need(isinstance(originality.get("voice_source_id"), str)
             and originality["voice_source_id"] in audio_ids,
             "Voiceover must use cleared and documented audio")
    if "original_explanatory_graphics" in modes:
        need(isinstance(originality.get("graphics_explanation"), str)
             and len(originality["graphics_explanation"].split()) >= 10,
             "Document how the new graphics explain something, not just decorative effects")
    need(isinstance(m.get("attribution"), str) and m["attribution"].strip(),
         "Credit notes missing, including usage changes")
    qa = m.get("editorial_review", {})
    if qa.get("approved") is True:
        need(qa.get("full_export_watched") is True and qa.get("audio_listened") is True
             and qa.get("all_moments_complete") is True
             and qa.get("substantive_transformation_confirmed") is True
             and qa.get("rights_confirmed") is True,
             "Full human audio/visual/rights/originality review required")
        need(isinstance(qa.get("reviewer"), str) and len(qa["reviewer"].strip()) >= 3
             and valid_date(qa.get("reviewed_on")), "Reviewer identity/date required")
    try:
        reference_report = validate_reference_profile(m, phase="plan")
    except ReferenceQualityError as exc:
        raise GateError(str(exc)) from exc
    return {"phase": "plan", "category": m["category"], "style": m["style"],
            "sources": len(media_ids), "audio_sources": len(audio_ids),
            "scenes": len(timeline), "risk_flags": risks,
            "editorial_review_approved": qa.get("approved") is True,
            "reference_quality": reference_report,
            "monetization_guaranteed": False}


def validate_release(m, root):
    result = validate_plan(m)
    try:
        reference_review = validate_reference_profile(m, phase="release")
    except ReferenceQualityError as exc:
        raise GateError(str(exc)) from exc
    qa = m.get("editorial_review", {})
    need(qa.get("approved") is True, "Publishing blocked: complete human review/sign-off first")
    need(not result["risk_flags"],
         "Publishing blocked: ambiguous/fair-use-exception source is not commercially cleared")
    root = Path(root).resolve()
    source_probe = {}
    for item in m["media_sources"] + m.get("audio_sources", []):
        path = local_file(root, item["file"])
        need(path.is_file(), f"Missing file: {path}")
        need(hash_file(path) == item["sha256"], f"Asset hash mismatch: {item['id']}")
        info = probe(path)
        require_kind = "video" if item in m["media_sources"] else "audio"
        need(any(s["codec_type"] == require_kind for s in info["streams"]),
             f"{item['id']}: expected {require_kind} stream missing")
        source_probe[item["id"]] = float(info["format"]["duration"])
    for number, shot in enumerate(m["timeline"], 1):
        need(shot["end_sec"] <= source_probe[shot["source_id"]] + 0.15,
             f"Shot {number}: timeline cut overruns source")
    output = m.get("output", {})
    path = local_file(root, output.get("file"))
    need(path.suffix.lower() == ".mp4" and path.is_file(), "Export MP4 is missing")
    need(re.fullmatch("[0-9a-f]{64}", output.get("sha256", "")) is not None,
         "Export SHA256 must be recorded after rendering")
    need(hash_file(path) == output["sha256"], "Rendered MP4 has changed since review")
    info = probe(path)
    need(any(s["codec_type"] == "video" for s in info["streams"]), "Missing output video")
    need(any(s["codec_type"] == "audio" for s in info["streams"]), "Missing output audio")
    need(float(info["format"]["duration"]) >= 5, "Suspiciously short output video")
    need(qa.get("reviewed_output_sha256") == output["sha256"],
         "Human approval must be tied to the exact exported MP4 hash")
    return {"phase": "release", "status": "INTERNAL_GATE_PASSED_NOT_YOUTUBE_MONETIZATION",
            "category": m["category"], "style": m["style"],
            "video_sha256": output["sha256"], "duration_sec": float(info["format"]["duration"]),
            "risk_flags": [], "reference_quality": reference_review,
            "monetization_guaranteed": False}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--phase", choices=["plan", "release"], required=True)
    p.add_argument("--assets-root", type=Path, default=Path("."))
    p.add_argument("--evidence-output", type=Path)
    a = p.parse_args(argv)
    try:
        manifest = json.loads(a.manifest.read_text())
        report = validate_plan(manifest) if a.phase == "plan" else validate_release(manifest, a.assets_root)
        print(json.dumps(report, indent=2))
        if a.evidence_output:
            a.evidence_output.parent.mkdir(parents=True, exist_ok=True)
            a.evidence_output.write_text(json.dumps(report, indent=2))
        return 0
    except (GateError, ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as err:
        print(f"UNIVERSAL_EDIT_GATE_BLOCKED: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
