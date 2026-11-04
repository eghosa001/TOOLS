# Universal natural speech and sound standard — TOOLS (November 2026)

This is the default for every spoken recording: history, football, gaming, cartoons, ASMR with speech, app prompts, educational explainers, long-form, Shorts and character dialogue. It does not impose a speaking rate on nonverbal ASMR, Foley or music.

## Sound like a real, fluent person

- Target **170–210 complete words per minute**, usually around **180–195 WPM**, for spoken video. The creator-approved Apollo Eleven rewrite was approximately **179 WPM**. Long-form narration also defaults to this brisk conversational pace unless the scene needs a documented slower cadence. A character, meditation or whispered ASMR may speak more slowly only when justified and approved.
- Natural conversational expression matters more than hitting the number: vary pitch, emphasis, sentence length and rhythm; avoid monotone, identical sentence endings, overacted emphasis, lecture voice, stilted emotional cues and long artificial pauses. Rewrite cumbersome scripts to speak naturally.
- Verify every important personal name, fictional name, team, city, foreign term, date and acronym against primary recorded pronunciation where available (player or performer self-pronunciation, official club/agency voice, native speaker audio). Do not invent confidence. Try the **canonical spelling first**, then edit speech input only if a real listening test demonstrates mispronunciation. Do not force hyphenated syllable-by-syllable phonetics; those sound unnaturally deliberate.
- Keep separately the correct written text and speech-engine-friendly input. Example: written year "1969", speech input "nineteen sixty nine"; written mission "Apollo 11", speech "Apollo Eleven". Keep original proper spelling on screen and in descriptions. Audit the pronunciation of every name in a short sample before rendering a long video.
- Prefer the naturalest **commercially licensed** voice demonstrated in an A/B recording. **Qwen3-TTS 0.6B CustomVoice does not officially support natural-language instruction control; Qwen3-TTS 1.7B CustomVoice and VoiceDesign do.** Do not send a rate instruction to 0.6B and assume it was obeyed; measure actual words per minute and choose model/hardware accordingly. Evaluate available Qwen3-TTS Ryan, Kokoro and other vetted speech models; never substitute blindly and never impersonate or clone a real speaker without permission. Qwen3-TTS supports natural prosody and optional speaking-style guidance for appropriate supported models, but model names alone do not prove quality.
- Do **not** speed up source audio excessively. Start by writing a concise script and generating an inherently quick conversational performance; use mild pitch-preserving FFmpeg tempo adjustment for final alignment. Above **1.25×** post-stretch, regenerate or select another voice rather than harming human rhythm and phonemes.
- Never cut words, syllables, breaths or sentence endings for shot timing. Retime visual scenes and subtitles to the actual resulting narration. Evaluate the final video rather than only the isolated voice WAV.
- Default mastered speech-forward output near **-16 LUFS integrated**, true peak no higher than **-1.5 dBTP**. Check real mobile playback, peaks, sibilants, pumping, clipped edges, underpowered consonants, unnaturally repeated samples and audio/video sync.
- All sounds, including Foley, ASMR and impact effects, must correspond to the visible material, force, environment, timing and sequence of physical events. Avoid unrelated taps, identical repeating loops, synthetic sounding crunch or empty silence where continuous contact should be audible.

## Mandatory approval process

1. Write and fact-check the canonical script and the separate spoken-word version.
2. Record each named entity with an authoritative pronunciation source and a pending human-listen result; resolve ambiguous spellings before publication.
3. Audition a 5–12-second sample containing the trickiest names/dates in a natural, quick, full sentence. Compare alternate voices against the same words; do not choose based only on an abstract benchmark.
4. Synthesize in coherent phrases, preserve natural connected speech, lightly master the output and synchronize subtitles/film to the exact waveform.
5. Run video/audio_quality/speech_gate.py in draft mode to check actual measured words per minute, source/licence record, speech duration, phonetic spelling, names and pauses.
6. A real human listens to the *whole* finished file, verifies naturalness, accurate names, no clipped syllables, appropriate sound design and visual alignment. They sign the exact output SHA-256 in the audio quality manifest; only then may the release-mode gate pass.

Manifest fields: canonical_script, spoken_script, mode (short/voiceover/longform/dialogue/spoken_asmr), target_wpm [170,210], post_tempo_factor, commercial_audio_rights_verified, a complete names array (canonical, reference_url, checked_against_reference, listener_verified_correct), and human_listening_review. Every proper name must be accounted for; if none exist, explicitly attest no_proper_names_attested: true. Human approval includes reviewer, notes, exact audio_sha256, complete_listen, natural_conversational_prosody, all_names_inventory_complete, all_proper_names_correct, no_clipped_or_swallowed_words and matches_picture_and_subtitles.

Example: python video/audio_quality/speech_gate.py --manifest speech_manifest.json --audio final_video.mp4 --stage draft --report speech_qc.json

A numeric speech gate **cannot prove voice naturalness**, linguistic correctness or human evaluation; do not claim a pass does. Actual listening and feedback take precedence over metrics.

## Exceptions and separation

- Nonverbal ASMR has no speech speed, but retains continuous material-appropriate Foley and scene-audio parity requirements.
- Story-specific slow delivery is allowed only with a documented human-approved pace exception; do not turn all voices into equally fast monotone speech.
- This speech rule does NOT change Facts Uncovered's **absolute ban on AI-generated pictures/videos and synthetic scenes**. Licensed TTS audio is distinct from visuals.
- Original media rights, personality rights, copyright, YouTube originality and individual channel safety checks still apply.
