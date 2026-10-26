# Tiny Trails, Big Surprises — E01 production package

**Title:** The Leaf That Wouldn't Stay  
**Status:** New *draft* children's-series pilot. Working title and voice casting are not lasting canon until approved.  
**Running time:** 104 seconds (2,496 frames at 24 fps). **Initial preview:** 3 seconds/72 frames at 1280 × 720.  
**Audience:** 4–8. **Cast:** Sprite and Elder Sprite only.

## Creative brief and show continuity

All original dialogue is in [story.json](story.json), with 15 time-coded spoken lines. Eleven shots have continuous timings, 0–104s, one problem, two escalating traps, a breeze observation, a leaf spinner and a moustache callback. No third character, no unnecessary mythology or new relationship is declared canon.

- **0–5s — hook:** The leaf sticks to Sprite's nose. “I'm a tree!”
- **5–23s — problem:** Sprite wants to keep the prized leaf with the little collection; it blows away.
- **23–44s — attempt one:** A rounded-pebble wall fails; the leaf sails over and wriggles under.
- **44–66s — attempt two:** An acorn cap becomes a flying umbrella and the leaf lands on Elder Sprite's nose.
- **66–76s — observation:** Elder notices the grass all bending in the same direction.
- **76–98s — solution:** Sprite loops the stem around a forked twig to make a leaf spinner that moves with the breeze instead of escaping.
- **98–104s — callback:** The leaf bumps Elder's nose again; an extremely dignified new “tree.”

The story uses the **exact actual** line text in its JSON. Do not manufacture extra dialogue or rewrite lines during speech synthesis.

## Source asset and role constraints

| Story key | Actual original actor | Required runtime file | Technical evidence | Unverified |
|---|---|---|---|---|
| `sprite` | Blender Studio **Sprite Fright** / RIG-Sprite | `actors/sprite_blender_studio.glb`, exported from the official original Blender film scene | Source technical jaw test; signed-off artist original is distinct from legacy Lelli/Brin/Odo | Fresh exported GLB jaw / skin performance in this exact scene, approved visual performance |
| `elder_sprite` | Blender Studio **Elder Sprite** native 1,430-bone artist rig | `actors/elder_sprite.blend`, SHA-256 `fba58c5a2779c0ebd32527e218362348c92842bf154f9d4abbf51532a514ecbe` | Verified source-file import and real WAV-following jaw test | Head and hand gesture readability, constraints, final artist expression and real face close-ups |

Both original character sources require verified **CC BY 4.0** attribution. The original source film stage is not a procedural or generic actor fallback. Official first-party source URLs and file mapping are in [assets.json](assets.json).

The environment builder imports existing **Kenney CC0** tree, foliage and rock GLBs, uses **Poly Haven CC0** PBR ground maps and the unmodified 1K HDRI, and makes three lightweight *episode-only props* (hero leaf, acorn cap and forked twig). It uses original Kenney stones for the pebble wall. No new or procedural talking characters are made. Independent beauty/acting review remains required to judge art-style fit.

The build records all physical SHA-256 values into an attested per-run `assets-verified.json`; the tentative [assets.json](assets.json) in the repository is **not silently edited**. The SHA record is valid only for the actual downloaded or exported bytes.

## What is implemented

- [`story.json`](story.json): every authored line, dialogue emotion/action, word-by-word timing bounds and 11 contiguous shot blocks.
- [`episode_preflight.py`](episode_preflight.py): verifies story, allowed speaker keys/actions/emotions, shot boundaries, 72-frame preview, exact protected legacy Git blob, full asset SHA/format and full WAV/model-card compliance. Rejects unavailable files.
- [`generate_voice_tracks.py`](generate_voice_tracks.py): real line-by-line Piper WAV synthesis using two **provisional** LibriVox-derived candidate models (Kristin and John). Downloads the MODEL_CARD and verifies its claimed public-domain basis; fails if actual WAV exceeds allotted shot duration. Their artistic fit has NOT been auditioned/approved.
- [`build_cc0_woodland.py`](build_cc0_woodland.py): actual Blender 3D stage and prop GLB creation using real CC0 imported assets. Never simulates character sources.
- [`attest_asset_pack.py`](attest_asset_pack.py): checks actual bytes, file headers, original Elder hash, physical CC0 provenance, then emits immutable technical pins.
- [`render_ep01_native.py`](render_ep01_native.py): loads the **original artist Elder Blender file**, imports the authentic source-extracted Sprite GLB, requires real weighted jaw bones, keys WAV loudness to the genuine jaw, keys restrained native arm/head bone gesture cues, loads the actual stage, props and HDRI, stages a camera and area lamps, and attaches original spoken audio. Default `--mode inspect` produces a JSON report, **not video**; requires an explicit preview authorization flag and environment variable before any 72-frame render. This is envelope jaw motion, **not phoneme-complete facial performance**.
- [Episode 1 safety CI](https://github.com/eghosa001/TOOLS/actions/workflows/cartoonstudio-tiny-trails-ep01-preflight.yml) and [real original-art integration CI](https://github.com/eghosa001/TOOLS/actions/workflows/cartoonstudio-tiny-trails-ep01-original-assets.yml). Neither invokes Kaggle or renders video.

## Runtime gates

1. Green **production preflight**: syntactic source checks, untouched 74-line legacy story, good SRT/cue output, rights fields and fail-closed negative tests.
2. Green **real-asset inspection**: actual character mesh files, pinned physical sha256, usable Kenney/PBR stage, authentic downloaded voice models, verified WAV durations, source mesh-to-jaw binding and no invalid Blender imports. This is the active technical gate.
3. **Not yet authorized**: manually requested 3-second preview, after passing import/rights checks. Inspect actual scene, character identity, jaw, mouths, eye lines, speaking, light, layout, wind/leaf and subtitles from the 72-frame MP4.
4. **Not authorized**: any full render. Requires the user's explicit approval of the *actual* three-second preview and distinct full-render selection.

**Important:** The existing `video/story.json` and `video/cartoonstudio-story-lock.json` stay byte-for-byte unchanged. The old `.github/workflows/cartoonstudio-kaggle.yml` is still a **BLOCKED LEGACY** flow and must never be revived as a substitute for native professional actors.

Do not publish `KAGGLE_API_TOKEN` or its value. It belongs only to GitHub Actions Secrets. Do not commit source original rigs just to create a public artifact. Never describe a green story CI or still-image/native-jaw test as a visually approved MP4.

## Commands — CPU validation without any render

```bash
python video/episodes/tiny-trails/ep01/episode_preflight.py --output /tmp/ep01-cues

# After building a real local actor/environment pack:
python video/episodes/tiny-trails/ep01/episode_preflight.py \
    --asset-dir /path/to/actual-assets \
    --assets /path/to/actual-assets/assets-verified.json \
    --audio-dir /path/to/real-line-wavs \
    --output /tmp/ep01-actual-cues

# Nonrendering original Blender rig / stage / audio inspection:
blender -b --disable-autoexec --python-exit-code 1 \
  --python video/episodes/tiny-trails/ep01/render_ep01_native.py -- \
  --mode inspect --asset-dir /path/to/actual-assets \
  --assets /path/to/actual-assets/assets-verified.json \
  --audio-dir /path/to/real-line-wavs \
  --output /tmp/ep01-native-inspection.json
```

**Next explicit user instruction once technical asset inspection is green:** “Run Tiny Trails Episode 1's three-second preview.” At that point use a dedicated guarded/manual production workflow that mounts the exact verified assets on Kaggle, never the legacy procedural notebook, and deliver an actual MP4 for review. Do not claim Kaggle preview capability is wired up until its exact native-asset upload and runtime mapping have been verified. No full render without subsequent visual approval.
