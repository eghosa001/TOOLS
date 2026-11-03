# Football video standard — genuine football first (3 November 2026)

**Scope:** every football video, edit, tactical preview, post-match analysis, classic match, player comparison, YouTube Short and longer football programme produced using TOOLS. This football-specific rule supersedes older slideshow-driven instructions. It does not modify unrelated channels or the Ninefold Tide project.

## Mandatory visual direction

The film should look like a professionally edited football-analysis video, not an automated deck of cards and AI paintings.

1. **Use actual past-match recordings as the main visual.** Pick genuine moving footage that shows the pass, run, positioning, duel or finish described in the narration. Select the precise in/out times after watching the source and preserve the play's setup and resolution. For previews, label prior-match footage as previous-match footage, never as tonight's match.
2. **Authentic player head-to-head photos.** For a versus segment, select a real, clearly identified photograph of BOTH players with individually verified commercial edit permission. Crop/mask and orient them to face each other where the original angles allow it. Use restrained split-screen, team colours, opposing poses, readable names and tasteful motion. Do not swap faces, manufacture appearances, or make a two-player comparison from a single-player photograph.
3. **Overlay tactics onto real action.** Small, original arrows, freeze frames, movement trails and meaningful player markers are useful. Standalone tactic boards/stat cards are limited supporting elements. Disclose that a diagram illustrates a proposed tactic, rather than depicting an actual event.
4. **NO AI-generated image or video anywhere.** No synthetic player likeness, AI stadium, fake match camera, AI-generated match scenes, text-to-image football photos, image-to-video substitutes or CGI football highlights. The natural Qwen Ryan **audio voice** is allowed as original scripted commentary, reviewed for naturalness.
5. **Real reporting and insight.** Verify all fixtures, injuries, player positions, predicted lineups, statistics and quoted forecast numbers as of the filming date. Predictions must be presented as predictions. Never invent footage or game events.

## Non-negotiable subject and clip relevance

**Not a single unrelated football video is allowed**, even if genuine, popular, HD, free to download, Creative Commons licensed, or already cached in TOOLS. The video must show the **specific team, player or actual match being discussed in the corresponding spoken passage**. Rights clearance and relevance are independent conditions: both are compulsory. For a Barcelona vs Aston Villa video, a Cristiano Ronaldo/Real Madrid goals montage is **not** acceptable just because it is authentic and available. Do not silently switch a requested Barcelona–Villa preview to a Ronaldo Short; changing subjects requires a separate user request.

**Match previews:** older recordings of Barcelona and/or Aston Villa are relevant when they genuinely depict the particular players, team shape, tactical behaviour, or action being discussed. Identify the original opponent and date and label such footage clearly as an earlier match. Do not use unrelated teams, generic football clips or stock footage as substitutes. An illustration of a possible future move must not be presented as actual match footage.

**Post-match reviews and classic-match videos:** footage called "the match" must show the **exact two teams playing the actual game on its real date**. Other matches cannot be spliced in as if they were the event under review. For any historical comparison, the narration and on-screen label must explicitly identify that earlier match; the main-match action still needs real source coverage.

**Player comparisons:** real film and photos must actually show one of the named compared players. A two-person versus image uses authenticated real photos of **both** named people. A photo or goal video of another footballer is not relevant, even if the players share a league, national team or position.

**Source and shot relevance is enforced before rendering.** The analysis manifest must identify the video's exact target teams, players and fixture date; each camera-recorded source must list the teams/players actually depicted and for each match source the actual two recorded opponents and historic game date. Each manually chosen shot must identify the named team/player it explains, and that person/team must be visible in its own source. Missing or contradictory identifiers stop the render; do not fill missing clips with unrelated footage or edit a different topic. Technical metadata is not proof of actual content; the full-shot human reviewer must reconfirm that the video *visibly* shows the declared entity before release.

## Enforced footage ratio

At least **80% of running time** must be actual moving, camera-captured football footage, **at least 70% genuine filmed match action** and at most **10% generic football B-roll**. Generic or unrelated football stock is prohibited, including within the optional 10% secondary footage allowance; any secondary training or context clip must still visibly depict the specific team/player being discussed. At most **20%** may be genuine static player photographs (including head-to-head compositions). At most **20%** may be standalone original diagrams, overlays without real video, and statistics cards. These limits apply independently. A still is not 'video footage' simply because a crop moves. No more than **eight consecutive seconds** may be non-moving footage. Individual still-photo segments may last at most **six seconds**; a standalone tactic/stat card at most eight. The football-action source must depict a real match at least once. If suitable commercially cleared moving football clips cannot be sourced, STOP production rather than filling the timeline with repeated photos or AI.

All sources need exact subject, camera/recording provenance, creator, landing-page URL, licence evidence, explicit editing/commercial rights and downloaded SHA-256. For real matches, note teams and original match date. Copyright exceptions/fair use are fact-dependent, not an automatic release permission. A platform upload or short quote does not mean a match video is rights-cleared.

Aim for **1080p at 30fps or higher**, sharp dynamic typography, readable subtitles, high-quality audio, tight editing and natural Qwen commentary slightly faster than the earlier default. Explicitly distinguish actual football film, authentic photos and editorial diagrams. Do not mislabel upscaled footage as natively 4K.

## Places to find candidates, not blanket licences

- [Wikimedia Commons — association football match videos](https://commons.wikimedia.org/wiki/Category:Videos_of_association_football_matches) contains genuine historic and modern moving match videos. Verify EACH file page, uploader authority and commercial/edit licence before reuse.
- [Wikimedia Commons](https://commons.wikimedia.org) contains authentic player photos with per-file licences, often requiring author credit and sometimes ShareAlike.
- [Pexels football videos](https://www.pexels.com/search/videos/football/) offers real training and generic football stock B-roll under the Pexels licence (including commercial editing in its terms); source-specific subjects, trademarks, people and derivative issues still require checks. Such generic video NEVER proves a tactical event in a named match and must not replace original match-action material.
- User-owned recordings or written commercial permissions for specific match footage are preferable where available.

Attribution alone is not permission. YouTube originality/monetization and Content ID are separate from commercial footage rights. Do not automatically classify copyrighted broadcasts as free because a commentator adds arrows.

## Actual production checklist

1. Research a factual, original football-analysis angle with named sources and date.
2. Locate and watch exact genuine moving match clips first. Check rights BEFORE scripting visuals, document hashes and author/source details. Identify real photo candidates for any named player duel.
3. Create an editor-authored timeline manifest in the football_analysis_real_media schema, with exact clip in/out and final shot in/out, spoken passage, editorial purpose, source IDs, real-photo duo, footage status and rights evidence. NO automated source or scene selection.
4. Run plan validation before cloud/Qwen render:
   python3 video/football_edits/analysis_visual_gate.py --manifest plan.json --phase plan
5. Manually edit the approved shot timeline with FFmpeg or the existing football production tool, preserving the source clips and real versus photos. Do not allow an agent to fill gaps with generated art, cloned footage, stock footage, placeholder diagrams or random media.
6. Review the entire actual export picture AND sound. Check every match action is genuine, previous-match notices, accurate photo identification, voice sync, ratios, complete goal action, rights and credits. Record human reviewer, date and exact MP4 SHA-256.
7. Run final gate:
   python3 video/football_edits/analysis_visual_gate.py --manifest plan.json --phase release --assets-root .
8. For re-edited third-party footage, additionally use the existing universal edit studio plan/release gate; for goal compilations retain the specialized football release gate. Neither is replaced by this new visual gate. No automatic YouTube upload; Google Drive only for quality-approved deliveries.

CI verifies plan structure, named-team/player relevance declarations and missing licence/motion claims, but cannot independently prove that the pixels really show the named team/player, the lawful chain of copyright ownership or visual creativity. Human review tied to actual exported MP4 remains mandatory.

## Rejected old workflow

The 3 November 2026 Barcelona–Aston Villa static/photo/pitch-diagram-heavy pilot is NOT an acceptable template. Its 720p/20fps automated six-scene storyboard does not meet the moving footage requirement. The old renderer (video/football_edits/barca_villa_tactical_qwen_20261103.py) is legacy-only and must never be used for new approved video production. Its GitHub Actions generator must remain disabled until replaced by a genuine manually authored real-footage plan passing this gate. The earlier Ronaldo real-video renderer can inform editing technique but must also meet current rights, editorial and release rules.

Regression tests:
   python3 -m unittest discover -s video/football_edits -p 'test_*.py' -v
