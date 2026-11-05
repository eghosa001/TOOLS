#!/usr/bin/env python3
"""Facts Uncovered: enforce free-authentic-first MANUALLY DIRECTED visual sourcing.

Only real photographs, physical-source scans and camera-captured video may pass.
AI-generated, CGI, 3D/2D rendered and otherwise synthetic visuals are prohibited,
with NO exception or generated-media fallback.
Stage 'plan' requires individual source, origin and commercial-rights evidence.
Stage 'release' also verifies the original asset's SHA-256.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

REAL_KINDS = frozenset({
    "AUTHENTIC_PHOTO", "ARCHIVAL_PHOTO", "HISTORICAL_DOCUMENT",
    "MUSEUM_OBJECT", "REAL_FOOTAGE", "ARCHAEOLOGICAL_RECORD"
})
ALLOWED_ORIGINS = frozenset({"CAMERA_PHOTO", "CAMERA_FILM", "SCAN_OF_PHYSICAL_ORIGINAL"})
BLOCKED_VISUAL_KINDS = frozenset({"AI_ART", "AI_STILL", "AI_VIDEO", "DOCUMENTARY_DIAGRAM",
                                  "ORIGINAL_RECONSTRUCTION_FILM", "CGI", "RENDERED_ANIMATION"})
APPROVED_LICENSES = frozenset({
    "CC0", "CC BY 2.0", "CC BY 3.0", "CC BY 4.0",
    "CC BY-SA 2.0", "CC BY-SA 2.5", "CC BY-SA 3.0", "CC BY-SA 4.0", "PUBLIC DOMAIN", "PDM",
    "COMMERCIAL LICENSE", "PEXELS LICENSE", "PIXABAY CONTENT LICENSE",
})
# A Creative Commons logo is not sufficient to establish derivative or commercial rights.
BLOCKED_LICENSE_PARTS = ("-NC", "-ND", "NONCOMMERCIAL", "NO DERIVATIVES",
                         "EDITORIAL ONLY", "ALL RIGHTS RESERVED")
REQUIRED_ASSET = (
    "source_page_url", "creator", "license", "license_url",
    "file_identity", "attribution", "commercial_use_confirmed",
    "modifications_allowed", "origin_type", "non_synthetic_verified",
    "authentic_capture_verified"
)
REQUIRED_COMMON = (
    "id", "spoken_text", "start_seconds", "end_seconds",
    "shot_subject", "why_this_visual", "visual_kind", "editor_approved_by",
)
LICENSE_DEEDS = {
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC BY 2.0": "https://creativecommons.org/licenses/by/2.0/",
    "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
    "CC BY-SA 2.5": "https://creativecommons.org/licenses/by-sa/2.5/",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "PUBLIC DOMAIN": "https://creativecommons.org/publicdomain/mark/1.0/",
    "PDM": "https://creativecommons.org/publicdomain/mark/1.0/",
    "PEXELS LICENSE": "https://www.pexels.com/legal-pages/license",
    "PIXABAY CONTENT LICENSE": "https://pixabay.com/service/license-summary/",
}

class SourcePolicyError(ValueError):
    pass

def _https(value: object) -> bool:
    return isinstance(value, str) and urlparse(value).scheme == "https" and bool(urlparse(value).netloc)

def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())

def _real_searches(shot: dict) -> list[dict]:
    result = shot.get("authentic_source_searches")
    return result if isinstance(result, list) else []

def check_shot(shot: dict, *, phase: str, root: Path, sha_seen: dict[str, str]) -> list[str]:
    errors = []
    label = shot.get("id", "(no shot id)")
    for key in REQUIRED_COMMON:
        if key not in shot or shot[key] is None or (isinstance(shot[key], str) and not shot[key].strip()):
            errors.append(f"{label}: missing {key}")
    try:
        begin, end = float(shot["start_seconds"]), float(shot["end_seconds"])
        if not 0 <= begin < end: errors.append(f"{label}: invalid timeline interval")
    except (KeyError, TypeError, ValueError):
        errors.append(f"{label}: invalid/missing in/out timecodes")
    kind = shot.get("visual_kind")
    if kind not in REAL_KINDS:
        return errors + [f"{label}: prohibited visual_kind {kind!r}; only real captured photos, physical-source scans and camera footage allowed"]
    if shot.get("editorial_status") != "APPROVED":
        errors.append(f"{label}: individually approved editor shot decision required")
    searches = _real_searches(shot)
    if not searches:
        errors.append(f"{label}: record exact free/open authentic source search first")
    for attempt in searches:
        if not isinstance(attempt, dict) or not _nonempty(attempt.get("query")) or not _https(attempt.get("source_url")) or not _nonempty(attempt.get("outcome")):
            errors.append(f"{label}: invalid search: query, source_url and outcome required")
    # No editorial exception can turn synthetic or generated pixels into original footage.
    asset = shot.get("asset")
    if not isinstance(asset, dict):
        return errors + [f"{label}: real image must have exact selected asset rights ledger"]
    if asset.get("origin_type") not in ALLOWED_ORIGINS:
        errors.append(f"{label}: origin_type must identify real camera film, camera photo or a physical-source scan")
    if asset.get("non_synthetic_verified") is not True or asset.get("authentic_capture_verified") is not True:
        errors.append(f"{label}: independent verification of genuine non-synthetic source required")
    if shot.get("synthetic_media") is True or asset.get("ai_generated") is True:
        errors.append(f"{label}: synthetic/AI-generated source explicitly prohibited")
    for key in REQUIRED_ASSET:
        if key not in asset or asset[key] is None or (isinstance(asset[key], str) and not asset[key].strip()):
            errors.append(f"{label}: missing asset.{key}")
    for key in ("source_page_url", "license_url"):
        if not _https(asset.get(key)):
            errors.append(f"{label}: asset.{key} must be an exact HTTPS rights/source page")
    if not _nonempty(asset.get("file_identity")) or not _nonempty(asset.get("creator")):
        errors.append(f"{label}: specific artifact identity and photographer required")
    license_name = asset.get("license", "")
    if not isinstance(license_name, str):
        license_name = ""
    upper = license_name.upper().strip()
    if any(flag in upper for flag in BLOCKED_LICENSE_PARTS):
        errors.append(f"{label}: noncommercial/ND/editorial-only/restricted images forbidden")
    if upper not in APPROVED_LICENSES:
        errors.append(f"{label}: unknown license {license_name!r}; manually verify commercial reuse")
    elif upper != "COMMERCIAL LICENSE" and asset.get("license_url") != LICENSE_DEEDS[upper]:
        errors.append(f"{label}: wrong license deed URL (must agree with individual image license)")
    if upper in {"PEXELS LICENSE", "PIXABAY CONTENT LICENSE"} and asset.get("usage_context") not in {"TRUTHFULLY_LABELLED_MODERN_ILLUSTRATION", "DIRECTLY_DEPICTED_GENUINE_SUBJECT"}:
        errors.append(f"{label}: commercial stock requires an explicit truthful visual usage_context")
    if upper in {"PEXELS LICENSE", "PIXABAY CONTENT LICENSE"} and not _nonempty(asset.get("asset_page_rights_verified_at")):
        errors.append(f"{label}: stock footage requires dated per-asset license verification")
    if asset.get("usage_context") == "TRUTHFULLY_LABELLED_MODERN_ILLUSTRATION" and not _nonempty(shot.get("on_screen_context_label")):
        errors.append(f"{label}: illustrative footage needs unobtrusive truthful context label")
    if upper == "COMMERCIAL LICENSE" and (
            not _nonempty(asset.get("rights_holder"))
            or not _nonempty(asset.get("license_evidence_ref"))):
        errors.append(f"{label}: paid/commercial licence needs rights holder and retained permission evidence")
    if asset.get("commercial_use_confirmed") is not True:
        errors.append(f"{label}: commercial usage rights not affirmatively checked")
    if asset.get("modifications_allowed") is not True:
        errors.append(f"{label}: no documented derivative/crop permission")
    if "BY" in upper and len(str(asset.get("attribution", "")).strip()) < 20:
        errors.append(f"{label}: incomplete creator/title/source/licence attribution")
    if upper.endswith("SA 4.0") or "BY-SA" in upper:
        if not _nonempty(asset.get("share_alike_compliance")):
            errors.append(f"{label}: CC BY-SA obligations require legal/editorial decision")
    if phase == "release":
        rel = asset.get("local_path")
        value = asset.get("sha256")
        if not _nonempty(rel) or not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value):
            errors.append(f"{label}: missing local file path and sha256 from validated source download")
        else:
            base = root.resolve()
            image = (base / rel).resolve()
            if not image.is_relative_to(base) or not image.is_file():
                errors.append(f"{label}: image missing, unsafe path or outside assets root")
            else:
                digest = hashlib.file_digest(image.open("rb"), "sha256").hexdigest()
                if digest.lower() != value.lower():
                    errors.append(f"{label}: actual image SHA256 differs from approved artifact")
                prior = sha_seen.get(str(image))
                if prior and prior != digest:
                    errors.append(f"{label}: asset changed while validating")
                sha_seen[str(image)] = digest
    return errors

def validate(manifest: dict, *, phase: str = "plan", root: Path = Path(".")) -> dict:
    if phase not in ("plan", "release"): raise ValueError(phase)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("shots"), list):
        raise SourcePolicyError("Manifest must contain editor-authored shots array")
    shots = manifest["shots"]
    if not shots: raise SourcePolicyError("No approved scenes")
    errors = []; sha_seen = {}
    labels = set()
    for shot in shots:
        if not isinstance(shot, dict):
            errors.append("Each shot must be a JSON object"); continue
        if shot.get("id") in labels:errors.append(f"Duplicate shot ID: {shot.get('id')}")
        labels.add(shot.get("id"))
        errors.extend(check_shot(shot, phase=phase, root=root, sha_seen=sha_seen))
    count_real = sum(shot.get("visual_kind") in REAL_KINDS for shot in shots if isinstance(shot, dict))
    count_illustration = 0  # Synthetic or diagram exceptions are prohibited.
    # For the Great Pyramid, authentic footage and photos are plentiful.
    # An explicit film-level editorial requirement avoids a "100% diagrams" workaround.
    min_ratio = manifest.get("min_authentic_shot_share", 0.6)
    if not isinstance(min_ratio, (int, float)) or not .0 <= min_ratio <= 1.:
        errors.append("Invalid min_authentic_shot_share between 0 and 1")
    elif count_real / len(shots) < min_ratio:
        errors.append(
            f"Verified real-source share {count_real}/{len(shots)} below required {min_ratio:.0%}; "
            "never pad with unrelated stock to satisfy target"
        )
    if manifest.get("source_first_editorial_approval") != "APPROVED":
        errors.append("Missing manifest-wide real-source-first editorial approval")
    result = {
      "status": "PASS" if not errors else "FAIL",
      "phase": phase,
      "total_shots": len(shots),
      "authentic_shots": count_real,
      "exceptions": count_illustration,
      "authentic_fraction": round(count_real / len(shots), 4),
      "errors": errors
    }
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--phase", choices=("plan","release"), default="plan")
    p.add_argument("--assets-root", type=Path, default=Path("."))
    p.add_argument("--report", type=Path)
    args=p.parse_args()
    data=json.loads(args.manifest.read_text(encoding="utf-8"))
    result=validate(data,phase=args.phase,root=args.assets_root)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if result["status"] != "PASS":sys.exit(1)

if __name__ == "__main__":main()
