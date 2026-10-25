#!/usr/bin/env python3
"""Conservative native-Blender facial screening of genuine DOGWALK actor masters.

Chocomel/Pinda remain unapproved identities even if they pass jaw geometry.
Read-only originals, no GLB material loss, no new character, no episode render.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_real_studio_speaking_morphs import inspect_actor
from audit_actual_native_jaw_bone_motion import main as inspect_jaw

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("Usage Blender --python audit_native_dogwalk_speech.py -- SOURCE.blend OUTPUT_DIR pinda|chocomel")
    source, output, actor = Path(args[0]).resolve(), Path(args[1]).resolve(), args[2]
    if actor not in ("pinda", "chocomel"):
        raise SystemExit("Must test a genuine, independently extracted original DOGWALK artist character")
    if not source.is_file():
        raise FileNotFoundError(source)
    output.mkdir(parents=True, exist_ok=True)
    shapes = inspect_actor(source, actor)
    jaw_path = output / (actor + "-weighted-jaw-geometry.json")
    inspect_jaw(source, jaw_path, actor)
    bones = json.loads(jaw_path.read_text())
    direct = shapes["has_direct_mouth_open_or_phoneme_not_just_correctives"]
    deformers = bones["individually_confirmed_deforming_jaw_bones"]
    conclusion = {
        "actor": actor,
        "original_native_blender_filename": source.name,
        "direct_noncorrective_mouth_morph_detected": bool(direct),
        "moving_weighted_jaw_bones": deformers,
        "mechanical_mouth_candidate": bool(direct or deformers),
        "wav_driven_speech_tested": False,
        "phoneme_lip_sync_verified": False,
        "visual_quality_speaking_ready": False,
        "user_approved_new_series_design": False,
        "technical_note": "Automatic conservative direct-bone and morph checks cannot validate a controller-driven face with complex Blender drivers. A negative result does not disprove all artist facial possibilities.",
        "no_episode_rendered": True,
    }
    (output / (actor + "-face-conclusion.json")).write_text(json.dumps(conclusion, indent=2) + "\n")
    (output / (actor + "-mouth-key-report.json")).write_text(json.dumps(shapes, indent=2) + "\n")
    print("ORIGINAL_DOGWALK_THIRD_SPEAKER_SCREEN", json.dumps(conclusion), flush=True)
