# Reusable CC0 animation assets (multi-genre)
This package is a **real download-and-provenance system**, not a promise that all possible free internet assets are safe or of reference-film quality.

- `cc0_catalog.json` contains individual licensed source pages, exact download URLs, roles, expected size and an editorial suitability flag.
- `fetch_cc0_assets.py --output artifacts/cc0-animation-assets` downloads the original zip/png/7z files **only from trusted hosts**; caches them locally, verifies file signatures and writes SHA-256 hashes and a per-pack failure report.
- `.github/workflows/cc0-animation-asset-library.yml` runs server-side (sparing the user's metered internet) and creates one ZIP for Google Drive. It keeps the real source files separate rather than checking hundreds of MB of binary images into Git.
- `SOURCE_CATALOG.json` and `DOWNLOAD_REPORT.json` travel with every archive.

## Production / copyright restrictions
1. CC0 generally permits commercial reuse of assets, but does **not** itself ensure YouTube monetization, originality, or reference-video quality. YouTube reused-content policies still apply.
2. Do not use the `film_use: exclude_premium` pixel packs for cinematic animation. Pixel art clashes with high-res rigs and has been rejected repeatedly.
3. Riggable characters still need coherent direction, expression sheets, alternate angles and human-reviewed physical action. A figure posing on a background is **not** a publishable animation.
4. Select every shot manually. Never auto-generate an edit from random catalog entries. Preserve asset source details, manually matched scene timing, creative direction, sound synchronization and quality approval.
5. Do not deliver a video or Drive review upload without watching the real rendering and verifying coherent 2D character movement, matched environment, storytelling and adequate sound.

## Included categories
- Vector characters and separated limbs: Kenney Toon Characters, Platformer Characters, source character.
- Adventure/nature/scenery/props/audio: New Platformer Pack, 4K seaview multilayer background, castle gate and flag set.
- Organic foley: 96 fantasy / practical sounds.
- Reference-only (NOT premium film): pixel castle tiles, sci-fi pixel lab.

Selectively expand this catalog later with individually verified CC0/CC-BY sources; never clone huge unrestricted libraries or treat unclear asset licences as CC0.
