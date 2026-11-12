# Required 8/10 scorecards for EVERY team member — Audiobook Studio (12 Nov 2026)

**Before beginning a new episode: PREPRODUCTION PASS required. Before sending the
owner ANY MP4, Drive video link or public/private review video: PREDELIVERY
PASS required. A video that fails ANY category is WITHHELD.** This applies to
all Mythveil audiobook stories, every assistant, human contributor and uploader.

No score below 8.0/10 is acceptable. Do NOT average a bad score away with a
good one. Missing evidence or a missing/unsigned member review is a failure.
The scorecard is mandatory **before production**, not an after-the-fact label.

## The two checkpoints

**PREPRODUCTION, before music, voice synthesis, artwork, compositing or render:**

- Load the latest approved private manuscript, story bible, episode text,
  source-anchored scene plan, known character references and asset rights.
- Roster EVERY person involved. Assign each member to actual review roles;
  one person may perform multiple roles, but must sign each review separately.
- Each person scores EACH readiness criterion assigned to that role >= 8.0,
  with specific real evidence and an actual signed review reference.
- All seven hard readiness gates must be true, all known blockers resolved,
  and the preflight must be dated before the first real production action.
- Run this exact command with the episode's PRIVATE packet:

  python video/audiobook_studio/episode_quality_gate.py /private/EPISODE_SCORECARD.json --phase preproduction

- Any failure: stop. Fix source, storyboard, character assets, proven image
  method, music rights, narration workflow, renderer or verified Drive plan.
  Do not waste hours creating a knowingly substandard video.

**PREDELIVERY, after the real completed MP4 has been checked and uploaded to
private Google Drive, but BEFORE sharing even a review URL with the owner:**

- All 15 final categories must score >= 8.0/10 for EVERY assigned reviewer.
- All 16 hard final gates must be true. Genuine full-video human watch,
  complete human audio listen, source-to-image scene review, rights, source
  coverage, technical checks, thumbnail and character consistency required.
- The real final MP4's local SHA256 and exact size must match the Drive file
  reference; signed review evidence must be stored PRIVATELY.
- Run:

  python video/audiobook_studio/episode_quality_gate.py /private/EPISODE_SCORECARD.json --phase predelivery --final-mp4 /private/ACTUAL_MASTER.mp4

- If any item fails, **do not provide a video, preview, review link, or
  publication**. Correct the failed item and repeat the check.

## Individual role scorecards

| Reviewer role | Final categories, each >=8 |
|---|---|
| Story editor | Story fidelity; scene accuracy |
| Visual director | Character identity; visual style; backgrounds/world; composition; color/lighting |
| Narration lead | Narration quality |
| Sound engineer | Audio mix quality |
| Video editor | Timing/pacing; technical video |
| Release QA | Thumbnail/packaging; repository compliance; Google Drive delivery readiness; final review confidence |

These are **15 distinct required final scores**. If two people work on visuals,
BOTH score EVERY visual category separately; neither score may be below 8.
A solo producer must explicitly cover and separately sign ALL six roles.
Each scored item needs a numeric score and source-specific evidence.
Do not fabricate reviewers, signatures, observation evidence or time records.

The signed private packet format and exact criteria are enforced by
episode_quality_gate.py. Copy EPISODE_TEAM_SCORECARD_TEMPLATE.json from this
repo into the PRIVATE episode Drive folder, fill it honestly, and keep it
private. The template intentionally FAILS until completed.

## Additional hard rules remain mandatory

This new 8/10 gate is cumulative with ALL_RULES_MANDATORY.md, the 109 Master
Source Rules v1.1, the 16-category story scorecard, six narration criteria
(>=8 each plus weighted >=8.5), original music-first receipt, human full-watch
and full-listen, five signed holds, title/playlist/thumbnail validation,
licensing, verified upload, and explicit owner approval before public YouTube
publication. The public upload validator rechecks the same private team packet.

An archived draft, successful image hash check, automated VLM assessment,
technically valid MP4, or team average of 9 does NOT make a failed episode
releasable. In particular, STORY_IMAGE_MATCH_FAILED remains a blocking failure
for Necromancer E03 until the scenes themselves are corrected and reviewed.

## Enforcement boundary

The repository assembler and reusable-art compositor now require the PRIVATE
preproduction scorecard before new full-color work. The release validator
requires the preproduction and predelivery scorecards before public release.
Other external tools, YouTube connectors or image generators may bypass local
Python; an uploader that has not integrated the gate is **NOT AUTHORIZED**.
Code validates submitted evidence and local hash, but cannot prove a human
really watched a video or force external providers to obey. Never mark these
as passed without real independent checks. Never commit private manuscripts,
review packets, signed references or release credentials to this public repo.

