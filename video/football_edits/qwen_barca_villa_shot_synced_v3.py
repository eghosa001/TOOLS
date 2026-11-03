#!/usr/bin/env python3
"""Per-shot genuine Qwen3 Ryan narration V3: creator-paced names corrected using pronunciation references.

Explicitly prevents old mismatched one-take narration being laid blindly across footage.
Created for real 2026 Barcelona–Alavés / Aston Villa–Fulham action,
and genuine licensed CC player portraits. REVIEW AUDIO ONLY.
"""
import json,os
from pathlib import Path
import numpy as np
import soundfile as sf
import torch

OUT=Path("football_edit_output/qwen_barca_villa_shot_synced_v3")
OUT.mkdir(parents=True,exist_ok=True)
MODEL="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
SPEAKER="Ryan"

SCENES=[
 {"id":"hook_yamal","visual":"Lamine Yamal actually scoring vs Alaves, 31 Oct 2026",
  "text":"This is the warning for Aston Villa. Lamine Yamal needs only one opening to punish a defence."},
 {"id":"historical_h2h","visual":"Live actual 2026 football with explicitly labelled 1983 archival RESULT, no fake historical footage",
  "text":"There is history here. In nineteen eighty-three, Villa beat Barcelona three nil at home to win the European Super Cup, three one on aggregate."},
 {"id":"raphinha_goal","visual":"Actual Raphinha goal vs Alaves, 31 Oct 2026, complete finish",
  "text":"Barcelona scored six against Alavés. Here, Raphinha meets the ball and finishes. One loose assignment, and you're punished."},
 {"id":"jackson_fulham_goal","visual":"Actual Nicolas Jackson Aston Villa goal vs Fulham, 31 Oct 2026, goal and celebration",
  "text":"Now Villa's threat. Johan Manzambi releases Nicolas Jackson against Fulham. Jackson rides two challenges, then slots it home."},
 {"id":"yamal_maatsen_duel","visual":"Actual Commons photographs of Yamal and Maatsen, with actual 2026 Barca action",
  "text":"The first key matchup is Yamal against Ian Maatsen. Maatsen must block the inside run, without giving Yamal room to deliver."},
 {"id":"jackson_cubarsi_duel","visual":"Original camera photos of Jackson and Cubarsi, actual Jackson replay",
  "text":"At the other end, Jackson tests Pau Cubarsí. If Villa beat the first press, space behind Barcelona's high line becomes dangerous."},
 {"id":"form_and_tactics","visual":"Actual 2026 match build-up showing high line and opponents",
  "text":"Villa have won all three Champions League games. Barcelona have won two of three. The next mistake after losing possession could matter most."},
 {"id":"outro_key_matchup","visual":"Actual Villa and Barcelona scoring replays, not synthetic image",
  "text":"So which decides it: Yamal against Maatsen, or Jackson against Cubarsí? What's your score prediction?"}
]
torch.set_num_threads(max(1,min(4,os.cpu_count() or 4)))
torch.set_num_interop_threads(2)
from qwen_tts import Qwen3TTSModel
print("LOADING_REAL_QWEN",MODEL,flush=True)
model=Qwen3TTSModel.from_pretrained(MODEL,device_map="cpu",dtype=torch.float32,attn_implementation="sdpa")
results=[]
# Qwen3 offline CustomVoice does not use commercial-Qwen hot_fix or SSML.
# Pronounce difficult names through a *speech-only* respelling, while keeping
# canonical player spelling in the editorial/description metadata.
# Sources: UEFA 2025 pronunciation guide for Cubarsí, Catalan pronunciation on
# Forvo, Dutch surname vowels, Portuguese Raphinha and Swiss French Manzambi.
PRONUNCIATION = {
  "Lamine Yamal": "La-meen Yah-mal",
  "Yamal": "Yah-mal",
  "Raphinha": "Ra-feen-ya",
  "Alavés": "Ah-la-vess",
  "Johan Manzambi": "Yo-hahn Man-zam-bee",
  "Ian Maatsen": "Eeyan Maht-sen",
  "Maatsen": "Maht-sen",
  "Pau Cubarsí": "Pow Koo-bar-see",
  "Cubarsí": "Koo-bar-see",
}
def spoken_text(original):
    result=original
    import re
    for term,respell in sorted(PRONUNCIATION.items(),key=lambda kv:-len(kv[0])):
        result=re.sub(r"(?<!\\w)"+re.escape(term)+r"(?!\\w)",respell,result)
    return result
for i,scene in enumerate(SCENES):
    print("VOICE_BEAT_START",i,scene["id"],flush=True)
    wavs,sr=model.generate_custom_voice(text=spoken_text(scene["text"]),speaker=SPEAKER,language="English",instruct="Energetic fast paced football analyst with short natural pauses, crisp diction, enthusiastic confident delivery.")
    sound=np.asarray(wavs[0],dtype=np.float32).flatten()
    peak=float(np.max(np.abs(sound))) if sound.size else 0.0
    rms=float(np.sqrt(np.mean(sound*sound))) if sound.size else 0.0
    if sound.size<0.8*sr or not np.isfinite(sound).all() or rms<.004:
        raise RuntimeError("ACTUAL QWEN segment missing or invalid: "+scene["id"])
    filename=f'{i:02d}_{scene["id"]}_Qwen3_Ryan.wav'
    sf.write(OUT/filename,sound,sr,subtype="PCM_16")
    sec=sound.size/sr
    results.append({**scene,"spoken_text":spoken_text(scene["text"]),"pronunciation_source":"UEFA, Forvo, native phonology and verified football reference pronunciation","audio_file":filename,"seconds_raw":round(sec,3),"sample_rate":sr,"rms":round(rms,4),"peak":round(peak,4)})
    print("VOICE_BEAT_COMPLETE",scene["id"],round(sec,2),"RMS",round(rms,3),flush=True)
manifest={"model":MODEL,"speaker":SPEAKER,"language":"English","speed_final_edit":"1.40x pitch-preserving",
          "kind":"REAL QWEN GENERATED PER STORYBOARD SHOT WITH PRONUNCIATION FIXES","generated_background_images":False,
          "note":"No sound substitutions. Speech-only name respellings; visible captions retain authentic names. Visual timing must follow durations.",
          "scenes":results,"total_raw_s":round(sum(s["seconds_raw"] for s in results),2)}
(OUT/"shot_synced_narration_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print("ALL_SHOT_VOICES_RENDERED",manifest["total_raw_s"],flush=True)
