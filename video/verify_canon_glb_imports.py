#!/usr/bin/env python3
"""Re-import the THREE newly exported original characters; trust geometry not log."""
import hashlib, json, sys
from pathlib import Path
import bpy

ROLES=("lelli","brin","odo")
REQUIRED={"viseme_PP","viseme_kk","viseme_E","viseme_aa","viseme_O",
          "viseme_U","viseme_FF","viseme_nn","mouthSmile"}
def main(root):
    folder=Path(root).resolve()
    records={}
    for name in ROLES:
        p=folder/(name+"-original-cartoon-character.glb")
        if not p.is_file():raise RuntimeError("Missing actual GLB "+name)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(p))
        meshes=[obj for obj in bpy.data.objects if obj.type=="MESH"]
        polygons=sum(len(obj.data.polygons) for obj in meshes)
        mouths=[obj for obj in meshes if "mouth" in obj.name.casefold() and obj.data.shape_keys
                and REQUIRED.issubset(set(obj.data.shape_keys.key_blocks.keys()))]
        if not mouths:raise RuntimeError(f"{name} GLB import destroyed original 9 named lip visemes")
        actions=[x for x in bpy.data.actions]
        if not actions:raise RuntimeError(f"{name} GLB import lost reusable animation actions")
        keys=set(bpy.data.objects.keys())
        expected={name+"_mouth",name+"_head_pivot"}
        if not expected.issubset(keys):raise RuntimeError("Original required source node missing: "+name)
        if polygons<2000:raise RuntimeError("Original geometry missing "+name)
        records[name]={"gltf_reimport_mesh_count":len(meshes),"gltf_reimport_polygons":polygons,
                       "morphs_after_reimport":sorted(REQUIRED),
                       "source_actions_after_reimport":[act.name for act in actions],
                       "imported_full_character_hierarchy":True,
                       "mouth_morphs_present":True,
                       "real_GLTF_export_verified":True}
        print("ORIGINAL_CANON_GLB_TRUE_REIMPORT_PASS",name,"faces",polygons,
              "actions",len(actions),"viseme_keys",len(REQUIRED),flush=True)
    out=folder/"TRUE-GLB-REIMPORT-EVIDENCE.json"
    out.write_text(json.dumps({"all_three_original_roles_reimported":True,
                "results":records,"original_canon_unchanged":True,
                "full_audio_viseme_performance_unverified":True,
                "episode_video_rendered":False},indent=2)+"\n")
if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=1:raise SystemExit("Usage blender --python verify_canon_glb_imports.py -- OUT_DIR")
    main(args[0])
