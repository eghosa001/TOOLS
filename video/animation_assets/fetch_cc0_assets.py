#!/usr/bin/env python3
"""Fetch a small, provenance-checked CC0 animation library. No video assembly.

Run locally or in Actions. Archives remain separate: artist-approved staging
must choose actual assets and match visual style before video production.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "cc0_catalog.json"

def fetch(pack: dict, directory: Path, cap_bytes: int) -> dict:
    url = pack["download"]
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"opengameart.org", "www.opengameart.org", "kenney.nl", "www.kenney.nl"}:
        raise ValueError("Unapproved download host: " + url)
    filename = Path(parsed.path).name
    suffix = "." + pack["format"]
    if not filename.lower().endswith(suffix.lower()):
        raise ValueError("File extension not as recorded in catalog: " + filename)
    target = directory / pack["id"] / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    scratch = target.with_suffix(target.suffix + ".partial")
    if target.exists() and target.stat().st_size > 100:
        data = target.read_bytes()
    else:
        last_error = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; FreeCC0AssetCatalog/1.0; personal-library)",
                    "Accept": "application/zip,image/png,application/octet-stream,*/*",
                })
                size = 0
                with urllib.request.urlopen(req, timeout=90) as response, scratch.open("wb") as file:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > cap_bytes:
                            raise ValueError("Asset exceeds per-file safety limit")
                        file.write(chunk)
                scratch.replace(target)
                break
            except (OSError, urllib.error.URLError, ValueError) as ex:
                last_error = str(ex)
                scratch.unlink(missing_ok=True)
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
        else:
            raise RuntimeError(last_error)
        data = target.read_bytes()
    if len(data) < 100 or data[:100].lower().lstrip().startswith((b"<!doctype", b"<html")):
        target.unlink(missing_ok=True)
        raise ValueError("Downloaded HTML/error page rather than asset bytes")
    fmt = pack["format"]
    if fmt == "zip" and not data.startswith(b"PK\\x03\\x04".replace(b"\\x03",bytes([3])).replace(b"\\x04",bytes([4]))):
        # Central directory data descriptors may use another valid PK prefix.
        if not data.startswith(b"PK"):
            target.unlink(missing_ok=True)
            raise ValueError("Not a ZIP archive")
    if fmt == "png" and not data.startswith(bytes([137,80,78,71,13,10,26,10])):
        target.unlink(missing_ok=True)
        raise ValueError("Not a PNG image")
    if fmt == "7z" and not data.startswith(b"7z\\xbc\\xaf'\\x1c".replace(b"\\xbc",bytes([188])).replace(b"\\xaf",bytes([175])).replace(b"\\x1c",bytes([28]))):
        if not data.startswith(b"7z"):
            target.unlink(missing_ok=True)
            raise ValueError("Not a 7z archive")
    return {
        "id": pack["id"], "status": "downloaded", "filename": str(target.relative_to(directory)),
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "license": pack["license"], "creator": pack["creator"],
        "landing": pack["landing"], "source_url": url,
        "film_use": pack["film_use"], "roles": pack["roles"],
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/cc0-animation-assets")
    parser.add_argument("--limit-mib", type=int, default=100)
    args = parser.parse_args()
    directory = Path(args.output).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if catalog.get("schema_version") != 1:
        raise SystemExit("Unexpected catalog schema version")
    packs = catalog["packs"]
    records = []
    total_estimate = sum(p["estimated_mib"] for p in packs)
    if total_estimate > args.limit_mib:
        raise SystemExit("Catalog exceeds configured download budget")
    for pack in packs:
        if pack["license"] != "CC0-1.0":
            raise SystemExit("Non-CC0 item in automatic fetch list: " + pack["id"])
        try:
            result = fetch(pack, directory, cap_bytes=60 * 1024 * 1024)
            print("OK", result["id"], result["bytes"], flush=True)
        except Exception as exc:
            result = {"id": pack["id"], "status": "error", "error": str(exc),
                "source_url": pack["download"], "landing": pack["landing"]}
            print("FAILED", result["id"], str(exc), file=sys.stderr, flush=True)
        records.append(result)
    successful = sum(r["status"] == "downloaded" for r in records)
    report = {"collection": "CC0 multi-genre reusable animation assets",
        "packs_requested": len(packs), "packs_downloaded": successful,
        "packs_failed": len(packs)-successful, "total_bytes":sum(r.get("bytes",0) for r in records),
        "do_not_claim_premium_approval": True,
        "rights_note":"Archive license only covers individual asset reuse; platform monetization and original creative value are separate.",
        "sources":records}
    (directory / "DOWNLOAD_REPORT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    shutil.copyfile(CATALOG,directory/"SOURCE_CATALOG.json")
    if successful < max(1,len(packs)//2):
        raise SystemExit("Too many download failures; no collection approval")
    print("DOWNLOAD_SUMMARY",json.dumps({"ok":successful,"failed":len(packs)-successful,"bytes":report["total_bytes"]}))
if __name__=="__main__":
    main()
