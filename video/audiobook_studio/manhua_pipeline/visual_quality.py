#!/usr/bin/env python3
"""Source-grounded visual contracts and image-review gate for 2D manhua.

This module never asserts that a scene matches speech just because the image
prompt contains the right words. Image evidence must come from an image
reviewer (automated visual comparison or a human), with explicit hold flags.
All source excerpts and QA records remain private.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

# Narrow, literal action hooks. Avoid turning guesses about plot into facts.
OBSERVABLE = {
    "eyes_open": {
        "pattern": r"\b(?:opened?|opening|opens?)\s+(?:his|her|their|the)\s+eyes\b|\beyes\s+(?:opened?|opening)\b",
        "direction": "The subject's EYES ARE OPEN, alert, not closed or meditating with shut eyes",
        "positive": "A young cultivator has his eyes wide open, visibly alert and awakening",
        "negative": "A young cultivator is sitting quietly with his eyes closed in meditation",
        "words": ("eye", "open"),
    },
    "spiritual_aura": {
        "pattern": r"\b(?:spiritual|spirit|mystic|magical)\s+(?:light|energy|aura|glow|power)\b|\b(?:qi|aura)\s+(?:gather|swirl|flow|glow|surge)",
        "direction": "VISIBLE luminous spiritual energy LIGHT gathers around the subject, with glowing trails or particles",
        "positive": "Bright glowing spiritual magical energy ribbons and luminous particles visibly surround the man",
        "negative": "A man in an ordinary room with no glowing energy, no magic and no aura",
        "words": ("light", "glow", "energy"),
    },
    "flames": {
        "pattern": r"\b(?:flames?|fire)\s+(?:burst|erupt|rise|spread|engulf|burn)|\b(?:burning|ablaze)\b",
        "direction": "VISIBLE fire or flames at the location specified by the narration",
        "positive": "Bright visible flames and fire engulf the setting",
        "negative": "A quiet unburned setting with no flames and no fire",
        "words": ("fire", "flame"),
    },
    "weapon_drawn": {
        "pattern": r"\b(?:drew|draws|unsheathed|unsheathes|raised|raises)\s+(?:a|his|her|their|the)\s+(?:sword|blade)\b",
        "direction": "The actor is visibly holding or drawing the sword or blade described in narration",
        "positive": "A person draws and holds an obvious sword or blade",
        "negative": "A person standing empty-handed with no visible sword or blade",
        "words": ("sword", "blade"),
    },
}
SINGLE_ACTOR = re.compile(
    r"\b(?:the|a)\s+(?:young\s+)?(?:cultivator|man|woman|boy|girl|warrior|disciple)\b", re.I)
MULTI_ACTOR = re.compile(
    r"\b(?:two|three|several|multiple|crowd|group|army|companions|together|they|both)\b", re.I)


def requirements_for(source: str) -> list[dict[str, Any]]:
    if not source or not source.strip():
        raise ValueError("A real narration passage is required")
    # Every scene needs at least one pixel-content comparison, even for
    # dialogue, atmosphere, or passages without a recognised action keyword.
    evidence = " ".join(source.split())[:180]
    result = [{
        "id": "narrated_beat",
        "must_show": "Illustrate a real event, character or location in THIS narration",
        "positive": "A specific original full-colour Chinese manhua illustration showing: " + evidence,
        "negative": "An unrelated generic fantasy wallpaper or abstract stock background with no narrated characters, place or action",
    }]
    for key, rule in OBSERVABLE.items():
        if re.search(rule["pattern"], source, re.I):
            result.append({"id": key, "must_show": rule["direction"],
                           "positive": rule["positive"], "negative": rule["negative"]})
    if SINGLE_ACTOR.search(source) and not MULTI_ACTOR.search(source):
        result.append({"id": "single_protagonist",
                       "must_show": "Show ONE protagonist only; no duplicate figures or second copy of the same character",
                       "positive": "One single male or female protagonist is alone in this illustrated scene",
                       "negative": "Two duplicate near-identical main characters stand or sit together in this scene"})
    return result


def source_grounded_prompt(*, passage: str, style: str, brief: str,
                           cast_descriptions: str = "") -> tuple[str, list[dict[str, Any]]]:
    """Visual directions take precedence over potentially vague supplied briefs."""
    obligations = requirements_for(passage)
    # Keep the actual source excerpt in the PRIVATE prompt. Avoid unrelated
    # wardrobe, events, effects or backgrounds that are absent from the story.
    quote = " ".join(passage.split())[:600]
    visual = " ; ".join(r["must_show"] for r in obligations)
    prompt = (
        f"{style}; SINGLE STORY MOMENT, ORIGINAL 2D MANHUA, NOT 3D. "
        f"Exact current narration: {quote}. "
        f"Source-consistent shot idea: {brief.strip() if brief else 'depict this exact narrated action, not generic atmosphere'}. "
        f"REQUIRED ON-SCREEN EVIDENCE: {visual or 'visible concrete action, place, or consequence from the narration'}. "
        f"Known character reference: {cast_descriptions.strip() or 'do not invent an extra character'}. "
        "Make the action legible at thumbnail size. Do not add a second copy of a person, "
        "unmentioned supernatural effects, plot spoilers, captions, or text. "
        "16:9 full-colour polished inked Chinese manhua panel, original, coherent hands and anatomy."
    )
    return prompt[:2200], obligations


def vision_review(image: Path, obligations: list[dict], *, model=None, processor=None) -> dict:
    """Inspect PIXELS with cached CLIP if provided. No model => review still pending.

    CLIP is a contrastive triage tool, not dependable human-quality certification.
    Never infer an image PASS from prompt wording. Keep human approval separate.
    """
    from PIL import Image, ImageStat
    path = Path(image)
    if not path.is_file():
        raise ValueError("Missing actual illustration")
    with Image.open(path) as pic:
        im = pic.convert("RGB")
        width, height = im.size
        # Minimum 16:9 art size and basic degeneracy detection.
        colours = [x for x in ImageStat.Stat(im.resize((96, 54))).stddev]
        technical_ok = width >= 896 and height >= 504 and 1.70 < width / height < 1.86 and min(colours) > 12
        data = {"image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "width": width, "height": height,
                "technical_ok": technical_ok, "requirements": [],
                "manual_review_required": True, "human_approved": False,
                "image_model_verified": bool(model is not None and processor is not None)}
        if not technical_ok:
            data["status"] = "REJECT_BAD_IMAGE"
            return data
        if model is None or processor is None:
            data["status"] = "VISUAL_REVIEW_PENDING"
            data["requirements"] = [{"id": r["id"], "result": "UNVERIFIED_PIXEL_CONTENT"} for r in obligations]
            return data
        import torch
        for rule in obligations:
            options = [rule["positive"], rule["negative"]]
            inputs = processor(text=options, images=im, return_tensors="pt", padding=True)
            device = next(model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.inference_mode():
                logits = model(**inputs).logits_per_image[0]
            probs = logits.softmax(-1).detach().float().cpu().tolist()
            good = float(probs[0])
            state = "MATCH_LIKELY" if good >= 0.72 else "MISMATCH_OR_UNCERTAIN"
            data["requirements"].append({"id": rule["id"], "result": state,
                                         "positive_probability": round(good, 4)})
        data["status"] = ("AUTOMATED_TRIAGE_PASS" if all(
            v["result"] == "MATCH_LIKELY" for v in data["requirements"]
        ) else "NEEDS_SCENE_CORRECTION")
        return data


def thumbnail_contract(*, required_single_protagonist: bool = True) -> list[dict]:
    return ([{"id": "single_protagonist_thumbnail",
              "must_show": "EXACTLY ONE main character, no cloned or doubled protagonist",
              "positive": "A YouTube manhua thumbnail with one single main hero",
              "negative": "A YouTube manhua thumbnail with two duplicate matching main heroes"}]
            if required_single_protagonist else [])


def episode_gate(*, scene_reviews: list[dict], thumbnail_review: dict,
                 scenes_expected: int) -> dict:
    if len(scene_reviews) != scenes_expected or not thumbnail_review:
        raise ValueError("Incomplete actual scene/thumbnail evidence")
    problems = [str(i) for i, r in enumerate(scene_reviews) if r.get("status") != "AUTOMATED_TRIAGE_PASS"]
    if thumbnail_review.get("status") != "AUTOMATED_TRIAGE_PASS":
        problems.append("thumbnail")
    # Even passing model comparisons still requires human listening and visual
    # confirmation before a video may be approved for publication.
    return {"automated_visual_triage_passed": not problems,
            "needs_correction": bool(problems),
            "failed_or_unverified_items": problems,
            "human_visual_review_required": True,
            "human_visual_review_approved": False,
            "ready_for_youtube": False}
