#!/usr/bin/env python3
"""Import original Kenney CC0 3D scene FX sprites; not AI art or generated geometry."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from urllib.request import urlopen,Request
REV="2b25427358dbfb6badd47f658ba71a6de748e548"
ORIGIN="https://github.com/npmiaman/game-forge/blob/"+REV+"/assets/sprites/particle-pack/"
ROOT=Path(__file__).resolve().parents[1]/"godot"/"assets"
SOURCES=[["fire_01.png",99891,"a83b6db8947cf7ea1c541d7184c160cde4da3339","fire"],["fire_02.png",88453,"8db26fe22e57fbac6a2fe2ddbe2f3821fb435e28","fire"],["smoke_01.png",97452,"1cd418e867b8f6bb7681c399d52dff2831fb5cb2","smoke"],["smoke_02.png",96825,"d866368ade39e8976cc5fd23f86523f8387fe713","smoke"]]
def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for filename,size,sha,kind in SOURCES:
        target=ROOT/("historical_"+filename)
        url="https://raw.githubusercontent.com/npmiaman/game-forge/"+REV+"/assets/sprites/particle-pack/"+filename
        if target.is_file():data=target.read_bytes()
        else:
            with urlopen(Request(url,headers={"User-Agent":"TOOLS-History-Shorts-CC0/1.0"}),timeout=35) as f:
                data=f.read(220000)
        if len(data)!=size or blob(data)!=sha or not data.startswith(bytes.fromhex("89504e470d0a1a0a")):
            raise ValueError("Original Kenney "+filename+" failed pinned blob/integrity check")
        if not target.is_file():target.write_bytes(data)
        rows.append({"file":target.name,"source":ORIGIN+filename,"license":"CC0-1.0","sha256":hashlib.sha256(data).hexdigest()})
    (ROOT/"historical_fx_source_manifest.json").write_text(json.dumps({"source":"Kenney Particle Pack","official":"https://kenney.nl/assets/particle-pack","copyright":"CC0-1.0","files":rows},indent=2)+"\n")
    print("ORIGINAL_KENNEY_CC0_FX_IMPORTED",len(rows))
if __name__=="__main__":main()
