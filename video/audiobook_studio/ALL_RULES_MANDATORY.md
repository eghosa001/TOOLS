> **TOP PRIORITY FOR AUDIOBOOK VIDEO (12 NOV 2026):** Story quality remains mandatory, but the **first and decisive VIDEO production/release criterion** is synchronized meaning: EVERY illustration must be relevant to the words actually spoken at that time. Every actual encoded shot needs 8/10 or higher **individually** in narration fidelity, image/event match, temporal synchronization, and character/prop consistency. A single wrong or mismatched image blocks handoff, even with perfect narration, music and 16/16 story criteria. Validate a full signed PRIVATE scene ledger (actual source/audio/image/video hashes, spoken excerpts, timecodes and genuine full human watch/listen) using `voice_image_priority_gate.py` as part of `episode_quality_gate.py` BEFORE any delivery or publication. The preproduction story/audio approval is still required. Do not fabricate viewing/ratings or bypass via another uploader. See `EPISODE_TEAM_SCORECARD_8_PLUS_STANDARD.md`.

> **NEW BINDING OWNER 8/10 PER-TEAM-MEMBER PRODUCTION GATE, 12 NOVEMBER 2026.**
> Before ANY new audiobook episode art, narration, music, compositing or video work,
> run episode_quality_gate.py --phase preproduction on the PRIVATE signed scorecard.
> Each assigned team member must score EVERY assigned readiness dimension at least 8/10;
> missing evidence or any failed hard gate blocks ALL production. Before showing,
> handing over, uploading to Drive for user access, or publishing ANY finished video,
> ALL 15 final categories must be at least 8/10 from EVERY assigned reviewer,
> and ALL 16 hard gates must pass, including human encoded-video review and verified
> real master MP4 in Drive. Low scores cannot be averaged away. Do not share draft
> cuts as finished videos or bypass the gate through another uploader.
> Details: EPISODE_TEAM_SCORECARD_8_PLUS_STANDARD.md.

# Audiobook Studio — ALL owner rules are mandatory (12 November 2026)

Applies to every Mythveil audiobook story, script, narration, illustration, assembly, title, description, thumbnail and public release. This does not alter other channels' production standards.

## Binding sources and precedence

- All **109 numbered requirements** in the owner's *AUDIOBOOK_STUDIO_MASTER_SOURCE_RULES_v1.1* and every relevant part of the *Universal Story Quality Scorecard* (16 dimensions) are binding.
- The latest explicitly approved manuscript, bible, continuity, character sheets and pronunciation notes define story canon.
- Every newer explicit owner rule is also binding. If a newer instruction replaces an older default, document the exact override rather than ignore or silently merge rules. Example: the 8 November Kokoro Michael production decision superseded the 6 November Qwen/Ryan initial audition rule.
- Rulebook planning estimates for duration, number of illustrations, word count and speech pacing are **not quotas**. Do not pad or slow an episode to satisfy them.
- A rule applies at its relevant stage. A genuinely inapplicable or superseded rule needs written reason, owner-approved exception and evidence. No silent waiver.

## Stop conditions

1. **Text stage:** No story drafting or revisions without the current approved source and bible. Require all 16 scorecard categories reviewed with actual scene evidence and scores of at least 8/10, plus genuine independent cold-reader feedback before any claim of publication-readiness. Do not fabricate reviews.
2. **Voice stage:** No finished narration without approved script and name auditions, full-length human listen on headphones and phone speaker, six audio scores each >=8/10 and weighted score >=8.5/10. Automated transcripts are not a substitute.
3. **Image and video stage:** No finished video without source-linked, full-color, continuous story art; proper rights; required soft melodic background; measured audio/image alignment; real final MP4 hash; and human inspection of the entire encoded video.
4. **Before YouTube upload:** No publication without exact approved series/episode number/title, canonical thumbnail and naming, verified channel/account, existing correct series playlist, uploader field mapping, five signed release holds and the owner's explicit release instruction. Run both:
   - python video/audiobook_studio/release_naming.py PRIVATE_RELEASE_MANIFEST.json --release-packet PRIVATE_RELEASE_PACKET.json
   - python video/audiobook_studio/mandatory_release_gate.py PRIVATE_RELEASE_PACKET.json
   Both must exit 0. Missing evidence means PUBLICATION_BLOCKED, not 'probably fine'.
5. **Immediately after upload:** Query the **live official YouTube video and playlist** and verify actual title character-for-character, channel, description headline, real playlist membership and approved thumbnail. Update the private packet with live data, then run:
   - python video/audiobook_studio/mandatory_release_gate.py PRIVATE_RELEASE_PACKET.json --phase postupload
   If failed, keep the existing video ID and correct its metadata with authorized credentials; never falsely claim completion or upload a duplicate.

## Required private release packet

Record master_rules_version 1.1; the exact release_manifest validated by release_naming; master_rule_reviews keyed 1..109 with reviewer, evidence, review date and status pass. For a genuinely superseded/not-applicable rule, add explicit reason, owner_exception_approved true and owner_approval_reference. Supply universal_story_scorecard_16 keyed 01..16 with scores and actual scene evidence. Supply full_episode_audio_review, final_video_review, release_holds (story/bible; independent literary/originality; voice/full audio; visuals/final MP4; explicit owner final publication approval), and upload_metadata with actual approved title, description headline, intended playlist and connector permissions. Postupload requires verified_live_youtube_metadata including the real playlist item.

**The release packet and evidence must remain private.** This public repository may contain validators and policy but never unpublished manuscripts, owner approval private messages or release secrets.

## Technical boundary

The validator is a fail-closed check for submitted evidence. It cannot independently verify whether humans really listened or whether a separate YouTube/Drive connector used it. Every actual uploader must integrate this pre-upload check and live post-upload verification. An internal rule, a successful CI test, and a passed packet alone do not establish that a third-party publishing flow is technically locked. Any unintegrated uploader must be treated as BLOCKED for unattended release.
