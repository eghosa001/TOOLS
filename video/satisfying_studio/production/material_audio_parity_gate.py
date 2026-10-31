#!/usr/bin/env python3
"""Pre-release structural ASMR sound/material/medium parity gate.

Compares an editor's time-coded visual and Foley observations. Can catch
documented hard-chop/soft-fig errors and false 3D claims, but does NOT listen to
sound or see physics; human or AV-capable editorial approval remains mandatory.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

MEDIUM={"CGI_3D","LIVE_ACTION_STOCK","HYBRID"}
FORCE_ORDER={"none":0,"delicate":1,"gentle":2,"moderate":3,"hard":4}

def check_manifest(d:dict, for_release:bool=False)->dict:
    blocks=[]; warnings=[]
    def fail(msg):blocks.append(msg)
    visual=d.get("visual",{})
    audio=d.get("foley",{})
    fps=d.get("fps")
    if type(fps) is not int or fps<=0:fail("Missing positive integer native delivery FPS")
    medium=visual.get("medium")
    req=visual.get("requested_medium")
    if medium not in MEDIUM:fail("Declare actual visual medium")
    if req not in MEDIUM|{"ANY"}:fail("Declare requested visual medium")
    if medium in MEDIUM and req in MEDIUM and medium!=req:
        fail("Requested visual medium mismatch: "+str(req)+" versus actual "+str(medium))
    if medium=="CGI_3D" and not visual.get("3d_scene_provenance"):
        fail("A true 3D video needs independently verifiable 3D scene/render provenance")
    if medium=="LIVE_ACTION_STOCK" and visual.get("3d_scene_provenance"):
        fail("Live-action footage cannot be claimed as a 3D render")
    if d.get("reference_clip_used_as_source"):
        fail("A user-supplied reference clip cannot be the production source without verified rights")
    if not visual.get("licensed_source"):
        fail("Missing independent video source/rights ledger")
    if not audio.get("licensed_source"):
        fail("Missing independent Foley source/rights ledger")
    if not audio.get("recorded_foley",False):
        warnings.append("AI-generated or unspecified Foley; verify commercial terms and material realism")

    vac=d.get("visual_action_structure")
    aac=d.get("foley_action_structure")
    if vac not in {"continuous_slice","discrete_chops","press","tear","pour","ambient","other"}:
        fail("Visual action structure not declared")
    if vac!=aac:
        fail("Foley action structure mismatch: visible "+str(vac)+" versus sound "+str(aac))
    if vac=="continuous_slice":
        vr=visual.get("contact_frame_range",[])
        ar=audio.get("contact_frame_range",[])
        if not (len(vr)==2 and len(ar)==2 and all(type(v)==int for v in [*vr,*ar])):
            fail("Continuous slice needs observed picture AND sound frame ranges")
        elif abs(vr[0]-ar[0])>1 or abs(vr[1]-ar[1])>1:
            fail("Continuous Foley contact duration not aligned within one frame")
    vc=visual.get("complete_cut_count")
    ac=audio.get("complete_cut_count")
    if type(vc) is not int or type(ac) is not int or vc<0 or ac<0:
        fail("Declare actual complete-cut counts on picture and Foley")
    elif vc != ac:
        fail(f"Number of completed cuts differs: visible {vc}, audio {ac}")
    vf=visual.get("force")
    af=audio.get("force")
    if vf not in FORCE_ORDER or af not in FORCE_ORDER:
        fail("Declare force for picture AND sound")
    elif abs(FORCE_ORDER[vf]-FORCE_ORDER[af])>1:
        fail(f"Audible impact strength {af} does not match visible force {vf}")
    vm=visual.get("texture_family")
    am=audio.get("texture_family")
    if not vm or not am:
        fail("Visual and recorded material/texture family mandatory")
    elif vm!=am:
        fail(f"Material/texture mismatch: picture {vm}, recorded Foley {am}")
    visible=d.get("visual_transients",[])
    sound=d.get("audible_transients",[])
    if len(visible)!=len(sound):
        fail("Number of discrete visual and audible contact transients differs")
    else:
        for i,(v,a) in enumerate(zip(visible,sound)):
            if not all(type(z.get("frame")) is int and z.get("kind") for z in (v,a)):
                fail("Missing frame or kind for transient "+str(i)); continue
            if v["kind"]!=a["kind"] or abs(v["frame"]-a["frame"])>1:
                fail(f"Transient {i}: visible {v['kind']}@{v['frame']} versus sound {a['kind']}@{a['frame']}, tolerance 1 frame")

    if for_release:
        review=d.get("human_or_av_capable_review",{})
        if review.get("status")!="APPROVED":
            fail("Release requires completed full-length visual + headphone audition with material parity review")
        if not review.get("master_sha256") or not review.get("review_evidence"):
            fail("Approval must identify the exact export SHA256 and review evidence")
    return {
       "passed_structural_checks":not blocks,"release_approved":for_release and not blocks,
       "blocking_issues":blocks,"warnings":warnings,
       "limitation":"Self-reported shot/timecode metadata only. Passing cannot establish true audio-video semantic quality without real playback review."
    }

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("manifest",type=Path);p.add_argument("--release",action="store_true")
    a=p.parse_args()
    result=check_manifest(json.loads(a.manifest.read_text()),for_release=a.release)
    print(json.dumps(result,indent=2))
    if result["blocking_issues"]:raise SystemExit(2)
if __name__=="__main__":main()
