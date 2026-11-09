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

def process_candidate_parts():
    """Read Parquet source column remotely; transfer image data only for relevant shards."""
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem
    fs = HfFileSystem()
    source_prefix = "datasets/" + DATASET + "/"
    # Museum images are clustered near the final 70 files. Skipping unrelated
    # shards by source-only parquet projection avoids a 200GB full download.
    for i in range(295, 373):
        remote = f"default/train/part-{i:05d}.parquet"
        with fs.open(source_prefix + remote, "rb") as fh:
            pf = pq.ParquetFile(fh)
            source_array = pf.read(columns=["source"]).column(0).to_pylist()
            matched = sum(v in ("met_china", "fsg") for v in source_array)
            if not matched:
                print("SKIP", remote, pf.metadata.num_rows, flush=True)
                continue
            print("TARGET_SHARD", remote, "rows", pf.metadata.num_rows, "target images", matched, flush=True)
            needed = [k for k in ["image", "source", "image_id", "object_no", "title", "artist", "culture", "view_type", "captions"] if k in pf.schema_arrow.names]
            for batch in pf.iter_batches(batch_size=4, columns=needed):
                for meta in batch.to_pylist():
                    part = str(meta.get("source", ""))
                    if part not in PARTS:
                        continue
                    try:
                        raw = meta.get("image")
                        if isinstance(raw, dict):
                            raw = raw.get("bytes")
                        if not isinstance(raw, (bytes, bytearray)):
                            raise ValueError("No embedded JPEG bytes")
                        with Image.open(io.BytesIO(raw)) as img:
                            img = ImageOps.exif_transpose(img).convert("RGB")
                            if img.width < 160 or img.height < 160:
                                raise ValueError("Image too small")
                            img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                            bio = io.BytesIO()
                            img.save(bio, format="JPEG", quality=82, optimize=True, progressive=True)
                            encoded = bio.getvalue()
                            w,h=img.size
                        digest = hashlib.sha256(encoded).hexdigest()
                        if digest in seen:
                            continue
                        seen.add(digest)
                        original_id = str(meta.get("image_id") or digest[:12])
                        image_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in original_id)[:100]
                        cap = meta.get("captions")
                        if isinstance(cap, dict):
                            meta["caption_en"] = str(cap.get("en", cap.get("caption_en", "")))
                        cat = category_for(meta)
                        z = get_zip(part)
                        relative = f"{cat}/{image_id}.jpg"
                        z.writestr(relative, encoded)
                        counts[part] = counts.get(part, 0) + 1
                        index.append({
                            "file": f"{part}/{(counts[part]-1)//PACK_SIZE+1:02d}/{relative}",
                            "source": "Metropolitan Museum of Art" if part == "met_china" else "Smithsonian National Museum of Asian Art / Freer Gallery",
                            "source_license": "CC0-1.0 (image); metadata annotation CC-BY-4.0",
                            "image_id": image_id, "object_no": str(meta.get("object_no", "")),
                            "title": str(meta.get("title", ""))[:320], "artist": str(meta.get("artist", ""))[:220],
                            "view_type": str(meta.get("view_type", "")), "culture": str(meta.get("culture", "")),
                            "category": cat, "sha256": digest,
                            "source_dataset": f"https://huggingface.co/datasets/{DATASET}",
                            "source_file": remote, "width": w, "height": h
                        })
                    except (UnidentifiedImageError, OSError, ValueError) as e:
                        failures.append({"source": remote, "image": str(meta.get("image_id", "")), "error": str(e)[:160]})
        print("COLLECTED_SO_FAR",dict(counts),flush=True)


def main():
    try:
        process_candidate_parts()
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
