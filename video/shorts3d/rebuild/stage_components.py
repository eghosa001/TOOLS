#!/usr/bin/env python3
"""Stage pinned CC0 textures and a few real props for the CUSTOM BUILT historical 3D scenes.

Original art is a component library, not the scene layout. No asset model appears
as an entire London street or as the city of Constantinople.
"""
import json,sys,shutil,hashlib
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
MODELS=["kenney__pirate-kit__boat-row-large"]
def main():
    known=catalog()
    ids=["forge__textures__"+x+"__diff" for x in MATERIALS]+MODELS
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
        short=ident.removeprefix("forge__textures__").removesuffix("__diff")+".jpg" if item["kind"]=="texture" else "rowboat.glb"
        target=dest/short
        shutil.copyfile(origin,target)
        sources.append({"file":short,"asset_id":ident,"original_url":item["source_url"],"license":item["license"],"sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
    (dest/"source_manifest.json").write_text(json.dumps(sources,indent=2)+"\n")
    print("CUSTOM_SCENE_COMPONENTS_READY",len(sources))
if __name__=="__main__":main()
