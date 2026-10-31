#!/usr/bin/env python3
"""Stage pinned CC0 textures and a few real props for the CUSTOM BUILT historical 3D scenes.

Original art is a component library, not the scene layout. No asset model appears
as an entire London street or as the city of Constantinople.
"""
import json,sys,shutil,hashlib
from urllib.request import Request,urlopen
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"library"))
from asset_library import catalog, import_assets
MATERIALS=[
 "cobblestone_01","grey_plaster","rough_wood","clay_roof_tiles_02",
 "stone_brick_wall_001","medieval_red_brick","sandstone_blocks_05",
 "dirt_floor","mossy_cobblestone","roof_slates_03",
 "castle_brick_07","planks_brown_10",
]
MODELS=["kenney__pirate-kit__boat-row-large","kenney__nature-kit__tree-oak","kenney__nature-kit__tree-default"]
def main():
    known=catalog()
    ids=["forge__textures__"+x+"__diff" for x in MATERIALS]+MODELS+["forge__hdri__kloofendal_48d_partly_cloudy_puresky"]
    missing=[x for x in ids if x not in known]
    if missing:raise ValueError("Missing pinned original art "+str(missing))
    library=ROOT/"library"/"imported"
    dest=Path(__file__).resolve().parent/"assets"
    dest.mkdir(exist_ok=True,parents=True)
    report=import_assets([known[x] for x in ids],library,max_mb=95,max_file_mb=20,workers=8)
    sources=[]
    for item in report["assets"]:
        ident=item["id"]
        extension=Path(item["path"]).suffix
        origin=library/("models" if item["kind"]=="model" else item["kind"])/(ident+extension)
        short=(ident.removeprefix("forge__textures__").removesuffix("__diff")+".jpg" if item["kind"]=="texture" else ("tree_oak.glb" if "tree-oak" in ident else "tree_default.glb" if "tree-default" in ident else "rowboat.glb") if item["kind"]=="model" else "daylight_sky.hdr")
        target=dest/short
        shutil.copyfile(origin,target)
        sources.append({"file":short,"asset_id":ident,"original_url":item["source_url"],"license":item["license"],"sha256":hashlib.sha256(target.read_bytes()).hexdigest()})

    # Small licensed Kenney particle artwork supplies FIRE DETAIL, never prefabs.
    # Originals are pinned at the binary blob level before staging.
    effects=[
      ("fire_01.png","a83b6db8947cf7ea1c541d7184c160cde4da3339",99891),
      ("fire_02.png","8db26fe22e57fbac6a2fe2ddbe2f3821fb435e28",88453),
      ("smoke_01.png","1cd418e867b8f6bb7681c399d52dff2831fb5cb2",97452),
    ]
    rev="2b25427358dbfb6badd47f658ba71a6de748e548"
    for name,sha,size in effects:
        url="https://raw.githubusercontent.com/npmiaman/game-forge/"+rev+"/assets/sprites/particle-pack/"+name
        destfile=dest/("kenney_"+name)
        if destfile.exists():data=destfile.read_bytes()
        else:
            with urlopen(Request(url,headers={"User-Agent":"TOOLS-Godot-Cinematic/1.0"}),timeout=45) as response:
                data=response.read(size+1)
        h=hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()
        if h!=sha or len(data)!=size or not data.startswith(bytes.fromhex("89504e470d0a1a0a")):
            raise ValueError("CC0 original Kenney fire sprite checksum mismatch: "+name)
        if not destfile.exists():destfile.write_bytes(data)
        sources.append({"file":destfile.name,"asset_id":"kenney-cc0-particle-pack/"+name,
                        "original_url":"https://kenney.nl/assets/particle-pack",
                        "license":"CC0-1.0","sha256":hashlib.sha256(data).hexdigest()})
    (dest/"source_manifest.json").write_text(json.dumps(sources,indent=2)+"\n")
    print("CUSTOM_SCENE_COMPONENTS_READY",len(sources))
if __name__=="__main__":main()
