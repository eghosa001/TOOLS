# Audiobook Studio — owner-approved Ryan narrator

**Approved:** 6 November 2026, after the owner listened to the actual 19.92-second Qwen Ryan technical MP4 preview in Google Drive.

This is the mandatory voice **identity and delivery standard** for all four original audiobook novellas and any future Audiobook Studio fiction unless the owner explicitly changes it.

## Exact approved generation profile

- Model: `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`
- Speaker: `Ryan`
- Language: `English`
- Exact `instruct`: `A warm, natural male audiobook narrator, calm suspense, clear and measured, no exaggerated acting.`
- Reference sample: `male_ryan_original_qwen_audition.mp3` (19.92 seconds)
- Verified MP3 SHA-256: `80485deabb10b8d181603ff82f55fb7b1c2e8ce3e899e077270bef1feb7c3886`
- Verified original WAV SHA-256: `779c5b3a6033a4483fa31d6d7b295c3b9fcddc60dbfc2007af19cfb2ca8b9bfa`
- Source audio: Kaggle Qwen3-TTS 1.7B CustomVoice with male speaker Ryan, produced on Tesla T4 with float32 inference and 24 kHz WAV.
- Approval scope: **voice timbre, identity, calm narration and delivery**. This was an approval of a generic technical audition, not the names or scripts of any particular chapter.

The original audition and source recordings are private. Do not commit them, unpublished manuscripts, or the private ZIP to this public repository. The private source ZIP includes the approved reference file plus the `VOICE_REFERENCE/RYAN_VOICE_STANDARD_APPROVED.json` metadata.

## Enforcement and fidelity

1. Future chapter synthesis must use **the exact model, speaker, language, and instruction string above**. The original private chapter scripts used an instruction different from the approved audition; the corrected owner-approved private package aligns both `gpu_narration.py` and `approved_scripts/qwen3_audiobook_runner.py` to the audition.
2. Lock the production profile into the real Kaggle private ZIP, validate the sample hashes and script constants, and refuse any silent substitute engine or voice. Model randomness means an exact voice match cannot be guaranteed by parameters alone; compare generated passages to the reference by listening.
3. Preserve original manuscript text, natural dialogue and sentence rhythm. Do not insert the audition text into chapter speech, voice clone, use another male speaker without approval, apply robotic speed changes, or artificially lengthen the episode.
4. **Character-name pronunciations are not yet approved.** Audition names in complete natural sentences and have a human listen before approving them.
5. **Individual chapters are not yet approved.** Listen to 100% of each generated narration and inspect omitted/duplicated words, names, abrupt timbre changes, pronunciation, audio joins and mastering. Sign off each final audio SHA-256 separately.
6. Keep visuals story-faithful and audio-led. Final MP4, title/rights clearance and public upload need their separate release gates. Owner voice approval is not public-release consent.

The owner's approved reference artifact is retained privately in Audiobook Studio / Google Drive. Refer to the voice profile ID `audiobook_ryan_qwen_1p7b_approved_2026_11_06_v1` in future chapter reports.