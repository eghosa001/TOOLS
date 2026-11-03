# Universal football-production runbook

**Effective 4 November 2026.** Read the scoped `AGENTS.md` and canonical `football_video_defaults.json` at the beginning of every project. The approved Barcelona–Villa V4 video is a *visual benchmark*, not a reusable script or match dataset. The existing rendered MP4 must **not** be re-rendered just because these rules changed.

## One request, two independent choices

When the user says "create a football video about X", derive the **format** and **editorial angle** separately. Never copy the previous fixture. Use `production_intake.py new` to produce the editable project manifest and fill in VERIFIED research before any rendering. If an essential fixture is unknown, search first; no fake results or assets.

| Requested format | Typical runtime and canvas | Editorial treatment |
|---|---|---|
| `short` | 35–59.8 seconds preferred, 1080×1920 vertical, 30fps | Immediate real-action hook; 1–3 tactical insights; quick clean Qwen Ryan narration; show at least one complete goal/decisive action when relevant |
| `long` | 6–10 minutes as a default, 1920×1080, 30fps; honor explicit length | Several sourced tactical arguments, formation/pressing analysis, player-by-player comparisons, off-ball movement, transitions, set pieces, coaching adjustments, credible statistics and fair conclusion |
| `analysis` | Detailed `long` by default, but may be a `short` if the user says so | Same production controls, only the depth/structure differs |

| Analysis type | Fact and media requirements |
|---|---|
| `match_preview` | Match **has not kicked off** as of publication; verify kickoff, venue, tournament, both clubs' latest completed matches, real player availability, H2H, tactics and plausible position duels; label predictions explicitly; prior-fixture footage must carry its **actual date/opponent** |
| `match_review` | Match **has finished**; final score, timeline/scorers, verified starting XI and substitutions, key turning points, exact-game camera recordings for game-specific claims, nuanced tactical cause/effect and player contributions; never depict an older fixture as this match |
| `classic_match` | Historic match actually occurred; precise date, tournament, result and key events, archival exact-match recordings where available, verified old team rosters; use separate labelled present-day clips only when explicitly analyzing later context, never as old match action |
| `player_comparison` | Two real named players; genuine credited photos **of each**, footage showing **each**, paired like-for-like attack/defence metrics, role-adjusted interpretation; no synthetic likenesses |

If the fixture is on the current calendar date, research the confirmed final-whistle/kickoff status rather than inferring preview/review merely from the date. Old match “preview” must be labelled a retrospective exercise, not teased as a real upcoming fixture.

## Hard preproduction gates
1. Verify source-based claims: fixture against ≥2 authoritative/independent sources; two clubs' last completed matches (dates, scorelines and actually relevant footage); historic direct meetings; intended tactical claims, latest injuries, formation and announced lineups, dates and timezones.
2. Search genuine media beyond club YouTube: opposing clubs, rights-holders, networks, UEFA/leagues, agency libraries, original independent social posts from TikTok, Instagram, Facebook, X, Reddit, Dailymotion, Vimeo, Wikimedia, etc. Collect **exact** URL, recorded match/opponent/date, who recorded it, who holds rights and whether it's a repost. Distinguish *watchable* from *commercially licensed*. No invented filename/link.
3. Review a moving contact sheet and source action chronology per recording. Confirm named player's movement, scoring team and the actual moment of pass, shot, goal and reaction. Never substitute a goal conceded while describing that club scoring.
4. The editor chooses every source and in/out timestamp. Every spoken sentence must have a corresponding real shot or genuine relevant real photograph. The first picture in the edit is actual football action; modest original overlays are acceptable over real video.
5. For two-name matchup lines, use both actual player headshots shown at once, correctly identified, with relevant genuine football motion continuing underneath or nearby. No AI-generated image, video or face manipulation.
6. Target ≥80% authentic meaningful recorded motion and ≥70% actual relevant match-action, including for previews and longer analysis. These are **editorial quality thresholds**, not a law, safe copyright proportion or permission.
7. Source credits in small legible video lower-thirds plus full source URLs and photo licence/author information in the YouTube description. Licence or carefully documented applicable copyright exception case is separate from YouTube reused-content monetization. No guarantee of no Content ID claim or strike. A strike is not erased by ordinary video deletion. No auto-post.
8. Narration: actual **Qwen3 CustomVoice Ryan**, canonical personal names supplied as normal words; no syllabified cues, separate WAV for each visual beat, pitch-preserving tempo **1.35**, not legacy 1.48. Review full spoken names, liaison, cadence and naturalness. Keep performance quick and conversational; never lengthen names artificially. Maintain low stadium sound, equalized speech, two-pass -16 LUFS/-1.5dBTP mastering.
9. Review the complete video and at least 2–3 representative frames per shot, listen to entire narration, verify no clipped goal/voice, exact source game/date and source rights and graphical legibility on a mobile screen. Score visual quality, relevance, voice, names, editing and factual accuracy independently; reject low-quality results. Do not promise completion when render or source collection fails.
10. Only once a genuine, QA-reviewed MP4 is created, upload the actual MP4 and credits to **Google Drive** and verify the returned exact file URL. Keep source media transfers cloud-side to minimize user data usage.

## Standard execution

```bash
# Prepare a plan only; this does NOT generate a video or fabricate footage.
python video/football_edits/production_intake.py new \
  --format short --analysis-type match_preview \
  --team-a "Club A" --team-b "Club B" --fixture-date "2026-11-18" \
  --output /tmp/football_project.json

# A past game, substantive landscape analysis:
python video/football_edits/production_intake.py new \
  --format long --analysis-type match_review \
  --team-a "Club A" --team-b "Club B" --fixture-date "2026-10-29" \
  --output /tmp/past_match.json

# Populate the manifest with independently verified facts, source rights
# findings and manually selected exact clips; then fail-closed preflight.
python video/football_edits/production_intake.py check \
  --manifest /tmp/football_project.json --phase plan

# Deep media-specific gate on compatible legacy analysis manifests:
python video/football_edits/analysis_visual_gate.py \
  --manifest /path/to/detailed_editorial_manifest.json --phase plan
```

**Production is not an automated slideshow:** The code validates the project and chosen timecodes; actual visual decisions require inspected media, verified rights and human editorial judgement. Production outputs should not be reported as copyright-cleared by default.

## Request examples to follow without extra setup

- "Make a Short on tomorrow's Real Madrid vs Bayern": `short` + `match_preview` after researching verified kickoff, prior matches and player duels.
- "Make a 9-minute analysis of last night's match": `long` + `match_review`, real action **from that exact finished game**.
- "Analyze the 1983 Villa–Barcelona Super Cup": `long` + `classic_match`, historic event dating and real archival football clips.
- "Short comparing Yamal and Saka": `short` + `player_comparison` with two actual faces and real action from each.

If a required match or club doesn't exist, is wrong-date, or is only supported by low-quality/illicit footage, do not silently switch to another match or invent visuals. Supply an honest gap report and sourcing next step instead of a bad video.

## Existing pipeline and backwards compatibility

The old `football-barca-villa-qwen-shot-synced-v4.yml` and `render_barca_villa_shot_synced_v4.py` are fixture-specific examples, not the central configuration; their exported V4 video remains unchanged. The canonical **1.35** in `football_video_defaults.json` and this agent rule govern new productions. Existing strict `analysis_visual_gate.py` continues to apply where the source plan uses its schema and its approved-rights criteria. A media exception argument does not bypass that existing rights gate.
