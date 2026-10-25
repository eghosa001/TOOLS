#!/usr/bin/env python3
"""Measure real professional cat/dog mouth controller deformation in Blender.

This is NOT cosmetic screenshot or a claimed lip-sync implementation.
Moves studio-authored ACT-Mouth_Move bone on a genuine imported GLB
and compares evaluated mesh vertices. Reports usable control axis,
vertex movement and limitations. Never changes source model.
"""
from pathlib import Path
import bpy,json,sys
from mathutils import Vector

CONTROL_NAMES=("ACT-Mouth_Move","Mouth_Bot.M","Mouth_Top.M","Lips_Bot","Lips_Top")
PROBES=(
    ("location","z",0.11),("location","y",0.11),("location","x",0.11),
    ("rotation_euler","x",0.18),("rotation_euler","y",0.18),
)

def measure_meshes(meshes,dg):
    values={}
    for mesh in meshes:
        evaluated=mesh.evaluated_get(dg)
        temporary=evaluated.to_mesh()
        if temporary:
            values[mesh.name]=(
                len(temporary.vertices),
                [tuple((mesh.matrix_world @ vertex.co)) for i,vertex in enumerate(temporary.vertices) if i%5==0]
            )
            evaluated.to_mesh_clear()
    return values

def compare(reference,other):
    moved=0
    peak=0.0
    for key,(n,coords) in reference.items():
        if key not in other or other[key][0]!=n:continue
        for a,b in zip(coords,other[key][1]):
            d=(Vector(a)-Vector(b)).length
            peak=max(peak,d)
            if d>0.0001:moved+=1
    return moved,peak

def run(original,result):
    source=Path(original).resolve()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    rigs=[x for x in bpy.data.objects if x.type=="ARMATURE"]
    if len(rigs)!=1:raise RuntimeError("Original actor skeleton not uniquely found")
    rig=rigs[0]
    meshes=[m for m in bpy.data.objects if m.type=="MESH" and m.data and len(m.data.vertices)>0]
    # Keep mesh test body-wide but log exactly the controller axis so true
    # speech-lip test can use narrower mouth geometry later.
    dg=bpy.context.evaluated_depsgraph_get()
    reference=measure_meshes(meshes,dg)
    results=[]
    for ctrl in CONTROL_NAMES:
        bone=rig.pose.bones.get(ctrl)
        if bone is None:continue
        for prop,axis,offset in PROBES:
            vec=getattr(bone,prop)
            pos={"x":0,"y":1,"z":2}[axis]
            original_value=vec[pos]
            vec[pos]=original_value+offset
            bpy.context.view_layer.update()
            other=measure_meshes(meshes,dg)
            moved,peak=compare(reference,other)
            results.append({"bone":ctrl,"mode":prop,"axis":axis,
                            "delta":offset,"moving_vertex_samples":moved,
                            "max_vertex_displacement":round(peak,6)})
            vec[pos]=original_value
            bpy.context.view_layer.update()
    best=sorted(results,key=lambda r:r["moving_vertex_samples"],reverse=True)
    payload={
        "model":source.name,
        "actor_bone_count":len(rig.data.bones),
        "tested_studio_face_controls":[r["bone"] for r in best],
        "probes":best,
        "mouth_bone_can_deform_mesh":bool(best and best[0]["moving_vertex_samples"]>=5
                                          and best[0]["max_vertex_displacement"]>0.002),
        "phoneme_viseme_accuracy_tested":False,
        "timeline_audio_lipsync_implemented":False,
        "source_model_not_modified":True,
    }
    path=Path(result)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,indent=2)+"\n")
    print("REAL_STUDIO_FACE_BONE_DEFORMATION_AUDIT",json.dumps(
        {k:v for k,v in payload.items() if k!="probes"}),flush=True)
    for item in best[:6]:
        print("PROFESSIONAL_ACTOR_FACE_PROBE",json.dumps(item),flush=True)
    if not results:
        raise RuntimeError("Artist rig does not expose any expected named mouth control")
if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:raise SystemExit("Usage Blender --python test_face.py -- input.glb report.json")
    run(*args)
