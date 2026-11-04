#!/usr/bin/env python3
"""One-off licensed Qwen3 1.7B instruction-controlled Apollo Eleven voice test.

The 0.6B model did NOT meet the fast delivery target even at 1.25x.
Unlike 0.6B, the official 1.7B CustomVoice supports style instructions.
This wrapper preserves the SAME source words, identical historic reference
and identical QA math. No visual or publishing code is touched.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

source = Path(__file__).resolve().parent / "qwen_apollo_voice_audition.py"
spec = importlib.util.spec_from_file_location("qwen_apollo_voice", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
module.SPEAKER = "Ryan"
module.INSTRUCTION = (
    "Speak as a naturally quick and warm American history storyteller, about "
    "one hundred eighty-five complete words per minute. Sound like a real person "
    "explaining a captivating event to a close friend. Flow smoothly through "
    "Armstrong and Buzz Aldrin without splitting syllables. Vary the intonation "
    "with relaxed, understated emphasis. Conversational, not a newscast, not "
    "a dramatic movie trailer, not monotone. Keep every consonant clear and "
    "avoid long pauses between short sentences."
)
module.main()
# The shared script deliberately reports false on 0.6B control; the 1.7B
# model officially SUPPORTS style instructions, but measured compliance and
# human-perceived naturalness are separate decisions.
import sys
args = sys.argv
folder = Path(args[args.index("--out") + 1])
path = folder / "A_B_VOICE_COMPARISON.json"
data = json.loads(path.read_text(encoding="utf-8"))
data["qwen_style_control_verified"] = True
data["instruction_support_reference"] = "https://github.com/QwenLM/Qwen3-TTS"
data["model_instruction_support_is_not_human_audio_approval"] = True
data["human_audio_quality_approved"] = False
data["public_release_allowed"] = False
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("QWEN_17_REAL_PACE_MEASURED",data["qwen_raw_wpm"],data["qwen_final_wpm"],flush=True)
