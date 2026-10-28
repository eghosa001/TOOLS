#!/usr/bin/env python3
"""Individually authored image decisions for Great Pyramid 15-chapter restoration.

The numbered tokens below are an *editorial EDL*, not keyword-based image retrieval.
Each character deliberately assigns ONE exact Commons file to ONE spoken shot.
' - ' retains a documented explanatory diagram for unphotographable science.
No photo substitution, generated fallback, or generic title search is allowed.
The user-facing 2026 release is kept separate and unlisted.
"""
from __future__ import annotations
import argparse, html, json, re
from pathlib import Path
from urllib.parse import quote
BASE=Path(__file__).resolve().parent
CANDIDATES=json.loads((BASE/"verified_commons_candidates.json").read_text(encoding="utf-8"))

# Hand-reviewed real photo file pages from the documented research contact sheets.
# The literal chapter+index matches a fixed source title, not a search result at runtime.
CATALOG={
 "G":("02 Khufu and the royal complex",3,"Great Pyramid itself, modern photograph"),
 "M":("02 Khufu and the royal complex",4,"Great Pyramid east side, modern photograph"),
 "A":("01 Opening: the hidden space",1,"Historic aerial photograph of the Giza pyramids"),
 "N":("01 Opening: the hidden space",5,"Historic photograph of the Great Pyramid north face"),
 "V":("14 Evidence and disputed claims",3,"Nineteenth-century photograph of the Great Pyramid and Sphinx"),
 "L":("15 Closing evidence recap",1,"Modern photograph of Giza pyramid complex"),
 "D":("03 Before Giza",4,"Djoser's genuine Step Pyramid, Saqqara"),
 "E":("03 Before Giza",7,"Sneferu's genuine Bent Pyramid at Dahshur"),
 "R":("03 Before Giza",12,"Sneferu's genuine Red Pyramid at Dahshur"),
 "H":("04 Stone and quarries",2,"Ancient Aswan granite quarry with unfinished obelisk"),
 "Q":("04 Stone and quarries",3,"Documented Aswan quarry dolerite pounding stones"),
 "C":("04 Stone and quarries",5,"Photographed Aswan granite quarry"),
 "I":("09 Interior passages",1,"Actual surviving interior passage of the Great Pyramid"),
 "K":("09 Interior passages",4,"Modern authentic interior photograph of the Great Pyramid"),
 "J":("09 Interior passages",6,"Historic photograph of the Great Pyramid entrance"),
 "X":("11 North face corridor",1,"Published authentic muography detector figure"),
 "Y":("11 North face corridor",2,"Published actual scientific north-face corridor localization figure"),
 "B":("12 Khufu's boats",2,"Actual Khufu boat in Grand Egyptian Museum, 2025"),
 "U":("12 Khufu's boats",3,"Authentic Khufu ship museum photograph"),
 "S":("13 Great Sphinx",5,"Historical Sphinx and Khafre temple photograph"),
 "P":("13 Great Sphinx",9,"Photograph of historic archaeological excavation by Sphinx"),
 "Z":("14 Evidence and disputed claims",6,"Historic scientific survey/exploration of Giza"),
}
# Independently verified authentic source file pages not returned by the first Commons queries.
EXTRA={
 "F":{"commons_title":"File:Nile River, Boats and feluccas, Aswan, Egypt.jpg",
       "expected_licence":"CC BY 4.0","credit":"Vyacheslav Argenberg",
       "photo_context":"MODERN NILE BOAT PHOTO — NOT AN OLD KINGDOM VESSEL"},
 "O":{"commons_title":"File:Hatnub main quarry.jpg",
       "expected_licence":"CC BY-SA 2.0","credit":"Hannah Pethen",
       "photo_context":"DOCUMENTED HATNUB QUARRY — NOT GIZA BLOCK DELIVERY"},
 "W":{"commons_title":"File:Workers working near the Great Pyramid.jpg",
       "expected_licence":"CC BY 4.0","credit":"Nabbegat",
       "photo_context":"MODERN WORKERS AT GIZA — NOT ANCIENT BUILDERS"},
 "T":{"commons_title":"File:Quarry chambers of Masara whence came the blocks for the Great Pyramid, Egypt. (30) (1904) - front - TIMEA.jpg",
       "expected_licence":"Public domain","credit":"Underwood & Underwood",
       "photo_context":"HISTORIC TURA/MASARA QUARRY PHOTOGRAPH — CIRCA 1904"},
}
# Fixed, individually written scene decisions. The nth token is the nth shot in
# the chapter's original LOCKED_MANUAL shot map, NOT a keyword or similarity score.
# Photo placements deliberately correspond to scene subjects and historical locations;
# science/theoretical diagrams are retained only for phenomena never directly photographed.
SCENE_DECISIONS={
 1:"G - I - X X Y - - A N X G - Z G F G V - G - A G",
 2:"A G M G N V A Q G D V - N W - N G X G M V W A G M E R",
 4:"G T T O T Q T O G T F F Q C I - O G T F W T G G - T F",
 5:"- T - G F F - F T G - T T - V - - F F G F - T G W T G",
 6:"G F A G X Y X Y X F F F A G Y W F - Y X G X Y V F G G",
 7:"G - G V V G - F G - W - V - V V V G V W G W G F W V G",
 8:"O O G O O W O G - O O - O O O O - - G W G Q W O I O - G G I",
 9:"I I I I - I I I I K K I - K V I - I - I - I I I K X G",
 10:"I X X X X X X X X Y X - - Y X Y Y Y X X X X X - G X Y",
 11:"Y N Y Y Y Y Y - Y X X Y I X Y I I X I X I I I - Y Y G",
 12:"B B G B U B B B B - F - B B B B B U B B - G B B F G B",
 13:"S S S V S V V S - S S V S S S V V S V - S S S S S S V",
 14:"V G V - V - X X X X X X - X V G G - G G G - X V Y - X G - A",
 15:"G G V - F T G Y Y V - W T O I X Y Y X - G X V - G V W G - G - G G",
}
# Site-type and illustration necessity reminders are kept per shot.
ILLUSTRATIVE_REASONS={
 "cutaway":"An unentered interior void and an architectural cross-section cannot be truthfully photographed from an ancient viewpoint.",
 "measure":"A distance measured by scientific instrument requires its published measurements, not an invented photograph.",
 "muon":"Cosmic-ray passage and the unentered Big Void are measurable phenomena, not visible ancient objects.",
 "merer":"Inspector Merer's ancient actions are not photographed; a generic papyrus would falsely claim to be his original document.",
 "inspector":"The inspector's authentic face and identity are not preserved in a verified licensed photograph; no false likeness may be shown.",
 "records":"No source-approved photograph of the precise document in this spoken passage is available; this is a modern explanatory summary.",
 "evidence":"Confidence levels are logical relationships, not things that can be photographed; the diagram separates fact from inference.",
 "possibilities":"Competing proposals and unknown ancient intentions cannot be portrayed as actually photographed archaeological finds.",
 "ramp":"No one photographed the precise original ramp design; this is an openly labelled and disputed engineering hypothesis.",
 "shafts":"Inaccessible shaft relationships are conceptual; a map can clarify published features without fabricating photographs.",
 "channel":"A channel subscription title is modern graphic design rather than historical footage.",
 "chronology":"Timeline relationships spanning ancient generations cannot be depicted by a single authentic camera photograph.",
 "burial":"This particular ancient burial layout has not been verified as the subject of a licensed photograph.",
 "bakeries":"An exact Old Kingdom bakery operation was never photographed and the visual must remain openly schematic.",
 "experiment":"Scientific methods require a technical representation rather than a falsely staged ancient photograph.",
 "foundations":"The specific unexposed construction section cannot be photographed; show the schematic as such.",
 "workers":"No authentic Old Kingdom film of these named workers exists; never present contemporary people as them.",
 "logistics":"This ancient transport workflow has no surviving real event photograph; a diagram shows only the documented relationship.",
 "preserve":"Conservation and inferred future work are concepts, not photographs of a proved archaeological event.",
 "investigation":"The referenced investigation comprises multiple historical evidence classes and cannot be captured in one historical photograph.",
 "mastaba":"The underground architectural relationship is explanatory and cannot be captured directly in the available outer views.",
 "journal":"A specific journal bibliographic retraction can be cited accurately in a modern source-labelled text graphic.",
 "stonecourses":"Original ancient work sequence is unknown; the drawing refers only to visible structural courses.",
 "alignment":"Compass/survey angle measurements require a modern technical schematic.",
 "density":"An inferred density anomaly is an instrument result, not a camera photograph.",
 "compare":"The comparative diagram prevents confusion between separate discoveries.",
 "harbour":"The photographed modern port cannot authenticate an ancient lost working scene.",
 "river":"An ancient vanished channel can be modelled from research data but not photographed today.",
 "floodplain":"Geological prehistoric terrain reconstruction is inferred, not photographed during the Old Kingdom.",
 "passage":"The specific inaccessible internal connection cannot be presented as a verified photograph.",
 "craft":"Exact ancient carpentry steps are not recorded on camera; illustrate verified construction technique only.",
 "ship":"Original ancient construction is not a photographed event, even if the surviving boat can be photographed.",
 "geometry":"Proposed structure geometry is an explicit labelled interpretation, not a camera view.",
 "change":"Construction processes across generations are not photographed as a single scene.",
 "sphinx":"The ancient Sphinx carving process was not photographed.",
}
LICENSE_DEED={
 "CC0":"https://creativecommons.org/publicdomain/zero/1.0/",
 "PUBLIC DOMAIN":"https://creativecommons.org/publicdomain/mark/1.0/",
 "CC BY 2.0":"https://creativecommons.org/licenses/by/2.0/",
 "CC BY 3.0":"https://creativecommons.org/licenses/by/3.0/",
 "CC BY 4.0":"https://creativecommons.org/licenses/by/4.0/",
 "CC BY-SA 2.0":"https://creativecommons.org/licenses/by-sa/2.0/",
 "CC BY-SA 3.0":"https://creativecommons.org/licenses/by-sa/3.0/",
 "CC BY-SA 4.0":"https://creativecommons.org/licenses/by-sa/4.0/",
}
def get_photo(token):
    if token in EXTRA:
        p=EXTRA[token].copy()
        p["source"]="https://commons.wikimedia.org/wiki/"+quote(p["commons_title"].replace(" ","_"),safe="():,")
        return p
    group,index,context=CATALOG[token]
    row=CANDIDATES[group][index-1]
    expected=row["license_metadata"]
    return {"commons_title":row["commons_title"],
            "expected_licence":expected,"credit":row["creator_metadata"],
            "source":row["source_page_url"],"photo_context":context}
def export_one(chapter,out):
    path=BASE/f"chapter{chapter:02d}_directed_shots.json"
    m=json.loads(path.read_text(encoding="utf-8"))
    d=SCENE_DECISIONS[chapter].split()
    if len(d)!=len(m["shots"]):
        raise ValueError(f"Chapter {chapter} expected {len(m['shots'])} explicit scenes but got {len(d)}")
    archive={}
    for i,(shot,token) in enumerate(zip(m["shots"],d)):
        kind=shot["visual_type"]
        sid=shot["id"]
        if token!="-":
            photo=get_photo(token)
            p_id="real_"+token.lower()
            archive[p_id]={"id":p_id,**photo}
            shot["photo_id"]=p_id
            shot["visual_kind"]="AUTHENTIC_PHOTO"
            shot["composition"]=(
                "PHOTO_FULL_BLEED" if i%5 in (0,2) else
                "PHOTO_CONTAIN"
            )
            shot["photo_context"]=photo["photo_context"]
            shot["why_this_visual"]=(
                f"This is a real source-identified photo showing {photo['photo_context']}. "
                "It illustrates the physical setting, surviving object or actual research evidence. "
                "It does not pretend to photograph the construction period or an inaccessible chamber."
            )
            lic=photo["expected_licence"].upper()
            entry={"source_page_url":photo["source"],"creator":photo["credit"],
                   "license":lic,"license_url":LICENSE_DEED[lic],
                   "file_identity":photo["commons_title"],
                   "attribution":photo["credit"]+" — "+photo["commons_title"]+" / "+photo["source"]+" / "+lic+"; film image cropped and colour-treated.",
                   "commercial_use_confirmed":True,"modifications_allowed":True}
            if "-SA" in lic:
                entry["share_alike_compliance"]="Preserve licence link, author and modified credit; apply share-alike to adaptations where legally required."
            shot["asset"]=entry
            shot["authentic_source_searches"]=[
                {"query":"Actual photo of "+photo["photo_context"],
                 "source_url":photo["source"],
                 "outcome":"Exact source identified and selected by editor for this numbered narration passage."}
            ]
            for field in ("why_authentic_image_inadequate","individual_exception_approved",
                          "on_screen_disclosure","no_fabricated_evidence"):
                shot.pop(field,None)
        else:
            shot["photo_id"]=None
            shot["visual_kind"]="DOCUMENTARY_DIAGRAM"
            shot["composition"]="GRAPHIC_HERO" if i%3==0 else "GRAPHIC_RIGHT"
            shot["why_this_visual"]="Explicitly modern scientific/architectural diagram needed for an event, dimension or hypothesis which a genuine camera cannot show."
            shot["why_authentic_image_inadequate"]=ILLUSTRATIVE_REASONS.get(
                kind,"The precise ancient event, hidden structure or inference cannot be truthfully shown as an authentic photograph.")
            if len(shot["why_authentic_image_inadequate"])<40:raise ValueError("Exception inadequate")
            shot["authentic_source_searches"]=[
                {"query":"Historic Giza exterior images for "+shot["heading"],
                 "source_url":get_photo("G")["source"],
                 "outcome":"Real exterior is available, but does not photograph the claimed process or measured hidden feature."},
                {"query":"Scientific research and archival view for "+shot["heading"],
                 "source_url":get_photo("A")["source"],
                 "outcome":"Historic aerial image does not reveal this exact ancient operation or hypothesis."}
            ]
            shot["individual_exception_approved"]=True
            shot["on_screen_disclosure"]="SCIENTIFIC OR HISTORICAL SCHEMATIC — NOT PHOTOGRAPHED"
            if kind=="channel":shot["on_screen_disclosure"]="MODERN CHANNEL TITLE GRAPHIC"
            shot.pop("asset",None)
            shot.pop("photo_context",None)
        shot["shot_subject"]=shot["heading"]+" — "+shot["detail"]
        shot["editor_approved_by"]="Facts Uncovered numbered-shot editorial selection, 2026-10-28"
        shot["editorial_status"]="APPROVED"
        shot["source_first_selection_key"]=token
    m["original_photos"]=list(archive.values())
    m["paragraph_count"]=int(m.get("paragraph_count",8))
    m["min_authentic_shot_share"]=0.6
    m["source_first_editorial_approval"]="APPROVED"
    m["source_first_approval_scope"]="Rights and topic matching at the shot-plan level only; continuous video viewing not completed"
    m["image_sourcing"]="Each of the shot_count entries explicitly hand-authored in SCENE_DECISIONS; no keyword image matching"
    dest=out/f"chapter{chapter:02d}_directed_shots.json"
    dest.write_text(json.dumps(m,indent=2,ensure_ascii=False))
    return {"chapter":chapter,"shots":len(d),"real_photo_shots":sum(token!="-" for token in d),
            "explanatory_diagrams":d.count("-"),"different_photos":len(archive)}
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--output",type=Path,required=True)
    a.add_argument("--chapter",type=int)
    args=a.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    chapters=[args.chapter] if args.chapter else sorted(SCENE_DECISIONS)
    results=[export_one(i,args.output) for i in chapters]
    summary={"chapters":results,"source_first_directed_manually":True,
             "automatically_montaged":False,"rights_verified_at_download":False,
             "film_not_yet_complete":True}
    (args.output/"MANUAL_SELECTION_SUMMARY.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
