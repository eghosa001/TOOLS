#!/usr/bin/env python3
"""Convert downloaded, verified original Episode 1 bytes to an immutable
per-run technical attestation. Never edits creative source assets.json or story.
Never claims artist visual approval merely because checksum passed.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def main(source,pack,output):
    source=Path(source).resolve();pack=Path(pack).resolve();output=Path(output).resolve()
    record=json.loads(source.read_text(encoding="utf-8"))
    stage_evidence=json.loads((pack/"STAGE_BUILD_EVIDENCE.json").read_text())
    if not stage_evidence["no_character_generated"] or len(stage_evidence.get("kenney_provenance",[]))<8:
        raise ValueError("Missing original CC0 woodland stage provenance")
    if not all(row["license"]=="CC0-1.0" for row in stage_evidence["kenney_provenance"]):
        raise ValueError("Unlicensed imported stage source")
    # Fail closed if someone silently returns to the older Kenney-only stage.
    # This checks the real original source archive and the 15 imported model
    # records, not release-quality facial acting or visual composition.
    from quaternius_stage import PINNED_SHA256, SOURCE_URL
    rows=stage_evidence.get("quaternius_provenance",[])
    if (stage_evidence.get("quaternius_archive_sha256")!=PINNED_SHA256 or
        stage_evidence.get("quaternius_source")!=SOURCE_URL or
        stage_evidence.get("quaternius_license")!="CC0-1.0" or len(rows)!=15):
        raise ValueError("15 original pinned Quaternius CC0 backdrop models required")
    if any(row.get("license")!="CC0-1.0" or row.get("source")!=SOURCE_URL or
           len(row.get("sha256",""))!=64 or not row.get("file","").endswith(".gltf")
           for row in rows):
        raise ValueError("Incomplete original Quaternius source provenance")
    if stage_evidence.get("quaternius_dependency_count",0)<15:
        raise ValueError("Original Quaternius glTF dependencies not documented")
    proof={"sources":[],"licenses_checked_only_not_release_quality":True,"preview_rendered":False}
    checks=[("actor."+key,rec["file"],rec) for key,rec in record["actors"].items()]
    checks += [("environment."+k,record["environment"][k]["file"],record["environment"][k])
               for k in ("stage","hdri")]
    checks += [("prop."+key,val,None)
               for key,val in record["environment"]["props"].items() if key!="note"]
    for kind,relative,target in checks:
        path=(pack/relative).resolve()
        if pack not in path.parents or not path.is_file() or path.stat().st_size<(200_000 if kind.startswith("actor.") else 500):
            raise FileNotFoundError("Missing genuine episode asset: "+kind+" "+str(path))
        extension=path.suffix.lower()
        head=path.open("rb").read(8)
        if extension==".blend" and head[:7]!=b"BLENDER":
            raise ValueError("Original native Blender file damaged")
        if extension==".glb" and head[:4]!=b"glTF":
            raise ValueError("Required professional/source GLB missing valid header")
        if extension==".hdr" and head[:2]!=b"#?":
            raise ValueError("Genuine Poly Haven HDRI has wrong Radiance header")
        sha=digest(path)
        if target:
            declared=target.get("sha256")
            if declared and sha!=declared:
                raise ValueError("Published original SHA changed "+kind)
            target["sha256"]=sha
            target["sha256_status"]="pin_calculated_from_actual_physically_present_file"
            target["verified_file_bytes"]=path.stat().st_size
        proof["sources"].append({"identity":kind,"path":relative,"sha256":sha,
                                 "bytes":path.stat().st_size})
    output.parent.mkdir(parents=True,exist_ok=True)
    record["generated_attestation"]=proof
    record["readiness"]="technical_bytes_pinned_not_scene_performance_or_preview_approved"
    record["no_kaggle_render_authorized"]=True
    output.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print("EP01_REAL_ASSET_BYTES_SHA256_ATTESTED",len(proof["sources"]),
          "no_video_rendered=true release_approval=false")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,default=ROOT/"assets.json")
    p.add_argument("--pack",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();main(a.source,a.pack,a.output)
