#!/usr/bin/env python3
"""Enforce explicit preview -> reviewed preview -> full-render workflow.

Never launch an episode just because asset builds or commits succeeded.
Only the separately dispatched video workflow invokes this validator.
"""
import argparse
import json
import os
import re
import urllib.error
import urllib.request

WORKFLOW_NAME="CartoonStudio Godot Video — Manual Preview Then Approved Full"
PREVIEW_ARTIFACT="cartoonstudio-episode-preview-mp4"

def get_json(url,token):
    headers={"Accept":"application/vnd.github+json","User-Agent":"CartoonStudio-preview-approval-validator"}
    if token:
        headers["Authorization"]="Bearer "+token
    request=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(request,timeout=20) as response:
        return json.load(response)

def verify(mode, approval, preview_id,repo,token):
    if mode=="preview":
        if approval:
            raise ValueError("Preview does not require full-render approval")
        print("PREVIEW_ONLY_REQUESTED seconds=3 full=false")
        return
    if mode!="full":
        raise ValueError("Unsupported render step")
    if not approval:
        raise ValueError("Full render requires explicit reviewed-preview approval")
    if not re.fullmatch(r"[0-9]{6,20}",str(preview_id)):
        raise ValueError("Provide the successful prior preview workflow run ID")
    base="https://api.github.com/repos/"+repo+"/actions/"
    run=get_json(base+"runs/"+str(preview_id),token)
    if (run.get("name")!=WORKFLOW_NAME or run.get("event")!="workflow_dispatch"
            or run.get("conclusion")!="success"):
        raise ValueError("Referenced preview must be a successful manual CartoonStudio render")
    artifact_data=get_json(base+"runs/"+str(preview_id)+"/artifacts?per_page=100",token)
    if not any(a.get("name")==PREVIEW_ARTIFACT and not a.get("expired",False)
               for a in artifact_data.get("artifacts",[])):
        raise ValueError("Referenced preview has no available completed MP4 artifact")
    print("FULL_RENDER_APPROVED prior_preview_run=",preview_id,flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("preview","full"),required=True)
    p.add_argument("--approval",choices=("true","false"),default="false")
    p.add_argument("--preview-run-id",default="")
    p.add_argument("--repo",default=os.getenv("GITHUB_REPOSITORY","eghosa001/TOOLS"))
    x=p.parse_args()
    verify(x.mode,x.approval=="true",x.preview_run_id,x.repo,
           os.getenv("GH_TOKEN",""))
