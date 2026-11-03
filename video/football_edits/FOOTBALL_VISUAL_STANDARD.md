# Football video standard — genuine football first (3 November 2026)

**Scope:** every football video, edit, tactical preview, post-match analysis, classic match, player comparison, YouTube Short and longer football programme produced using TOOLS. This football-specific rule supersedes older slideshow-driven instructions. It does not modify unrelated channels or the Ninefold Tide project.

## Mandatory research-first gate: do NOT begin rendering before this

**Search properly before making videos.** A fixture being announced, one match report, or one watchable highlights page is not sufficient preproduction research. For every match preview, the editor must:

1. **Verify the fixture twice**, preferably with the tournament organiser/UEFA and a club's official page; record the original fixture date, competition, kickoff in the target timezone, venue, and research date. Verify injuries, recent form and any actual tactical claims with source links. Check for late lineup/injury changes before export.
2. **Research BOTH clubs' latest completed games**, including their actual final results, opponents, match dates, key moments and potential relevant footage. Never assume a game in one competition is the latest across all competitions.
3. **Run a diversified footage sweep for BOTH clubs:** at least one club-origin search, one broadcaster/league/competition search, and one independent-creator/opposition-club/rights-controlled archive search per team (at least three different origin types per team). Search actual match name + date + highlights/extended highlights/full match/independent camera + named players. Collect the original candidate URLs, not unverified download mirrors.
4. **Inspect candidate recordings and record explicit decisions**: relevant and authorised (approved), permission needed, uncertain original rights, unrelated, outdated or too low-quality. A YouTube Creative Commons label from an uploader other than the rights holder requires independent origin review. Never treat an accessible video as cleared simply because it appears on Sky Sports, NBC, club channels or Commons. If relying on a potential copyright exception for criticism/analysis, document that separately; neither uploading nor Content ID establishes legality. Do not pretend a rights-uncertain clip is licensed.
5. **Author a clear spoken-claim to real-clip mapping** with the source match, player/team actually shown, source in/out, full pass/run/goal payoff, camera quality, intended crop, rights and audio. Pre-calculate the actual real moving footage percentage (minimum 80%, including at least 70% true, relevant match action). Locate enough usable footage **before** generating Qwen narration or the final edit.
6. **Fail closed when it isn't ready**: record exactly which missing sources or permissions prevent a high-quality cut, and continue source research rather than randomly substituting footage, recycling irrelevant videos or inventing a completed MP4. This is an honest production blocker, not proof that relevant football videos do not exist online.

The video/football_edits/analysis_visual_gate.py --phase plan check now requires preproduction_research evidence of the multi-origin search, two fixture references, two sourced factual claims and the actual selected media's individual visual/rights review. The gate checks the existence and consistency of declarations; human inspection and legal assessment are still essential. The fixture research must be refreshed for its actual publication date; an outdated pre-match preview should not be passed off as fresh after kickoff.

## Mandatory visual direction

The film should look like a professionally edited football-analysis video, not an automated deck of cards and AI paintings.

1. **Use actual past-match recordings as the main visual.** Pick genuine moving footage that shows the pass, run, positioning, duel or finish described in the narration. Select the precise in/out times after watching the source and preserve the play's setup and resolution. For previews, label prior-match footage as previous-match footage, never as tonight's match.
2. **Authentic player head-to-head photos.** For a versus segment, select a real, clearly identified photograph of BOTH players with individually verified commercial edit permission. Crop/mask and orient them to face each other where the original angles allow it. Use restrained split-screen, team colours, opposing poses, readable names and tasteful motion. Do not swap faces, manufacture appearances, or make a two-player comparison from a single-player photograph.
3. **Overlay tactics onto real action.** Small, original arrows, freeze frames, movement trails and meaningful player markers are useful. Standalone tactic boards/stat cards are limited supporting elements. Disclose that a diagram illustrates a proposed tactic, rather than depicting an actual event.
4. **NO AI-generated image or video anywhere.** No synthetic player likeness, AI stadium, fake match camera, AI-generated match scenes, text-to-image football photos, image-to-video substitutes or CGI football highlights. The natural Qwen Ryan **audio voice** is allowed as original scripted commentary, reviewed for naturalness.
5. **Real reporting and insight.** Verify all fixtures, injuries, player positions, predicted lineups, statistics and quoted forecast numbers as of the filming date. Predictions must be presented as predictions. Never invent footage or game events.

## Where genuine footage may come from — NOT club-only

**There is absolutely no requirement that match footage originate from either club's official channel.** Search for the actual teams, players and matches across all reasonably accessible sources before concluding that footage is unavailable. The working source pool includes: official club uploads; **the opposing club's own camera footage**; UEFA, LaLiga, Premier League and other league/competition archives; licensed **Sky Sports, TNT Sports, NBC, beIN, Eurosport, DAZN, other broadcasters and regional rights holders**; independent videographers and fan-shot footage; news agencies; Wikimedia Commons; archive.org; creators publishing an original recording under a genuine reusable Creative Commons licence; footage specifically licensed to the user or owned by them.

**Search by the actual game, player and timestamp**, not by channel ownership. In particular check **both clubs' last completed match from broadcasters, league videos and independent creators**, plus other current games that genuinely illustrate the exact tactics or named players. Do not give up after checking Barça Play or AVFC's website. Search and cache candidate URLs, then inspect each original video and licence.

Ownership and permission still matter: a free-to-watch Sky Sports, Premier League or YouTube clip may be perfectly relevant but is NOT automatically free to re-edit and monetize. A reuploader's "Creative Commons" notice alone is not proof that the original broadcast rightsholder licensed the action. Verify the licensor's authority and the licence covering the original recording and audio, or obtain commercial permission. A legitimate independent camera recording licensed by its actual creator is eligible without club endorsement (check any event/venue restrictions). A licensed broadcaster clip is eligible without originating from a club, provided the licence covers this use. Do not scrape/evade restrictions or silently make unlicensed footage the background.

**Source discovery should not become an excuse for low quality or a different subject.** The 80% authentic-action ratio, exact relevance to the two teams, appropriate camera footage and human audiovisual review remain binding. When the available licensed material is irrelevant or poor, report the gap and keep the video blocked rather than making a slideshow.

## Non-negotiable subject and clip relevance

**Not a single unrelated football video is allowed**, even if genuine, popular, HD, free to download, Creative Commons licensed, or already cached in TOOLS. The video must show the **specific team, player or actual match being discussed in the corresponding spoken passage**. Rights clearance and relevance are independent conditions: both are compulsory. For a Barcelona vs Aston Villa video, a Cristiano Ronaldo/Real Madrid goals montage is **not** acceptable just because it is authentic and available. Do not silently switch a requested Barcelona–Villa preview to a Ronaldo Short; changing subjects requires a separate user request.

**Match previews:** older recordings of Barcelona and/or Aston Villa are relevant when they genuinely depict the particular players, team shape, tactical behaviour, or action being discussed. Identify the original opponent and date and label such footage clearly as an earlier match. Do not use unrelated teams, generic football clips or stock footage as substitutes. An illustration of a possible future move must not be presented as actual match footage.

**Post-match reviews and classic-match videos:** footage called "the match" must show the **exact two teams playing the actual game on its real date**. Other matches cannot be spliced in as if they were the event under review. For any historical comparison, the narration and on-screen label must explicitly identify that earlier match; the main-match action still needs real source coverage.

**Player comparisons:** real film and photos must actually show one of the named compared players. A two-person versus image uses authenticated real photos of **both** named people. A photo or goal video of another footballer is not relevant, even if the players share a league, national team or position.

**Source and shot relevance is enforced before rendering.** The analysis manifest must identify the video's exact target teams, players and fixture date; each camera-recorded source must list the teams/players actually depicted and for each match source the actual two recorded opponents and historic game date. Each manually chosen shot must identify the named team/player it explains, and that person/team must be visible in its own source. Missing or contradictory identifiers stop the render; do not fill missing clips with unrelated footage or edit a different topic. Technical metadata is not proof of actual content; the full-shot human reviewer must reconfirm that the video *visibly* shows the declared entity before release.

## Each club's latest previous completed match — mandatory pre-production check

For every **upcoming match preview**, **research both teams' most recent completed match before the upcoming fixture**. Determine each club's last game as of the video's research/cutoff date, not simply the last Champions League game, the best-looking highlight, or the most recent match with freely available footage. Record opponent, date, competition, verified final result, official/credible result citation, and the exact source of potential footage. Repeat the preflight if the production date crosses a new scheduled fixture. No invented scores, dates, video availability or rights.

Decide **independently for each team** whether footage from that latest game directly supports a point in the narration (form, current shape, pressing behaviour, key goal, defensive weakness, availability). When useful **and separately cleared for commercial adaptation from ANY legitimate rights holder, not necessarily the clubs**, use manually selected meaningful passages of that exact latest recording, with opponent and match date shown on screen. Otherwise record **not_needed** (editorial irrelevance) or **rights_unavailable** (with a real clip viewing page URL). An official public/free-to-watch highlights page **does not itself grant editing rights**. If rights cannot be verified, the footage must be omitted rather than recorded as an approved source. Do not replace it with unrelated clips or keep a slide on screen to meet duration.

The plan validator requires a structured latest_previous_matches record for EACH of the two clubs and an explicit footage decision and explanation. An **include** decision also requires an exact rights-verified, correctly dated source from the latest game, explicitly referenced by a real-match action shot in the edit. The 80% genuine-footage, 70% relevant match-action and no-unrelated-clip standards still apply; latest-match research does not override them.

**Research example (3 November 2026 Barcelona–Aston Villa):**
- Barcelona's most recent completed match: **31 October 2026, Barcelona 6–1 Alavés (La Liga)**. Club result: https://www.fcbarcelona.com/en/football/first-team/results. Barcelona's own recent match video is only publicly viewable under restrictive content terms; written authorisation to republish its broadcast film has not been shown.
- Aston Villa's most recent completed match: **31 October 2026, Aston Villa 1–1 Fulham (Premier League)**. Official club match report: https://www.avfc.co.uk/news/2026/october/31/report-aston-villa-1-1-fulham/. Villa's own video page: https://www.avfc.co.uk/videos. Permission to commercially republish the current match footage has not been established.
- As a result neither most-recent match broadcast is **currently approved as a usable edit asset**. Research can still cite the results, but a Barcelona–Villa video must remain blocked until enough truly related footage has been sourced/cleared. Do not silently pivot to Cristiano Ronaldo, 2009 Barcelona footage, or another team's goals.

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
