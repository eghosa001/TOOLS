# The Ninefold Tide — Natural AI Voice Production

This is the dedicated free-first voice studio for all 14 recurring characters. Read the canonical [Drive voice guide](https://docs.google.com/document/d/1hjalqkcACCJYyQ5sXVXGfv2ZsGkEhxGXV0LZs9L0NhU/edit), [Episode 101 v2](https://docs.google.com/document/d/1f3ACxh4rUrafPbcZV8KJSzTbM4x5nIwVuGtVfd1xRd8/edit), and [Pilot Handoff](https://docs.google.com/document/d/1uEkF-T7kziU_gEz1VaRWSnWQjz-PQJIfp-DBX9bYBSM/edit). Canon text and name spellings are never silently changed.

## Model choice

* **Primary:** [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) 1.7B VoiceDesign creates original synthetic references. In a **separate run**, the 1.7B Base model reuses the same reference WAV/transcript via create_voice_clone_prompt for each dialogue line. Both official checkpoints are Apache-2.0.
* **Expressive A/B:** [Chatterbox](https://github.com/resemble-ai/chatterbox) MIT open-source. Its original model provides emotional exaggeration controls; Turbo provides optional vocal-reaction tags. Neither is automatically approved.
* Piper is not the first-choice character acting model. Do not copy anyone's actual voice without permission; do not pitch-shift an adult voice to impersonate a 12-year-old.

Qwen3 Base **does not offer VoiceDesign's natural-language per-line emotion instruction**. Three seeds provide candidate takes but not guaranteed interpretation. Recast individual emotionally weak lines through alternative models, with the SAME approved synthetic speaker anchor and a human comparison for identity drift.

## Bandwidth and GPU

The two Qwen model repositories are roughly 4.5 GB **each**, plus dependencies. Run on a genuinely available free Kaggle CUDA GPU when possible, not on the user's metered mobile connection. Save the downloaded checkpoints in a reusable cache or mounted dataset within Kaggle rules. The worker loads VoiceDesign and Base in separate processes, never together, and uses FP16 + SDPA for T4-class GPUs. Do not assume a GPU is available until checked.

## Workflow

In the GitHub repository on a GPU-enabled Linux machine:

~~~bash
python -m pip install -U qwen-tts soundfile
python video/ninefold_tide/audio/voice_pipeline.py prepare
python video/ninefold_tide/audio/qwen_audio_worker.py gpu-check
# Requires explicit permission for huge downloads on the remote machine:
python video/ninefold_tide/audio/qwen_audio_worker.py design --characters naya,kito,iri --allow-download
python video/ninefold_tide/audio/qwen_audio_worker.py perform --characters naya,kito,iri --takes-per-line 3 --name-drills --allow-download
# Chatterbox original is an alternative after pip installing chatterbox-tts:
# python video/ninefold_tide/audio/qwen_audio_worker.py perform --engine chatterbox-original --characters kito --allow-download
python video/ninefold_tide/audio/voice_pipeline.py audit --stage casting
python video/ninefold_tide/audio/voice_pipeline.py audit --stage release
~~~

Omitting --allow-download makes the inference stage use only locally cached weights. All generated files go to the gitignored workspace. Each real WAV stays unapproved, even after successful synthesis.

## Natural performance checks

* Kito: believable preteen, rapid boast -> genuine startled stammer -> fear; never chipmunk or adult narrator.
* Naya: annoyed sharpness -> precise rescue instructions; emotional vulnerability stays audible.
* Iri: calm trained commands with breath/physical effort, not an artificial announcer.
* The other 11 have separate vocal character descriptions, reference text and planned emotions in cast.json.
* Each key line has three contrasting director interpretations in pilot_voice_lines.json. These are guidance for audition selection; the Qwen Base model does not automatically receive these as acting instructions.
* Pronunciation lexicon has 32 names/places. All hints are provisional until listened to, compared across speakers and explicitly approved. The names command never invents phonetic fixes.
* Artificially accelerating audio to fit a short edit is forbidden. Re-time the manually authored shot when needed.
* Scores for naturalness, emotional truth, identity, clarity, age, names and adjacent-speaker interaction are reviewed by listening; require no subscore below 4/5 and mean at least 4.5/5. The final WAV must have a verified hash and zero serious clipping.

## Evidence and release gates

audio/voice_pipeline.py performs canon matching, voice-reference identity checks, PCM signal checks, exact selected WAV hash, pronunciation lock and review checks. Every candidate has NOT APPROVED status by default. No video editor or automated model may self-certify age, dialect, timbre, acting, rights or name quality. Approved WAVs and voice anchors belong with the existing Ninefold Tide project in Drive. The local folder is working storage, not proof of uploaded files.
