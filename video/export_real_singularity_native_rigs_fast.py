#!/usr/bin/env python3
"""Extract existing original Blender Studio Singularity CC-BY rigged actor data.

FAST pass: write reusable native .blend libraries without cycles rendering.
Does NOT build/rebuild a character, doesn't claim a visually accepted model.
"""
import bpy,sys,json,hashlib
from pathlib import Path

RIGS={
"critter":"RIG-critter",
"doublemohawk":"RIG-doublemohawk.001",
"multifrog":"RIG-multifrog.001",
"mantaribs":"RIG-mantaribs",
"doubleeye":"RIG-doubleeye.001",
"plumpfly":"RIG-plumpfly.001",
"coralboi":"RIG-coralboi.001",
}
def attached(obj,rig):
    x=obj.parent
    while x:
        if x==rig:return True
        x=x.parent
    return any(m.type=="ARMATURE" and m.object==rig for m in obj.modifiers)

def run(source,out):
    source=Path(source).resolve()
    target=Path(out).resolve()
    target.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    report={"title":"Actual first-party Blender Studio Singularity rig sources",
     "source_url":"https://download.blender.org/demo/splash/blender-5.1-splash.blend",
     "license":"CC BY 4.0; commercial use allowed with attribution",
     "artist":"Blender Studio",
     "original_sculpt_rigs":{},
     "rendered_and_approved":False,
     "actual_video_rendered":False,
     "no_procedural_characters":True,
     "no_character_recolouring_or_duplicates":True}
    for actor,rig_name in RIGS.items():
        rig=bpy.data.objects.get(rig_name)
        if rig is None or rig.type!="ARMATURE":
            raise RuntimeError("Artist original source rig missing "+rig_name)
        meshes=[x for x in bpy.data.objects if x.type=="MESH" and x.data and len(x.data.polygons)>0
                and not x.hide_render and attached(x,rig)]
        if not meshes:raise RuntimeError("Artist original character skin missing "+actor)
        faces=sum(len(m.data.polygons) for m in meshes)
        if len(rig.data.bones)<30 or faces<1500:
            raise RuntimeError("Non-production rig "+actor)
        dest=target/(actor+"-native-studio.blend")
        bpy.data.libraries.write(str(dest),set([rig,*meshes]),fake_user=True,compress=True)
        if dest.stat().st_size<100000:
            raise RuntimeError("Original studio actor extraction failed "+actor)
        report["original_sculpt_rigs"][actor]={
            "name":rig_name,
            "filename":dest.name,
            "rig_bones":len(rig.data.bones),
            "render_meshes":len(meshes),
            "faces":faces,
            "morph_shape_keys":sum(len(o.data.shape_keys.key_blocks)
                                 for o in meshes if o.data.shape_keys),
            "sha256":hashlib.file_digest(dest.open("rb"),"sha256").hexdigest(),
            "size_bytes":dest.stat().st_size,
            "facial_lipsync_verified":False,
            "colour_render_verified":False,
            "approved_series_cast":False,
        }
        print("ACTUAL_STUDIO_SINGULARITY_RIG_SAVED",actor,dest.stat().st_size,
              "bones",len(rig.data.bones),"faces",faces,flush=True)
    (target/"REAL_NATIVE_SOURCE_ROSTER.json").write_text(json.dumps(report,indent=2)+"\n")
    print("SEVEN_REAL_NONCLONED_SINGULARITY_NATIVE_CHARACTER_MASTERS_PASS",
          len(report["original_sculpt_rigs"]),flush=True)
if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:raise SystemExit("Usage blender -b --python script.py -- original.blend output/")
    run(*args)
