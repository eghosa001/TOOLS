#!/usr/bin/env python3
"""Audit real speaking mouth geometry on original licensed Blender Studio rigs.

No new meshes, no fake face controls, no character recolours, no episode render.
A named "mouth" key is not enough: we numerically compare vertices to Basis.
This does not prove a film-quality lip-sync track; it identifies candidates.
Run from Blender with --disable-autoexec to avoid untrusted rig scripts.
"""
import json,re,sys,math
from pathlib import Path
import bpy

MOUTH=re.compile(r"jaw|mouth|lip|phon|visem|vowel|tongue|teeth|smile|frown|open",re.I)
EYE=re.compile(r"eye|blink|brow|lid|pupil",re.I)

def test_shape(mesh,block,base):
    if len(block.data)!=len(base.data):
        return {"moved_vertices":0,"max_offset":0,"mean_moved_offset":0}
    moved=0
    maxdist=0.
    total=0.
    for i in range(len(block.data)):
        delta=(block.data[i].co-base.data[i].co).length
        if delta>0.00003:
            moved+=1
            maxdist=max(maxdist,delta)
            total+=delta
    return {"moved_vertices":moved,"max_offset":round(maxdist,6),
            "mean_moved_offset":round(total/max(1,moved),6)}

def inspect_actor(source,key):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(Path(source).resolve()),load_ui=False)
    meshes=[x for x in bpy.data.objects if x.type=="MESH" and x.data is not None and len(x.data.vertices)>0]
    armatures=[x for x in bpy.data.objects if x.type=="ARMATURE"]
    candidate=[]
    eyes=[]
    allkeys=0
    for mesh in meshes:
        sk=mesh.data.shape_keys
        if sk is None or len(sk.key_blocks)<2:continue
        blocks=sk.key_blocks
        base=blocks[0]
        for block in list(blocks)[1:]:
            allkeys+=1
            mouth=MOUTH.search(block.name) is not None
            eye=EYE.search(block.name) is not None
            if not mouth and not eye:continue
            data=test_shape(mesh,block,base)
            record={"object":mesh.name,"shape_key":block.name,"movement":data,
                    "actual_nonzero_geometry":data["moved_vertices"]>3 and data["max_offset"]>0.0001}
            if mouth:candidate.append(record)
            elif eye:eyes.append(record)
    controllers=[]
    for rig in armatures:
        for bone in rig.pose.bones:
            if MOUTH.search(bone.name) and len(controllers)<100:
                controllers.append({"rig":rig.name,"bone":bone.name})
    usable=[x for x in candidate if x["actual_nonzero_geometry"]]
    report={"actor":key,"real_source_file":Path(source).name,
      "mesh_objects":len(meshes),"skeletons":len(armatures),
      "actual_total_shape_keys":allkeys,
      "named_mouth_shape_candidates":candidate,
      "mouth_shapes_with_measurable_real_geometry":usable,
      "usable_mouth_shape_names":sorted({x["shape_key"] for x in usable}),
      "eye_shape_candidates":eyes,
      "mouth_named_pose_controllers":controllers,
      "can_drive_at_least_one_mouth_shape_directly":bool(usable),
      "visemes_tested_with_spoken_wav":False,
      "rendered_talking_performance":False,
      "user_has_approved_actor_for_canon":False}
    print("REAL_STUDIO_SPEAKING_FACE_AUDIT",key,json.dumps({
        "mesh_objects":report["mesh_objects"],"total_shapes":allkeys,
        "shape_keys_with_measurable_mouth_deformation":len(usable),
        "shape_names":report["usable_mouth_shape_names"][:30],
        "mouth_pose_controllers":len(controllers)}),flush=True)
    return report

def main(root,out):
    root=Path(root)
    manifest=json.loads((root/"ASSET_PROVENANCE_AND_LIMITS.json").read_text())
    results={}
    for key,item in manifest["models"].items():
        file=root/item["relative_file"]
        if not file.is_file():raise RuntimeError("Original Blender source absent: "+key)
        results[key]=inspect_actor(file,key)
    result={
      "scope":"Eight genuine original high-quality Blender Studio rigs",
      "test_method":"Numerically compare actual shape-key vertex positions to original basis",
      "actors_tested":len(results),
      "actors_with_direct_deforming_mouth_shapes":[k for k,v in results.items()
          if v["can_drive_at_least_one_mouth_shape_directly"]],
      "not_tested":"lip-sync fidelity, phoneme alignment, natural facial acting, voice, video",
      "results":results}
    target=Path(out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+"\n")
    print("REAL_STUDIO_NATIVE_MOUTH_GEOMETRY_SUMMARY",json.dumps({
        "actors_tested":result["actors_tested"],
        "actors_with_direct_deforming_mouth_shapes":result["actors_with_direct_deforming_mouth_shapes"]}),flush=True)
    if len(results)!=8:raise RuntimeError("All eight original models are required for the audit")

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:raise SystemExit("Blender --python ... -- ORIGINAL_LIBRARY_DIR OUTPUT_JSON")
    main(*args)
