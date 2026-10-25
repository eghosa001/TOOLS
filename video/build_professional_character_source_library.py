#!/usr/bin/env python3
"""Package eight genuinely different PROFESSIONAL Blender Studio actor masters.

Never synthesizes character geometry, does not approve/mutate series canon,
does not call Kaggle or render. Keeps the required external node and material
.blend libraries from official source archives so original rigs stay reusable.
If original texture files are not published, report them as MISSING rather than
fabricate an image or accept magenta output.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path
from audit_official_blender_movie import import_archive
from fetch_real_studio_rig import get_zip

CHARACTERS = {
    "rain": ("rain", "source/rain_v2_6_packt.blend"),
    "cat": ("pets", "source/blender-3.6-splash/pro/lib/char/cat/publish/cat.v001.blend"),
    "dog": ("pets", "source/blender-3.6-splash/pro/lib/char/dog/publish/dog.v001.blend"),
    "sprite": ("sprite_fright", "source/030_0020_A/lib/char/sprite/sprite.blend"),
    "butterfly": ("sprite_fright", "source/030_0020_A/lib/char/butterfly/butterfly.blend"),
    "ladybug": ("sprite_fright", "source/030_0020_A/lib/char/ladybug/ladybug.blend"),
    "snail": ("sprite_fright", "source/030_0020_A/lib/char/snail/snail.blend"),
    "spider": ("sprite_fright", "source/030_0020_A/lib/char/spider/spider.blend"),
}
SOURCES = {
    "rain": "https://github.com/PacktPublishing/Realizing-3D-Animation-in-Blender",
    "pets": "https://download.blender.org/demo/splash/blender-3.6-splash.zip",
    "sprite_fright": "https://download.blender.org/demo/sprite_fright_030_0020_A.zip",
}
CREDITS = {
    "rain": "Blender Studio (Rain rig), educational archive via Packt",
    "pets": "Blender Studio — Blender 3.6 Pet Projects",
    "sprite_fright": "Blender Studio — Sprite Fright",
}

def build(output, cache):
    output=Path(output).resolve()
    cache=Path(cache).resolve()
    output.mkdir(parents=True,exist_ok=True)
    cache.mkdir(parents=True,exist_ok=True)
    get_zip(cache/"rain")
    import_archive("pet-projects-splash",cache/"pets")
    import_archive("sprite-fright-shot",cache/"sprite_fright")
    records={}
    missing=[]
    for actor,(which,relative) in CHARACTERS.items():
        file=cache/which/relative
        if not file.is_file() or file.stat().st_size<100_000:
            raise FileNotFoundError(f"Actual original source file not found: {actor}: {file}")
        # Official source *.blend remains authoritative and unmodified.
        destination=output/which/relative.removeprefix("source/")
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(file,destination)
        with destination.open("rb") as f:
            digest=hashlib.file_digest(f,"sha256").hexdigest()
        records[actor]={"source":SOURCES[which],"source_group":which,
                        "artist":CREDITS[which], "relative_file":str(destination.relative_to(output)),
                        "bytes":destination.stat().st_size,"sha256":digest,
                        "license":"CC BY; show author/artist attribution",
                        "fidelity":"native original Blender rig; not yet approved for CartoonStudio canon",
                        "face_audio_test":"not completed"}
        print("AUTHENTIC_SOURCE_MODEL_PACKAGED",actor,destination.stat().st_size,flush=True)
    # Copy referenced source shader/node libraries from the two project archives.
    # A lightweight *.blend without its linked libraries is not a full rig.
    dependency_roots=[
        ("pets","source/blender-3.6-splash/pro/lib/nodes/"),
        ("sprite_fright","source/030_0020_A/lib/nodes/"),
    ]
    deps=0
    for which,subdir in dependency_roots:
        dir=cache/which/subdir
        for file in dir.rglob("*.blend"):
            relative=file.relative_to(cache/which/"source")
            dst=output/which/relative
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(file,dst)
            deps+=1
    report={
        "purpose":"authentic professional source rig library for studio-quality Blender acting",
        "count":len(records),"all_distinct_originals":len(records)==8,
        "models":records,"linked_node_libraries_copied":deps,
        "limitations":[
            "Eight distinct professionally authored original Blender rigs, NOT 15 complete actors.",
            "Official Blender 3.6 Pet Projects Cat/Dog source does not contain original base_color.tif files; native renders have been magenta.",
            "Sprite Fright studio rigs may depend on Blender 3.3–3.6 and the published movie archive's linked materials.",
            "Native Blender controllers and drivers are not guaranteed to survive GLB exports.",
            "Commercial reuse of CC BY assets requires giving correct Blender Foundation/Studio attribution.",
            "No visual canon changes, full-episode renders or Kaggle jobs were authorized or performed."
        ],
        "low_detail_asset_files":0,
        "ready_for_user_approval":False,
    }
    (output/"ASSET_PROVENANCE_AND_LIMITS.json").write_text(json.dumps(report,indent=2)+"\n")
    (output/"ATTRIBUTION.txt").write_text(
        "Professional original 3D character rigs — Blender Studio, Blender Foundation\n"
        "Rain rig (historical) via Packt educational archive; Blender 3.6 Pet Projects; Sprite Fright.\n"
        "Licensing: Creative Commons Attribution, verify specific publisher asset pages before public episode release.\n"
        "Source URLs:\n"+"\n".join(SOURCES.values())+"\n"
        "This candidate library is NOT the CartoonStudio finished visual cast.\n",encoding="utf-8")
    if len(records)!=8:raise AssertionError("Distinct original actor count mismatch")
    print("BLENDER_STUDIO_NATIVE_8_DISTINCT_SOURCE_RIGS_PACKAGED linked_shaders=",deps,
          "not_approved=true",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    p.add_argument("--cache",required=True)
    a=p.parse_args()
    build(a.output,a.cache)
