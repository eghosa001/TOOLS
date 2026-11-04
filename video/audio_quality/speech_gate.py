#!/usr/bin/env python3
"""Repository-wide narration QA. A technical gate cannot certify human-sounding speech.

Drafts: enforce measurable pace, clean spoken text and speech signal.
Release: additionally require a human's complete listening review, verified
name pronunciations and approval tied to the EXACT audio file hash.

Example:
 python video/audio_quality/speech_gate.py --manifest speech.json \
   --audio narrated_short.mp4 --stage draft --report speech_qc.json

This rule concerns actual SPEECH, not silent visual exports, music, Foley or
nonverbal ASMR. Voice model/vendor choice is never evidence of naturalness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

SHORT_DEFAULT_LO = 170
SHORT_DEFAULT_HI = 210
SHORT_HARD_LO = 160
SHORT_HARD_HI = 225
WORD_RE = re.compile(r"\b[\w]+(?:['’\-][\w]+)*\b", re.UNICODE)
YEAR_RE = re.compile(r"\b(?:18|19|20)\d{2}\b")
SILENCE_RE = re.compile(r"silence_start:\s*([\d.]+).*?silence_end:\s*([\d.]+)", re.S)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def valid_https(url: object) -> bool:
    if not isinstance(url, str) or not url.strip():
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.netloc)


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def media_duration(path: Path) -> float:
    data = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)], timeout=75
    ))
    return float(data["format"]["duration"])


def long_silences(path: Path, minimum: float = .85) -> list[dict]:
    """Measure long silence via FFmpeg; intros/outros are editorially reviewed."""
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-vn", "-af", f"silencedetect=noise=-44dB:d={minimum}",
        "-f", "null", "-",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
    if r.returncode:
        raise RuntimeError("FFmpeg audio read/silence scan failed: " + r.stderr[-500:])
    return [{"start": float(a), "end": float(b), "length": round(float(b)-float(a), 3)}
            for a, b in SILENCE_RE.findall(r.stderr)]


def audit(manifest: dict, audio_file: Path, stage: str = "draft",
          *, duration: float | None = None, silence: list | None = None) -> dict:
    """Pure validation (duration/silence may be injected for unit tests)."""
    errors: list[str] = []
    warnings: list[str] = []
    if stage not in {"draft", "release"}:
        raise ValueError("stage must be 'draft' or 'release'")

    written = manifest.get("canonical_script", "")
    spoken = manifest.get("spoken_script", "")
    if not isinstance(written, str) or not written.strip():
        errors.append("Missing actual display/canonical script")
        written = ""
    if not isinstance(spoken, str) or not spoken.strip():
        errors.append("Missing complete text actually sent to the speech engine")
        spoken = ""
    words = count_words(spoken)
    if words < 3:
        errors.append("Insufficient real spoken text")
    if YEAR_RE.search(spoken):
        errors.append("Speech engine input contains a numeric year: write it out as spoken words")
    if re.search(r"\b\d+(?:/\d+)+\b", spoken):
        errors.append("Ambiguous slash-form numerals in TTS text")
    # Catch artificial hyphenated syllables, but preserve real hyphenated words.
    if re.search(r"\b(?:[A-Z][a-z]{1,4}-){2,}[A-Za-z]+\b", spoken):
        warnings.append("Possible phonetic syllable-splitting; review name fluency")

    if not audio_file.is_file() or audio_file.stat().st_size < 200:
        errors.append("Real audio file absent/empty")
        actual_duration = 0.
        actual_sha = ""
    else:
        actual_sha = sha256(audio_file)
        try:
            actual_duration = float(duration) if duration is not None else media_duration(audio_file)
        except (ValueError, KeyError, subprocess.SubprocessError, OSError) as e:
            errors.append("Could not verify decoded audio length: " + str(e))
            actual_duration = 0.
        if actual_duration <= 0:
            errors.append("Nonpositive audio duration")

    mode = manifest.get("mode", "short")
    if mode not in {"short", "voiceover", "longform", "dialogue", "spoken_asmr"}:
        errors.append("Unknown speech mode")
        mode = "short"
    # By default 170–210 WPM for ALL narration, including longform. A verified
    # need for a slower character/dialogue role is recorded explicitly.
    target = manifest.get("target_wpm", [SHORT_DEFAULT_LO, SHORT_DEFAULT_HI])
    if not isinstance(target, list) or len(target) != 2 or any(
        isinstance(x, bool) or not isinstance(x, (int, float)) for x in target
    ) or not 100 <= target[0] <= target[1] <= 250:
        errors.append("Invalid target_wpm; require [low, high] numeric range")
        target = [SHORT_DEFAULT_LO, SHORT_DEFAULT_HI]
    if target[0] < SHORT_DEFAULT_LO or target[1] > SHORT_DEFAULT_HI:
        exception = manifest.get("pace_exception", {})
        if not isinstance(exception, dict) or not exception.get("approved_by") or not exception.get("reason"):
            errors.append("Pace exception requires a specific reviewer and creative justification")
    wpm = round(60 * words / actual_duration, 2) if actual_duration > 0 else 0
    if wpm and (wpm < target[0] or wpm > target[1]):
        errors.append(f"Measured speaking rate {wpm:.1f} WPM outside chosen {target[0]}–{target[1]}")
    if wpm and (wpm < SHORT_HARD_LO or wpm > SHORT_HARD_HI) and not manifest.get("pace_exception"):
        errors.append(f"Unacceptable default speaking pace {wpm:.1f} WPM; default requires 160–225")
    speed_factor = manifest.get("post_tempo_factor", 1.0)
    if isinstance(speed_factor, bool) or not isinstance(speed_factor, (int, float)) or speed_factor <= 0:
        errors.append("Invalid post_tempo_factor")
        speed_factor = 1.0
    if speed_factor > 1.25:
        errors.append("Pitch-preserving time compression above 1.25x risks robotic phrasing; regenerate faster source")
    elif speed_factor > 1.12:
        warnings.append("Time compression is significant; manually review sibilants, vowel lengths and pacing")

    names = manifest.get("names", [])
    if not isinstance(names, list):
        errors.append("names must be a list of individually checked pronunciation targets")
        names = []
    for index, name in enumerate(names, 1):
        label = f"name[{index}]"
        if not isinstance(name, dict) or not str(name.get("canonical", "")).strip():
            errors.append(f"{label}: missing name")
            continue
        canonical = name["canonical"].strip()
        if canonical.casefold() not in written.casefold():
            errors.append(f"{label}: {canonical!r} not found in canonical script")
        if name.get("checked_against_reference") is not True:
            warnings.append(f"{label}: pronunciation source not independently confirmed")
            if stage == "release":
                errors.append(f"{label}: pronunciation must be checked against a reliable real source")
        if not valid_https(name.get("reference_url")) and name.get("reference_type") != "user_supplied":
            warnings.append(f"{label}: add official/self-pronunciation/native reference URL")
            if stage == "release":
                errors.append(f"{label}: missing verified reference URL or explicit user-supplied source")
        if name.get("listener_verified_correct") is not True:
            warnings.append(f"{label}: actual synthesized name pronunciation still needs listening")
            if stage == "release":
                errors.append(f"{label}: synthesized name not confirmed by human listener")
        speech_form = name.get("spoken_form")
        if speech_form is not None and (not isinstance(speech_form, str) or not speech_form.strip()):
            errors.append(f"{label}: invalid pronunciation variant")
    if not names:
        warnings.append("No proper-name entries supplied; editor must affirm no ambiguous names remain")
        if stage == "release" and manifest.get("no_proper_names_attested") is not True:
            errors.append("No pronunciation inventory: list all names, or affirm there truly are none")

    if manifest.get("commercial_audio_rights_verified") is not True:
        errors.append("Missing recorded commercial-use rights for speech engine/model and any voice source")
    silences = silence if silence is not None else []
    if actual_duration and silence is None:
        try:
            silences = long_silences(audio_file)
        except (OSError, subprocess.SubprocessError, ValueError, RuntimeError) as e:
            errors.append("Audio decoding/silence test failed: " + str(e))
    # Long silence is a warning until an actual editorial review decides if
    # it's purposeful for the scene. Speech gaps without a justified reason fail.
    pauses = [x for x in silences if x.get("length", 0) > .95]
    if pauses:
        warnings.append(f"{len(pauses)} unreviewed silent spans over 950ms: inspect the narration mix")

    review = manifest.get("human_listening_review", {})
    if stage == "release":
        required = ("complete_listen", "natural_conversational_prosody",
                    "all_proper_names_correct", "all_names_inventory_complete",
                    "no_clipped_or_swallowed_words", "matches_picture_and_subtitles")
        if not isinstance(review, dict):
            errors.append("human_listening_review must be completed by an actual listener")
        else:
            if not str(review.get("reviewer", "")).strip():
                errors.append("Human review must name an actual reviewer")
            if len(str(review.get("notes", "")).strip()) < 24:
                errors.append("Human review needs substantive concrete listening notes")
            for field in required:
                if review.get(field) is not True:
                    errors.append("Human listening review missing confirmation: " + field)
            if review.get("audio_sha256", "").lower() != actual_sha:
                errors.append("Listener approval does not match exact final audio hash")
            if pauses and review.get("intentional_pauses_reviewed") is not True:
                errors.append("Unreviewed long gaps are not permitted in release voice")
    return {
        "status": "PASS" if not errors else "FAIL",
        "stage": stage, "errors": errors, "warnings": warnings,
        "duration_seconds": round(actual_duration, 3),
        "spoken_word_count": words, "measured_wpm": wpm,
        "target_wpm": target, "post_tempo_factor": speed_factor,
        "audio_sha256": actual_sha,
        "silences_over_950ms": pauses,
        "human_naturalness_certified": stage == "release" and not errors,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--audio", required=True, type=Path)
    p.add_argument("--stage", choices=("draft", "release"), default="draft")
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    result = audit(json.loads(args.manifest.read_text(encoding="utf-8")),
                   args.audio, args.stage)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
