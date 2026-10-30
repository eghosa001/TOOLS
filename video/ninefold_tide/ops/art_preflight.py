#!/usr/bin/env python3
"""Fail-closed, offline intake for Ninefold Tide E101 CAM03B.
No video assembly, media downloads, new artwork, or creative self-approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import zipfile
import xml.etree.ElementTree as ET

CANON = {
    "v07_sha256": "98c5f655860f53d68019605955f3c5e3951b139eb1570153f9fb1cf1a7655e91",
    "nested_v05_sha256": "24c0fb2ae611b4ba50792eb20abc6e192df016401dfa94e0b1eef452dfb77d2c",
    "cam_name": "CAM_03B",
    "cam_xyz": [10.0, -1.7, 6.4],
    "look_at": [2.1, -3.17, 4.15],
    "naya_root": [2.1, -3.17, 3.355],
    "hand_target": [2.36, -2.685, 4.16],
    "model_heights_m": {"naya": 1.64, "kito": 1.45, "iri": 1.72},
    "frame": {"width": 1280, "height": 720, "fps": 24},
}
GATES = (
    "painted_background", "naya_five_view_model", "drawn_naya_contact_pose",
    "hand_rail_overlap", "foot_ground_contact", "original_art_rights",
    "facial_acting_keys", "voice_take_listened", "camera_composite_review",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("top-level JSON must be an object")
    return data


def safe_zip(path: Path) -> list[str]:
    """Inspect untrusted archive metadata only; never extract ZIP members."""
    with zipfile.ZipFile(path) as source:
        names = source.namelist()
        for member in source.infolist():
            name = PurePosixPath(member.filename.replace("\\", "/"))
            if name.is_absolute() or ".." in name.parts or not name.parts:
                raise ValueError("unsafe archive member path")
            if member.file_size > 256_000_000 or member.compress_size > 256_000_000:
                raise ValueError("oversized archive member")
        return names


def inspect_transfer(path: Path | None) -> tuple[dict, list[str]]:
    if path is None or not path.is_file():
        return {"present": False, "validated": False}, ["v07 source transfer ZIP is not locally mounted"]
    issues = []
    try:
        names = safe_zip(path)
        builder = any(x.endswith("BUILD_2D_GREASE_PENCIL_WORKSPACE_v07.py") for x in names)
        foundation = any(x.endswith("NINEFOLD_Production_Foundation_v05_Blender_GLTF_Assets.zip") for x in names)
        if not builder:
            issues.append("v07 Grease Pencil stage builder absent from archive")
        if not foundation:
            issues.append("v05 foundation GLB ZIP absent from archive")
        actual = sha256(path)
        if actual != CANON["v07_sha256"]:
            issues.append("v07 archive SHA-256 differs from prior verified transfer")
        return {
            "present": True, "sha256": actual, "builder_present": builder,
            "foundation_present": foundation, "validated": not issues
        }, issues
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        return {"present": True, "validated": False}, ["transfer archive rejected: " + str(exc)]


def inspect_ora(path: Path | None) -> tuple[dict, list[str]]:
    if path is None or not path.is_file():
        return {"present": False, "layered": False}, ["v08 Krita/OpenRaster editable template not mounted"]
    issues = []
    try:
        names = safe_zip(path)
        with zipfile.ZipFile(path) as source:
            if "mimetype" not in names or source.read("mimetype") != b"image/openraster":
                issues.append("OpenRaster mimetype is incorrect")
            if "stack.xml" not in names:
                issues.append("OpenRaster stack.xml missing")
                return {"present": True, "layered": False}, issues
            tree = ET.fromstring(source.read("stack.xml"))
            dims = [int(tree.attrib.get("w", 0)), int(tree.attrib.get("h", 0))]
            layers = []
            for layer in tree.iter("layer"):
                name = layer.attrib.get("name", "")
                src = layer.attrib.get("src", "")
                visibility = layer.attrib.get("visibility", "visible")
                layers.append({"name": name, "src": src, "visibility": visibility})
                if src not in names:
                    issues.append("Missing ORA layer image: " + src)
            if dims != [1280, 720]:
                issues.append("template dimensions mismatch v08 camera")
            if len(layers) < 4:
                issues.append("expected separate background, actor, shadow and foreground layers")
            if any("TEMP" in x["name"].upper() and x["visibility"] != "hidden" for x in layers):
                issues.append("temporary character scale guide is VISIBLE")
            return {
                "present": True, "sha256": sha256(path), "dimensions": dims,
                "layers": layers, "layered": bool(layers) and not issues
            }, issues
    except (OSError, zipfile.BadZipFile, ET.ParseError, ValueError, KeyError) as exc:
        return {"present": True, "layered": False}, ["ORA rejected: " + str(exc)]


def near_vec(actual, expected, tolerance=0.015) -> bool:
    return isinstance(actual, (list, tuple)) and len(actual) == len(expected) and all(
        isinstance(a, (int, float)) and math.isfinite(a) and abs(a - b) <= tolerance
        for a, b in zip(actual, expected)
    )


def inspect_blender(path: Path | None) -> tuple[dict, list[str]]:
    if path is None or not path.is_file():
        return {"present": False, "checked": False}, ["no actual Blender 4.5 scene probe JSON supplied"]
    issues = []
    try:
        v = read_json(path)
        version = v.get("blender_version", [0, 0, 0])
        if not isinstance(version, list) or len(version) < 2 or version[:2] < [4, 5]:
            issues.append("Blender 4.5+ GPv3 runtime not verified")
        if v.get("active_camera") != CANON["cam_name"]:
            issues.append("active camera is not CAM_03B")
        for key in ("cam_xyz", "look_at", "naya_root", "hand_target"):
            if not near_vec(v.get(key), CANON[key]):
                issues.append("camera or actor geometry mismatch: " + key)
        if v.get("resolution") != [1280, 720] or v.get("fps") != 24:
            issues.append("preview camera dimensions or frame rate do not match v08")
        for actor, height in CANON["model_heights_m"].items():
            spec = (v.get("actors") or {}).get(actor, {})
            if abs(float(spec.get("height_m", 0)) - height) > 0.015:
                issues.append(actor + " physical height wrong")
            if spec.get("grease_pencil_layers", 0) < 9:
                issues.append(actor + " has fewer than 9 GPv3 layers")
            if spec.get("is_2d") is not True:
                issues.append(actor + " final actor is not Grease Pencil 2D")
        if v.get("temporary_actor_planes_visible") is not False:
            issues.append("temporary PNG or 3D actor proxies remain visible")
        if v.get("distinct_rope_systems") != 3:
            issues.append("three distinct rope systems are not identified")
        return {
            "present": True, "checked": not issues,
            "blender_version": version, "active_camera": v.get("active_camera")
        }, issues
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return {"present": True, "checked": False}, ["Blender probe invalid: " + str(exc)]


def inspect_approvals(path: Path | None) -> tuple[dict, list[str]]:
    if path is None or not path.is_file():
        return {"present": False, "approved": False}, ["named artist/director signoffs have not been supplied"]
    issues = []
    try:
        record = read_json(path)
        values = record.get("gates") or {}
        for gate in GATES:
            evidence = values.get(gate) or {}
            if (evidence.get("approved") is not True
                    or not evidence.get("reviewer")
                    or not evidence.get("evidence_path")):
                issues.append("no human-approved evidence for: " + gate)
            elif not Path(evidence["evidence_path"]).is_file():
                issues.append("approved evidence file missing: " + gate)
        return {"present": True, "approved": not issues,
                "gates_passed": len(GATES) - len(issues)}, issues
    except (OSError, ValueError, TypeError) as exc:
        return {"present": True, "approved": False}, ["approvals invalid: " + str(exc)]


def audit(transfer=None, ora=None, blender=None, approvals=None) -> dict:
    checks = {
        "transfer": inspect_transfer(transfer), "openraster": inspect_ora(ora),
        "blender": inspect_blender(blender), "signoffs": inspect_approvals(approvals)
    }
    issues = [issue for result in checks.values() for issue in result[1]]
    return {
        "project": "The Ninefold Tide", "shot": "E101_CAM03B",
        "stage": "visual-production-intake",
        "status": "BLOCKED" if issues else "PROOF_INTAKE_APPROVED",
        "checks": {key: value[0] for key, value in checks.items()},
        "issues": issues, "creative_release_approval": False,
        "notice": "File metadata cannot judge drawing quality, voice acting, or rights. The full animated proof needs real picture-and-sound human review."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transfer", type=Path)
    parser.add_argument("--ora", type=Path)
    parser.add_argument("--blender-probe", type=Path)
    parser.add_argument("--approvals", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--strict", action="store_true", help="exit nonzero if evidence is missing")
    args = parser.parse_args()
    result = audit(args.transfer, args.ora, args.blender_probe, args.approvals)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 1 if args.strict and result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
