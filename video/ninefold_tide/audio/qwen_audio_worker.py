#!/usr/bin/env python3
"""Run high-quality offline auditions on a real CUDA GPU (e.g. Kaggle T4).

TWO PHASES: design original voices once, then run a separate Base clone model
once to generate all pilot takes. This avoids loading two 1.7B models at once.
No model weights download unless --allow-download is passed explicitly.
Not a voice-approval tool and never mixes final picture or audio.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Set offline environment before importing Hugging Face/torch.
def audio_home():
    return Path(__file__).resolve().parent


def refuse_auto_download(allow: bool):
    if not allow:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"


def prepare_gpu():
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("High-quality model jobs require verified CUDA GPU; do not silently fall back to slow CPU.")
    free, total = torch.cuda.mem_get_info(0)
    if free < 6 * 1024 ** 3:
        raise RuntimeError(f"Less than 6 GiB GPU memory free ({free / 1024**3:.2f} GiB). Stop before loading.")
    return torch, {"name": torch.cuda.get_device_name(0),
                   "total_gib": round(total / 1024 ** 3, 2),
                   "free_gib": round(free / 1024 ** 3, 2)}


def save_wav(path: Path, samples, sr: int):
    import soundfile as sf
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), samples, sr, subtype="PCM_16")


def load_manifest(workspace: Path):
    import voice_pipeline
    cast = voice_pipeline.load(workspace / "cast.json")
    lines = voice_pipeline.load(workspace / "pilot_voice_lines.json")
    lex = voice_pipeline.load(workspace / "pronunciation_lexicon.json")
    return cast, lines, lex


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("gpu-check", "design", "perform"))
    p.add_argument("--workspace", type=Path, default=audio_home().parent / "workspace" / "04_voice_foley_music")
    p.add_argument("--allow-download", action="store_true",
                   help="Explicitly authorize multi-gigabyte pretrained model download, if not cached")
    p.add_argument("--model-path", help="Mounted local model folder or official HuggingFace model ID")
    p.add_argument("--engine", choices=("qwen-base", "chatterbox-turbo", "chatterbox-original"), default="qwen-base")
    p.add_argument("--characters", default="naya,kito,iri",
                   help="Comma-separated cast IDs, or 'all'; default only first pilot cast to save downloads")
    p.add_argument("--takes-per-line", type=int, default=3)
    p.add_argument("--name-drills", action="store_true", help="Also audition recurring names across characters")
    args = p.parse_args()
    refuse_auto_download(args.allow_download)
    torch, gpu = prepare_gpu()
    if args.mode == "gpu-check":
        print(json.dumps({"CUDA": gpu, "note": "GPU available; model compatibility and performance not yet tested."}, indent=2))
        return
    if not args.workspace.exists():
        raise RuntimeError("First run voice_pipeline.py prepare --workspace OUTPUT")
    cast, lines, lex = load_manifest(args.workspace)
    from voice_pipeline import apply_lexicon, inspect_wav
    people = {person["id"]: person for person in cast["characters"]}
    wanted = set(people) if args.characters == "all" else set(args.characters.split(","))
    if not wanted <= set(people):
        raise ValueError(f"Unknown character IDs: {sorted(wanted - set(people))}")

    if args.mode == "design":
        from qwen_tts import Qwen3TTSModel
        model_id = args.model_path or "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
        model = Qwen3TTSModel.from_pretrained(
            model_id, device_map="cuda:0", dtype=torch.float16, attn_implementation="sdpa")
        results = []
        for id in sorted(wanted):
            person = people[id]
            output = args.workspace / "references" / f"{id}_unapproved.wav"
            if output.exists():
                results.append({"id": id, "skipped": True, "reason": "existing voice reference preserved"})
                continue
            # A designed original voice is not a clone of any human performer.
            waves, sr = model.generate_voice_design(
                text=person["reference_text"], language="English",
                instruct=person["voice_design_prompt"])
            save_wav(output, waves[0], sr)
            evidence = inspect_wav(output)
            person["reference"].update({
                "path": str(output.relative_to(args.workspace)), "sha256": evidence["sha256"],
                "sample_rate": sr, "generated_with": model_id,
                "provenance": "original synthetic voice design; no real human voice impersonated",
                "approved": False, "approved_by": None,
            })
            results.append({"id": id, "path": str(output), "evidence": evidence,
                            "approved": False})
        (args.workspace / "cast.json").write_text(json.dumps(cast, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "UNAPPROVED_CANDIDATES_ONLY", "designs": results}, indent=2))
        return

    if not 1 <= args.takes_per_line <= 5:
        raise ValueError("Use between one and five purposeful audition takes per line")
    chosen_lines = [line for line in lines["dialogue_lines"] if line["speaker"] in wanted]
    if args.name_drills:
        for drill in lines["pronunciation_drills"]:
            if drill["speaker"] not in wanted:
                continue
            chosen_lines.append({
                "line_id": drill["id"], "speaker": drill["speaker"],
                "canonical_text": drill["text"], "frame_in": 0, "frame_out": 600,
                "variants": [
                    "Name pronunciation in relaxed speech; not performed as isolated words",
                    "Name pronunciation while calling across a room",
                    "Name pronunciation with concern and urgency"
                ],
            })
    if not chosen_lines:
        raise RuntimeError("No matching pilot lines")
    import soundfile as sf
    from voice_pipeline import sha256

    model_id = args.model_path
    if args.engine == "qwen-base":
        from qwen_tts import Qwen3TTSModel
        model_id = model_id or "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
        model = Qwen3TTSModel.from_pretrained(
            model_id, device_map="cuda:0", dtype=torch.float16, attn_implementation="sdpa")
    elif args.engine == "chatterbox-turbo":
        from chatterbox.tts_turbo import ChatterboxTurboTTS
        model_id = "ResembleAI/chatterbox-turbo" if not model_id else model_id
        if args.model_path:
            raise ValueError("Chatterbox local model-dir loader not verified; use default cached checkpoint")
        model = ChatterboxTurboTTS.from_pretrained(device="cuda")
    else:
        from chatterbox.tts import ChatterboxTTS
        model_id = "ResembleAI/chatterbox" if not model_id else model_id
        if args.model_path:
            raise ValueError("Chatterbox local model-dir loader not verified; use default cached checkpoint")
        model = ChatterboxTTS.from_pretrained(device="cuda")

    ref_prompts = {}
    for id in wanted:
        if not any(l["speaker"] == id for l in chosen_lines):
            continue
        person = people[id]
        source = person["reference"]
        ref = args.workspace / str(source.get("path"))
        if not ref.is_file() or sha256(ref) != source.get("sha256"):
            raise RuntimeError(f"Reference missing or changed for {id}; design voice and lock its checksum first")
        if args.engine == "qwen-base":
            ref_prompts[id] = model.create_voice_clone_prompt(
                ref_audio=str(ref), ref_text=person["reference_text"],
                x_vector_only_mode=False)
        else:
            ref_prompts[id] = str(ref)

    output_manifest = []
    for line in chosen_lines:
        text, problems = apply_lexicon(line["canonical_text"], lex, strict=False)
        for take_index in range(1, args.takes_per_line + 1):
            output = args.workspace / "takes" / f"{line['line_id']}_{args.engine}_take{take_index:02d}.wav"
            if output.exists():
                output_manifest.append({"line_id": line["line_id"], "take": take_index,
                                        "skipped": True, "reason": "cached WAV preserved"})
                continue
            # Sampling changes are an AUDITION, not guaranteed emotional direction.
            # Qwen3 Base generate_voice_clone does NOT expose a reliable per-line
            # instruct channel; use Chatterbox original as an alternative audition.
            seed = 20261030 + take_index * 101 + int(line["line_id"].split("_")[-1])
            torch.manual_seed(seed)
            if args.engine == "qwen-base":
                waves, sr = model.generate_voice_clone(
                    text=text, language="English", voice_clone_prompt=ref_prompts[line["speaker"]])
                signal = waves[0]
            elif args.engine == "chatterbox-turbo":
                wav = model.generate(text, audio_prompt_path=ref_prompts[line["speaker"]])
                signal, sr = wav.squeeze().detach().float().cpu().numpy(), model.sr
            else:
                wav = model.generate(text, audio_prompt_path=ref_prompts[line["speaker"]],
                                     exaggeration=(0.4, 0.6, 0.72)[(take_index - 1) % 3],
                                     cfg_weight=0.35)
                signal, sr = wav.squeeze().detach().float().cpu().numpy(), model.sr
            save_wav(output, signal, sr)
            info = inspect_wav(output)
            max_len = (line["frame_out"] - line["frame_in"]) / 24
            output_manifest.append({
                "line_id": line["line_id"], "cast": line["speaker"], "take": take_index,
                "engine": args.engine, "model_id": model_id,
                "seed": seed, "file": str(output), "sha256": info["sha256"],
                "duration_seconds": info["duration_seconds"], "fits_existing_shot": info["duration_seconds"] <= max_len,
                "provisional_name_warnings": problems, "acting_direction": line["variants"][take_index - 1],
                "acting_direction_applied_by_engine": False,
                "human_approved": False,
                "notice": "No emotion was guaranteed by sampling; editor must listen, select or rerender.")
    path = args.workspace / "reviews" / f"auditions_{args.engine}.json"
    if path.exists():
        raise FileExistsError(f"Review manifest exists: {path}; preserve review history")
    path.write_text(json.dumps({"engine": args.engine, "candidates": output_manifest}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "UNAPPROVED_WAV_AUDITIONS_ONLY",
                      "candidate_count": len(output_manifest), "review_manifest": str(path),
                      "note": "No voice may be released without a full human audio review."}, indent=2))


if __name__ == "__main__":
    main()
