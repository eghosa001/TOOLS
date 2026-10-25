#!/usr/bin/env python3
"""Find direct FIRST-PARTY animation demo downloads and record licence evidence.

Search only official blender.org pages. This is discovery, not 3D character
generation. Never import a model unless a subsequent real-geometry audit passes.
"""
import html.parser
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

PAGES=[
    "https://www.blender.org/download/demo-files/",
    "https://download.blender.org/demo/splash/",
    "https://download.blender.org/demo/asset-bundles/",
    "https://download.blender.org/demo/",
]
TERM=re.compile(r"sprite.?fright|blender.?3\.0|animation.?fundamental|rain|snow|ellie|cartoon|character|rig|animal|creature|pet.?projects",re.I)

class Anchors(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.result=[]
        self.active=None
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            self.active={"href":dict(attrs).get("href",""),"caption":""}
    def handle_data(self,data):
        if self.active is not None:
            self.active["caption"]+=data
    def handle_endtag(self,tag):
        if tag=="a" and self.active is not None:
            self.result.append(self.active)
            self.active=None

def inspect(out):
    entries=[]
    for page in PAGES:
        try:
            req=urllib.request.Request(page,headers={"User-Agent":"Mozilla/5.0 CartoonStudio-Creator/1.0"})
            with urllib.request.urlopen(req,timeout=30) as resp:
                data=resp.read(5_000_000).decode("utf-8","replace")
            parser=Anchors()
            parser.feed(data)
            for item in parser.result:
                href=urllib.parse.urljoin(page,item["href"])
                if not href.startswith(("https://www.blender.org/","https://download.blender.org/")):
                    continue
                if not TERM.search(href+" "+item["caption"]):
                    continue
                entries.append({"from_page":page,"href":href,"caption":item["caption"].strip()[:100]})
            print("OFFICIAL_BLENDER_DISCOVERY",page,"anchors",len(parser.result),
                  "matches",len([e for e in entries if e["from_page"]==page]),flush=True)
        except Exception as e:
            print("SOURCE_ERROR",page,str(e)[:150],flush=True)
    output=Path(out)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(entries,indent=2)+"\n",encoding="utf-8")
    if not entries:
        raise RuntimeError("No official Blender demo animation source links found")
    for item in entries:
        print("SOURCE_LINK",item["href"],item["caption"],flush=True)

if __name__=="__main__":
    import sys
    inspect(sys.argv[1])
