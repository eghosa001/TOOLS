# Football narration pronunciation and pace — November 2026

## Production rule
Before every new football voiceover, collect all named players/clubs/managers from the factual script and verify unusual names against official UEFA team or competition pronunciation guides, club videos in which the player says their own name, native-language audio, and Forvo clips in the source language. Never treat an LLM approximation as native audio ground truth. Keep **two distinct strings**: canonical spelling for script, description and on-screen text; a *speech-only* pronunciation hint for Qwen3-TTS 0.6B CustomVoice Ryan where ordinary spelling is misread. Do not add a phonetic respelling to on-screen visuals or the publishable description.

### Current preview player glossary (short-form, English Ryan; approximations)
| Correct written name | English-readable voice cue | Linguistic note | Supporting source |
| --- | --- | --- | --- |
| Lamine Yamal | La-meen Yah-mal | Stress final -mal, Lamine has long -meen | https://en.wikipedia.org/wiki/Lamine_Yamal ; https://www.youtube.com/watch?v=vl-Ya7DU4ZE |
| Raphinha | Ra-feen-ya | Stress -FEEN-, Portuguese 'nh' palatal nasal; this approximates Portuguese ɲ | https://forvo.com/word/raphinha/ ; https://en.wikipedia.org/wiki/Raphinha |
| Ian Maatsen | Eeyan Maht-sen | Dutch aa represents a long open vowel; first syllable of Maatsen stressed | https://en.wiktionary.org/wiki/Maatsen ; https://en.wiktionary.org/wiki/matsen (short-vowel comparator; NOT same spelling) |
| Pau Cubarsí | Pow Koo-bar-see | UEFA's exact English-language cue, stress SEE | https://www.uefa.com/uefanationsleague/news/0299-1de1ce75fa3c-700e961ed3f8-1000--how-to-pronounce-the-uefa-nations-league-players-names-corr/ |
| Johan Manzambi | Yo-hahn Man-zam-bee | Adapted from French /jɔan mɑ̃zɑ̃bi/ and audible name references; distinguish Yo-hahn from English Joe-han | https://youpronounce.it/europe-footballers/johan-manzambi/ |
| Alavés | Ah-la-vess | Spanish club-name stress on accented final syllable; ordinary English cue | https://en.wikipedia.org/wiki/Deportivo_Alav%C3%A9s |

These are pragmatic TTS cues, not exact IPA, and some accents/pronunciations vary. Prefer self-pronunciation or authoritative audio when available. Do not claim the resulting Qwen waveform has been audited by a native speaker without actually doing that check.

## Correction from V3 listener feedback (4 November 2026)

**Native pronunciation is not the same as natural prosody.** The V3 speech-only phonetic replacements ("La-meen Yah-mal", "Pow Koo-bar-see") sounded accurately articulated but too carefully pronounced. Hyphens cause artificial beat divisions that cannot be fixed reliably with an overall 40% time stretch. For subsequent videos, NEVER default to splitting proper names into syllables. Give the actual orthographic name to Qwen first (Yamal, Pau Cubarsí, Raphinha, Ian Maatsen), add a conversational *delivery* instruction, and listen to a 10-second sample before sending the full render. Do not claim a word's correct pronunciation proves the waveform is natural.

**Creator delivery preference:** quick, fluid, football creator talking to friends, not textbook/diction-coach syllabification. Avoid exaggerated strong stress, emotional shouting and presenter pauses. Write short energetic lines and remove extraneous formal clauses. Use voice-level rate instructions plus careful, pitch-preserving modest post-processing. V4 previously tested 1.48×; that historical export is left unchanged. New films use the locked 1.35× default above, while natural sound remains the decisive quality test.

## Locked current voice tempo: 1.35× (4 November 2026)

**This overrides the experimental 1.48× V4 test and previous broad 1.35–1.45× guidance.** The user's selected future-video default is **exactly 1.35×** with FFmpeg's pitch-preserving `atempo=1.35`, applied to genuine independently generated Qwen3 Ryan voice WAVs after natural conversational TTS. Use this for both Shorts and detailed long-form previews/reviews, historical videos and player comparisons. Natural connected speech and correctly stressed but **unstretched** real player names remain the requirement; no phonetic hyphen fragments by default.

The repository's single source of truth is `football_video_defaults.json → audio.tempo`; invoke `python video/football_edits/football_audio.py --show-defaults` or `--input SOURCE.wav --output PACED.wav` in future new productions. **Do not recreate or overwrite the approved V4 Barcelona–Villa export just because this setting changed.** V4 code/manifest and 1.48× metadata describe the historical already rendered version, not what should be generated next.

## Technical constraints
- **Do not switch Qwen 0.6B to remote Qwen-Audio or CosyVoice** merely to use SSML/hot_fix; those APIs' SSML controls are not evidence that the offline `Qwen3-TTS-12Hz-0.6B-CustomVoice` package supports them. Its documented `generate_custom_voice(..., instruct=...)` supports broad delivery guidance such as quick sports-commentator pacing.
- Text should be independently generated in **short separately timed segments** aligned with real match video. Match action first frame; narration cannot say Villa scored while showing Villa conceding.
- For ALL football Shorts, long-form videos and analyses, use **exactly 1.35×** pitch-preserving FFmpeg `atempo` applied to actual Qwen Ryan audio, and request a natural, energetic rapid analyst voice during synthesis. Adjust by listening for clear names, not by just setting the percentage. The earlier 1.08× was rejected as too slow.
- Use original voice track and stadium ambience with separate gain staging, check absence of clipping and ensure both are loud enough on Android speakers.
- Shorten pauses and video segments as a single edit; don't let shots hang for 4 seconds after a line ends.
- Each matchup requiring a player photograph must continue to use real photographic reference with correct names.
- Copyright checks still apply. YouTube's 1–3 minute Shorts can be blocked worldwide if an active copyright claim exists. Avoid treating a 59-second target as a guarantee of safety. Source credit is not a licence.
- **Never describe the faster football voice as an inherently native/exact pronunciation if only a spelling-based cue was used.**

## Universal natural speech rule (4 November 2026)

This list of pronunciation *candidates* must not cause a name to be pronounced in disconnected, robotic syllables. The repository default is 170–210 fully spoken WPM, aiming for a fluent ~180–195; football should sound like a quick conversation, not a slow read or a shouted sports-announcer stereotype. Native pronunciations require actual player/club audio and *human listening* verification. Do not automatically apply the older 1.35–1.48x FFmpeg stretches from legacy test workflows: post-synthesis atempo must be <=1.25x, or regenerate using a naturally quicker Qwen source. Keep canonical on-screen names and optionally corrected speech input separate. Run video/audio_quality/speech_gate.py and record the actual listener's final approval before any future published football commentary. See video/audio_quality/README.md.
