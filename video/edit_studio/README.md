# Universal Edit Studio — rights, originality, scene completeness

Use for ANY re-edit: anime, movies, TV characters, gaming, football, other sports, celebrity, music, comedy, documentaries, and other genres. No genre is banned as a class. Rights are checked **per exact asset**. This process is a gate for internal editorial release, NOT a guarantee of YouTube monetization or Content ID safety.

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
- New edit-production/publishing workflows MUST invoke the plan and release guards and enforce them before any monetization-ready tag, public media release or YouTube upload.
- Keep specialized football scene checks as additional requirements; likewise retain the historical authentic-footage rule and other existing project-specific gates.
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
