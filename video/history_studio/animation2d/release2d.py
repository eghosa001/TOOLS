#!/usr/bin/env python3
"""Fail-closed documentary publication metadata check (not a quality score)."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_LICENSES={"CC0-1.0","CC-BY-4.0","public-domain-verified","original"}


def valid_url(s):
    if not isinstance(s,str):return False
    u=urlparse(s)
    return u.scheme=="https" and bool(u.hostname) and not u.username and not u.password


def validate(episode,root):
    failures=[]
    def require(ok,explanation):
        if not ok:failures.append(explanation)
    require(episode.get("format")=="history_2d_cartoon","Incorrect episode format")
    require(episode.get("production_status")=="final_human_reviewed","No professional/human review status")
    research=episode.get("research_sources",[])
    domains=set()
    for x in research if isinstance(research,list) else []:
        if not isinstance(x,dict):failures.append("Invalid citation entry");continue
        require(valid_url(x.get("url")) and bool(x.get("supports")),"Unverifiable source")
        domain=urlparse(str(x.get("url", ""))).hostname
        if domain:domains.add(domain)
    require(len(domains)>=2,"Two independent historical research domains required")
    review=episode.get("review",{})
    for flag in ("historical_accuracy","visual_quality","script_originality","rights_clearance","audio_quality","human_signoff"):
        require(review.get(flag) is True,"Missing human review: "+flag)
    voice_rights=episode.get("voice_rights")
    require(isinstance(voice_rights,dict) and valid_url(voice_rights.get("source_url")),
            "Voice/speech commercial-use provenance missing")
    licensed=episode.get("asset_rights",{})
    used=set()
    for character in episode.get("characters",{}).values():used.update((character.get("sprites") or {}).values())
    for scene in episode.get("scenes",[]):
        for k in ("background_image",):
            if scene.get(k):used.add(scene[k])
        if not scene.get("background_image"):
            failures.append("Generated placeholder backgrounds cannot be published")
        for actor in scene.get("actors",[]):
            sprites=episode.get("characters",{}).get(actor.get("id"),{}).get("sprites",{})
            required={"head","torso","upper_arm","lower_arm","thigh","shin","foot"}
            if not sprites or not required.issubset(sprites):
                failures.append("Placeholder or incomplete character art is not publishable")
            if actor.get("speaking") and "mouth_open" not in sprites:
                failures.append("Speaking character requires an authored mouth layer")
    for rel in sorted(used):
        target=(root/rel).resolve()
        if not target.is_relative_to(root.resolve()) or not target.is_file():
            failures.append("Missing or unsafe illustration "+str(rel));continue
        item=licensed.get(rel)
        if not isinstance(item,dict):failures.append("No asset rights proof for "+rel);continue
        require(item.get("license") in ALLOWED_LICENSES,"Unapproved visual licence: "+rel)
        require(valid_url(item.get("source_url")) and bool(item.get("creator")),"Missing creator/source rights: "+rel)
        require(item.get("sha256")==hashlib.sha256(target.read_bytes()).hexdigest(),"Wrong art checksum: "+rel)
        if item.get("license")=="CC-BY-4.0":require(bool(item.get("attribution")),"Required attribution absent: "+rel)
    require(bool(used),"No artist-drawn historical scenes supplied")
    return failures


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("episode",type=Path)
    a=p.parse_args(argv)
    epi=json.loads(a.episode.read_text(encoding="utf8"))
    issues=validate(epi,a.episode.parent)
    if issues:
        for issue in issues: print("BLOCKED:",issue)
        raise SystemExit(1)
    print("RIGHTS_AND_REVIEW_METADATA_VERIFIED — human reviewer responsible for correctness")

if __name__=="__main__":main()