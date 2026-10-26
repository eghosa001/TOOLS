#!/usr/bin/env python3
"""Independent genuine Blender Studio Elder Sprite/Rex mouth topology tests."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_real_studio_speaking_morphs import inspect_actor
from audit_actual_native_jaw_bone_motion import main as inspect_weighted_jaws

def main(source,out,actor):
    if actor not in ("elder_sprite","rex"):
        raise ValueError("Only official first-party Rex or Elder Sprite native source")
    root=Path(out).resolve()
    root.mkdir(parents=True,exist_ok=True)
    results=inspect_actor(source,actor)
    (root/f"{actor}-original-mouth-morphs.json").write_text(json.dumps(results,indent=2)+"\n")
    jaw=root/f"{actor}-original-weighted-jaw-motion.json"
    inspect_weighted_jaws(source,jaw,actor)
    found=json.loads(jaw.read_text())
    mechanically=bool(results["has_direct_mouth_open_or_phoneme_not_just_correctives"]
                      or found["individually_confirmed_deforming_jaw_bones"])
    report={
        "original_blender_studio_actor":actor,
        "original_source_file":Path(source).name,
        "raw_source_original_files_unchanged":True,
        "original_source_mouth_controller_count":len(results["mouth_named_pose_controllers"]),
        "native_direct_wav_capable_morph_keys":results["direct_mouth_open_or_phoneme_names"],
        "actual_mesh_deforming_jaw_bones":found["individually_confirmed_deforming_jaw_bones"],
        "direct_mechanical_mouth_candidate":mechanically,
        "complex_cloudrig_driver_interactions_tested":False,
        "actual_spoken_wav_sync_tested":False,
        "approved_episode_talking_role":False,
        "cast_identity_assigned":False,
        "episode_rendered":False
    }
    (root/f"{actor}-speech-conclusion.json").write_text(json.dumps(report,indent=2)+"\n")
    print("OFFICIAL_REAL_RIG_ELDER_REX_FACIAL_AUDIT",json.dumps(report),flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3:raise SystemExit("Blender --python audit_official_elder_rex_speech.py -- ORIGINAL.blend OUT_DIR elder_sprite|rex")
    main(*args)
