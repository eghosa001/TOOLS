#!/usr/bin/env python3
"""Build a render-agnostic rehearsal package from exact canonical story.

No procedural fallback, no Kaggle token, no unapproved character mapping.
This is intentionally NOT a render trigger: models are only source candidates.
Future per-episode story dialogue is never rewritten.
"""
import argparse,hashlib,json
from pathlib import Path
from godot_episode_timeline import compile_timeline

EXPECTED_LICENSE="CC BY 4.0"
REJECTED=("quaternius","kaykit","procedural","clay","placeholder","prototype","low_poly","low-poly")
def compile_review(story_file,library_file,output_dir):
    story_file=Path(story_file).resolve()
    library_file=Path(library_file).resolve()
    output=Path(output_dir).resolve()
    story_bytes=story_file.read_bytes()
    story=json.loads(story_bytes.decode("utf-8"))
    catalog=json.loads(library_file.read_text(encoding="utf-8"))
    models=catalog.get("models",{})
    if len(models)<15 or len(models)!=len(set(models)):
        raise ValueError("At least fifteen DISTINCT actual authored character sources needed")
    checksums=set()
    for identity,record in models.items():
        if str(record.get("license",""))!=EXPECTED_LICENSE:
            raise ValueError("Commercial licence not verifiable for "+identity)
        basename=str(record.get("asset_file",""))
        if any(bad in (identity+" "+basename).lower() for bad in REJECTED):
            raise ValueError("Rejected low-detail source: "+identity)
        sha=record.get("sha256")
        if not isinstance(sha,str) or len(sha)!=64 or not all(c in "0123456789abcdef" for c in sha):
            raise ValueError("Missing actual source SHA-256 "+identity)
        if sha in checksums:
            raise ValueError("Duplicated actual source model "+identity)
        checksums.add(sha)
    if not isinstance(story.get("dialogue"),list) or len(story["dialogue"])<1:
        raise ValueError("Missing episode dialogue")
    active=set(story.get("characters",{}))
    if not active:raise ValueError("Missing speakers")
    if any(entry.get("speaker") not in active for entry in story["dialogue"]):
        raise ValueError("Dialogue speaker has no stable character key")
    output.mkdir(parents=True,exist_ok=True)
    timing=compile_timeline(story,output/"timeline")
    stored=story_file.read_bytes()
    if stored!=story_bytes:raise RuntimeError("Canonical story has been modified")
    suggested={
        "title":story["title"],
        "source_story_sha256":hashlib.sha256(story_bytes).hexdigest(),
        "dialogue_sha256":timing["dialogue_sha256"],
        "original_dialogue_lines":len(story["dialogue"]),
        "all_original_dialogue_preserved":all(
            line["text"]==event["text"] and line["speaker"]==event["speaker"]
            for line,event in zip(story["dialogue"],timing["events"])),
        "story_active_keys":list(story["characters"]),
        "real_artist_authored_models_available":len(models),
        "artist_model_candidates":list(models.keys()),
        "model_library_reference_workflow_run":40233910527,
        "model_library_source_artifact":"cartoonstudio-15plus-licensed-professional-original-rig-candidates",
        "selected_story_character_models":{key:None for key in story["characters"]},
        "visual_mapping_approved":False,
        "full_lip_sync_quality_verified":False,
        "all_actor_source_files_mounted_for_episode":False,
        "preview_rendered":False,
        "full_render_approved":False,
        "ready_to_render":False,
        "recommended_manual_step":"Review actual character images and choose canonical character-to-model assignments before preview",
        "no_fallback_policy":"No old procedural clay, KayKit or Quaternius 3D actor may ever be substituted",
        "copyright_policy":"Credit Blender Studio and specific source creators under CC BY in description/credits",
        "renderer_note":"Prefer Blender native .blend rigs to preserve studio materials and facial controllers; GLB import may degrade both",
        "audio_note":"Estimated timing only, until original dialogue voice WAVs have been generated and duration validated",
        "assets_reference_only":"This lightweight review package does NOT contain or install the large .blend models; use the separately uploaded real-model artifact"
    }
    (output/"PROFESSIONAL_EPISODE_REVIEW.json").write_text(json.dumps(suggested,indent=2)+"\n",encoding="utf-8")
    if not suggested["all_original_dialogue_preserved"]:
        raise RuntimeError("Original dialogue changed")
    print("HIGH_QUALITY_PRODUCTION_REVIEW_PLAN_READY",
          "real_model_candidates",len(models),
          "original_dialogue_lines",len(story["dialogue"]),
          "original_story_sha256",suggested["source_story_sha256"],
          "canon_changed=false","render_started=false",flush=True)
    return suggested
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--story",default="video/story.json")
    p.add_argument("--library",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    compile_review(a.story,a.library,a.output)
