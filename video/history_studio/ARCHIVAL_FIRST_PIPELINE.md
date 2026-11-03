> **3 November 2026 — actual motion-video first:** The current archived documentary builds were too heavily based on photos. For NEW Facts Uncovered documentaries, an MP4 made from Ken Burns stills is not sufficient. Source historically accurate, commercially reusable **moving film** first. Use existing genuine film where it covers a claim; otherwise independently verified **live-action filmed** reenactments or contemporary real-world location footage, each correctly labelled. Preserve authentic still photographs, maps and documents only when they are editorially necessary. Aim for at least **65% of final runtime made of genuinely moving source/video frames**, measured by the approved per-shot ledger, excluding zoompan, sliding stills, screen recordings of static images and animated still backgrounds. Do not pad with irrelevant stock to meet a quota. If quality footage is not available, flag the unsupported section and block delivery instead of silently substituting photo sequences. Run `video/history_studio/video_motion_gate.py` before render; keep separate source/rights verification and human final-viewing approval. This is a motion quality floor, not a license clearance, not an instruction to fake historical footage, and not a replacement for the source-first policy.

# Facts Uncovered — default historical documentary production pipeline

Episode 01 v3 adopts **real-source-only; no AI visuals, no synthetic media, no exceptions**. No Blender, 3D models, or puppets are required for the primary faceless documentary workflow. Preserve old 2D materials in Git as optional assets.

## Production order

1. Research each factual claim and script from primary sources and reliable investigators.
2. Search for authentic historical footage of the *actual event*. Confirm filming year, place, license, and identity. If no event footage exists, use labelled period-city footage only as context.
3. Gather incident photographs, maps, primary newspapers, period diagrams, and original documents. Cite their archives.
4. Build the storyboard using archival material first. If any narration remains visually unsupported, search additional rights-cleared real footage or photos, rewrite the unsupported passage, or block the release. AI pictures/video and CGI substitutes are prohibited.
5. Use actual filmed footage for the main picture track. Real archival photographs may have minimal documentary camera moves but these never count as genuine footage in motion-coverage checks.
6. Keep Kokoro v1.0 am_michael at speed 0.94, the Episode 01 v2 narrator. Add normal chapter pauses and balanced original music.
7. **Open with the historical story hook first.** A spoken or visual invitation to subscribe in the introduction is **optional**, never automatically inserted, and should appear only when it naturally follows a compelling opening; do not require a downward arrow or a promotional intro card.
8. **Close every long-form video and every Short with a consciously designed subscribe invitation:** a natural spoken request naming the Facts Uncovered channel, matched to a readable branded SUBSCRIBE end shot in the editor-authored timeline. Target approximately 5–10 seconds for long films and 1–3 seconds for Shorts, without forcing speech into unnatural timing. For long films, reserve an intentionally composed region for eligible YouTube end-screen elements. Check this sequence in the real final export. Do not use an automated outro generator.
9. Produce 1920x1080 at 24fps, SRT captions, a factual thumbnail, MP4 master, script and source ledger.
10. Verify full video/audio tracks, scene completeness, archival source SHA256 and individual rights records. Perform a human viewing review before publishing.

## Historical and commercial rights rules

- Document event relevance, date, creator, originating archive, usage status, source link and checksum for each photograph or movie.
- Do not assume everything on Wikimedia Commons or Internet Archive has the same license. Each record must be checked.
- Never call 1903 Boston streetcar footage actual footage of the 1919 Great Molasses Flood: label it 'Boston, 1903 — period context, NOT the flood'.
- All final visuals must be authentic camera captures or scans of physical records (zero synthetic visual content). There is no generated fallback quota.
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
