# Qwen3-TTS 1.7B genuine instruction-controlled voice test — 4 November 2026

The user requested **human-like and naturally fast narration** in every TOOLS project, especially accurate proper names and no slow presenter pacing. This is a real controlled A/B test of the correctly instruction-capable 1.7B Qwen3 model against the existing brisk Apollo Eleven narrator.

## Results — 51 identical spoken words

| Candidate | Natural synthesis WPM | Post tempo | Audition WPM | Human listening verdict |
|---|---:|---:|---:|---|
| Existing Kokoro reference | approx. 177 | baseline | approx. 177 | Existing video user-approved for speed, not certified maximal naturalness |
| Qwen3-TTS Ryan 0.6B CustomVoice | 131.9 | 1.25x max allowed | 164.8 | Too slow; reject as default |
| **Qwen3-TTS Ryan 1.7B CustomVoice** | **158.7** | **1.1656x** pitch-preserving | **185.2** | **User-approved natural voice sample (4 November 2026); new full productions still require QA** |

The Qwen 1.7B test used the official instruction-control capable `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` model, the same 51 original words and the real reference recording. Its instruction requested a fast, warm, conversational historian voice, smooth pronunciation of Armstrong and Buzz Aldrin, and natural stress with no announcer tone. The model's documented ability to accept these instructions does not, by itself, certify how the WAV sounds.

**Google Drive direct listening comparison:**

- [Qwen 1.7B Ryan at 185 WPM — 51-word audio sample](https://drive.google.com/file/d/14vfA-GDPPZiwArJzDWKMsjZA3r0wXyxp/view?usp=drivesdk)
- [Existing voice at ~177 WPM — identical 51 words](https://drive.google.com/file/d/1c13Waw__vViESsei1IZzt7dV71AK3aq7/view?usp=drivesdk)
- [Machine-readable 1.7B WPM, audio source SHA-256 and test metadata](https://drive.google.com/file/d/1p_ASFmZIRz7x_CcbYrvSbTefA1r4b5C9/view?usp=drivesdk)

[Actual GitHub Actions test run 41744628200](https://github.com/eghosa001/TOOLS/actions/runs/41744628200) completed successfully. Free model and package usage, no generative video or imagery, no voice cloning, no copyrighted soundtrack.

## Decision

**User decision on 4 November 2026: APPROVED as the preferred natural narration voice reference for future projects.** It meets the pace target with modest pitch-preserving processing, unlike 0.6B, and the project owner has listened to and approved this voice sample. Individual names, new words and each finished synchronized video still require independent review. Keep the existing 43.9-second Apollo Eleven video unchanged until new full-length narration has been generated, synchronized and reviewed. Approving a sample is not equivalent to approving a new video.

For frequent short-form production, this CPU test required a larger instruction-capable model and additional generation time. Prefer GPU execution if available and authorised; the test does not demonstrate a working Kaggle GPU deployment or prove that CPU usage meets the high-volume throughput target.

The universal repository-wide release gate is [speech_gate.py](speech_gate.py) and the standard is [README.md](README.md). Human listening must check every named entity, complete rhythm, sentence prosody, word endings, perceived expressiveness, source rights and actual synchronized final master. False-positive model-marketing scores are not permitted.

## Subsequent explicit project-owner approval

On 4 November 2026, after listening to the [actual 185.2-WPM sample](https://drive.google.com/file/d/14vfA-GDPPZiwArJzDWKMsjZA3r0wXyxp/view?usp=drivesdk), the user confirmed: “Yes, this is natural voice sample is very good. Approve it”. This sample is now the project's preferred natural narrator reference. Its immutable fingerprint and approved scope are in [APPROVED_NARRATION_VOICE.json](APPROVED_NARRATION_VOICE.json). This approval covers the **voice sample/style**, not future entire narrations or final-video releases.
