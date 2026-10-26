#!/usr/bin/env python3
"""Short technical animation only; eSpeak is NOT the proposed production voice."""
import argparse
import json
import subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--dir',type=Path,default=Path('artifacts/history2d-demo'));x=p.parse_args();out=x.dir.resolve();out.mkdir(parents=True,exist_ok=True)
    script='In this illustrative scene, a historian walks through the past. The figure uses articulated arms and legs, with recorded narration.'
    wav=out/'scene1.wav'
    import shutil
    if not shutil.which('espeak'):raise SystemExit('Requires espeak for smoke test: not a premium TTS voice')
    subprocess.run(['espeak','-s','155','-w',str(wav),script],check=True)
    from create_reference_rig import create
    create(out/'scholar','scholar')
    doc={'kind':'historical_2d_animation','title':'Technical demo: original jointed 2D animation, not an authentic historical documentary','characters':{'historian':{'rig':'scholar/rig.json'}},'scenes':[{'chapter':'Technical rig animation demonstration','stage':'medieval','visual_label':'STYLIZED TEST • NOT HISTORICAL EVIDENCE','audio':'scene1.wav','speaker':'historian','actors':[{'id':'historian','x':.5,'scale':.65,'action':'walk'}]}]}
    ep=out/'demo.json';ep.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf8');print(ep)

if __name__=='__main__':main()
