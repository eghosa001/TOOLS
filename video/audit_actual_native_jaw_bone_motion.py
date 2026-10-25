#!/usr/bin/env python3
"""Measure actual 3D mesh deformation from native Blender jaw rig bone poses.

Excludes procedural characters. Does not enable original Blender scripts,
edit source .blend files, or run an episode. A rig bone named "jaw" alone
is NOT evidence of a working mouth: evaluated world vertex position must move.
"""
from __future__ import annotations
import json,math,re,sys
from pathlib import Path
import bpy
from mathutils import Vector

PATTERN=re.compile(r"jaw|mouth",re.I)
def main(master,out,actor):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    master=Path(master).resolve()
    bpy.ops.wm.open_mainfile(filepath=str(master),load_ui=False)
    arms=[obj for obj in bpy.data.objects if obj.type=="ARMATURE"]
    meshes=[obj for obj in bpy.data.objects if obj.type=="MESH" and obj.data and len(obj.data.vertices)>40]
    candidates=[]
    for rig in arms:
        connected=[mesh for mesh in meshes if (
            any(m.type=="ARMATURE" and m.object==rig for m in mesh.modifiers)
            or mesh.parent==rig)]
        if not connected:continue
        for p in rig.pose.bones:
            if not PATTERN.search(p.name):continue
            used=[m for m in connected if p.name in m.vertex_groups]
            if not used:continue
            used.sort(key=lambda obj:len(obj.data.vertices),reverse=True)
            candidates.append((rig,p,used))
    candidates.sort(key=lambda x:(0 if re.search(r"(?:^|[-_.])(?:DEF|jaw)[-_.]",x[1].name,re.I) else 1,
                                  -sum(len(m.data.vertices) for m in x[2])))
    reports=[]
    def positions(mesh,n=300):
        depsgraph=bpy.context.evaluated_depsgraph_get()
        obj=mesh.evaluated_get(depsgraph)
        data=obj.to_mesh()
        try:
            size=len(data.vertices)
            ids=range(0,size,max(1,size//n))
            return [obj.matrix_world@data.vertices[i].co for i in ids]
        finally:
            obj.to_mesh_clear()
    for rig,p,connected in candidates[:14]:
        target=connected[0]
        original_mode=p.rotation_mode
        original_euler=p.rotation_euler.copy()
        try:
            bpy.context.view_layer.update()
            baseline=positions(target)
            p.rotation_mode="XYZ"
            p.rotation_euler=original_euler.copy()
            p.rotation_euler.x+=math.radians(18)
            bpy.context.view_layer.update()
            modified=positions(target)
            movement=[(a-b).length for a,b in zip(baseline,modified)]
            substantial=sum(v>0.0001 for v in movement)
            largest=max(movement) if movement else 0.
            reports.append({"bone":p.name,"rig":rig.name,"sample_mesh":target.name,
                "sampled_vertices":len(movement),
                "moved_vertex_samples":substantial,
                "max_world_vertex_displacement":round(largest,6),
                "actual_deformation_confirmed":substantial>3 and largest>0.0002})
            print("REAL_NATIVE_JAW_POSE_GEOMETRY_TEST",actor,p.name,
                  "moved",substantial,"largest",round(largest,6),flush=True)
        except Exception as ex:
            reports.append({"bone":p.name,"rig":rig.name,"error":str(ex)[:400],
                            "actual_deformation_confirmed":False})
        finally:
            p.rotation_mode=original_mode
            p.rotation_euler=original_euler
            bpy.context.view_layer.update()
    outcome={"actor":actor,"original_blender_master":master.name,
             "candidate_named_jaw_or_mouth_weighted_bones":len(candidates),
             "tested_bone_count":len(reports),
             "individually_confirmed_deforming_jaw_bones":[r["bone"] for r in reports
                  if r.get("actual_deformation_confirmed")],
             "results":reports,"source_artist_original_unchanged":True,
             "original_scripts_executed":False,"live_speech_lip_sync_tested":False,
             "frame_by_frame_video_rendered":False,
             "reason":"A measurable bone pose is only one building block; phoneme animation still requires character-specific controls and WAV alignment"}
    out=Path(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(outcome,indent=2)+"\n")
    print("NATIVE_JAW_BONE_REAL_MESH_TEST_SUMMARY",actor,
         json.dumps({"tested":len(reports),"deforming_bones":outcome["individually_confirmed_deforming_jaw_bones"]}),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3:raise SystemExit("Usage native_jaw_audit.py -- ORIGINAL.blend REPORT.json KEY")
    main(*args)
