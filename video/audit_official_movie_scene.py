#!/usr/bin/env python3
"""Inspect official Blender open-movie scene for real REUSABLE character rigs.

A 300MB animation shot is NOT automatically a reusable cast library. Inspect
armatures, bone counts, skinned meshes, face morphs, animation actions,
external references, library linking and asset identity. Do not run scripts.
"""
import bpy,json,sys
from pathlib import Path

def inspect_archive(root,target):
    root=Path(root).resolve()
    sources=json.loads((root/"OFFICIAL_SOURCE.json").read_text())
    report={"source":sources["download_url"],"license":sources["license"],
            "files":[],"approved_as_reusable_character_pack":False,
            "reason":"Not reviewed as separable real speaking rigs"}
    for item in sources["blender_scenes"][:8]:
        path=Path(item["filename"])
        bpy.ops.wm.read_factory_settings(use_empty=True)
        try:
            bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
            arm=[]
            for obj in bpy.data.objects:
                if obj.type!="ARMATURE":
                    continue
                users=sum(
                    1 for mesh in bpy.data.objects if mesh.type=="MESH" and (
                    mesh.parent==obj or any(m.type=="ARMATURE" and m.object==obj
                        for m in mesh.modifiers)))
                arm.append({"name":obj.name,"bones":len(obj.data.bones),"skinned_mesh_objects":users,
                            "linked_library":bool(obj.library)})
            keys=sum(len(o.data.shape_keys.key_blocks)
                     for o in bpy.data.objects if o.type=="MESH" and o.data.shape_keys)
            info={"filename":str(path.name),
                  "mesh_objects":sum(o.type=="MESH" for o in bpy.data.objects),
                  "armatures":arm,
                  "pose_rigs_30_bones":sum(x["bones"]>=30 and x["skinned_mesh_objects"]>=1 for x in arm),
                  "shape_keys":keys,
                  "actions":len(bpy.data.actions),
                  "external_libraries":[lib.filepath for lib in bpy.data.libraries],
                  "linked_armature_rigs":sum(x["linked_library"] for x in arm)}
            report["files"].append(info)
            print("MOVIE_ACTUAL_RIG_DATA",json.dumps(info),flush=True)
        except Exception as e:
            report["files"].append({"filename":path.name,"error":str(e)})
            print("MOVIE_INSPECTION_ERROR",path.name,str(e),flush=True)
    report["found_multiple_reusable_rigs"]=any(
        file.get("pose_rigs_30_bones",0)>=2 for file in report["files"])
    target=Path(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("MOVIE_SCENE_REUSABLE_RIG_SUMMARY",report["found_multiple_reusable_rigs"],flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2: raise SystemExit("args ROOT REPORT")
    inspect_archive(*args)
