# Mythveil Audiobooks — Mandatory Episode Naming Standard

Owner instruction: 10 November 2026. Applies to every new episode across all Mythveil Audiobooks series. A specific later owner-approved series convention overrides this general rule; do not improvise titles independently.

## Public YouTube title (fixed structure)

`{Official Series Title} | Episode {NN}: {Official Episode Title} | Audiobook`

- Keep the **official**, currently approved series title and episode title verbatim, including correct spelling and apostrophes.
- Use sequential **two-digit, zero-padded episode numbers** (`01`, `02`, ..., `99`, `100`). Never renumber episodes to suit a new production batch.
- No keyword-stuffed endings, duplicated genre labels, marketing claims, random subtitles, production jargon, emojis, hashtags, artificial hype, or generic titles invented by the assembler.
- The public title must reflect the same series, episode number, and story title shown on the video and thumbnail; do not confuse volume/chapter numbering with episode numbering.
- Chapter names belong in the **description chapter markers**, not in a convoluted video title. When an episode covers multiple chapters, use the episode title approved in the source episode plan.

**Example:** `The Villain's Second Son | Episode 02: The Blue Thread | Audiobook`

## YouTube thumbnail

- Display the official series title (in its approved typography), an unambiguous `EP 02` episode marker, and the short episode title where it remains readable on mobile.
- One consistent visual template per series, maintaining its approved characters, full-color style and layout. No unrelated titles, decorative marketing slogans or cluttered text.
- Thumbnail filename matches the same episode identity.

## Google Drive folder and production filenames

Folder: `{Series_Slug}/E{NN}_{Episode_Slug}/`

Use plain ASCII letters, numbers, and underscores for production file portability. Series and episode slugs should be meaningful versions of the canonical titles, not arbitrary job IDs. No spaces, date prefixes, `FINAL_FINAL`, `NEW`, `FIXED`, or `v3_REAL` names.

- Master MP4: `{Series_Slug}_E{NN}_{Episode_Slug}_MASTER_1080p.mp4`
- Narration: `{Series_Slug}_E{NN}_{Episode_Slug}_NARRATION_KokoroMichael.wav` (or matching actual .mp3 extension)
- Thumbnail: `{Series_Slug}_E{NN}_{Episode_Slug}_THUMBNAIL.jpg`
- Scene artwork: `{Series_Slug}_E{NN}_S{SS}_ILLUSTRATION.png` (or actual file extension)
- QA: `{Series_Slug}_E{NN}_{Episode_Slug}_QA.json`

**Example:** `The_Villains_Second_Son_E02_The_Blue_Thread_MASTER_1080p.mp4`

Increment versions explicitly only when preserving more than one legitimate revision: `_v02` etc., in internal production folders. The **published** master has one canonical name.

## Mandatory pre-upload validation

Before publishing a video:
1. Read the official series title, episode number and episode title from the **approved story/episode source of truth**, not from an image-generator prompt or old filename.
2. Construct the YouTube title, description headline, chapter list, thumbnail overlay, Drive folder, master filename and narration filename from that same identity.
3. Compare all identity fields exactly. Block upload on a mismatch, wrong channel, duplicate episode, or unclear episode title.
4. Keep the existing private-owner release and visual/audio QA requirements in force.

This rule concerns **future episodes**. Do not rename historical public videos without a direct owner instruction, because doing so can affect existing audience links and metadata.
