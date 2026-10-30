#!/usr/bin/env python3
"""Check actual painted OpenRaster layers before approving a 2D+3D scene.

This is a technical art-readiness gate, NEVER an aesthetic-quality approval.
The real Naya v09 templates in Google Drive include hidden pose/actor guides
and transparent artist layers; a structurally valid .ora is not finished art.
Run on a local/Kaggle copy downloaded privately from the connected Drive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from pathlib import Path

REQUIRED_PAINT_LAYERS = (
    "NAYA FINAL INK + SHADOW",
    "BG PAINT OVER",
    "FOREGROUND ink paint-over",
)
REFERENCE = "https://drive.google.com/file/d/1qTMTUe-GR0O-IFsqvohgP_HAGJSq5-rf/view"
MAX_PNG_BYTES = 24 * 1024 * 1024

def inspect_ora(path: Path) -> dict:
    from PIL import Image
    result = {
        "source_file": str(path),
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "art_source": REFERENCE,
        "required_paint_layers": list(REQUIRED_PAINT_LAYERS),
        "status": "BLOCKED",
        "human_artistic_approval": False,
        "safety_note": "Nontransparent pixels are required for a human art-review submission; they do not prove premium quality.",
        "layers": [],
        "failures": [],
    }
    if not zipfile.is_zipfile(path):
        raise ValueError("OpenRaster input is not a valid ZIP")
    with zipfile.ZipFile(path) as archive:
        if "stack.xml" not in archive.namelist():
            raise ValueError("OpenRaster stack.xml missing")
        root = ET.fromstring(archive.read("stack.xml"))
        w = int(root.attrib["w"])
        h = int(root.attrib["h"])
        result["size"] = [w, h]
        if (w, h) != (1280, 720):
            result["failures"].append("Expected exact camera-locked 1280x720 v09 source")
        found = []
        for layer in root.iter("layer"):
            label = layer.get("name", "")
            imagepath = layer.get("src", "")
            visible = layer.get("visibility", "visible") != "hidden"
            if imagepath not in archive.namelist():
                result["failures"].append("Missing PNG in ORA layer: " + label)
                continue
            info = archive.getinfo(imagepath)
            if info.file_size > MAX_PNG_BYTES:
                result["failures"].append("Unexpectedly large PNG layer: " + label)
                continue
            with Image.open(BytesIO(archive.read(imagepath))) as image:
                rgba = image.convert("RGBA")
                if rgba.size != (w, h):
                    result["failures"].append("Layer dimensions mismatch: " + label)
                alpha = rgba.getchannel("A")
                painted = sum(alpha.histogram()[1:])
                bbox = alpha.getbbox()
            item = {"name": label, "visible": visible, "nontransparent_pixels": painted,
                    "nontransparent_bbox": list(bbox) if bbox else None}
            result["layers"].append(item)
            found.append(item)
            if ("[GUIDE ONLY]" in label or "TEMP guide" in label) and visible:
                result["failures"].append("Temporary actor or motion guide incorrectly visible: " + label)

        for wanted in REQUIRED_PAINT_LAYERS:
            match = [x for x in found if x["name"].casefold().startswith(wanted.casefold())]
            if len(match) != 1:
                result["failures"].append("Missing or duplicated artist paint layer: " + wanted)
            else:
                selected = match[0]
                if not selected["visible"]:
                    result["failures"].append("Artist paint layer hidden: " + wanted)
                if selected["nontransparent_pixels"] < 250:
                    result["failures"].append("Artist paint layer empty or essentially unpainted: " + wanted)

        result["required_paint_layer_count"] = len(REQUIRED_PAINT_LAYERS)
        result["status"] = "READY_FOR_HUMAN_ART_REVIEW" if not result["failures"] else "BLOCKED"
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ora", required=True, type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    try:
        report = inspect_ora(args.ora)
    except (ValueError, ET.ParseError, OSError, zipfile.BadZipFile) as err:
        report = {"status": "BLOCKED", "source_file": str(args.ora),
                  "failures": [type(err).__name__ + ": " + str(err)[:350]],
                  "human_artistic_approval": False}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "READY_FOR_HUMAN_ART_REVIEW" else 2

if __name__ == "__main__":
    sys.exit(main())
