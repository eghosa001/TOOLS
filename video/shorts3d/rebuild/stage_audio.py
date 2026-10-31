#!/usr/bin/env python3
"""Create verified reusable free Foley for history films. No commercial audio services."""
from __future__ import annotations
import hashlib,json,sys,shutil
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"library"))
from asset_library import catalog,import_assets
DEST=Path(__file__).resolve().parent/"audio"
KENNEY={
 "forge__sounds__impact-sounds__impactwood_heavy_000":"timber-impact.ogg",
 "forge__sounds__impact-sounds__footstep_concrete_000":"steps-stone.ogg",
 "forge__sounds__sci-fi-sounds__lowfrequency_explosion_000":"low-impact-boom.ogg",
}
def main():
    DEST.mkdir(parents=True,exist_ok=True)
    indexed=catalog()
    records=[]
    chosen=[]
    for ident in KENNEY:
        if ident not in indexed:raise ValueError("Missing pinned Kenney CC0 Foley: "+ident)
        chosen.append(indexed[ident])
    output=import_assets(chosen,ROOT/"library"/"imported",max_mb=12)
    for row in output["assets"]:
        origin=ROOT/"library"/"imported"/"audio"/(row["id"]+".ogg")
        target=DEST/KENNEY[row["id"]]
        shutil.copy2(origin,target)
        records.append({"name":target.name,"source":row["source_url"],"license":"CC0-1.0",
                        "sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
    # Source: AntumDeluge, OpenGameArt #16327, public domain/CC0.
    # 22.8 KB OGG sample. If the CDN blocks automated retrieval, keep
    # the Kenney originals and do NOT replace it with unlicensed sound.
    url="https://opengameart.org/sites/default/files/fire-1_0.ogg"
    try:
        with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=40) as response:
            data=response.read(300000)
        if not (20000<len(data)<300000 and data.startswith(b"OggS")):
            raise ValueError("Fire CC0 clip invalid")
        target=DEST/"fire-crackle.ogg"
        target.write_bytes(data)
        records.append({"name":target.name,"source":"https://opengameart.org/content/fire-crackling",
                        "original_file":url,"license":"CC0-1.0",
                        "sha256":hashlib.sha256(data).hexdigest()})
    except Exception as exc:
        print("CC0_FIRE_CLIP_UNAVAILABLE_KEEP_LICENSED_KENNEY_ONLY",str(exc)[:180])
    (DEST/"LICENSED_FOLEY_MANIFEST.json").write_text(json.dumps(records,indent=2)+"\n")
    print("FREE_LICENSED_FOLEY_READY",len(records))
if __name__=="__main__":main()
