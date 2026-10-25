#!/usr/bin/env python3
"""Measure speech anatomy on genuine six additional Singularity original rigs.

Do not treat successful asset extraction as evidence of a moving mouth.
Keep source masters unmodified and classify negative tests truthfully.
"""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_real_studio_speaking_morphs import inspect_actor
from audit_actual_native_jaw_bone_motion import main as inspect_bones
KNOWN=("doublemohawk","multifrog","mantaribs","doubleeye","plumpfly","coralboi")
if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3:raise SystemExit("Usage Blender --python audit_other_singularity_speech.py -- SOURCE.blend OUTPUT_DIR actor")
    original,root,actor=Path(args[0]).resolve(),Path(args[1]).resolve(),args[2]
    if actor not in KNOWN:raise ValueError("Only six independently imported original Singularity creatures are eligible")
    if not original.is_file():raise FileNotFoundError(original)
    root.mkdir(parents=True,exist_ok=True)
    shapes=inspect_actor(original,actor)
    jaw_path=root/f"{actor}-jaw-geometry.json"
    inspect_bones(original,jaw_path,actor)
    bones=json.loads(jaw_path.read_text(encoding="utf-8"))
    verified=bool(shapes["has_direct_mouth_open_or_phoneme_not_just_correctives"]
                  or bones["individually_confirmed_deforming_jaw_bones"])
    report={"original_blender_actor":actor,
        "actual_direct_open_morphs":shapes["direct_mouth_open_or_phoneme_names"],
        "actual_weighted_moving_bones":bones["individually_confirmed_deforming_jaw_bones"],
        "mechanically_opening_candidate":verified,
        "rhubarb_wav_alignment_tested":False,
        "independently_verified_speaking_lead":False,
        "original_artist_geometry_rebuilt":False,
        "series_canon_changed":False,
        "episode_video_rendered":False,
        "conservative_limit":"Complex rig controller/facial driver movement can escape a direct-bone check; negative result does not establish that no animation is possible"}
    (root/f"{actor}-conclusion.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ORIGINAL_SINGULARITY_NONHUMAN_ACTOR_SPEECH_CANDIDATE",json.dumps(report),flush=True)
