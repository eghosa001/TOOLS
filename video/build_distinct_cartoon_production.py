#!/usr/bin/env python3
"""Package existing CC0 rigged character files into a working Godot episode studio.

No old procedural cast files. No Blender mesh generation. Does not render.
"""
import argparse
import json
import shutil
from pathlib import Path
from godot_episode_timeline import compile_timeline

ASSET_ROOT="assets/production"
SCRIPTS=("production_studio.gd","production_episode_player.gd")
SCENES=("production_studio.tscn","production_gallery.tscn")

def build(output,assets,source,story,audio_dir=None):
    output=Path(output).resolve()
    assets=Path(assets).resolve()
    source=Path(source).resolve()
    story=Path(story).resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for folder,files in (("scripts",SCRIPTS),("scenes",SCENES)):
        (output/folder).mkdir(exist_ok=True)
        for file in files:
            shutil.copy2(source/folder/file,output/folder/file)
    (output/ASSET_ROOT).mkdir(parents=True)
    registry=json.loads((assets/"production_cast_manifest.json").read_text(encoding="utf-8"))
    records=registry.get("characters",{})
    if registry.get("character_count")!=15 or len(records)!=15:
        raise ValueError("Fifteen distinct rigged imported character files required")
    if len(set(v["source_name"] for v in records.values()))!=15:
        raise ValueError("Duplicate base meshes are disallowed")
    for key,entry in records.items():
        if entry.get("skeletons",0)<1 or len(entry.get("animations",[]))<4:
            raise ValueError("Unrigged character: "+key)
        if entry.get("filename")!=key+".gltf":
            raise ValueError("Unexpected character mapping for "+key)
        src=assets/entry["filename"]
        if not src.is_file() or src.stat().st_size<200000:
            raise FileNotFoundError(src)
        shutil.copy2(src,output/ASSET_ROOT/src.name)
    shutil.copy2(assets/"production_cast_manifest.json",output/ASSET_ROOT/"production_cast_manifest.json")
    script=json.loads(story.read_text(encoding="utf-8"))
    if not set(script["characters"]).issubset(set(records)):
        raise ValueError("Story requires a missing character")
    cues=compile_timeline(script,output/"episode",audio_dir)
    (output/"project.godot").write_text("""config_version=5
[application]
config/name="CartoonStudio — Distinct Imported CC0 Character Production"
run/main_scene="res://scenes/production_studio.tscn"
config/features=PackedStringArray("4.7", "GL Compatibility")
[display]
window/size/viewport_width=1280
window/size/viewport_height=720
[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
""",encoding="utf-8")
    report={"models":15,"distinct_source_meshes":15,
            "legacy_procedural_character_files":0,
            "kaykit_recolored_clones":0,
            "original_episode_lines_preserved":cues["line_count"],
            "audio_lines":cues["audio_line_count"],
            "face_visemes_available":False,
            "stage":"simple temporary floor; full scenery needs separate imported set",
            "source":"Quaternius Cute Animated Monsters CC0",
            "no_video_render_was_run":True}
    (output/"PRODUCTION_REPORT.json").write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("PRODUCTION_PACKAGE_READY",json.dumps(report),flush=True)
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    p.add_argument("--assets",required=True)
    p.add_argument("--source",default="video/godot_studio")
    p.add_argument("--story",default="video/story.json")
    p.add_argument("--episode-audio")
    a=p.parse_args()
    build(a.output,a.assets,a.source,a.story,a.episode_audio)
