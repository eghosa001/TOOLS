#!/usr/bin/env python3
"""Reuse approved full-color backgrounds and RGBA character cutouts in audiobook scenes.

Safe pre-assembly art stage. Never synthesizes narration, invents timing, finds
assets online, creates new characters, or publishes. Output is compatible with
manhua_pipeline/assemble_existing.py --art-policy full_color_panels.

Manifest is private (episode script and imagery must NOT enter public GitHub).
Usage: python -m video.audiobook_studio.manhua_pipeline.compose_reusable \
         --manifest /private/E04/compositions.json \
         --output /private/E04/composed --source-text /private/E04/spoken.txt
Pillow only. Intended to be added to the existing manhua_pipeline directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps

SIZE = (1920, 1080)
SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$")


def norm(s: str) -> str:
    return " ".join(s.lstrip("\ufeff").split())


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def safe_asset(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts:
        raise ValueError(f"Asset must be a private relative file path: {value}")
    p = (root / value).resolve(strict=True)
    if not p.is_relative_to(root.resolve()) or not p.is_file():
        raise ValueError(f"Unsafe or missing input: {value}")
    if p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError(f"Unsupported image: {value}")
    return p


def unit(x: object, label: str) -> float:
    if not isinstance(x, (int, float)) or isinstance(x, bool) or not 0 <= x <= 1:
        raise ValueError(f"{label} must be a number between 0 and 1")
    return float(x)


def canvas_cover(im: Image.Image, *, zoom: float = 1.0, focus_x: float = .5,
                 focus_y: float = .5) -> Image.Image:
    """True cover-crop; never stretch landscapes or characters."""
    unit(focus_x, "background focus_x")
    unit(focus_y, "background focus_y")
    if not .95 <= zoom <= 1.4:
        raise ValueError("background zoom must be 0.95 to 1.4")
    w, h = im.size
    factor = max(SIZE[0] / w, SIZE[1] / h) * max(1.0, zoom)
    nw, nh = max(SIZE[0], round(w * factor)), max(SIZE[1], round(h * factor))
    im = im.convert("RGB").resize((nw, nh), Image.Resampling.LANCZOS)
    left = round((nw - SIZE[0]) * focus_x)
    top = round((nh - SIZE[1]) * focus_y)
    return im.crop((left, top, left + SIZE[0], top + SIZE[1])).convert("RGBA")


def paint_cast(scene: dict, root: Path, canvas: Image.Image) -> list[dict]:
    identities = []
    for person in scene.get("characters", []):
        if not isinstance(person, dict):
            raise ValueError("Characters must be objects")
        path = safe_asset(root, person.get("file"))
        with Image.open(path) as raw:
            if raw.mode not in ("RGBA", "LA", "P") or "A" not in raw.convert("RGBA").getbands():
                raise ValueError(f"Character cutout must use transparency: {path.name}")
            # Transparent color channels and palette alpha both supported.
            if raw.mode != "RGBA" and (raw.mode != "P" or "transparency" not in raw.info):
                raise ValueError(f"Character cutout has no real alpha: {path.name}")
            actor = raw.convert("RGBA")
        alpha = actor.getchannel("A")
        a0, a1 = alpha.getextrema()
        if a1 < 240 or a0 > 235:
            raise ValueError(f"Not an isolated transparent cutout: {path.name}")
        crop = alpha.getbbox()
        if not crop:
            raise ValueError(f"Empty cutout: {path.name}")
        actor = actor.crop(crop)
        scale = float(person.get("height", .7))
        if not .1 <= scale <= 1.3:
            raise ValueError("Character height must be 0.1 to 1.3 of frame")
        dst_h = round(SIZE[1] * scale)
        dst_w = round(actor.width * dst_h / actor.height)
        if dst_w > 2 * SIZE[0]:
            raise ValueError("Character aspect ratio/scale invalid")
        actor = actor.resize((dst_w, dst_h), Image.Resampling.LANCZOS)
        if person.get("flip", False):
            actor = ImageOps.mirror(actor)
        x = unit(person.get("x", .5), "character x")
        y = unit(person.get("bottom", .98), "character bottom")
        px = round(x * SIZE[0] - dst_w / 2)
        py = round(y * SIZE[1] - dst_h)
        shadow = person.get("shadow", True)
        if shadow:
            # Soft grounded shadow behind approved cutout, not a generated face.
            a = actor.getchannel("A").filter(ImageFilter.GaussianBlur(14))
            shade = Image.new("RGBA", actor.size, (0, 0, 0, 0))
            shade.putalpha(a.point(lambda v: round(v * .35)))
            canvas.alpha_composite(shade, (px + 9, py + 7))
        canvas.alpha_composite(actor, (px, py))
        identities.append({"file": person["file"], "sha256": file_sha(path),
                           "x": x, "bottom": y, "height": scale})
    return identities


def compose(manifest: Path, source: Path, output: Path) -> dict:
    root = manifest.parent.resolve()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    story, episode = data.get("story_id"), data.get("episode_id")
    if not all(isinstance(x, str) and SAFE.fullmatch(x) for x in (story, episode)):
        raise ValueError("Missing/invalid story_id and episode_id")
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("At least one real illustrated scene is required")
    spans = [s.get("source_excerpt", "") for s in scenes if isinstance(s, dict)]
    if len(spans) != len(scenes) or not all(isinstance(s, str) and norm(s) for s in spans):
        raise ValueError("Each scene must provide a real narration excerpt")
    if norm(" ".join(spans)) != norm(source.read_text(encoding="utf-8-sig")):
        raise ValueError("Source mismatch: scene text must cover locked speech exactly")
    # Validate every asset and parameter before creating output files.
    seen = set()
    prepared = []
    for i, s in enumerate(scenes):
        key = s.get("id")
        if not isinstance(key, str) or not SAFE.fullmatch(key) or key in seen:
            raise ValueError(f"Invalid/duplicate scene id at {i}")
        seen.add(key)
        seconds = s.get("seconds")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not .04 <= seconds <= 180:
            raise ValueError(f"Missing measured speech seconds for scene {key}")
        back = safe_asset(root, s.get("background"))
        chars = s.get("characters", [])
        if not isinstance(chars, list):
            raise ValueError("characters must be a list")
        if not chars and not s.get("environment_only", False):
            raise ValueError(f"Scene {key} needs a character or explicit environment_only=true")
        for c in chars:
            if not isinstance(c, dict):
                raise ValueError("Invalid character object")
            safe_asset(root, c.get("file"))
        prepared.append((key, seconds, back, s))
    output.mkdir(parents=True, exist_ok=True)
    receipt_path = output / "PRIVATE_COMPOSITING_RECEIPT.json"
    try:
        previous = json.loads(receipt_path.read_text(encoding="utf-8"))
        cached = previous.get("scene_cache", {})
    except (OSError, ValueError, TypeError):
        cached = {}
    new_cache = {}
    timeline = []
    rendered = 0
    reused = 0
    for key, seconds, back, s in prepared:
        # Cache on exact visuals and source assets, not filename or mtime.
        image_fingerprint = sha(json.dumps({"scene": s, "background_sha256": file_sha(back),
            "characters": [(c["file"], file_sha(safe_asset(root, c["file"])))
                           for c in s.get("characters", [])]}, sort_keys=True).encode("utf-8"))
        final = output / f"{story}_{episode}_{key}.png"
        old = cached.get(key, {}) if isinstance(cached, dict) else {}
        if (final.is_file() and old.get("fingerprint") == image_fingerprint
            and old.get("file_sha256") == file_sha(final)):
            reused += 1
        else:
            with Image.open(back) as raw:
                if raw.width < 1280 or raw.height < 720:
                    raise ValueError(f"Background too small for premium video: {back.name}")
                bg = canvas_cover(raw, zoom=float(s.get("zoom", 1.0)),
                                  focus_x=float(s.get("focus_x", .5)),
                                  focus_y=float(s.get("focus_y", .5)))
            paint_cast(s, root, bg)
            bg.convert("RGB").save(final, optimize=True)
            rendered += 1
        # Existing policy is an objective color gate, not a semantic/rights approval.
        from video.audiobook_studio.manhua_pipeline.color_panel_policy import full_color_check
        full_color_check(final)
        final_sha = file_sha(final)
        new_cache[key] = {"fingerprint": image_fingerprint, "file_sha256": final_sha}
        passage = s["source_excerpt"]
        timeline.append({
            "story_id": story, "episode_id": episode,
            "page_id": s.get("page_id", key), "panel_id": key,
            "image": final.name, "image_sha256": final_sha,
            "source_excerpt": passage,
            "source_sha256": sha(passage.encode("utf-8")),
            "seconds": seconds,
        })
    path = output / "PRIVATE_COMPOSITED_TIMELINE.json"
    path.write_text(json.dumps(timeline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt = {"status": "COMPOSED_ART_ONLY_NOT_A_VIDEO", "story_id": story,
               "episode_id": episode, "scene_count": len(timeline),
               "scenes_rendered": rendered, "scenes_reused_from_cache": reused,
               "total_measured_seconds": sum(x["seconds"] for x in timeline),
               "timeline": str(path), "source_sha256": file_sha(source),
               "human_visual_approval": False,
               "scene_cache": new_cache,
               "note": "Full script, continuity, rights and visual-event QA required; no automatic publication."}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--source-text", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    print(json.dumps(compose(args.manifest, args.source_text, args.output), indent=2))


if __name__ == "__main__":
    main()