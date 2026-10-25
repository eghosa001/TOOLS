#!/usr/bin/env python3
"""Independent Blender validation of all 8 real CC-BY CartoonStudio source rigs.

Check geometry, actor skeletons, key names, missing image maps and unresolved
linked .blend libraries on the packaged artifact (NOT on donor repo/source).
Opening files with Blender --disable-autoexec prevents untrusted Python drivers
being run during the audit. Reports true limitations; never converts/fakes.
"""
import bpy
import json
import sys
from pathlib import Path

def main(root,output):
    root=Path(root).resolve()
    manifest=json.loads((root/"ASSET_PROVENANCE_AND_LIMITS.json").read_text(encoding="utf-8"))
    results={}
    for key,entry in manifest["models"].items():
        source=root/entry["relative_file"]
        bpy.ops.wm.read_factory_settings(use_empty=True)
        result={"source":str(source.relative_to(root)),"master_size":source.stat().st_size,
                "open_ok":False,"error":None,"meshes":0,"polygon_faces":0,
                "armatures":0,"bones":0,"skinned_meshes":0,"shape_keys":0,
                "actions":0,"external_libraries_missing":[],"images_missing":[],
                "artist_materials":0,"ready_for_rig_retarget":False,
                "speaking_face_reviewed":False}
        try:
            bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
            result["open_ok"]=True
            rigs=[o for o in bpy.data.objects if o.type=="ARMATURE"]
            meshes=[o for o in bpy.data.objects if o.type=="MESH" and o.data.vertices]
            result["meshes"]=len(meshes)
            result["polygon_faces"]=sum(len(o.data.polygons) for o in meshes)
            result["armatures"]=len(rigs)
            result["bones"]=max([len(x.data.bones) for x in rigs] or [0])
            result["skinned_meshes"]=sum(bool(any(
                    m.type=="ARMATURE" and m.object is not None for m in o.modifiers)
                    or o.parent in rigs) for o in meshes)
            result["shape_keys"]=sum(len(o.data.shape_keys.key_blocks)
                       for o in meshes if o.data.shape_keys)
            result["artist_materials"]=len(bpy.data.materials)
            result["actions"]=len(bpy.data.actions)
            for asset in bpy.data.libraries:
                p=Path(bpy.path.abspath(asset.filepath))
                if not p.exists():
                    result["external_libraries_missing"].append(asset.filepath)
            for image in bpy.data.images:
                if image.users<1 or image.source not in ("FILE","TILED"):
                    continue
                if image.packed_file or image.packed_files:
                    continue
                path=bpy.path.abspath(image.filepath)
                if image.source=="TILED" and "<UDIM>" in path:
                    # Blender's UDIM path is a token, not a literal filename:
                    # a shipped 1001 tile is enough to resolve the texture source.
                    path=path.replace("<UDIM>","1001")
                if not Path(path).exists():
                    result["images_missing"].append(image.filepath)
            result["ready_for_rig_retarget"]=bool(
                result["skinned_meshes"] and result["bones"]>=30
                and not result["external_libraries_missing"])
        except Exception as e:
            result["error"]=repr(e)
        results[key]=result
        print("PROFESSIONAL_NATIVE_RIG_REAL_AUDIT",key,json.dumps(result),flush=True)
    out=Path(output)
    out.parent.mkdir(parents=True,exist_ok=True)
    good=[k for k,v in results.items() if v["ready_for_rig_retarget"]]
    missing=[k for k,v in results.items() if v["external_libraries_missing"] or v["images_missing"]]
    summary={"count":len(results),"open_files":sum(v["open_ok"] for v in results.values()),
             "armature_ready_count":len(good),"ready_keys":good,
             "missing_external_asset_keys":missing,
             "production_cast_approved":False,"results":results}
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print("PROFESSIONAL_EIGHT_NATIVE_AUDIT_RESULT",json.dumps(
        {k:v for k,v in summary.items() if k!="results"}),flush=True)
    if len(results)!=8 or summary["open_files"]!=8:
        raise RuntimeError("Packaged professional character masters failed to open")
if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:raise SystemExit("Usage blender -b --disable-autoexec --python audit... -- PACK REPORT.json")
    main(*args)
