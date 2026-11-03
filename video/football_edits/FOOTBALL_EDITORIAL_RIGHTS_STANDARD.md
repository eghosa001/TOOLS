# Football edit rights and monetization-readiness standard

Applies to **every football video made or released through TOOLS**, including compilation videos, single-goal Shorts, player tributes and full-length breakdowns. This is an enforceable **internal publication gate**, not an assurance of YouTube monetization.

## Before editing
- Use original match footage with a per-file provenance ledger: exact file page, creator, explicit commercial/derivative-use licence, dated licence review, original hash and required credit. Never use TikTok rips, random YouTube clips, social reposts, club broadcast images or copyrighted music by default.
- Only **real football footage**. No AI-generated match scenes or images. Generated voice reading a creator-written analytical script may be used, but must be distinguishable from the real footage and may not impersonate players or commentators.
- Determine the scope first: a selection of highlights is **not** all the goals. Claim "all 48" only after checking that every one of the 48 complete goals is visible. A source titled "all 48" is evidence of its title, not proof that any edited output contains all 48.

## Edit and narration
- Every selected goal must include the buildup or identifiable attacking action, ball crossing the line, and sufficient result/reaction to understand the finish. Record exact manually reviewed in/out timecodes. **Never make arbitrary equal-duration cuts** across football footage.
- Use a distinct original story or analytical thesis. Explain a player's movement, finishing decision, tactical problem, passing option, or a documented match-specific insight; avoid interchangeable praise, generic quotes, meaningless text stickers and beat-only compilation edits.
- Keep real action visible, especially ball, defender, goalmouth, replay and end of goal. Use overlays to illuminate the play, not obscure it. Do not claim an isolated timestamp proves a goal was completed if no editor watched it.
- Use an original authored and performed narration (or natural recorded narration of an original script), explanatory annotations and a real edit structure. Sound effects, zooms and colour grade **alone do not pass**.
- Ensure facts are traceable, sports statistics dated and each voiceover remark can be verified against the actual scene. Cite sources in the narration's fact ledger.
- Maintain original soundtrack rights. Proof of voice being included and audible must be checked on exported audio.
- Original editorial contribution and source reuse documentation must be retained in the ZIP or release with the MP4, and visible attribution put in the video description when required.

## Release
- Check exact hashes of source files; then run `release_gate.py --phase plan`.
- Export a candidate to a separate review location, never directly to a live publishing step.
- A human must actually watch the entire candidate, verify every selected goal finishes, verify audible original commentary, confirm substantive transformation and rights, and record dated sign-off. Then run `release_gate.py --phase release`.
- Do not mark an MP4 "approved for monetization" because it rendered successfully. YouTube reviews the **whole channel**, and a third-party Content ID claim can still be raised even against CC-licensed footage.

Policy sources checked 2026-11-03: [YouTube channel monetization/reused content](https://support.google.com/youtube/answer/1311392?hl=en), [YouTube eligibility for commercial material](https://support.google.com/youtube/answer/2490020?hl=en), [YouTube Content ID](https://support.google.com/youtube/answer/6013276?hl=en).

Ronaldo archival source: [Wikimedia Commons — all 48 goals of Cristiano Ronaldo, 2014–15](https://commons.wikimedia.org/wiki/File:All_48_goals_of_Cristiano_Ronaldo,_in_35_league_matches_for_Real_Madrid_(2014-15).ogv), creator **Real Madrid**, reviewed **CC BY 3.0**; [deed](https://creativecommons.org/licenses/by/3.0/). Its source publication and historic licence review are documented at the Commons file page.

**Known bad legacy:** `ronaldo_2015_ccby.py` used eight arbitrary 2.6-second fragments. Its previous output may cut goals short, is not all 48, and lacks scene-specific original commentary. Do not reuse the 2026-11-03 download as a production-ready template. It remains available only as a historical failed sample, not a release-approved cut.
