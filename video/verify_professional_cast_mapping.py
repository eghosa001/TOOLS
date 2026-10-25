#!/usr/bin/env python3
"""Hard quality gate for all commercial CartoonStudio speaking character models.

Accept imported, licensed, audited professional character models only.
The shipped roster is a REQUIREMENTS manifest, not fabricated 15 finished rigs.
Do NOT fall back to clay, Quaternius or KayKit when a model is missing.
"""
import argparse
import hashlib
import json
from pathlib import Path

REQUIRED=("lelli","brin","odo","tavi","miko","pippa","nori","kolo",
          "suri","marn","fen","rumi","bex","luma","zaza")
FORBIDDEN=("original_clay","proposed_clay","quaternius","kaykit","cuto","cutemonster",
           "procedural","prototype","fallback")
VALID_LICENSES={"CC0-1.0","CC-BY-4.0"}

def audit(manifest_path,model_root):
    manifest_path=Path(manifest_path)
    model_root=Path(model_root).resolve()
    root=json.loads(manifest_path.read_text(encoding="utf-8"))
    records=root.get("characters",{})
    errors=[]
    if set(records)!=set(REQUIRED):
        errors.append("Required exactly fifteen stable cast keys: "+",".join(REQUIRED))
    used=set()
    for key in REQUIRED:
        record=records.get(key)
        if not isinstance(record,dict):
            errors.append("MISSING_MODEL "+key)
            continue
        src=record.get("filename","")
        if not isinstance(src,str):
            errors.append("INVALID_PATH "+key)
            continue
        path=(model_root/src).resolve()
        if model_root not in path.parents or not path.is_file():
            errors.append("NO_ACTUAL_3D_FILE "+key)
            continue
        if path.suffix.lower() not in (".glb",".blend"):
            errors.append("NOT_3D "+key)
        if path.stat().st_size<500_000:
            errors.append("SUSPICIOUSLY_SMALL_MODEL "+key)
        if path in used:
            errors.append("DUPLICATE_MODEL "+key)
        used.add(path)
        if any(word in (src+" "+str(record.get("creator",""))+" "+str(record.get("source",""))).lower()
               for word in FORBIDDEN):
            errors.append("REJECTED_LOW_DETAIL_SOURCE "+key)
        license_value=record.get("license")
        if license_value not in VALID_LICENSES:
            errors.append("NONCOMMERCIAL_OR_UNVERIFIED_LICENSE "+key)
        if license_value=="CC-BY-4.0" and not record.get("attribution"):
            errors.append("MISSING_CREATOR_CREDIT "+key)
        if not record.get("source"):
            errors.append("MISSING_ORIGINAL_SOURCE "+key)
        visual=record.get("visual_review",{})
        if not visual.get("approved_by_user"):
            errors.append("VISUAL_NOT_APPROVED "+key)
        tech=record.get("technical_audit",{})
        if tech.get("rig_bones",0)<20 or tech.get("faces",0)<9000:
            errors.append("NOT_HIGH_DETAIL_SKINNED "+key)
        if not tech.get("speaking_face_test_passed"):
            errors.append("SPEAKING_FACE_NOT_VERIFIED "+key)
        if record.get("sha256"):
            try:
                digest=hashlib.file_digest(path.open("rb"),"sha256").hexdigest()
                if digest!=record["sha256"]:
                    errors.append("ASSET_CHECKSUM_MISMATCH "+key)
            except OSError:
                errors.append("READ_FAILURE "+key)
    return errors

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--models",required=True)
    a=p.parse_args()
    issues=audit(a.manifest,a.models)
    if issues:
        print("PROFESSIONAL_CAST_BLOCKED",len(issues))
        for problem in issues:print("REJECT",problem)
        raise SystemExit(1)
    print("PROFESSIONAL_CAST_15_VERIFIED distinct licensed high-detail actors")
