#!/usr/bin/env python3
"""Fail-closed editorial/asset release metadata validator. Human factual review still required."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

KINDS = {"archive", "3d", "map", "photo", "diagram"}
RIGHTS = {"CC0-1.0", "CC-BY-4.0", "public-domain-verified", "original"}

def validate(data, base, release=False):
    issues = []
    def check(ok, msg):
        if not ok: issues.append(msg)
    check(isinstance(data.get("title"), str) and len(data.get("title","")) > 12, "Specific title required")
    check(bool(data.get("date_or_period")) and bool(data.get("location")), "Historical period and location required")
    check(data.get("format") == "original_historical_documentary", "Invalid program format")
    sources = data.get("research_sources", [])
    check(isinstance(sources, list) and len(sources) >= 2, "At least two independently sourced references required")
    domains = set()
    for entry in sources if isinstance(sources, list) else []:
        if not isinstance(entry, dict):
            issues.append("Malformed historical source"); continue
        url = urlparse(str(entry.get("url","")))
        check(url.scheme == "https" and bool(url.hostname) and not url.username and
              bool(entry.get("publisher")) and bool(entry.get("supports")), "Invalid source metadata")
        if url.hostname: domains.add(url.hostname)
    check(len(domains) >= 2, "Sources must span two independent domains")
    shots = data.get("shots", [])
    check(isinstance(shots,list) and bool(shots), "Shotlist required")
    for n, shot in enumerate(shots if isinstance(shots,list) else [], 1):
        label = "shot " + str(n)
        if not isinstance(shot,dict): issues.append(label+" is malformed"); continue
        check(shot.get("kind") in KINDS and bool(shot.get("purpose")),label+" requires type and editorial purpose")
        if shot.get("kind") in ("3d","diagram"):
            check(shot.get("label") == "historical reconstruction",label+" missing reconstruction label")
        if release:
            relative = shot.get("asset","")
            check(bool(relative) and isinstance(relative,str),label+" missing licensed local asset")
            if not isinstance(relative,str) or not relative: continue
            target = (base / relative).resolve()
            if not target.is_relative_to(base.resolve()) or not target.is_file():
                issues.append(label+" asset missing or outside working folder"); continue
            check(hashlib.sha256(target.read_bytes()).hexdigest()==shot.get("sha256"),label+" SHA-256 mismatch")
            check(shot.get("rights") in RIGHTS and bool(shot.get("creator")) and
                  bool(shot.get("rights_url")),label+" missing rights proof")
            if shot.get("rights")=="CC-BY-4.0":
                check(bool(shot.get("attribution")),label+" missing required attribution")
    if release:
        for flag in ("original_script_approved","historical_accuracy_reviewed",
                     "visual_qc_approved","audio_rights_approved","release_approved"):
            check(data.get(flag) is True,flag+" must be true")
    return issues

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("episode",type=Path);p.add_argument("--release",action="store_true")
    args=p.parse_args()
    errors=validate(json.loads(args.episode.read_text(encoding="utf8")),args.episode.parent,args.release)
    if errors:
        for e in errors:print("FAIL:",e)
        raise SystemExit(1)
    print("PASS:","release metadata (not video preview)" if args.release else "storyboard schema")
