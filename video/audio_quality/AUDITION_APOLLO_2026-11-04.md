# Apollo Eleven voice audition — 4 November 2026

A genuine CPU Qwen3-TTS comparison was run after the user approved the **~179 WPM** fast 43.9-second Kokoro narrated master and requested the most natural human-like speech possible across TOOLS.

## Controlled A/B test

Both voices spoke the **same 51 words** from the actual Apollo Eleven narration: a hook, the original video/date, Armstrong avoiding boulders, and Buzz Aldrin walking. This tested real names, a spoken year and connected explanatory sentences. No generated pictures or video were created.

- Qwen3-TTS model: Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice, voice Ryan (open-source Apache-2.0 model).
- The input contained a natural, brisk, fluent conversational style hint around 185 WPM. **Official Qwen3-TTS model documentation does NOT list instruction control for 0.6B CustomVoice**, so that hint cannot be assumed to control the actual speaking rate. The 1.7B CustomVoice and VoiceDesign variants support instruction control. Reference: https://github.com/QwenLM/Qwen3-TTS
- Qwen unprocessed take: **23.20 seconds, 131.9 WPM**. Too slow.
- Qwen after the maximum permitted **1.25× pitch-preserving atempo**: **164.8 WPM**, still below the creator-approved default 170–210 WPM.
- Existing Kokoro reference of the same 51 words: **17.26 seconds, approximately 177 WPM**. It meets the user's chosen short-form speed.

Decision: **Do not replace the current 43.9-second Apollo Eleven final with this slower Qwen take.** Qwen's timbre/prosody may be preferable, but that remains a subjective listener decision. Audio technical tests cannot honestly certify human-like speech or accurate pronunciation. The A/B is a listening aid, not a recommended YouTube master. The original unchanged, approved-speed video remains on Drive.

## Google Drive listening evidence

- [Qwen Ryan 164.8 WPM candidate sample](https://drive.google.com/file/d/18lJsREvQzFpigpQu96jBlx6iPWV1ZE2H/view?usp=drivesdk)
- [Current voice 177 WPM baseline for identical 51 words](https://drive.google.com/file/d/1c13Waw__vViESsei1IZzt7dV71AK3aq7/view?usp=drivesdk)
- [Machine-readable A/B measurements](https://drive.google.com/file/d/1JAKGi87-EQEn_CbL7Y7bfaBi29XOzVZs/view?usp=drivesdk)
- [Current finished 43.9-second Apollo video](https://drive.google.com/file/d/1svdjBKVHw81QTQ_JiKOCzLQmLXxnFG68/view?usp=drivesdk)

GitHub Actions [actual Qwen voice audition run 41743005168](https://github.com/eghosa001/TOOLS/actions/runs/41743005168) succeeded; original WAVs and source text remain in its artifact archive. The temporary Action was removed from active workflows after the result to preserve the cleaned repo.

## Recommendations for next voices

For new productions, trial expressive, licence-verified voice engines **at the normal target pace natively**, with natural pitch variation and intact names. The 0.6B preset did not deliver the required fast natural cadence in this real-world test and cannot be presumed to honour a style instruction; do not simply stretch it by 1.4× or declare it better based on the brand name. A Qwen3-TTS 1.7B CustomVoice/VoiceDesign GPU test may be worthwhile when a licensed GPU runtime is available; it has not been benchmarked here. Preserve the current audience-approved fast narration until a new candidate passes actual listening and name checks.

Cross-repository instructions and audio gate: video/audio_quality/README.md, video/audio_quality/speech_gate.py.

Existing history visuals remain **real camera footage only**; no AI-generated pictures or film are authorized.
