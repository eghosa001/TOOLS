#!/usr/bin/env python3
"""Compatibility entrypoint for the retired 2026-10-29 texture-lab montage.

The original version mixed unrelated materials and endlessly looped a
five-second Foley recording across the full 180s. That export was rejected.
Use the editor-approved one-material shot+contact-cue manifest instead.
No automatic stock substitutions, no recycled Foley bed, no fake approval.
"""
import os
from pathlib import Path
from build_cohesive_episode import build

def assemble():
    root=Path(os.environ.get("ASMR_FILM_OUT","artifacts/asmr_3min")).resolve()
    manifest=Path(os.environ.get("ASMR_EPISODE_MANIFEST",str(root/"episode_manifest.json"))).resolve()
    if not manifest.is_file():
        raise RuntimeError(
            "BLOCKED: the retired random-stock 3-minute montage cannot run. "
            "Provide editor-approved episode_manifest.json, uniquely edited "
            "single-material video takes and per-contact licensed Foley. "
            "See production/build_cohesive_episode.py and ASMR_EPISODE_AUDIO_RULES.md.")
    return build(manifest,root/"COHESIVE_ASMR_3_MINUTES_720x1280.mp4")

if __name__=="__main__":
    assemble()
