# Original 3D kiwi slicing — 31 October 2026

**Status: rendered 6-second private 3D technical prototype. NOT premium / publication approved.** This is a genuinely 3D moving-scene render, unlike the previous live-action fig stock-footage example. The visual realism, cutting dynamics and knife finish remain below the owner's strict 9/10 visual benchmark.

## Google Drive — verified outputs

- [720 × 1280, 24fps MP4 with accepted soft-fruit recorded Foley](https://drive.google.com/file/d/1WwwcbB1mNRWtrDXoEir6-XfIs6MbqZQl/view?usp=drivesdk) — 144 video frames, 6.000 s, SHA256 `c73b72ac4bce6891a247654e320ae444396e6e822c3219933018b958330c2597`.
- [540 × 960 data-saving mobile MP4](https://drive.google.com/file/d/1vr-JGA9ALr7e_cI7G2J8nK45ZzPfJ-aW/view?usp=drivesdk) — SHA256 `253127ed9b0b87dabd4cf43150d12f33b9ff637e801f73488b01b18a1cb7b156`.
- [Nine-frame storyboard/contact sheet](https://drive.google.com/file/d/1-9qJ1oKD7uGgKNzsngUmUnQIo-wPBltM/view?usp=drivesdk)
- [Full factual technical QA and exact rights evidence](https://drive.google.com/file/d/1zcNUiYlVqa9VUC08Y6zfp4CQw1jOon-P/view?usp=drivesdk)
- [Authorized CC0 Poly Haven photo-scanned kiwi source bundle](https://drive.google.com/file/d/14fFTjMJUxQR7vyCjur3P8Q5H5niA2k8x/view?usp=drivesdk)
- [Reproducible 3D rendering Python](https://drive.google.com/file/d/1fD-ONxQcMyobN5IYIeGjS4FS1RHaheG8/view?usp=drivesdk)
- [Approved gentle soft-fruit 48 kHz/24-bit PCM Foley master](https://drive.google.com/file/d/1WUbqS_BHUXyOR1jAwlk8ypNxwd_bFm-s/view?usp=drivesdk) — SHA256 `57704fc7e4409fcd56e611bf471587524fd1f649b6198d7b20335a68a6d887d4`.

[Open the complete Google Drive folder](https://drive.google.com/drive/folders/1xTqsO2-mDLAdr6wZ_Ieh-7iDJ6aG7_8_).

## Verified licensing

- Fruit mesh: [Poly Haven Food Kiwi 01](https://polyhaven.com/a/food_kiwi_01), photogrammetry by Oliver Harries, [CC0](https://polyhaven.com/license); downloaded via [Poly Haven API](https://api.polyhaven.com/files/food_kiwi_01). **Powered by Poly Haven**. The 3D fruit exterior source includes an actual 4,313-vertex photo-scanned geometry, 7,748 source triangles, textures and originals. UV seams in the scan were addressed by vertex-color baking and mesh smoothing. The 3D cut surface, studio scene, cutting board and animated knife are new authored geometry. Original user-provided strawberry reference footage is NOT used.
- Sound: [Freesound frodeims #812387](https://freesound.org/people/frodeims/sounds/812387/), originally recorded genuine gentle tomato cutting, [CC0](https://creativecommons.org/publicdomain/zero/1.0/); original permitted HQ audio preview source SHA256 `8323de2b393b31d6df1b208fa5339821ce1ab2462dfe1ca2b40c0d10399dc0fa`. Same six-second sound profile previously explicitly approved by the owner. The original phone/video is NOT used. No counterfeit or unlicensed reference footage/audio.

## 3D and audiovisual quality checks

- 144/144 720p frames decoded, constant 24fps, no detected black or frozen frames.
- Full H.264/AAC mux 6.0s, native 720 × 1280 9:16 frame, stereo 48 kHz.
- No >=0.45s near-silent intervals at -55 dBFS/100ms RMS windows, integrated approximately -24.1 LUFS, true peak -5.0 dBTP.
- Single continuous downward knife movement with a visible fruit split and original radial seeded interior. User-approved soft fruit Foley continues during the cutting contact; tail includes release/handling.
- **Not certified:** complete headphone listening approval of the NEW kiwi master, premium material realism, believable soft-body physics, fine metal/shadow polish, publication or YouTube monetization eligibility.

## Reusable, no-credit-cost production sources

- [Download CC0 scan in clean GitHub runner](../production/kiwi_acquire.py) and [source workflow](../../../../.github/workflows/asmr-kiwi-3d-source.yml).
- [Render author-directed true 3D frames in Python/VTK](../production/kiwi3d/render_kiwi_3d.py).
- [Reproduce original user-approved CC0 Foley](../production/kiwi3d/prepare_approved_soft_foley.py).
- [Manual GitHub cloud render wrapper](../production/kiwi3d/run_in_github_actions.sh), invoked through [workflow_dispatch](../../../../.github/workflows/asmr-kiwi-3d-render-and-foley.yml).

**Release gate:** The owner approved the characteristic SOFT FRUIT SOUND on the prior fig revision. That is not approval of this kiwi visual, new audiovisual parity, or release. Future productions must not claim 9/10 simply because signal/file tests pass.
