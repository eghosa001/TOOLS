#!/usr/bin/env python3
"""Import only CC0 Met and Smithsonian Chinese artworks from the public Hugging Face dataset.
Produces organized 1080p-ready JPEG ZIP packs and a provenance index.
Does not upload anything automatically or use noncommercial/research-only components.
"""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import time
import zipfile

import requests
from huggingface_hub import HfApi, hf_hub_url
from PIL import Image, ImageOps, UnidentifiedImageError

DATASET = "kaupane/chinese-painting-collection"
PARTS = ("met_china", "fsg")
DEST = Path("artifacts/mythveil_cc0").resolve()
DEST.mkdir(parents=True, exist_ok=True)
Image.MAX_IMAGE_PIXELS = 180_000_000
HEADERS = {"User-Agent": "MythveilAudiobook/1.0 CC0 public archive importer"}
FIELDNAMES = ["file", "source", "source_license", "image_id", "object_no", "title", "artist", "view_type", "culture", "category", "sha256", "source_dataset", "source_file", "width", "height"]
SCORE_KEYS = {
    "Temple_Palace_City": ("temple", "pagoda", "palace", "pavilion", "building", "architecture", "courtyard", "village", "garden", "bridge", "monastery", "gate", "tower", "hall", "house", "city"),
    "Landscapes_Mountains_Water": ("landscape", "mountain", "river", "waterfall", "mist", "valley", "forest", "lake", "stream", "rock", "peak", "cliff", "snow", "cloud", "coast", "tree"),
    "Characters_Figures": ("figure", "person", "people", "scholar", "warrior", "horseman", "immortal", "monk", "portrait", "emperor", "woman", "man", "deity", "official", "soldier"),
    "Creatures_Animals": ("dragon", "tiger", "horse", "bird", "fish", "deer", "crane", "phoenix", "animal", "cricket", "insect"),
    "Botanicals": ("flower", "plum", "bamboo", "lotus", "blossom", "plant", "orchid", "pine", "peony"),
    "Scrolls_Objects": ("calligraphy", "scroll", "inkstone", "fan", "inscription", "seal", "vase", "brush"),
}
packs = {}
counts = {}
seen = set()
index = []
failures = []
max_count = int(os.getenv("ASSET_TARGET", "0"))
PACK_SIZE = 200

def category_for(meta):
    text = " ".join(str(meta.get(k, "")) for k in ("caption_en", "title")).lower()
    ranks = [(sum(text.count(s) for s in words), name) for name, words in SCORE_KEYS.items()]
    score, category = max(ranks)
    return category if score else "Other_Chinese_Paintings"

def list_shards():
    api = HfApi()
    for part in PARTS:
        files = [x for x in api.list_repo_tree(repo_id=DATASET, repo_type="dataset", path_in_repo=f"data/{part}", recursive=True) if str(getattr(x, "path", "")).endswith(".tar")]
        files = sorted(files, key=lambda x: x.path)
        if not files:
            raise RuntimeError(f"No dataset image shards found for {part}")
        print("SOURCE", part, "SHARDS", [(x.path, getattr(x, "size", None)) for x in files], flush=True)
        for x in files:
            yield part, x.path

def download_shard(path):
    from urllib.parse import quote
    url = hf_hub_url(DATASET, path, repo_type="dataset")
    dst = DEST / ("_source_" + path.split("/")[-2] + "_" + path.split("/")[-1])
    for attempt in range(3):
        try:
            with requests.get(url, stream=True, timeout=(30, 120), headers=HEADERS) as r:
                r.raise_for_status()
                with dst.open("wb") as f:
                    for block in r.iter_content(1024 * 1024):
                        if block:
                            f.write(block)
            if dst.stat().st_size < 1024:
                raise ValueError("Shallow download")
            return dst
        except Exception as e:
            dst.unlink(missing_ok=True)
            print("RETRY", path, repr(e), flush=True)
            if attempt == 2:
                raise
            time.sleep((attempt + 1) * 8)

def get_zip(part):
    count = counts.get(part, 0)
    chunk_id = count // PACK_SIZE + 1
    key = (part, chunk_id)
    if key not in packs:
        filename = f"MYTHVEIL_CC0_{part.upper()}_PART_{chunk_id:02d}.zip"
        packs[key] = zipfile.ZipFile(DEST / filename, "w", compression=zipfile.ZIP_STORED, allowZip64=True)
    return packs[key]

def process_shard(part, path, local):
    global index
    with tarfile.open(local, mode="r:*") as tar:
        members = {Path(m.name).stem: m for m in tar.getmembers() if m.isfile()}
        jpgs = [m for m in tar.getmembers() if m.isfile() and m.name.lower().endswith((".jpg", ".jpeg", ".png"))]
        print("PROCESS", part, path, "images", len(jpgs), flush=True)
        for member in jpgs:
            stem = Path(member.name).stem
            meta = {}
            m = members.get(stem)
            # Sidecar JSON is indexed separately because both files share a stem.
            sidecar = next((x for x in tar.getmembers() if x.isfile() and x.name.endswith("/" + stem + ".json") or x.name == stem + ".json"), None)
            if sidecar:
                try:
                    meta = json.load(tar.extractfile(sidecar))
                except Exception:
                    meta = {}
            try:
                orig = tar.extractfile(member).read()
                with Image.open(io.BytesIO(orig)) as img:
                    img = ImageOps.exif_transpose(img).convert("RGB")
                    if img.width < 160 or img.height < 160:
                        raise ValueError("too small for a video asset")
                    img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                    bio = io.BytesIO()
                    img.save(bio, format="JPEG", quality=82, optimize=True, progressive=True)
                    b = bio.getvalue()
                    w, h = img.size
                digest = hashlib.sha256(b).hexdigest()
                if digest in seen:
                    continue
                seen.add(digest)
                image_id = str(meta.get("image_id") or stem).replace("/", "_").replace("\\", "_")[:100]
                cat = category_for(meta)
                outname = f"{cat}/{image_id}.jpg"
                z = get_zip(part)
                z.writestr(outname, b)
                counts[part] = counts.get(part, 0) + 1
                index.append({
                    "file": f"{part}/{(counts[part]-1)//PACK_SIZE+1:02d}/{outname}",
                    "source": "Metropolitan Museum of Art" if part == "met_china" else "Smithsonian National Museum of Asian Art / Freer Gallery",
                    "source_license": "CC0-1.0 (image); metadata annotation CC-BY-4.0",
                    "image_id": image_id, "object_no": str(meta.get("object_no", "")),
                    "title": str(meta.get("title", ""))[:320], "artist": str(meta.get("artist", ""))[:220],
                    "view_type": str(meta.get("view_type", "")), "culture": str(meta.get("culture", "")),
                    "category": cat, "sha256": digest, "source_dataset": f"https://huggingface.co/datasets/{DATASET}",
                    "source_file": path, "width": w, "height": h
                })
            except (UnidentifiedImageError, OSError, ValueError) as e:
                failures.append({"source": path, "image": stem, "error": str(e)[:120]})
        print("COUNT", part, counts.get(part, 0), flush=True)

def main():
    try:
        for part, path in list_shards():
            if max_count and len(index) >= max_count:
                break
            local = download_shard(path)
            try:
                process_shard(part, path, local)
            finally:
                local.unlink(missing_ok=True)
    finally:
        for pack in packs.values():
            pack.close()
        with (DEST / "MASTER_LICENSE_INDEX.csv").open("w", encoding="utf-8-sig", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=FIELDNAMES)
            wr.writeheader()
            wr.writerows(index)
        (DEST / "README_LICENSES.txt").write_text(
            "MYTHVEIL CC0 CHINESE PAINTING EXPANSION\n"
            "Source: kaupane/chinese-painting-collection on Hugging Face.\n"
            "This release imports ONLY met_china (The Metropolitan Museum of Art) and fsg (Smithsonian Freer Gallery/NMAA), each identified by the dataset as CC0 public-domain images.\n"
            "Images were downscaled (up to 1920 pixels longest side) and JPEG optimized for audiobook video editing. This is not original-resolution backup.\n"
            "Metadata/annotations are CC BY 4.0, dataset credit: kaupane, Chinese Painting Collection (Hugging Face), with source museum identified per image. Museum image rights remain source-defined.\n"
            "Use individual source item license checks for commercial distribution. This collection is not a guarantee of YouTube monetization.\n"
            f"Imported image count: {len(index)}\n"
            "Each ZIP contains category folders and JPG images; MASTER_LICENSE_INDEX.csv records provenance, sha256 and source dataset.\n",
            encoding="utf8"
        )
        (DEST / "IMPORT_REPORT.json").write_text(json.dumps({"target": "all Met+Smithsonian CC0 images", "count": len(index), "per_source": counts, "pack_count": len(packs), "failures": failures[:300], "error_total": len(failures)}, indent=2), encoding="utf8")
        print("FINAL_REPORT", json.dumps({"count": len(index), "per_source": counts, "pack_count": len(packs), "failures": len(failures)}), flush=True)
    if len(index) < 2000:
        raise SystemExit("Collected fewer than 2000 eligible files; inspect report and do not claim completion.")
if __name__ == "__main__":
    main()
