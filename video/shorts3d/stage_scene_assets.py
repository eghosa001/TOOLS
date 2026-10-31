#!/usr/bin/env python3
"""Stage only the assets chosen by the human editor in a 3D Short shotlist.

Never picks assets, invents scenes, falls back to generative art or auto-sequences media.
"""
from __future__ import annotations
import argparse,hashlib,json,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"library"))
from asset_library import catalog,import_assets
def build_plan(scene_path,known,workspace):
    scene=json.loads(scene_path.read_text(encoding="utf8"))
    if scene.get("format")!="vertical_3d_short":raise ValueError("Not a 3D Shorts manual timeline")
    needs=[]
    for part in scene.get("set",[]):
        id=part.get("asset")
        if not isinstance(id,str) or not re.fullmatch(r"[a-z0-9_-]{1,180}",id):
            raise ValueError("Unsafe asset ID in manual scene")
        if id in known:
            if known[id]["kind"]!="model":raise ValueError("Non-3D asset as scene model "+id)
            needs.append(id)
    world=scene.get("world",{})
    hdri=world.get("hdri_asset")
    if hdri:
        if hdri not in known or known[hdri]["kind"]!="hdr":
            raise ValueError("Unknown approved HDRI asset "+str(hdri))
        needs.append(hdri)
    return list(dict.fromkeys(needs))
def stage(scene_path,dest,library_root,download=False,allow_mit=False):
    known=catalog();ids=build_plan(scene_path,known,ROOT)
    selected=[known[id] for id in ids]
    if any(x["license"]=="MIT" for x in selected) and not allow_mit:
        raise ValueError("MIT character requires --allow-mit and legal notice")
    if download and selected:
        import_assets(selected,library_root,max_mb=350)
    staged=[]
    dest.mkdir(parents=True,exist_ok=True)
    for item in selected:
        ext=Path(item["path"]).suffix.lower()
        kind_folder="models" if item["kind"]=="model" else item["kind"]
        src=library_root/kind_folder/(item["id"]+ext)
        if not src.is_file():raise FileNotFoundError(f"Original {item['id']} not imported. Use --download only after shot approval")
        target=dest/(item["id"]+ext)
        if not target.exists() or hashlib.sha256(target.read_bytes()).digest()!=hashlib.sha256(src.read_bytes()).digest():
            shutil.copy2(src,target)
        staged.append({"asset_id":item["id"],"source":item["source_url"],"license":item["license"],
                       "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
                       "staged_name":target.name,"editor_selected_in":scene_path.name})
    if any(x["license"]=="MIT" for x in selected):
        notice=library_root/"LICENSE-Microsoft-Rocketbox-MIT.txt"
        if not notice.is_file():raise FileNotFoundError("License notice required for Rocketbox")
        shutil.copy2(notice,dest/notice.name)
    doc={"type":"explicit_human_scene_selection","items":staged,"no_generated_assets":True}
    (dest/"staged_manifest.json").write_text(json.dumps(doc,indent=2)+"\n")
    return doc
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("scene",type=Path)
    p.add_argument("--download",action="store_true")
    p.add_argument("--allow-mit",action="store_true")
    p.add_argument("--godot-assets",type=Path,default=ROOT/"godot"/"assets")
    p.add_argument("--library",type=Path,default=ROOT/"library"/"imported")
    a=p.parse_args()
    print(json.dumps(stage(a.scene,a.godot_assets,a.library,a.download,a.allow_mit),indent=2))
