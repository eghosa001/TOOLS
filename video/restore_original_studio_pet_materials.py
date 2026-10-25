#!/usr/bin/env python3
"""Review-only restoration of CC-BY Blender Studio Wing It! pet materials.

The official 3.6 Pet Projects splash ZIP omits critical TIFF color maps.
Keep every original mesh, rig, morph target and binary buffer intact; provide
a distinct, openly labelled PBR colour approximation using existing source
material-slot names and official public character-design stills.

These are MATERIAL RESTORATIONS, not Blender Studio's original textures, and
cannot become series canon without actual visual review.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct

CAT={
"suit_blue":"#2376BF","suit_red":"#DC514B","patch_dark_gray":"#424954",
"patch_light_gray":"#D0D3DB","patch_red":"#D75650","blue_dark":"#123A70",
"fur_dark":"#929AA4","ear":"#E6A2AD","lines_black":"#252C39",
"eyebrows":"#363C46","highlights":"#FFFFFF",
"fur_spikes_bright":"#B5BAC4","metal":"#A6B5C3","goggles":"#41444F",
"goggles_red":"#CE5545","goggles_glass":"#6F9CB3","claws":"#D8DDE2",
"fur_bright":"#F0F2F1","inner_mouth":"#33202B","fur_lips":"#8C919A",
"nose":"#E6A0B7","nose_dark":"#A7657B","pupils":"#1F2531",
"shoes":"#303C51","teeth":"#FFF7E7","tongue":"#E88D92"}
DOG={
"suit_orange":"#ED8D23","suit_red":"#EA551D","tape":"#D8AA77",
"straps":"#909EAA","straps_dark":"#4D586A","boots":"#234888",
"boots_sole":"#263652","metal":"#9FAFBB","suit_blue":"#2867B3",
"suit_blue_dark":"#173C7A","eye_highlights":"#FFFFFF",
"eyes_white":"#FFF8E6","fur":"#BA7A3D","fur_dark":"#815025",
"inner_mouth":"#301C24","metal_collar":"#ADB4BE","nose":"#20252D",
"eyes_pupils":"#171C22","teeth":"#FCF4E7","togue":"#D76C7C"}

def parts(raw):
    if raw[:4]!=b"glTF" or len(raw)!=struct.unpack_from("<I",raw,8)[0]:
        raise ValueError("Malformed original GLB")
    blocks=[]
    offset=12
    while offset<len(raw):
        count,kind=struct.unpack_from("<I4s",raw,offset)
        offset+=8
        blocks.append((kind,raw[offset:offset+count]))
        offset+=count
    js=[json.loads(part.decode()) for kind,part in blocks if kind==b"JSON"]
    if len(js)!=1:raise ValueError("Missing GLB JSON")
    return js[0],blocks

def color(c):
    def srgb(v):
        t=int(v,16)/255
        return t/12.92 if t<=.04045 else ((t+.055)/1.055)**2.4
    return [srgb(c[p:p+2]) for p in (1,3,5)]+[1.]

def restore(source,destination,key):
    palette=CAT if key=="cat" else DOG
    data,blocks=parts(Path(source).read_bytes())
    fixed={"light blue":"#7DC7E4","lines.dark_brown":"#392D24"}
    present={x.get("name","") for x in data.get("materials",[])}
    expected={"cat."+v for v in CAT}|{"light blue"} if key=="cat" else {"dog."+v for v in DOG}|{"lines.dark_brown"}
    if present!=expected:
        raise ValueError("Original professional source material names changed unexpectedly: "+str(present^expected))
    keep={field:json.dumps(data.get(field),sort_keys=True) for field in ("meshes","nodes","skins","accessors","bufferViews","buffers")}
    for mat in data["materials"]:
        name=mat["name"]
        rgb=fixed[name] if name in fixed else palette[name.partition(".")[2]]
        shader=mat.setdefault("pbrMetallicRoughness",{})
        shader.clear()
        shader.update({"baseColorFactor":color(rgb),
                       "metallicFactor":.55 if "metal" in name else .02,
                       "roughnessFactor":.34 if ("goggle" in name or "metal" in name or "nose" in name) else .70})
        for field in ("normalTexture","occlusionTexture","emissiveTexture","extensions"):
            mat.pop(field,None)
        mat["alphaMode"]="OPAQUE"
        mat["doubleSided"]=True
        mat["name"]=name+" [reference colour restoration — not original TIFF]"
    if any(json.dumps(data.get(f),sort_keys=True)!=v for f,v in keep.items()):
        raise AssertionError("Source geometry, rig or morph metadata changed")
    j=json.dumps(data,separators=(",",":"),ensure_ascii=False).encode()
    j+=b" " * (-len(j)%4)
    final=b""
    for kind,part in blocks:
        if kind==b"JSON":part=j
        final+=struct.pack("<I4s",len(part),kind)+part
    binary=b"glTF"+struct.pack("<II",2,12+len(final))+final
    output=Path(destination)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(binary)
    new,new_blocks=parts(binary)
    if len(new.get("skins",[]))!=1 or len(new.get("meshes",[]))<20:
        raise ValueError("Original high detail skeleton/meshes lost")
    old_bins=[hashlib.sha256(x).hexdigest() for k,x in blocks if k==b"BIN\x00"]
    new_bins=[hashlib.sha256(x).hexdigest() for k,x in new_blocks if k==b"BIN\x00"]
    if old_bins!=new_bins:raise AssertionError("Underlying original GLB mesh and morph bytes were changed")
    return {"name":key,"source":"Blender Studio Wing It! CC BY",
            "source_original":"https://www.blender.org/download/demo-files/",
            "appearance":"REFERENCE-GUIDED REVIEW ONLY; NOT ORIGINAL TEXTURES",
            "user_approved":False,"file":output.name,"bytes":output.stat().st_size,
            "skins":len(new["skins"]),"meshes":len(new["meshes"]),
            "binary_mesh_rig_and_morph_data_unchanged":True}
def main(originals,output):
    root=Path(originals)
    out=Path(output)
    all=[]
    for key in ("cat","dog"):
        all.append(restore(root/(key+"-professional.glb"),out/(key+"-studio-restored.glb"),key))
    (out/"RESTORATION_PROVENANCE.json").write_text(json.dumps(all,indent=2)+"\n")
    print("AUTHENTIC_PET_MATERIAL_RESTORATION_PASS",json.dumps(all),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("originals")
    p.add_argument("output")
    a=p.parse_args()
    main(a.originals,a.output)
