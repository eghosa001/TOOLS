# The Glass Meridian — original 2D animated-series preproduction

**Status:** concept illustration delivered; character rigging, actual animation and voiced WAV auditions have **not yet been produced or approved**.

## Goal and reference

Build a 15-minute original fantasy-adventure episode with *The Legend of Korra* as an **art-direction and action-quality benchmark**, never as a source of copied characters, plot, costumes or footage. Strong silhouettes, cinematic painted backgrounds, anatomy-led poses, real character acting and clean expressive faces come before duration. Do not accept a procedural stick figure, static-image slideshow, camera-pan-only scene or over-smoothed AI morph as animation.

This is an independent fiction series, deliberately separate from the Facts Uncovered documentary projects. Respect the repository prohibition on automatic video assembly: a director/editor must author each shot and approve its timing and visuals; tools can render that approved timeline.

## Completed in this initial check-in

- Four **original** detailed, age-specific, recurring characters with design and movement specifications: `cast.json`.
- Six audition dialogue exchanges with emotionally directed beats and intentional pauses: `pilot_lines.json`.
- A Qwen3-TTS voice audition CLI: `voice_pipeline.py`. No fabricated audio claims. It supports preflight without downloading models, experimental voice-design auditions and reference-based consistent-voice auditions (two separately loaded models to fit constrained GPU VRAM).
- First illustrated ensemble/turnaround concept created in ChatGPT, currently **not stored in GitHub**; see `ART_HANDOFF.md`.

## Real production phases, not automatic quality assertions

1. Character lock: approve the original concept, then paint **true model sheets** (front, 3/4, profile, back) and matching separated head/body/mouth layers; front/profile/backs must match proportions. Current AI picture is *not* proof of turnarounds.
2. Cast voices and approve a recurring reference for each. Special attention to Kito (11): sound legitimately youthful, never a pitch-shifted adult or caricature. Honor accent/consent/licences and check pronunciation by ear.
3. Directed pilot: hand-animate 20–30 seconds with a real turnaround, facial acting, speech, contact animation and an impact/recovery moment. Animators control key poses and in-betweens.
4. Quality gate: full audiovisual viewing of pilot; reject face drift, missing mouth forms, sliding feet, deformed hands, unmotivated pauses, inaccurate names, robotic intonation, inconsistent background perspective, bad mixing and unstable motion.
5. Build 1-minute coherent scene; only then scope a 15-minute original episode. Individual shots are editor-approved, and only changed shots get re-rendered.

## GPU options

Do **not** assume Kaggle access, exact GPU, or remaining credits/hours. When available, use a T4 with FP16/SDPA inference in a short GPU notebook session. The T4 **does not support native BF16**. Run `python voice_pipeline.py preflight` on any normal CPU before installing TTS; audition and casting need model downloads and accelerator access. Model loading is sequential to avoid loading both models at once.

## Voice audition on Kaggle

```bash
pip install -U qwen-tts soundfile
python video/glass_meridian/voice_pipeline.py preflight
python video/glass_meridian/voice_pipeline.py cast --out /kaggle/working/glass-meridian-voices
python video/glass_meridian/voice_pipeline.py audition --out /kaggle/working/glass-meridian-voices --strategy clone
# Alternative A/B: expressive but may drift in identity:
python video/glass_meridian/voice_pipeline.py audition --out /kaggle/working/glass-meridian-voices --strategy design
```

Verify the current Qwen3-TTS install instructions and CUDA/PyTorch compatibility in each notebook runtime. The Qwen3-TTS VoiceDesign and Base models are distinct downloads; a free Kaggle session may fail due to memory/disk/availability and has not been benchmarked here.

`preflight` exports a transparent plan, never pretending to have generated WAV. `cast` creates reusable synthetic audition voice references. `audition --strategy clone` synthesizes each beat with the same voice reference and joins in actual gaps between beats. Since the Base cloning API lacks a per-line emotion instruction, `clone` **does not enforce acting direction**: the human director selects/times/retakes lines. `design` applies direction instructions but voice identity may vary, so it is only an experimental A/B audition.

No synthetic voice is approved until listeners check name pronunciation, emotion, age impression, cadence, intelligibility, audio artifacts and consistency. For a published cartoon, a human-performed line may be substituted when AI voices fail. Preserve explicit consent and licences for any real-person reference, especially minor voices.

## Official tools

- Qwen3-TTS code and examples: https://github.com/QwenLM/Qwen3-TTS (Apache 2.0)
- Resemble Chatterbox fallback: https://github.com/resemble-ai/chatterbox (MIT)
- OpenToonz: https://opentoonz.github.io/e/
- Krita: https://krita.org/
- Rhubarb offline lip-sync cue generation: https://github.com/DanielSWolf/rhubarb-lip-sync

These are candidate tools, not an assertion that full production-quality animation or audio has already been created.
