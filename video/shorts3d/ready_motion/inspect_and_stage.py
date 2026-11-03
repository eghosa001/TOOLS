#!/usr/bin/env python3
"""Stage the existing public-domain Knight, castle and 30-clip KayKit motion GLBs.
Never modify/copy any 2D animation files.
"""
import hashlib,io,json,pathlib,struct,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"stage_assets"
ACTOR="https://raw.githubusercontent.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0/672074b73ba276876a19e8816ecdc5241817ab47/addons/kaykit_character_pack_adventures/Characters/gltf/Knight.glb"
CASTLE="https://files.innerscene.com/library/castle-with-keep-1a75a9e1/be0d9411a3e3b580b2b5/castle-with-keep.glb"
MOTION="https://opengameart.org/sites/default/files/kaykit_character_animations_1.2.zip"
def download(url, cap):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (OpenAssetStaging/1.0)"})
    with urllib.request.urlopen(req,timeout=90) as r:
        content=r.read(cap+1)
    if len(content)>cap or len(content)<512: raise ValueError("Suspicious asset size")
    return content
def glb_json(data):
    if data[:4]!=b"glTF":raise ValueError("Not a GLB")
    _,version,length=struct.unpack_from("<III",data,0)
    n,t=struct.unpack_from("<II",data,12)
    if version!=2 or length!=len(data) or t!=0x4E4F534A:raise ValueError("Invalid GLB header")
    return json.loads(data[20:20+n])
def analyze(data):
    j=glb_json(data)
    nodes=j.get("nodes",[])
    targets={nodes[c["target"]["node"]].get("name","") for a in j.get("animations",[]) for c in a.get("channels",[]) if c["target"]["node"]<len(nodes)}
    return {"nodes":[x.get("name") for x in nodes],"skins":[{"joints":[nodes[n].get("name") for n in s.get("joints",[])]} for s in j.get("skins",[])],"animations":[x.get("name") for x in j.get("animations",[])],"targets":sorted(targets),"materials":len(j.get("materials",[])),"meshes":len(j.get("meshes",[]))}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sources={"knight":ACTOR,"castle":CASTLE}
    original={}
    for key,url in sources.items():
        filename=OUT/(key+".glb")
        if not filename.exists():filename.write_bytes(download(url,30_000_000))
        data=filename.read_bytes();original[key]={"url":url,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),"gltf":analyze(data)}
    z=download(MOTION,12_000_000)
    with zipfile.ZipFile(io.BytesIO(z)) as arc:
        filename="Animations/gltf/KayKit_AnimatedCharacter_v1.2.glb"
        data=arc.read(filename)
    (OUT/"kaykit_motion.glb").write_bytes(data)
    original["motion"]={"url":MOTION,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),"gltf":analyze(data)}
    knight=set(original["knight"]["gltf"]["nodes"]); motion=set(original["motion"]["gltf"]["targets"])
    shared=sorted(knight & motion)
    original["rig_match"]={"knight_nodes_matched_to_animated_targets":shared,"count":len(shared),"animation_count":len(original["motion"]["gltf"]["animations"])}
    (OUT/"RIG_COMPATIBILITY.json").write_text(json.dumps(original,indent=2))
    print("ASSET_RIG_INSPECTION",json.dumps({"knight_nodes":original["knight"]["gltf"]["nodes"][:90],"knight_skins":original["knight"]["gltf"]["skins"][:2],"motion_targets":original["motion"]["gltf"]["targets"],"matching":shared,"animations":original["motion"]["gltf"]["animations"],"castle_meshes":original["castle"]["gltf"]["meshes"]},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
