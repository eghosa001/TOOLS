# Facts Uncovered — default historical documentary production pipeline

Episode 01 v3 adopts **archival-first, AI only for gaps**. No Blender, 3D models, or puppets are required for the primary faceless documentary workflow. Preserve old 2D materials in Git as optional assets.

## Production order

1. Research each factual claim and script from primary sources and reliable investigators.
2. Search for authentic historical footage of the *actual event*. Confirm filming year, place, license, and identity. If no event footage exists, use labelled period-city footage only as context.
3. Gather incident photographs, maps, primary newspapers, period diagrams, and original documents. Cite their archives.
4. Build the storyboard using archival material first. If key narration remains visually unsupported, add as few historically researched AI stills as needed, permanently marked ARTISTIC RECONSTRUCTION; never present them as 1919 film.
5. Apply Ken Burns movements with FFmpeg, preserving full-frame archive views and identifying cropped detail views.
6. Keep Kokoro v1.0 am_michael at speed 0.94, the Episode 01 v2 narrator. Add normal chapter pauses and balanced original music.
7. Open each video with a short spoken request to subscribe, including FACTS UNCOVERED / STORIES & EVIDENCE branding, large PLEASE SUBSCRIBE text, and a downward arrow.
8. **Close every long-form video and every Short with a consciously designed subscribe invitation:** a natural spoken request naming the Facts Uncovered channel, matched to a readable branded SUBSCRIBE end shot in the editor-authored timeline. For long films leave end-screen space. Check this sequence in the real final export. Do not use an automated outro generator.
9. Produce 1920x1080 at 24fps, SRT captions, a factual thumbnail, MP4 master, script and source ledger.
10. Verify full video/audio tracks, scene completeness, archival source SHA256 and individual rights records. Perform a human viewing review before publishing.

## Historical and commercial rights rules

- Document event relevance, date, creator, originating archive, usage status, source link and checksum for each photograph or movie.
- Do not assume everything on Wikimedia Commons or Internet Archive has the same license. Each record must be checked.
- Never call 1903 Boston streetcar footage actual footage of the 1919 Great Molasses Flood: label it 'Boston, 1903 — period context, NOT the flood'.
- If relevant archives fully cover a script, AI imagery count can be zero. No 80/20 quota forces unnecessary reconstruction.
- Software licenses, film licenses, voice-model rights and archival-image rights are separate.
- Passing automated checks cannot replace final editorial and legal review.

## Free verified sources

- Library of Congress: https://www.loc.gov/pictures/
- Boston Elevated Railway January 1919 photos: https://commons.wikimedia.org/wiki/Category:Boston_Elevated_Railway_after_the_Molasses_Flood
- 1903 Boston streetcar contextual film: https://commons.wikimedia.org/wiki/File:Boston_by_streetcar,_1903._Boston_Elevated_Railway_trolley_and_elevated_cars..theora.ogv
- City of Boston Archives: https://www.boston.gov/departments/archives-and-records-management
- Prelinger Archives licensing caution: https://www.panix.com/~footage/prelarch.html

## Current implementation

Episode 01 research/story stays at video/history_studio/films/molasses_1919/episode.json
Episode 01 v3 producer: video/history_studio/films/molasses_1919_v3/build_episode_v3.py
Build workflow: .github/workflows/facts-uncovered-episode01-v3.yml
Proven narrator retained from video/history_studio/films/molasses_1919_v2/build_episode_v2.py
