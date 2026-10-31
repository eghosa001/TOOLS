# Rain on textured glass — Kandinsky 6 Lite five-second ASMR experiment

This run deliberately tests a **simpler ambient ASMR format**, not foam cutting or compression. It reuses the previously successful Kaggle T4 + Diffusers Kandinsky 6 Lite image-to-audio-video pipeline.

- Reference: original vertical rain macro image, cropped to remove player controls, SHA256-pinned in `reference_manifest.json`.
- Motion: single continuous tripod shot; subtle droplets drift downward and merge while glass and bokeh composition stay stable.
- Audio: gentle rain-on-glass patter, no speech/music.
- Video: 480×864, 121 frames at 24 fps, ~5.1 seconds, model-generated synchronized audio.
- Model: `kandinskylab/Kandinsky-6.0-Lite-distill-5s-Diffusers`, 10 steps, seed 20261101.
- Resource budget: only one Kaggle generation. No alternate model, paid credits, fallback CGI video, or continuous rerun.
- Quality gate: technical pass requires actual MP4 + H.264 video & AAC audio streams; content must be manually checked for droplet geometry, slow downward movement, stable bokeh and synchronized rain sound.
- The previous Kandinsky foam branch and its rendered videos remain unchanged. This code lives on a separate rain experiment branch and stays unpublished pending inspection.

Workflow: `.github/workflows/asmr-kandinsky6-rain-kaggle.yml`; source is `kaggle_generate.py`; packaging reuses `../prepare_i2v_reference.py`.
