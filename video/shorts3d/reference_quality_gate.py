#!/usr/bin/env python3
"""Fail-closed 3D history Short reference-standard production / delivery gate.

No machine metrics or "AI similarity" score can approve artistic equivalence.
Real media, documented editorial comparison and shot-by-shot human observation
are required. This gate does not publish or deliver videos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
REGISTRY = HERE / "reference_benchmark.json"
REAL_SHA256 = re.compile(r"^[a-f0-9]{64}$")
APPROVED_LICENSES = {
    "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "public-domain",
}


class ReferenceGateFailure(ValueError):
    pass


def require(test: bool, explanation: str) -> None:
    if not test:
        raise ReferenceGateFailure(explanation)


def load_json(path: Path) -> dict:
    require(path.is_file(), "Missing input: " + str(path))
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ReferenceGateFailure("Malformed JSON " + str(path) + ": " + str(exc))
    require(isinstance(result, dict), "Expected JSON object at " + str(path))
    return result


def sha256(path: Path) -> str:
    require(path.is_file(), "File missing: " + str(path))
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def substantial(s: object, n: int = 22) -> bool:
    return isinstance(s, str) and len(s.strip()) >= n


def verify_registry(registry: dict) -> list[dict]:
    refs = registry.get("reference_files")
    require(isinstance(refs, list) and len(refs) == 2,
            "Both original reference benchmarks are compulsory")
    ids = set()
    for item in refs:
        require(isinstance(item, dict), "Invalid reference")
        rid = item.get("id")
        require(rid not in ids and rid in {"reference-3d-a", "reference-3d-b"},
                "Unknown or duplicate reference id")
        ids.add(rid)
        require(bool(REAL_SHA256.fullmatch(str(item.get("sha256", "")))),
                "Reference SHA-256 missing")
        require(item.get("width") == 720 and item.get("height") == 1280 and item.get("fps") == 30,
                "Reference media specifications changed")
        require(62 < float(item.get("duration_seconds", 0)) < 67,
                "Reference duration changed")
    require(registry.get("minimum_each_score") == 8.5,
            "Reference threshold lowered: fail closed")
    return refs


def test_reference_identification(review: dict, refs: list[dict]) -> None:
    observed = review.get("references_compared")
    require(isinstance(observed, list) and len(observed) == len(refs),
            "Reviewer must compare against BOTH supplied references")
    expected = {(r["id"], r["sha256"]) for r in refs}
    actual = {
        (r.get("id"), r.get("sha256"))
        for r in observed if isinstance(r, dict)
    }
    require(actual == expected, "Reference IDs/hashes do not match the user's actual videos")
    for item in observed:
        require(substantial(item.get("specific_comparison_notes"), 35),
                "Describe a concrete visual feature noticed in each original reference")


def check_editorial_scores(review: dict, registry: dict) -> None:
    require(review.get("schema_version") == 1, "Review schema version missing")
    require(substantial(review.get("reviewer"), 4), "Real reviewer name/role missing")
    require(substantial(review.get("reviewed_at_utc"), 10), "UTC review date missing")
    test_reference_identification(review, verify_registry(registry))
    scores = review.get("editorial_scores")
    dims = registry["required_review_dimensions"]
    require(isinstance(scores, dict) and set(scores) == set(dims),
            "Missing five separate human reference-comparison ratings")
    for dimension in dims:
        item = scores[dimension]
        require(isinstance(item, dict), dimension + " must have rating and evidence notes")
        rating = item.get("score")
        require(type(rating) in (int, float) and math.isfinite(rating),
                dimension + ": invalid editorial rating")
        require(8.5 <= rating <= 10, dimension + " below 8.5/10 — remake rather than deliver")
        require(substantial(item.get("observations"), 40),
                dimension + " needs concrete, original comparative observations")
    require(review.get("visual_reference_near_parity_confirmed") is True,
            "Editor has not personally confirmed near-parity with user references")
    require(review.get("unresolved_hard_failures") == [],
            "Any outstanding factual, visual, motion, rights or audio defect blocks delivery")


def check_assets_and_shots(storyboard: dict, review: dict) -> None:
    shots = storyboard.get("shots")
    plans = review.get("shot_plans")
    require(isinstance(shots, list) and len(shots) > 0, "Storyboard shots missing")
    require(isinstance(plans, list) and len(plans) == len(shots),
            "An authored visual/asset plan is required for EVERY shot")
    plan_ids = {item.get("shot_id") for item in plans if isinstance(item, dict)}
    require(len(plan_ids) == len(shots) and plan_ids == {s["id"] for s in shots},
            "Plan and storyboard shot IDs differ")
    for shot in shots:
        sid = shot["id"]
        plan = next(p for p in plans if p.get("shot_id") == sid)
        require(substantial(plan.get("visible_action"), 35),
                sid + ": describe the EXACT visible physical event, not only scenery")
        require(substantial(plan.get("camera_and_motion"), 25),
                sid + ": specify deliberate camera and object motion")
        require(substantial(plan.get("why_this_matches_narration"), 35),
                sid + ": explain how visuals demonstrate the stated narration")
        assets = plan.get("assets")
        require(isinstance(assets, list) and assets,
                sid + ": missing concrete free/commercially reusable 3D assets")
        for asset in assets:
            require(isinstance(asset, dict), sid + ": invalid asset")
            require(substantial(asset.get("title"), 4),
                    sid + ": asset title absent")
            source = asset.get("source_url", "")
            license_url = asset.get("license_url", "")
            require(isinstance(source, str) and urlsplit(source).scheme == "https"
                    and bool(urlsplit(source).netloc),
                    sid + ": no exact HTTPS asset landing-page source")
            require(isinstance(license_url, str) and urlsplit(license_url).scheme == "https"
                    and bool(urlsplit(license_url).netloc),
                    sid + ": no verified license URL")
            license_name = asset.get("license")
            require(license_name in APPROVED_LICENSES or
                    (license_name == "other-commercial-with-evidence" and
                     substantial(asset.get("rights_evidence"), 30)),
                    sid + ": unverified commercial-use license")
            require(asset.get("commercial_reuse_verified") is True,
                    sid + ": rights must be confirmed individually")
            require(bool(REAL_SHA256.fullmatch(str(asset.get("sha256", "")))),
                    sid + ": asset download SHA-256 missing")
        require(plan.get("assets_are_final_manual_selection") is True,
                sid + ": editor must select every asset, not keyword-based automation")


def ffprobe(path: Path) -> dict:
    require(path.is_file() and path.stat().st_size > 20000,
            "Playable movie missing/too small: " + str(path))
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,width,height,avg_frame_rate,channels,sample_rate",
             "-of", "json", str(path)],
            text=True, capture_output=True, timeout=60, check=True
        )
        return json.loads(p.stdout)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise ReferenceGateFailure("Invalid/unreadable movie: " + str(exc))


def validate_video(path: Path, min_duration: float, max_duration: float,
                   needs_audio: bool) -> dict:
    info = ffprobe(path)
    streams = info.get("streams", [])
    video = [x for x in streams if x.get("codec_type") == "video"]
    audio = [x for x in streams if x.get("codec_type") == "audio"]
    require(len(video) == 1, "Video stream missing")
    v = video[0]
    require(v.get("width") >= 720 and v.get("height") >= 1280,
            "Video below portrait reference minimum 720x1280")
    require(v["height"] > v["width"], "Not vertical")
    rate = v.get("avg_frame_rate", "")
    try:
        num, den = [int(n) for n in rate.split("/")]
        fps = num / den
    except (ValueError, ZeroDivisionError):
        raise ReferenceGateFailure("Unable to read video frame rate")
    require(fps >= 29.0, "Reference video is 30fps; do not regress to 24fps")
    duration = float(info["format"]["duration"])
    require(min_duration <= duration <= max_duration,
            "Wrong approved runtime: " + str(duration))
    if needs_audio:
        require(len(audio) == 1, "Silent video cannot be delivered")
        a = audio[0]
        require(int(a.get("channels", 0)) == 2, "Stereo output required")
        require(int(a.get("sample_rate", 0)) >= 44100,
                "Audio sampling rate below reference output")
    return info


def relative_proof(folder: Path, rel: str) -> Path:
    require(isinstance(rel, str) and rel and
            not Path(rel).is_absolute() and ".." not in Path(rel).parts,
            "Proof path must be local inside approved proof directory")
    return folder / rel


def image_fingerprint(file: Path, second: float | None = None) -> bytes:
    """Decode a real frame to 64x64 RGB with free FFmpeg; reject fake image files."""
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin"]
    if second is not None:
        args += ["-ss", f"{second:.3f}"]
    args += ["-i", str(file), "-frames:v", "1", "-vf",
             "scale=64:64:flags=bilinear,format=rgb24",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
    try:
        result = subprocess.run(args, capture_output=True, timeout=50, check=True)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ReferenceGateFailure("Cannot decode shot evidence from " + str(file) +
                                   ": " + str(exc))
    require(len(result.stdout) == 64 * 64 * 3,
            "Evidence is not a decoded single video/image frame: " + str(file))
    return result.stdout


def verify_frame_is_from_export(movie: Path, proof: Path, at_seconds: float) -> None:
    """A proof JPG must depict the ACTUAL export at the specified narration time."""
    actual = image_fingerprint(movie, at_seconds)
    observed = image_fingerprint(proof)
    distance = sum(abs(x - y) for x, y in zip(actual, observed)) / len(actual)
    # Tolerate JPEG re-encoding; reject completely different or fabricated frames.
    require(distance <= 24.0,
            f"Proof image does not match actual MP4 at {at_seconds:.2f}s: "
            f"{proof} (mean RGB distance {distance:.1f} > 24)")


def check_delivery_shots(storyboard: dict, review: dict, proofs: Path, media: Path) -> None:
    accepted = review.get("shot_reviews")
    required = storyboard.get("shots", [])
    require(isinstance(accepted, list) and len(accepted) == len(required),
            "Every narrated scene must have independent visual sign-off")
    by_id = {s.get("shot_id"): s for s in accepted if isinstance(s, dict)}
    require(len(by_id) == len(required) and
            set(by_id) == {s["id"] for s in required},
            "Missing, duplicate or wrong shot review")
    for shot in required:
        sid = shot["id"]
        item = by_id[sid]
        require(item.get("visible_action_matches_spoken_words") is True,
                sid + ": the visible event does not match the narration")
        require(item.get("required_objects_and_motion_visible") is True,
                sid + ": required subject/prop movement is missing")
        require(item.get("period_and_rights_verified") is True,
                sid + ": history or rights unverified")
        require(substantial(item.get("observations"), 40),
                sid + ": actual full-shot visual review notes missing")
        evidence = item.get("proof_frames", {})
        require(isinstance(evidence, dict) and
                set(evidence) == {"first_frame", "midpoint", "end_frame"},
                sid + ": first/middle/end frame proofs are all required")
        start = float(shot["start_seconds"])
        end = float(shot["end_seconds"])
        expected_times = {"first_frame": start + 0.15,
                          "midpoint": (start + end) / 2.0,
                          "end_frame": end - 0.15}
        for label, filename in evidence.items():
            proof = relative_proof(proofs, filename)
            require(proof.is_file() and proof.stat().st_size > 1500,
                    sid + ": missing real " + label + " proof image")
            verify_frame_is_from_export(media, proof, expected_times[label])


def evaluate(phase: str, registry: dict, storyboard: dict, review: dict,
             media: Path, proofs: Path | None) -> dict:
    check_editorial_scores(review, registry)
    check_assets_and_shots(storyboard, review)
    require(review.get("phase") == phase,
            "The review is for the wrong phase; look-development cannot approve a finished video")
    require(media.is_file(), "Required file not present: " + str(media))
    digest = sha256(media)
    require(review.get("media_sha256") == digest,
            "Editor review not bound to THIS exact video export (SHA-256 differs)")
    seconds = float(storyboard.get("seconds", 0))
    if phase == "preproduction":
        require(review.get("lookdev_sample_visually_compared") is True,
                "Mandatory authored 3–5s look-development sample has not been compared")
        meta = validate_video(media, 3.0, 5.1, needs_audio=False)
        require(review.get("preproduction_approved") is True,
                "No artistic greenlight: do not start costly full rendering or TTS")
    else:
        require(proofs is not None and proofs.is_dir(),
                "Full-film first/mid/end shot evidence missing")
        meta = validate_video(media, seconds - 0.25, seconds + 0.25, needs_audio=True)
        require(review.get("viewed_every_second_of_export") is True and
                review.get("listened_to_entire_final_mix") is True,
                "Editor must watch/listen to entire actual final export")
        require(review.get("voice_foley_synchronized") is True and
                review.get("no_unintended_long_silence") is True,
                "Audio and Foley must be verified scene by scene")
        require(review.get("delivery_approved") is True,
                "Artistic delivery approval missing; keep as internal diagnostic")
        check_delivery_shots(storyboard, review, proofs, media)
    return {
        "status": "PASS_" + phase.upper(),
        "media_sha256": digest,
        "reviewer": review["reviewer"],
        "individual_reference_scores": {
            key: value["score"] for key, value in review["editorial_scores"].items()
        },
        "checks": "editorial evidence + media file + authored assets + reference fingerprint",
        "media": meta,
        "publication_approved": False,  # Never auto-authorize YouTube publishing.
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=["preproduction", "delivery"])
    p.add_argument("--storyboard", type=Path, required=True)
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--media", type=Path, required=True)
    p.add_argument("--proofs", type=Path)
    p.add_argument("--registry", type=Path, default=REGISTRY)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    try:
        report = evaluate(args.phase, load_json(args.registry),
                          load_json(args.storyboard), load_json(args.review),
                          args.media, args.proofs)
    except (ReferenceGateFailure, KeyError, TypeError, AttributeError, IndexError) as exc:
        print("REFERENCE_QUALITY_GATE_BLOCKED:", str(exc), file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(report, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
