# Facts Uncovered — Episode 01, manually authored v4

This is an **editorial rebuild, not the old automatic matching pipeline**.

## Editorial status
- **88 individually directed narration/visual pairings**, plus a spoken subscription invitation after the opening hook.
- An independently written eight-beat, portrait YouTube Short.
- Visual modes: actual dated archival photograph, original information graphic, or one permanently labelled artistic reconstruction.
- The assembly program handles encoding and WAV placement only. **Shot selection is pre-authored**, never chosen by keyword or a randomized source pool.
- Missing historical photographs are fatal: no fallback photograph, proxy film, or silently reused illustration.
- Final editorial approval is **not** automatically granted by video rendering.

## Sources
The five original archive photographs are individually identified in `manual_editor.py:ASSETS`. Fetch them using `fetch_archives.py`, which stores SHA-256 hashes and rights/identity links in `archives/RIGHTS_AND_CHECKSUMS.json`. Do not change a source filename without a new rights and relevance review.

Research:
- City of Boston archives, 2019 centenary: https://content.boston.gov/news/100-years-ago-today-molasses-crashes-through-bostons-north-end
- Library of Congress Red Cross photograph: https://www.loc.gov/item/2017679979/
- Massachusetts State House historical account: https://www.sec.state.ma.us/divisions/state-house-tours/did-you-know/Molasses-Flood.htm
- Hugh Ogden audit (1925): https://www.massmoments.org/moment-details/great-molasses-flood/submoment/hugh-ogden-issues-report-on-cause-of-the-molasses-flood.html
- Further engineering review: https://www.history.com/articles/great-molasses-flood-science

## Technical process
1. Check the original 22-scene script in `../molasses_1919/episode.json`.
2. Cross-check every `shot_map.py` sentence boundary and visually inspect the proposed image.
3. Fetch the **exact** required archive originals, keeping creator/year/copyright record.
4. Produce one Kokoro narrator WAV per approved shot, using `am_michael` at 0.94 speed. Every image is linked to the exact text spoken in its own WAV; there is no general photo playlist.
5. Prepare native-resolution archive compositions and original graphics for all 89 main beats.
6. Render MP4 at 1920×1080, 24 fps, H.264 CRF19, AAC stereo 48 kHz, and a separate 1080×1920 vertical Short.
7. Generate SRT captions and timing manifest.
8. **Before publishing:** listen to the entire narration, view every frame and transition, check correct date/source labels, manually retime subtitles from the audible words, adjust mix and music using rights-verified recordings, and inspect Shorts on mobile.
9. Only create release master and upload when all gates are signed off. **No scheduled jobs, no social posting or YouTube upload are part of this production build.**

## Production caveat and editorial upgrade
The existing 22-scene narration currently produces a roughly 13–15-minute film; the separate long-form 32:50 outline in the editorial plan is not yet fully scripted. **Do not claim the v4 technical film fulfills that longer documentary plan.** Further research-supported chapters should be recorded and approved before extending the runtime. Length is never padded with repeated photographs.

## Publishing suggestions (not uploaded)
**Title:** The Great Molasses Flood of 1919: The Tank Failure That Killed 21 People

**Short:** Boston Was Hit by 2.3 Million Gallons of Molasses | True History #shorts

**Description:** On January 15, 1919, a giant steel tank ruptured in Boston's North End. Approximately 2.3 million gallons of molasses swept through Commercial Street, killing 21 people and injuring about 150. Using original 1919 photographs and evidence from subsequent investigations, Facts Uncovered explains why the disaster happened, the warnings that were missed and the 1925 finding of negligence. References and image credits are provided in the source ledger.

**Search terms:** Great Molasses Flood, Boston Molasses Flood 1919, Boston disaster, Purity Distilling Company, North End, Industrial disaster, American history, historical documentary, structural engineering failures.

**Thumbnail intention:** Artistically reconstructed Boston waterfront plus the large readable words *THE TANK THAT BROKE BOSTON*. The original illustration must retain an unobscured ARTISTIC RECONSTRUCTION label.

## Not approved for publication
The generated `QA_HANDOFF.json` explicitly sets `upload_permitted: false`. A technically valid MP4 is not proof of visual storytelling quality.
