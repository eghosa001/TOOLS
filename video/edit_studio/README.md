# Universal Edit Studio — rights, originality, scene completeness

This is the **only active video-edit pipeline** in TOOLS. Use for ANY re-edit: anime, films, TV characters, gaming, sports, celebrities, music, comedy, documentaries, history, user-shot content and every other genre. No genre is banned as a class. Rights are checked **per exact asset**. This process is a gate for internal editorial release, NOT a guarantee of YouTube monetization or Content ID safety.


## One pipeline for any edit (active default, 4 Nov 2026)

The earlier `video/football_edits/` specialization and its GitHub Actions jobs were retired from the active repository at the user's direction. Git history preserves old versions but **do not route any new edit through those files**. This is for cinematic character edits, anime, game montages, movie scenes, football or other sport moments, comedic recontextualizations, tutorials and other source-based edits. No category is privileged.

1. `python3 video/edit_studio/new_edit.py --title "..." --category anime --style character_study --platform short --output edits/subject.json` creates a fill-in, **unverified** project manifest.
2. Manually choose relevant genuine footage and any voice/music. Track original creator, source page, dated commercial reuse terms, clip SHA-256, actual in/out and why each shot matters. Voice is optional. Originality must go beyond a sequence of simple cuts, captions or music sync.
3. `python3 video/edit_studio/release_gate.py --manifest edits/subject.json --phase plan` checks the sourced storyboard. A plan is not publication clearance.
4. `python3 video/edit_studio/render_edit.py --manifest edits/subject.json --assets-root . --output candidate/subject.mp4` renders a real MP4 using only locally provided verified sources (1080x1920, 1920x1080 or 1080x1080; 30fps default), optional editor-specified playback speeds and licensed audio bed. This is an *unpublished review cut*, not a final release. It never downloads or invents third-party clips.
5. A human watches/listens to the entire export and documents both source rights and meaningful creative interpretation, then scores it in six broadly applicable categories: story/context, voice or sound, visual design, genuine relevant footage, entertainment/retention and publishing readiness. Each has evidence; weighted total must reach 8/10 and the individual minimums. Use `quality_gate.py` for automatic completeness enforcement.
6. Only after the exact export is reviewed and signed with its SHA-256, run `release_gate.py --phase release --assets-root .`. That internal gate is **not** a guarantee of fair use, Content ID avoidance or monetization. YouTube/TikTok upload requires a separately authorized action and platform/account review.

A generic manual GitHub Actions production entrypoint is `.github/workflows/universal-edit-production.yml`. It accepts a checked-in manifest and reviewed source assets, and can prepare a draft without publishing. The existing project-specific historical/ASMR/animation pipelines are unchanged.

## Two independent tests
1. **Commercial rights**: exact clip/photo/music owner, source page, licence/permission evidence, derivative and commercial permission, conditions, dated review and SHA256. Attribution is not permission. A streamed show, anime, game, TikTok video or football broadcast is not automatically free to reuse. Unclear rights or a fair-use exception claim can be catalogued for research but **cannot pass automatic commercial release**. Legal exceptions need separate, case-specific advice.
2. **Original contribution**: a specifically authored interpretation, character study, story, analysis or critical/comedic recontextualization. Transitions, reordering, filters, zooms, beat-synced edits, basic captions or licensed footage alone do not automatically satisfy YouTube reused-content policy. The actual export must be watched.

**Voiceover is optional for a genuinely substantive non-narrated edit.** A music-led original narrative or meaningful explanatory visual storytelling can be reviewed, but music sync/beat cuts alone are insufficient. If using existing music, document commercial-use rights independently.

Use only licensed or original existing footage/images; no AI-generated substitute scenes. Newly authored captions, annotations and diagrams may explain existing real footage.

## Editing and review sequence
- Manually select footage and in/out points. Preserve the action AND payoff (goal, character decision, emotional reaction, gaming outcome). Do not arbitrarily cut identical-length fragments.
- Record each scene's exact rights status, source, hash, reason for selection and what new narrative contribution it makes. If claiming "all 48" or any complete set, maintain a countable, independently checked event ledger; otherwise label it highlights.
- Run the plan guard:
  python3 video/edit_studio/release_gate.py --manifest chosen_edit.json --phase plan
- Render a draft using the already-installed editing/FFmpeg pipeline from this author-approved timeline. No automatic source selection, bulk slide shows or unsupervised publication.
- Watch and listen to the complete actual export; check rights, no premature cuts, specific original contributions, attribution and accurate title. Sign the reviewed export's SHA256, date and reviewer in the manifest.
- Only then run:
  python3 video/edit_studio/release_gate.py --manifest chosen_edit.json --phase release --assets-root .
- Publication requires a separately authorized uploader and verified channel identity. Neither a successful MP4 nor an internal gate pass means YouTube will monetize it.

## GitHub integration
- Run generic unit tests and fail-closed plan tests in .github/workflows/universal-edit-studio-gates.yml.
- New edit-production/publishing workflows MUST invoke the plan and release guards, plus the genre-neutral six-part quality score gate, before any monetization-ready tag, public media release or YouTube upload. This universal studio never auto-publishes.
- No football-only template, fixture validation, tactical diagram requirement or sports-specific visual quota applies globally. Respect other independent history/ASMR/animation production pipelines when creating content for those projects.
- Existing bespoke upload workflows are not automatically intercepted by adding a script. Before using a legacy workflow to publish a third-party-footage edit, explicitly integrate this universal gate or use a gated publishing workflow.
- The example_manifest.json uses placeholders and is NOT publication-ready.

References: https://support.google.com/youtube/answer/1311392?hl=en (reused content); https://support.google.com/youtube/answer/2490020?hl=en (commercial rights); https://support.google.com/youtube/answer/6013276?hl=en (Content ID). 

## TikTok platform profile (3 Nov 2026)

The generic release gate also applies to edits planned for TikTok. Platform-specific checks live at video/edit_studio/tiktok_profile.py. Keep **posting eligibility** separate from **Creator Rewards**; a short edit can be posted when rights and originality have been reviewed but is not automatically eligible for per-view payments.

CLI commands for an author-reviewed edit manifest and planned duration:

    python3 video/edit_studio/tiktok_profile.py --manifest chosen_edit.json --objective publish --duration-sec 28 --phase plan
    python3 video/edit_studio/tiktok_profile.py --manifest chosen_edit.json --objective creator_rewards --duration-sec 75 --account-json account_status.json --phase plan

For a real export, supply --phase release --assets-root . after the signed universal release gate succeeds. The profile requires verified TikTok Studio Creator Rewards availability, Personal account, age 18+, good standing, >=10K followers, >=100K views over 30 days and >=60s video. These are minimum checks, not TikTok acceptance. The profile blocks Creator Rewards claims for Nigerian accounts as of Nov 2026; TikTok Studio's live entitlement must be verified even in listed countries.

Anime/movies/TV/football/music edits can still be published if all relevant rights are cleared, but clips originating from other rightsholders carry a separate originality and reward-eligibility risk. Third-party licensed footage cannot be assumed to satisfy TikTok Creator Rewards originality rules. Do not use sounds licensed inside TikTok as automatically licensed for YouTube or external commercial use. Brand/promotion posts require commercial music clearance, such as TikTok's Commercial Music Library within its terms. Do not publish or make account eligibility assertions from this tool without reviewing the real account.

Primary references: https://newsroom.tiktok.com/introducing-the-new-creator-rewards-program ; https://support.tiktok.com/en/business-and-creator/creator-rewards-program/creator-rewards-program ; https://support.tiktok.com/en/business-and-creator/creator-and-business-accounts/commercial-use-of-music-on-tiktok ; https://t.tiktok.com/legal/page/global/copyright-policy/en
