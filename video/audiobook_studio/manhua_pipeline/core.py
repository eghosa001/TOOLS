#!/usr/bin/env python3
"""Story-unlimited, original-fiction manhua audiovisual planning and private packaging.

No manuscript, image or spoken words are ever sent to public GitHub by this module.
No chapter is silently re-written or cut to satisfy a runtime quota.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path
import zipfile

SCHEMA = "audiobook-manhua-v1"
BUNDLE = "MANHUA_STORY_PACKAGE.zip"
VOICE = "audiobook_ryan_qwen_1p7b_approved_2026_11_06_v1"
STYLES = {
    "cultivation": "original polished Chinese manhua, xianxia fantasy, ink-defined outlines, elegant silk robes, architectural scale, refined cel shading",
    "dark_fantasy": "original mature dark fantasy manhua, strong silhouettes, inked contours, painterly shadows, controlled muted color",
    "urban": "original modern urban manhua, clean line art, cinematic comic panels, grounded streets and clothing, restrained shading",
    "apocalypse": "original survival manhua, post-apocalyptic urban ruins, gritty ink linework, atmospheric lighting, practical equipment",
    "science_fiction": "original science fiction manhua, precise hard-surface design, rich atmosphere, graphic-novel linework, readable technology",
    "mystery": "original mystery manhua, grounded interiors, expressive faces, dramatic shadows, subtle visual clues",
    "romance": "original romantic drama manhua, refined expressions, graceful contemporary design, natural light and color",
    "generic": "original high-quality Asian graphic novel, 2D hand-drawn illustration, cinematic composition, professional ink and coloring",
}
NEGATIVE = "3d render, photorealistic, cgi, plastic skin, watermark, captions, text, comic lettering, logo, extra fingers, duplicated person, sloppy anatomy, blurry, low quality"
SLUG = re.compile(r"^[a-z][a-z0-9-]{1,62}$")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_slug(value: str) -> str:
    if not SLUG.fullmatch(value):
        raise ValueError("Story ID must be lower-case kebab-case, 2–63 characters")
    return value


def read_text(path: Path) -> str:
    """Read approved source without modifying its narrative or guessing an edition."""
    path = Path(path)
    if path.suffix.lower() in (".txt", ".md"):
        text = path.read_text(encoding="utf-8-sig")
    elif path.suffix.lower() == ".docx":
        from docx import Document
        text = "\n\n".join(p.text for p in Document(str(path)).paragraphs if p.text.strip())
    else:
        raise ValueError("Supported private story source: .txt, .md, .docx")
    if not text.strip():
        raise ValueError("Story source is empty")
    return text


def split_chunks(text: str, *, max_words: int = 170) -> list[dict]:
    """Sentence-aligned Qwen chunks; source words/order remain unchanged."""
    if not 100 <= max_words <= 230:
        raise ValueError("Narration chunk size must be 100–230 words")
    paras = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    sentences = []
    for p in paras:
        sentences.extend(s.strip() for s in re.split(r'(?<=[.!?])\s+(?=["“‘(]?[A-Z0-9])', p) if s.strip())
    if not sentences:
        raise ValueError("No narration")
    result, buffer, words = [], [], 0
    for sentence in sentences:
        count = len(sentence.split())
        if count > max_words:
            raise ValueError("Long uninterrupted sentence exceeds safe Qwen chunk size")
        if buffer and words + count > max_words:
            result.append({"index": len(result), "text": " ".join(buffer), "words": words})
            buffer, words = [], 0
        buffer.append(sentence)
        words += count
    if buffer:
        result.append({"index": len(result), "text": " ".join(buffer), "words": words})
    source_norm = " ".join(" ".join(text.split()).split())
    output_norm = " ".join(" ".join(r["text"] for r in result).split())
    if source_norm != output_norm:
        raise RuntimeError("Narration chunking lost or changed manuscript text")
    return result


def scene_plan(chunks: list[dict], *, style: str, characters: list[dict] | None = None,
               target_words: int = 185, briefs: list[str] | None = None) -> list[dict]:
    """Source-grounded beats, never a fixed 20-image/story cap."""
    if style not in STYLES:
        raise ValueError("Unrecognized style preset")
    if not chunks:
        raise ValueError("No narration chunks")
    descriptions = [c.get("visual_description", "") for c in characters or []]
    cast_hint = "; ".join(str(v)[:180] for v in descriptions if v)[:500]
    scenes = []
    start, total = 0, 0
    for i, chunk in enumerate(chunks):
        total += chunk["words"]
        if total >= target_words or i == len(chunks) - 1:
            batch = chunks[start:i + 1]
            text = " ".join(c["text"] for c in batch)
            brief = briefs[len(scenes)] if briefs and len(briefs) > len(scenes) else ""
            # Story evidence is kept in a PRIVATE manifest; never put excerpts in GitHub logs.
            excerpt = " ".join(text.split()[:84])
            subject = brief.strip() if brief else "Accurately portray one concrete moment or setting from: " + excerpt
            prompt = (f"{STYLES[style]}; {subject}. "
                      f"Character continuity: {cast_hint or 'follow approved story character designs'}. "
                      "16:9 scenic comic panel, no typography, coherent anatomy and architecture")
            scenes.append({"scene": len(scenes), "start_chunk": start, "end_chunk": i+1,
                           "source_sha256": digest(text.encode()), "prompt": prompt[:1300],
                           "needs_editorial_visual_review": not bool(brief),
                           "key": digest(json.dumps([style, prompt, start, i+1], sort_keys=True).encode())[:20]})
            start, total = i+1, 0
    return scenes


def create_package(*, story_id: str, title: str, manuscript: Path,
                   episodes: dict[int, Path], output: Path, style="cultivation",
                   characters: list[dict] | None = None, references: dict[str, Path] | None = None,
                   source_approved=False, image_model_rights_reviewed=False,
                   thumbnail_hook: str | None = None,
                   scene_briefs: dict[int, list[str]] | None = None) -> dict:
    validate_slug(story_id)
    if style not in STYLES or not title.strip() or not episodes:
        raise ValueError("Story title, valid genre preset and episode(s) are required")
    if not source_approved:
        raise ValueError("Owner-approved story source required before making a production package")
    full = read_text(manuscript)
    characters = characters or []
    for ch in characters:
        if not isinstance(ch, dict) or not ch.get("id") or not ch.get("visual_description"):
            raise ValueError("Characters need stable id and story-accurate visual_description")
        validate_slug(ch["id"])
    if len(set(c["id"] for c in characters)) != len(characters):
        raise ValueError("Duplicate character identities")
    if sorted(episodes) != list(range(1, len(episodes)+1)):
        raise ValueError("Episodes must be consecutive from 1")
    parts = [read_text(episodes[i]) for i in sorted(episodes)]
    if " ".join(" ".join(parts).split()) != " ".join(full.split()):
        raise ValueError("Episode sources must exactly cover the complete manuscript in order")
    stored = {}
    for no, text in enumerate(parts, 1):
        stored[f"episodes/ep{no:03}.txt"] = text.encode("utf-8")
    meta = {"schema": SCHEMA, "story_id": story_id, "title": title, "style": style,
            "full_source_sha256": digest(full.encode()), "source_approved": True,
            "voice_profile": VOICE, "image_model_rights_reviewed": bool(image_model_rights_reviewed),
            "characters": characters,
            "episodes": [{"number": i, "file": f"episodes/ep{i:03}.txt",
                          "sha256": digest(parts[i-1].encode())} for i in sorted(episodes)]}
    ref_meta = {}
    for key, file in sorted((references or {}).items()):
        if not SLUG.fullmatch(key):
            raise ValueError("Reference key must be safe and stable")
        p = Path(file)
        if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            raise ValueError("References must be original image files")
        raw = p.read_bytes()
        stored[f"references/{key}{p.suffix.lower()}"] = raw
        ref_meta[key] = {"file": f"references/{key}{p.suffix.lower()}", "sha256": digest(raw)}
    meta["references"] = ref_meta
    meta["thumbnail_hook"] = (thumbnail_hook or title).strip()[:100]
    meta["scene_briefs"] = {}
    for number, briefs in (scene_briefs or {}).items():
        if number not in episodes or not isinstance(briefs, list) or not all(isinstance(b, str) and b.strip() for b in briefs):
            raise ValueError("Invalid source-grounded scene briefs for episode")
        meta["scene_briefs"][str(number)] = briefs
    output = Path(output)
    if output.suffix.lower() != ".zip":
        raise ValueError("Private package must be .zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as z:
        for name, raw in sorted(stored.items()):
            z.writestr(name, raw, compress_type=zipfile.ZIP_STORED if name.startswith("references/") else zipfile.ZIP_DEFLATED)
        z.writestr("manifest.json", json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


def open_package(archive: Path, *, expected_story_id: str, episode: int) -> tuple[dict, str, dict[str, bytes]]:
    """Never extract arbitrary ZIP paths; read only declared files, verify hashes."""
    validate_slug(expected_story_id)
    with zipfile.ZipFile(archive) as z:
        if any(n.startswith("/") or ".." in Path(n).parts or "\\" in n for n in z.namelist()):
            raise ValueError("Unsafe private archive path")
        meta = json.loads(z.read("manifest.json"))
        if (meta.get("schema") != SCHEMA or meta.get("story_id") != expected_story_id
                or meta.get("voice_profile") != VOICE or meta.get("source_approved") is not True):
            raise ValueError("Wrong, unapproved or incompatible source package")
        episodes = meta.get("episodes") or []
        if not isinstance(episode, int) or episode < 1 or episode > len(episodes):
            raise ValueError("Requested episode is absent")
        item = episodes[episode - 1]
        if item.get("number") != episode:
            raise ValueError("Episode ordering wrong")
        raw = z.read(item["file"])
        if digest(raw) != item.get("sha256"):
            raise ValueError("Episode manuscript changed")
        refs = {}
        for name, record in meta.get("references", {}).items():
            data = z.read(record["file"])
            if digest(data) != record.get("sha256"):
                raise ValueError("Character reference changed")
            refs[record["file"]] = data
    return meta, raw.decode("utf-8"), refs


def cli() -> None:
    parser = argparse.ArgumentParser(description="Private unlimited-story manhua package builder")
    parser.add_argument("--story-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--manuscript", type=Path, required=True)
    parser.add_argument("--episode", action="append", required=True, help="N:episode.txt (all parts, sequential, exact coverage)")
    parser.add_argument("--style", choices=STYLES.keys(), default="cultivation")
    parser.add_argument("--characters-json", type=Path)
    parser.add_argument("--thumbnail-hook", help="Owner-approved source-accurate thumbnail text")
    parser.add_argument("--scene-briefs-json", type=Path,
                        help="Optional private JSON: episode number -> ordered story-grounded visual briefs")
    parser.add_argument("--reference", action="append", default=[], help="character-id=/private/portrait.png")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--confirm-approved-private", action="store_true")
    parser.add_argument("--confirm-image-rights", action="store_true")
    args = parser.parse_args()
    eps, refs = {}, {}
    for item in args.episode:
        number, sep, name = item.partition(":")
        if not sep or not number.isdecimal() or int(number) in eps:
            parser.error("Each --episode must be unique N:path")
        eps[int(number)] = Path(name)
    for item in args.reference:
        key, sep, name = item.partition("=")
        if not sep or key in refs:
            parser.error("Each --reference must be unique character-id=path")
        refs[key] = Path(name)
    people = json.loads(args.characters_json.read_text()) if args.characters_json else []
    briefs = json.loads(args.scene_briefs_json.read_text()) if args.scene_briefs_json else {}
    briefs = {int(k): v for k, v in briefs.items()}
    result = create_package(story_id=args.story_id, title=args.title, manuscript=args.manuscript,
                            episodes=eps, output=args.out, style=args.style, characters=people,
                            references=refs, source_approved=args.confirm_approved_private,
                            image_model_rights_reviewed=args.confirm_image_rights,
                            thumbnail_hook=args.thumbnail_hook, scene_briefs=briefs)
    print(json.dumps({"package": args.out.name, "story_id": result["story_id"],
                      "episodes": len(result["episodes"]), "private": True}))


if __name__ == "__main__":
    cli()