# Football video standard — genuine football first (3 November 2026)

**Scope:** every football video, edit, tactical preview, post-match analysis, classic match, player comparison, YouTube Short and longer football programme produced using TOOLS. This football-specific rule supersedes older slideshow-driven instructions. It does not modify unrelated channels or the Ninefold Tide project.

## Mandatory visual direction

The film should look like a professionally edited football-analysis video, not an automated deck of cards and AI paintings.

1. **Use actual past-match recordings as the main visual.** Pick genuine moving footage that shows the pass, run, positioning, duel or finish described in the narration. Select the precise in/out times after watching the source and preserve the play's setup and resolution. For previews, label prior-match footage as previous-match footage, never as tonight's match.
2. **Authentic player head-to-head photos.** For a versus segment, select a real, clearly identified photograph of BOTH players with individually verified commercial edit permission. Crop/mask and orient them to face each other where the original angles allow it. Use restrained split-screen, team colours, opposing poses, readable names and tasteful motion. Do not swap faces, manufacture appearances, or make a two-player comparison from a single-player photograph.
3. **Overlay tactics onto real action.** Small, original arrows, freeze frames, movement trails and meaningful player markers are useful. Standalone tactic boards/stat cards are limited supporting elements. Disclose that a diagram illustrates a proposed tactic, rather than depicting an actual event.
4. **NO AI-generated image or video anywhere.** No synthetic player likeness, AI stadium, fake match camera, AI-generated match scenes, text-to-image football photos, image-to-video substitutes or CGI football highlights. The natural Qwen Ryan **audio voice** is allowed as original scripted commentary, reviewed for naturalness.
5. **Real reporting and insight.** Verify all fixtures, injuries, player positions, predicted lineups, statistics and quoted forecast numbers as of the filming date. Predictions must be presented as predictions. Never invent footage or game events.

## Enforced footage ratio

At least **60% of running time** must be actual moving, camera-captured football footage. At most **30%** may be genuine static player photographs (including head-to-head compositions). At most **25%** may be standalone original diagrams, overlays without real video, and statistics cards. These limits apply independently. A still is not 'video footage' simply because a crop moves. No more than **eight consecutive seconds** may be non-moving footage. Individual still-photo segments may last at most **six seconds**; a standalone tactic/stat card at most eight. The football-action source must depict a real match at least once. If suitable commercially cleared moving football clips cannot be sourced, STOP production rather than filling the timeline with repeated photos or AI.

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

CI verifies plan structure and missing licence/motion claims, but cannot independently prove real camera footage, the lawful chain of copyright ownership or visual creativity. Human review tied to actual exported MP4 remains mandatory.

## Rejected old workflow

The 3 November 2026 Barcelona–Aston Villa static/photo/pitch-diagram-heavy pilot is NOT an acceptable template. Its 720p/20fps automated six-scene storyboard does not meet the moving footage requirement. The old renderer (video/football_edits/barca_villa_tactical_qwen_20261103.py) is legacy-only and must never be used for new approved video production. Its GitHub Actions generator must remain disabled until replaced by a genuine manually authored real-footage plan passing this gate. The earlier Ronaldo real-video renderer can inform editing technique but must also meet current rights, editorial and release rules.

Regression tests:
   python3 -m unittest discover -s video/football_edits -p 'test_*.py' -v
