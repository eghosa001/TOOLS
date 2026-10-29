#!/usr/bin/env python3
"""No-credit real vision reviewer for actual Blender contact-sheet frames.

The open Apache-2.0 SmolVLM-256M model analyses real (not generated)
rendered pixels. No GPT/API key, paid video credits, or remote AI inference.
The model is a *suggestion*, never a self-awarded 9/10 signoff.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

MODEL_ID = "HuggingFaceTB/SmolVLM-256M-Instruct"
MODEL_REV = "main"
LABELS = ("GLASSY", "WAXY", "DARK", "OK", "UNKNOWN")


def classify(raw: str) -> str:
    """Handle noise conservatively: only a single unambiguous first label."""
    first = re.search(r"\b(?:GLASSY|WAXY|DARK|OK|UNKNOWN)\b", raw.upper())
    return first.group(0) if first else "UNKNOWN"


def observation_to_command(label: str, present: dict, source_sha: str) -> dict | None:
    """An AI cannot invent Python commands or change baked physics."""
    if label == "GLASSY":
        changes = {
            "gel_roughness": min(.35, round(present["gel_roughness"]*1.13, 4)),
            "gel_transmission": max(.18, round(present["gel_transmission"]*.92, 4)),
            "gel_subsurface": min(.60, round(present["gel_subsurface"]*1.12, 4)),
        }
        reason = "Vision model describes glass-like reflections in real Blender contact frames 1, 70 and 120"
    elif label == "WAXY":
        changes = {
            "gel_subsurface": max(.05, round(present["gel_subsurface"]*.90, 4)),
            "gel_transmission": min(.85, round(present["gel_transmission"]*1.10, 4)),
        }
        reason = "Vision model describes waxy opaque gelatin in real Blender frames 1, 70 and 120"
    elif label == "DARK":
        changes = {"key_light_energy": min(400, round(present["key_light_energy"]*1.10, 4))}
        reason = "Vision model describes inadequately lit tactile detail in Blender frames 1, 70 and 120"
    else:
        return None
    # Prevent nil-change/invalid targets from being presented as actual edits.
    changes = {k:v for k,v in changes.items() if v != present[k]}
    if not changes:
        return None
    from director_commands import validate_directive
    data = {"source_blend_sha256": source_sha, "reason": reason,
            "changes": changes}
    validate_directive(data, present)
    return data


def infer(image_path: Path) -> tuple[str, str]:
    import torch
    from PIL import Image
    from transformers import AutoProcessor, AutoModelForVision2Seq

    torch.set_num_threads(min(4, os.cpu_count() or 2))
    processor = AutoProcessor.from_pretrained(MODEL_ID, revision=MODEL_REV)
    # Do not let the image processor upscale tiny ASMR previews to 2048px:
    # keeps free CPU vision inference bounded and downloads modest.
    processor.image_processor.size = {"longest_edge": 512}
    model = AutoModelForVision2Seq.from_pretrained(
        MODEL_ID, revision=MODEL_REV, torch_dtype=torch.float32,
        _attn_implementation="eager")
    model.eval()
    image = Image.open(image_path).convert("RGB")
    # 3 physical checkpoints stitched side by side; minimal cloud bandwidth.
    image.thumbnail((960, 640))
    question = (
        "This is a three-frame contact sheet from an actual Blender 3D ASMR "
        "video: left frame=1 (rest), middle frame=70 (tool presses jelly), "
        "right frame=120 (release). Examine the jelly material and light. "
        "Which ONE problem is most noticeable? Answer with exactly ONE word "
        "from GLASSY (looks like hard glass), WAXY (looks opaque wax), "
        "DARK (insufficient light to read texture), OK (neither defect), "
        "UNKNOWN (cannot tell). Do not guess if uncertain."
    )
    chat = [{"role":"user","content":[{"type":"image"},{"type":"text","text":question}]}]
    prompt = processor.apply_chat_template(chat, add_generation_prompt=True)
    inputs = processor(text=prompt, images=[image], return_tensors="pt")
    with torch.no_grad():
        tokens = model.generate(**inputs, max_new_tokens=28, do_sample=False)
    reply = processor.batch_decode(tokens[:,inputs["input_ids"].shape[1]:],
                                   skip_special_tokens=True)[0].strip()
    return classify(reply), reply[:350]


def run(image_path: Path, out: Path, context_path: Path | None):
    if not image_path.is_file():
        raise FileNotFoundError("Missing real Blender frame; AI vision may not invent source")
    out.mkdir(parents=True, exist_ok=True)
    label, raw = infer(image_path)
    proof = {
        "vision_model": MODEL_ID,
        "image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        "image_name": image_path.name,
        "model_observation_label": label,
        "raw_model_response": raw,
        "actual_vision_inference_ran": True,
        "artist_quality_score": None,
        "render_approval": False,
        "reason": "Tiny local model is an assistant, NOT a reliable artistic judge",
    }
    if context_path:
        data = json.loads(context_path.read_text(encoding="utf-8"))
        cmd = observation_to_command(label, data["present"],
                                     data["source_blend_sha256"])
        if cmd is not None:
            (out/"director_reviewed_actions.json").write_text(
                json.dumps(cmd, indent=2)+"\n", encoding="utf-8")
            proof["controlled_edit_proposed"] = True
        else:
            proof["controlled_edit_proposed"] = False
    (out/"actual_vision_observation.json").write_text(
        json.dumps(proof, indent=2)+"\n", encoding="utf-8")
    print("ASMR_REAL_LOCAL_VISION_MODEL_RAN",json.dumps(proof), flush=True)
    return proof


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--context", type=Path)
    a = p.parse_args()
    run(a.image, a.output, a.context)
