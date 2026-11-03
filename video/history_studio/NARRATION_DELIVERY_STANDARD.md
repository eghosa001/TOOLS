# Facts Uncovered — narration quality for historical Shorts

This rule applies to the historical documentary narration/audio track only; the existing **no AI-generated pictures or video** policy remains absolute.

**Default for fast history Shorts:** 175–210 fully spoken words per minute. An individual scene may vary for dramatic effect, but the finished video must feel brisk without swallowing consonants or clipping endings. Do not reach a number by chopping audio, removing words, or raising pitch. Prefer a natural synthesis setting combined with measured, pitch-preserving FFmpeg `atempo`; retime every shot and subtitle to the actual encoded audio after the speed change.

- **Write dates for speech.** Example, keep the written video title "Apollo 11, 1969" but synthesize the narration as "Apollo Eleven, nineteen sixty nine". Use "twenty twenty six" where appropriate. Avoid numerals, slashes, abbreviations and ambiguous year formatting in the words sent directly to the voice model.
- **Word choice matters.** Write brief, connected, conversational factual sentences with clear subjects. Remove repeated explanations, stilted introductory filler and artificial emphasis. Keep the hook immediate.
- **Name checks.** Expand specialized names or acronyms when they are unclear to the voice engine. For each difficult term, render an isolated sentence and listen; change the spoken input only when the original word is still clear to the listener. Never change a name's factual identity to force pronunciation.
- **Full audio quality control.** Verify that no syllable is clipped, all spoken words survive, year pronunciations are natural, and pauses are short but comprehensible. Listen to the whole final rendered video, not just the standalone audio; approve audiovisual synchronization and captions.
- **Measurable approval.** Record transcript word count, finished audio duration and computed speaking rate; reject inappropriate durations and major mismatches with the intended timing. A numerical test cannot by itself prove clear pronunciation, so maintain editorial approval.
- **Sound:** high intelligibility, no peaking or harsh limiting, consistent perceived loudness, natural human cadence; finish around −16 LUFS integrated for speech-led Shorts where appropriate.

For long-form documentaries, pacing may be slower; this Short-specific speed guidance does not override factual precision or accessibility.

The Apollo 11 reference implementation is `video/history_studio/productions/apollo11_real/produce.py`, including spoken-out years and a pitch-preserving tempo pass.
