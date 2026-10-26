#!/usr/bin/env python3
"""Locate actual OFFICIAL published Blender Studio free CC-BY cartoon rig binaries.

Inspect only first-party pages/links (no scraping mirrors, gated downloads or
unauthorized bypass). Do not claim a rig was imported until downloaded and
opened by compatible Blender. This is discovery, not a model or episode render.
"""
import html.parser
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

PUBLISHER="https://studio.blender.org"
ACTORS=("elder-sprite","rex","sprite")

class AnchorScanner(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag!="a":return
        attributes=dict(attrs)
        if attributes.get("href"):
            self.links.append({"href":attributes["href"],"download":attributes.get("download"),
                               "class":attributes.get("class"),"aria_label":attributes.get("aria-label")})


def safe_url(url):
    parsed=urllib.parse.urlparse(url)
    return parsed.scheme=="https" and parsed.hostname in {
        "studio.blender.org","download.blender.org","storage.blender.org",
        "cloud.blender.org","www.blender.org"
    }


def inspect(slug):
    url=f"{PUBLISHER}/characters/{slug}/v1/"
    request=urllib.request.Request(url,headers={"User-Agent":"CartoonStudio-public-free-asset-intake/1.0"})
    status=None
    try:
        with urllib.request.urlopen(request,timeout=30) as response:
            status=response.status
            content=response.read(3_000_000).decode("utf-8",errors="replace")
            actual=response.url
    except Exception as exc:
        return {"character":slug,"official_page_url":url,"page_accessible":False,
                "reason":f"{type(exc).__name__}: {str(exc)[:150]}",
                "downloadable_first_party_binary_verified":False,"source_license":"CC BY listed on official public page"}
    parser=AnchorScanner()
    parser.feed(content)
    candidates=[]
    for entry in parser.links:
        href=urllib.parse.urljoin(actual,entry["href"])
        if not safe_url(href):continue
        if re.search(r"download|\.blend(?:\.gz)?|\.zip(?:\?|$)|\.blend1",href,re.I) or entry["download"]:
            candidates.append({"url":href.split("?")[0],"file_extension_looks_binary":bool(
                re.search(r"\.(?:blend|zip|blend\.gz)$",urllib.parse.urlparse(href).path,re.I)),
                "download":entry["download"]})
    unique=list({x["url"]:x for x in candidates}.values())
    return {"character":slug,"official_page_url":url,"page_accessible":True,
            "page_status":status,"html_bytes":len(content),
            "published_free_page_mentions_license":("CC-BY" in content or "CC BY" in content),
            "official_download_candidates":unique[:20],
            "downloadable_first_party_binary_verified":False,
            "original_blend_imported_into_blender":False,
            "speaking_face_audited":False,
            "creator_visual_identity_approved":False}


def main():
    out=Path("artifacts/official-free-cartoon-character-discovery")
    out.mkdir(parents=True,exist_ok=True)
    results=[inspect(actor) for actor in ACTORS]
    record={"publisher":"Blender Studio","first_party_free_licenses":"CC BY; attribution required",
            "original_source_intake_candidates":results,"download_attempted":False,
            "copyright_protection":"No untrusted mirror or paywall bypass, no user credentials",
            "models_installed":0,"canon_changed":False,"episode_rendered":False}
    (out/"OFFICIAL_SOURCE_ONLY_FREE_RIG_DISCOVERY.json").write_text(json.dumps(record,indent=2)+"\n")
    print("OFFICIAL_BLENDER_STUDIO_RIG_LINK_DISCOVERY",json.dumps(results),flush=True)


if __name__=="__main__":main()
