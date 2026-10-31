# Satisfying Texture ASMR — Stock-First Shorts Editing (31 October 2026)

> **MANDATORY AUDIO CORRECTION, 31 October 2026.** The archived four-scene renders and V5 are **not approved** as premium sound masters. Earlier scripts allowed almost inaudible candle/ink sections and ran no no-silence check on the exact final MP4. All subsequent outputs must pass the shared `audio_continuity_gate.py` (100-ms frames, ≤ -55 dBFS, maximum 0.45-s near-silent interval), including low-data exports and compilations. A positive scanner result proves *only* measurable continuity; contact-aligned, material-correct, force-proportionate sound still requires visual frame mapping and genuine full-length headphone/phone audition. No generic hiss, synthetic noise-bed padding, fake pops, silence masking or unrelated Foley to trick the measurement. If the authentic material is acoustically quiet, choose a different active shot or verified quiet matching recording. Do not release the original archives merely because they encode successfully.

> **Qwen clarification.** Qwen3-TTS is a speech model, not an established reliable non-speech Foley generator. Do not attribute the legacy Stable Audio 3 Small-SFX tracks to Qwen. Qwen audio-analysis tools can help *describe* candidates but cannot replace recorded source/rights/eyewitness sync checks. The owner requested Qwen-derived audio where genuinely feasible; do not silently swap in speech synthesis, invent a nonexistent run or make unsupported Foley-quality claims. Verified material-specific recorded SFX is the release fallback.


This is an original, sound-led **four-scene** editing pilot. It sources existing licensed footage before considering AI video. The audio master comes from the earlier private *Stable Audio 3 Small-SFX* Kaggle run; the cartoon-project Qwen3-TTS engine is not a sound-effects synthesizer.

## Delivered scenes

| Scene | Video concept | Visual build | Sound |
|---|---|---|---|
| Embers | Coal and smoke; ember/glow intercuts | 5 edited angles from 2 real clips | Close-fire crackles |
| Candle | Close natural candle flame | 5 edited angles from 2 real clips | Quiet real candle/room texture (measurable continuity required) |
| Ripples | Droplets, puddles, and surface patterns | 5 edited angles from 2 real clips | Water plinks and small ripples |
| Ink | Yellow/pink dye against monochrome pigments | 5 edited angles from 2 real clips | Audible source-matched soft liquid texture required |

The previous, unapproved 18-second candidates each included purposeful five-shot sequencing, non-identical source offsets, reframing, colour continuity, short authored title, custom rendered Foley, fade and final mix. The 43-second compilation groups four movements, with transitions previously faded into near-silence; this is prohibited in new exports. Exports: 1080x1920 24fps masters and 720x1280 low-data previews, H.264 + AAC stereo. No artificial physics, no claim that stock footage is original camera work.

## Source rights

Read `SOURCE_LICENSES.json` for the **eight exact original asset names, source page, fetched link, license URL, SHA-256 and resolution**. Six video sources originated on Mixkit under its item-level **Stock Video Free License** and were obtained via a research mirror when the official CDN blocked automated access. Two ink clips came directly from Pexels under the Pexels License. Neither requires attribution, but provide source acknowledgement for transparency. All sources remain attributable to their original creators; edits do not create exclusive footage ownership.

Note: the *water jet striking a plate* idea was **not** sourced here; the water scenes show puddle droplets and ripples. Do not describe them as a plate-impact test.

## Reproducible production

Use the Python editor file with: `ASMR_STOCK_ROOT=your/workspace ASMR_SFX_ZIP=your/four_asmr_real_foley_generated.zip python edit_stock_asmr.py`. Place the eight licensed inputs as `stock/{jets,ripple,fire,coal,candle,candles,ink,inkmono}.mp4` alongside `stock/SOURCE_LICENSES.json`. Python 3, FFmpeg/FFprobe, `libx264`, and DejaVuSans are needed. Then run the delivery helper to render low-bandwidth previews and a four-movement compilation. Source files should be cached, never repeatedly downloaded to a phone.

## YouTube and quality

This pilot materially edits and curates stock, but that alone **does not guarantee YouTube monetization eligibility**. YouTube reviews the channel as a whole for reused/inauthentic content. Do not bulk-upload near-duplicate videos. Human visual/audio review, rights verification, and differentiated creative purpose remain required for a public release. No upload to YouTube was performed.
