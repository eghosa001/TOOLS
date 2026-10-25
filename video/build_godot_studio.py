#!/usr/bin/env python3
"""Package verified CC0 assets into an independent Godot 4 studio project.

Does not start an episode render, and never changes canonical dialogue.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import shutil
import zipfile
from godot_episode_timeline import compile_timeline


def unpack_safe(archive: zipfile.ZipFile, destination: pathlib.Path):
    names=archive.namelist()
    if len(names)>3000:
        raise RuntimeError("Too many asset files")
    for member in archive.infolist():
        p=pathlib.PurePosixPath(member.filename.replace("\\","/"))
        if p.is_absolute() or ".." in p.parts:
            raise ValueError("Refusing unsafe zip path")
        if member.file_size>32_000_000:
            raise RuntimeError("Oversized unpacked asset: "+member.filename)
        output=destination.joinpath(*p.parts)
        if member.is_dir():
            output.mkdir(parents=True,exist_ok=True)
        else:
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_bytes(archive.read(member))


def build(output,original,quality,kenney,source,story=None,audio_dir=None,expanded=None):
    output=pathlib.Path(output).resolve()
    original=pathlib.Path(original).resolve()
    quality=pathlib.Path(quality).resolve()
    kenney=pathlib.Path(kenney).resolve()
    source=pathlib.Path(source).resolve()
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(source,output)
    for name in ("lelli_original_clay.glb","brin_original_clay.glb",
                 "odo_original_clay.glb","sunpatch_court.glb"):
        file=original/name
        if not file.is_file():
            raise FileNotFoundError(file)
        target=output/"assets/original"/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(file,target)
    shutil.copy2(original/"asset_manifest.json",output/"assets/original/original_asset_manifest.json")
    textures=json.loads((quality/"quality_manifest.json").read_text())
    assert len(textures["materials"])>=2
    for item in textures["files"]:
        src=quality/item["file"]
        blob=src.read_bytes()
        if hashlib.sha256(blob).hexdigest()!=item["sha256"]:
            raise RuntimeError("Corrupted downloaded CC0 quality file: "+item["file"])
        target=output/"assets/quality"/item["file"]
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(blob)
    shutil.copy2(quality/"quality_manifest.json",
                 output/"assets/quality/quality_manifest.json")
    with zipfile.ZipFile(kenney) as archive:
        with __import__("tempfile").TemporaryDirectory() as tmp:
            temp=pathlib.Path(tmp)
            unpack_safe(archive,temp)
            catalog=json.loads((temp/"asset_manifest.json").read_text())
            eligible=[a for a in catalog["assets"] if a["role"]=="environment_prop"]
            extra=eligible[:32]
            for entry in extra:
                src=temp/entry["file"]
                dest=output/"assets/imported"/entry["file"]
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(src,dest)
            # Some Kenney GLBs reference a neighbouring shared colormap PNG.
            # Retain the vendor's original folder layout so Godot can resolve it.
            for entry in extra:
                model=(temp/entry["file"]).resolve()
                texture_dir=model.parent/"Textures"
                if texture_dir.is_dir():
                    for tex in texture_dir.glob("*.png"):
                        relative=tex.relative_to(temp)
                        dest=output/"assets/imported"/relative
                        dest.parent.mkdir(parents=True,exist_ok=True)
                        shutil.copy2(tex,dest)
            backgrounds=[a for a in catalog["assets"] if a["role"]=="background_character"]
            library=[a for a in catalog["assets"] if a["role"]=="retarget_animation_library"]
            sounds=[a for a in catalog["assets"] if a["role"]=="sound_effect"]
            # Retain the actual source FBX/skin, Godot-compatible animation
            # library GLB and playable audio. Existing series heroes remain
            # separate and cannot be randomly replaced.
            for entry in backgrounds+library+sounds:
                paths=[entry["file"]]
                if entry.get("skin"):
                    paths.append(entry["skin"])
                if isinstance(entry.get("animation_files"), dict):
                    paths.extend(entry["animation_files"].values())
                for filename in paths:
                    src=temp/filename
                    if not src.is_file():
                        raise FileNotFoundError(src)
                    target=output/"assets/imported"/filename
                    target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(src,target)

            # Animation clips remain in downloadable source pack until retargeted.
            (output/"assets/imported").mkdir(parents=True,exist_ok=True)
            index={"props":extra,"background_characters":backgrounds,
                   "available_humanoid_animation_packs":library,
                   "sound_effect_count":len(sounds),
                   "commercial_license":"CC0-1.0",
                   "note":"CC0 rigged FBX models and animation GLB are provided. Skeleton compatibility and retargeting must be verified before use."}
            (output/"assets/imported/import_manifest.json").write_text(
                json.dumps(index,indent=2)+"\n",encoding="utf-8")
    proposed_count=0
    if expanded is not None:
        expanded=pathlib.Path(expanded).resolve()
        manifest_path=expanded/"proposed_cast_manifest.json"
        index=json.loads(manifest_path.read_text(encoding="utf-8"))
        if index.get("status")!="proposed_not_canon" or index.get("count")!=12:
            raise ValueError("Expanded cast must contain exactly twelve unapproved candidate characters")
        entries=index.get("characters",{})
        if len(entries)!=12 or set(entries) & {"lelli","brin","odo"}:
            raise ValueError("Expanded cast must not replace original series heroes")
        destination=output/"assets/proposed"
        destination.mkdir(parents=True,exist_ok=True)
        for key,item in entries.items():
            if not isinstance(key,str) or not key.isidentifier() or key.lower()!=key:
                raise ValueError("Invalid proposed cast key: "+str(key))
            if item.get("canon") or item.get("skeletal_rig"):
                raise ValueError("Unverified canon or skeleton claim for "+key)
            basename=key+"_proposed_clay.glb"
            if item.get("filename")!=basename:
                raise ValueError("Unexpected expanded model filename")
            src=expanded/basename
            if not src.is_file() or src.stat().st_size<2500:
                raise FileNotFoundError(src)
            shutil.copy2(src,destination/basename)
            proposed_count+=1
        for extra_file in ("proposed_cast_manifest.json","proposed_cast_contact_sheet.png","proposed_cast.json"):
            source_file=expanded/extra_file
            if not source_file.is_file():
                raise FileNotFoundError(source_file)
            shutil.copy2(source_file,destination/extra_file)
        print("GODOT_PROPOSED_CAST_IMPORTED count=",proposed_count,flush=True)
    if story is not None:
        episode = json.loads(pathlib.Path(story).read_text(encoding="utf-8"))
        cues = compile_timeline(episode, output/"episode", audio_dir)
        print("GODOT_PACKAGED_CUES", cues["line_count"], cues["timing_source"], flush=True)
    payload_files=[p for p in output.rglob("*") if p.is_file()]
    if len(payload_files)<12:
        raise RuntimeError("Godot library lacks assets")
    stats={"project":"CartoonStudio","character_models":3+proposed_count,"original_leads":3,"proposed_supporting_models":proposed_count,
           "environment_models":1,
           "pbr_materials":len(textures["materials"]),
           "hdris":1,"imported_decorations":len(extra),
           "rigged_background_characters":len(backgrounds),
           "animation_libraries":len(library),
           "sound_effects":len(sounds),
           "provenance":"See respective CC0 source manifests",
           "animation_status":"Facial morph GLBs available. Rigged humanoid retargeting not completed.",
           "story_dialogue":"Not modified"}
    (output/"ASSET_BUILD_REPORT.json").write_text(json.dumps(stats,indent=2)+"\n")
    print("GODOT_PROJECT_ASSEMBLED",json.dumps(stats),flush=True)
    return stats


if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("output","original","quality","kenney","source"):
        p.add_argument("--"+name,required=True)
    p.add_argument("--story", default="video/story.json")
    p.add_argument("--episode-audio", default=None)
    p.add_argument("--expanded-characters", default=None)
    a=p.parse_args()
    build(a.output,a.original,a.quality,a.kenney,a.source,a.story,a.episode_audio,a.expanded_characters)
