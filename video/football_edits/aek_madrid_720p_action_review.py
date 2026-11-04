#!/usr/bin/env python3
"""Cut 720p editorial action excerpts, never unauthorized distribution.
Only exact original match 2026 sources, triple short sequences per fixture.
"""
import json,subprocess,re,os
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path("football_edit_output/aek_madrid_2026_action_720p");ROOT.mkdir(parents=True,exist_ok=True)
SOURCES={
"city_aek":{"url":"https://www.cbssports.com/watch/champions-league/video/manchester-city-vs-aek-athens-game-highlights",
 "title":["Manchester City","AEK"],"windows":[[39,49],[67,77],[107,120]]},
"madrid_leipzig":{"url":"https://www.cbssports.com/watch/champions-league/video/real-madrid-vs-rb-leipzig-game-highlights-2",
 "title":["Real Madrid","Leipzig"],"windows":[[63,74],[184,195],[208,220]]}}
notes={}
for name,info in SOURCES.items():
    r=requests.get(info["url"],timeout=40,headers={"User-Agent":"Mozilla/5.0 (editorial research; licensed filming and commentary check)"})
    r.raise_for_status()
    source=None
    for t in BeautifulSoup(r.text,"html.parser").find_all("script",attrs={"type":"application/ld+json"}):
        try:q=json.loads(t.string or t.get_text())
        except Exception:continue
        for v in (q if isinstance(q,list) else [q]):
            if v.get("@type")=="VideoObject" and all(x in str(v.get("name","")) for x in info["title"]):
                source=v.get("contentUrl");break
        if source:break
    if not source or not source.startswith("https://sports.play.cbsi.video/"):raise RuntimeError("Exact source missing: "+name)
    filt=[];outputs=[]
    for i,(a,b) in enumerate(info["windows"]):
        filt.append(f"[v{i}]trim=start={a}:end={b},setpts=PTS-STARTPTS,scale=-2:720,fps=30,format=yuv420p[s{i}]")
        outputs.append(f"[s{i}]")
    graph="[0:v]split=3"+''.join(f"[v{i}]" for i in range(3))+";"+';'.join(filt)+";"+''.join(outputs)+"concat=n=3:v=1:a=0[out]"
    out=ROOT/(name+"_720p_action_review.mp4")
    p=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-i",source,
            "-filter_complex",graph,"-map","[out]","-an","-c:v","libx264","-preset","veryfast","-crf","23","-movflags","+faststart",str(out)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=250)
    if p.returncode:raise RuntimeError(name+" extraction failed: "+p.stderr.decode(errors="replace")[-1600:])
    if out.stat().st_size<3000000:raise RuntimeError(name+" exported stream invalid/too small")
    check=subprocess.check_output(["ffprobe","-v","error","-show_entries","stream=width,height:format=duration,size","-of","json",str(out)])
    meta=json.loads(check)
    print("ACTION_EXTRACT_OK",name,json.dumps(meta)[:800],flush=True)
    sec=0;mapshots=[]
    for i,(a,b) in enumerate(info["windows"]):
        mapshots.append({"original_in_seconds":a,"original_out_seconds":b,"compiled_in_seconds":sec,"compiled_out_seconds":sec+b-a})
        sec+=b-a
    notes[name]={"source":info["url"],"match_title":" / ".join(info["title"]),"source_windows":mapshots,"probe":meta,
      "rights":"Current broadcast copyright NOT CLEARED. Do not publish without separate commercial licence or researched lawful exception."}
    for i,s in enumerate([1,sec*.50,sec-1]):
        subprocess.run(["ffmpeg","-v","error","-y","-ss",str(s),"-i",str(out),"-frames:v","1",str(ROOT/f"{name}_720_review_{i}.jpg")],check=True,timeout=20)
(ROOT/"clip_map_and_rights.json").write_text(json.dumps(notes,indent=2))
