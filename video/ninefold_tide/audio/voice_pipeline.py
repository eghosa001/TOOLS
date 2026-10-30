#!/usr/bin/env python3
"""Ninefold Tide voice-director preflight. Pure Python; does not synthesize audio."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import shutil
import sys
import wave
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERIES = ROOT.parent
CORE_CAST = ("naya", "kito", "iri")
CORE_TERMS = ("Naya", "Kito", "Iri", "Maela", "Tovan", "Mastmarket", "Morrow Reach")
QUALITIES = ("naturalness", "emotional_truth", "identity_consistency",
             "intelligibility", "age_authenticity", "pronunciation", "interaction")
LOWEST_ACCEPTED = 4
MINIMUM_MEAN = 4.5


def load(path: Path) -> dict:
    obj = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return obj


def sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as audio:
        for chunk in iter(lambda: audio.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def resolve_file(value: str | None, root: Path) -> Path | None:
    if not value:
        return None
    value = Path(value)
    return value if value.is_absolute() else root / value


def inspect_wav(path: Path) -> dict:
    """Check actual PCM WAV signal and levels; subjective quality is never inferred."""
    with wave.open(str(path), "rb") as wav:
        if wav.getcomptype() != "NONE":
            raise ValueError("Only uncompressed WAV is accepted")
        rate, count, channels, width = wav.getframerate(), wav.getnframes(), wav.getnchannels(), wav.getsampwidth()
        if width != 2 or channels not in (1, 2) or rate < 22050 or count <= 0:
            raise ValueError("Expect nonempty 16-bit mono/stereo PCM at >=22.05 kHz")
        raw = wav.readframes(count)
    samples = array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max((abs(v) for v in samples), default=0)
    clipped = sum(abs(v) >= 32760 for v in samples)
    if peak == 0:
        raise ValueError("WAV contains digital silence only")
    duration = count / rate
    return {"duration_seconds": round(duration, 4), "sample_rate": rate,
            "channels": channels, "peak_dbfs": round(20 * math.log10(min(32768, peak) / 32768), 2),
            "clipped_ratio": round(clipped / max(1, len(samples)), 7),
            "sha256": sha256(path)}


def prepare(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for path in ("cast.json", "pilot_voice_lines.json", "pronunciation_lexicon.json"):
        target = out / path
        if not target.exists():
            shutil.copyfile(ROOT / path, target)
            made.append(path)
    (out / "references").mkdir(exist_ok=True)
    (out / "takes").mkdir(exist_ok=True)
    (out / "reviews").mkdir(exist_ok=True)
    return {"working_directory": str(out), "created": made, "existing_files_preserved": True}


def apply_lexicon(text: str, lexicon: dict, *, strict: bool) -> tuple[str, list[str]]:
    """Only apply previously approved engine-specific speech aliases, not speculative hints."""
    import re
    warnings = []
    result = text
    rows = sorted(lexicon["terms"], key=lambda row: len(row["written"]), reverse=True)
    for row in rows:
        written = row["written"]
        regex = re.compile(r"(?<!\w)" + re.escape(written) + r"(?!\w)", re.IGNORECASE)
        if not regex.search(result):
            continue
        if not row.get("approved"):
            warnings.append(f"Pronunciation not approved: {written}")
        alias = row.get("model_speech_alias")
        if alias and row.get("approved") and row.get("alias_verified"):
            result = regex.sub(lambda match: alias, result)
    if strict and warnings:
        raise ValueError("; ".join(warnings))
    return result, warnings


def check_review(review: dict) -> list[str]:
    errors = []
    scores = review.get("scores") or {}
    for metric in QUALITIES:
        score = scores.get(metric)
        if not isinstance(score, (int, float)) or not LOWEST_ACCEPTED <= score <= 5:
            errors.append(f"{metric} not reviewed at >= {LOWEST_ACCEPTED}/5")
    values = [scores[k] for k in QUALITIES if isinstance(scores.get(k), (int, float))]
    if len(values) == len(QUALITIES) and sum(values) / len(values) < MINIMUM_MEAN:
        errors.append("Mean reviewer score below full-quality threshold")
    if not review.get("reviewed_by") or not review.get("reviewed_on"):
        errors.append("No named human/audio-listening reviewer and date")
    for key in ("heard_complete_clip", "no_robotic_cadence", "no_cloned_real_person",
                "no_pitch_shifted_child", "names_confirmed"):
        if review.get(key) is not True:
            errors.append(f"Review gate not passed: {key}")
    return errors


def audit(cast: dict, lexicon: dict, lines: dict, workspace: Path, stage: str) -> list[str]:
    errors = []
    ids = [c.get("id") for c in cast.get("characters", [])]
    speakers = set(ids)
    if len(ids) != len(set(ids)) or len(ids) != 20:
        errors.append("Cast must have 20 unique canon recurring characters (19 plus Supervisor Ren)")
    lex = [t.get("written") for t in lexicon.get("terms", [])]
    if len(lex) != len(set(lex)) or len(lex) < 30:
        errors.append("Name dictionary missing terms or has duplicates")
    story = load(SERIES / "pilot_shots.json")
    slots = {s["id"]: s for s in story["shots"]}
    expected = {key: val for key, val in slots.items() if val.get("dialogue")}
    planned = lines.get("dialogue_lines", [])
    if len(planned) != len(expected):
        errors.append("Not all speaking pilot shots accounted for")
    for line in planned:
        label = line.get("line_id", "")
        source = expected.get(label)
        if not source:
            errors.append(f"Unknown/duplicate pilot dialogue ID {label}")
            continue
        if line.get("speaker") not in speakers:
            errors.append(f"{label}: missing cast speaker")
        canon = source["dialogue"].split(": ", 1)[-1]
        if line.get("canonical_text") != canon:
            errors.append(f"{label}: canonical screenplay line changed")
        if (line.get("frame_in"), line.get("frame_out")) != (source["start_frame"], source["end_frame"]):
            errors.append(f"{label}: no longer matches director-locked shot")
        if len(line.get("variants", [])) != 3:
            errors.append(f"{label}: needs three different audition approaches")
    if len({x["line_id"] for x in planned}) != len(planned):
        errors.append("Duplicate line IDs")
    if stage == "structure":
        return errors

    cast_map = {c["id"]: c for c in cast["characters"]}
    for name in CORE_CAST:
        person = cast_map.get(name)
        if not person:
            errors.append(f"Missing core character: {name}")
            continue
        ref = person.get("reference") or {}
        clip = resolve_file(ref.get("path"), workspace)
        if not ref.get("approved") or not ref.get("approved_by"):
            errors.append(f"{name}: original voice anchor not auditioned and approved")
        if ref.get("provenance", "").startswith("cloned human"):
            errors.append(f"{name}: real-person reference needs explicit verified rights")
        if clip is None or not clip.is_file():
            errors.append(f"{name}: persistent reference audio missing")
        else:
            try:
                record = inspect_wav(clip)
                if record["sha256"] != ref.get("sha256"):
                    errors.append(f"{name}: reference checksum mismatch")
                if record["clipped_ratio"] > .001:
                    errors.append(f"{name}: reference audio clips")
            except (OSError, ValueError) as exc:
                errors.append(f"{name}: invalid reference WAV {exc}")
    if stage == "casting":
        return errors

    for term in CORE_TERMS:
        entry = next((t for t in lexicon["terms"] if t["written"] == term), None)
        if not entry or not entry.get("approved") or not entry.get("approved_audio_sha256"):
            errors.append(f"Core name pronunciation not listened to and approved: {term}")
    for line in planned:
        label = line["line_id"]
        if not line.get("approved") or not line.get("selected_by"):
            errors.append(f"{label}: no approved natural-performance take")
        take = resolve_file(line.get("selected_take"), workspace)
        if take is None or not take.is_file():
            errors.append(f"{label}: approved WAV does not exist")
            continue
        try:
            w = inspect_wav(take)
            if w["sha256"] != line.get("approved_wav_sha256"):
                errors.append(f"{label}: selected WAV checksum mismatch")
            if w["clipped_ratio"] > .001:
                errors.append(f"{label}: audible digital clipping detected")
            maximum = (line["frame_out"] - line["frame_in"]) / story["fps"]
            if w["duration_seconds"] > maximum:
                errors.append(f"{label}: WAV {w['duration_seconds']}s exceeds {maximum}s shot; "
                              "re-edit timing, do not force pitch/speed")
        except (OSError, ValueError) as exc:
            errors.append(f"{label}: {exc}")
        review_file = resolve_file(line.get("review_path"), workspace)
        if review_file is None or not review_file.is_file():
            errors.append(f"{label}: human comparative review missing")
        else:
            errors.extend(f"{label}: {e}" for e in check_review(load(review_file)))
    return errors


def cli() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("prepare", "audit", "names", "inspect"))
    p.add_argument("--workspace", type=Path, default=SERIES / "workspace" / "04_voice_foley_music")
    p.add_argument("--stage", choices=("structure", "casting", "release"), default="structure")
    p.add_argument("--text", default="")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--wav", type=Path)
    args = p.parse_args()
    try:
        if args.command == "prepare":
            report = prepare(args.workspace)
        elif args.command == "inspect":
            if args.wav is None:
                p.error("--wav is required for inspect")
            report = inspect_wav(args.wav)
        else:
            castfile = args.workspace / "cast.json" if (args.workspace / "cast.json").exists() else ROOT / "cast.json"
            lexfile = args.workspace / "pronunciation_lexicon.json" if (args.workspace / "pronunciation_lexicon.json").exists() else ROOT / "pronunciation_lexicon.json"
            linefile = args.workspace / "pilot_voice_lines.json" if (args.workspace / "pilot_voice_lines.json").exists() else ROOT / "pilot_voice_lines.json"
            cast, lexicon, lines = load(castfile), load(lexfile), load(linefile)
            if args.command == "names":
                normalized, warnings = apply_lexicon(args.text, lexicon, strict=args.strict)
                report = {"display_text": args.text, "model_input_text": normalized, "warnings": warnings}
            else:
                problems = audit(cast, lexicon, lines, args.workspace, args.stage)
                report = {"stage": args.stage, "status": "PASS" if not problems else "BLOCKED",
                          "problems": problems}
                print(json.dumps(report, indent=2))
                return 1 if problems else 0
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as e:
        print(json.dumps({"status": "BLOCKED", "reason": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
