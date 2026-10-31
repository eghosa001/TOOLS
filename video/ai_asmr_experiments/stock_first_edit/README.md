# Satisfying Texture ASMR — Stock-First Shorts Editing (31 October 2026)

This is an original, sound-led **four-scene** editing pilot. It sources existing licensed footage before considering AI video. The audio master comes from the earlier private *Stable Audio 3 Small-SFX* Kaggle run; the cartoon-project Qwen3-TTS engine is not a sound-effects synthesizer.

## Delivered scenes

| Scene | Video concept | Visual build | Sound |
|---|---|---|---|
| Embers | Coal and smoke; ember/glow intercuts | 5 edited angles from 2 real clips | Close-fire crackles |
| Candle | Close natural candle flame | 5 edited angles from 2 real clips | Nearly silent room tone |
| Ripples | Droplets, puddles, and surface patterns | 5 edited angles from 2 real clips | Water plinks and small ripples |
| Ink | Yellow/pink dye against monochrome pigments | 5 edited angles from 2 real clips | Very quiet liquid room ambience |

Each 18-second Short includes purposeful five-shot sequencing, non-identical source offsets, reframing, colour continuity, short authored title, custom rendered Foley, fade and final mix. The 43-second compilation groups four movements, with softly faded audio at the scene boundaries. Exports: 1080x1920 24fps masters and 720x1280 low-data previews, H.264 + AAC stereo. No artificial physics, no claim that stock footage is original camera work.

## Source rights

Read `SOURCE_LICENSES.json` for the **eight exact original asset names, source page, fetched link, license URL, SHA-256 and resolution**. Six video sources originated on Mixkit under its item-level **Stock Video Free License** and were obtained via a research mirror when the official CDN blocked automated access. Two ink clips came directly from Pexels under the Pexels License. Neither requires attribution, but provide source acknowledgement for transparency. All sources remain attributable to their original creators; edits do not create exclusive footage ownership.

Note: the *water jet striking a plate* idea was **not** sourced here; the water scenes show puddle droplets and ripples. Do not describe them as a plate-impact test.

## Reproducible production

Use the Python editor file with: `ASMR_STOCK_ROOT=your/workspace ASMR_SFX_ZIP=your/four_asmr_real_foley_generated.zip python edit_stock_asmr.py`. Place the eight licensed inputs as `stock/{jets,ripple,fire,coal,candle,candles,ink,inkmono}.mp4` alongside `stock/SOURCE_LICENSES.json`. Python 3, FFmpeg/FFprobe, `libx264`, and DejaVuSans are needed. Then run the delivery helper to render low-bandwidth previews and a four-movement compilation. Source files should be cached, never repeatedly downloaded to a phone.

## YouTube and quality

This pilot materially edits and curates stock, but that alone **does not guarantee YouTube monetization eligibility**. YouTube reviews the channel as a whole for reused/inauthentic content. Do not bulk-upload near-duplicate videos. Human visual/audio review, rights verification, and differentiated creative purpose remain required for a public release. No upload to YouTube was performed.
