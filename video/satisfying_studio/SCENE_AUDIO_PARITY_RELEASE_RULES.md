# Mandatory per-scene sound-to-picture release gate — ALL ASMR formats
Effective: 2026-11-01. **Publication blocker**, not advisory. Covers stock footage, CGI, licensed hybrid, natural field recordings, rain, sand, fire, jelly, and future studio formats. Does not govern separate history-documentary production.

## Why this exists
The 2026-10-31 2m45 rain video exposed the defect: AAC soundtrack was continuous and started within ~21 ms of the picture, but unchanged apartment-window rain audio was mixed across **22 different scenes**. Rooftops, leaf drips, puddle splashes, forest, hand on glass and wet-road traffic lacked scene-matched Foley. Adding animated falling rain did NOT regenerate or re-audition the audio. Codec checks, loudness and peak measurements passed while the sound-design promise failed.

**Never equate track alignment, no silence, a genuine rain recording or a signal-QA score with actual audio-video parity.**

## Required editorial sequence
1. Before full production: author scene list with timecoded visual source, material, force, acoustical environment, visible salient events, licensed recorded sound, source SHA256 and specific sound cue placement. Approve a 6–15-second mobile-quality actual moving sound-and-picture proof.
2. After picture lock, observe each distinct **salient audible** event (glass touches, splashes, rooftop-drip impacts, wet-road tire pass, tool contact). Not every raindrop needs a separate sound. A continuous diffuse rain bed may be physically correct only when the scene contains no individualized audible cue; document why.
3. Source and mix genuine physically appropriate Foley for the actual material, rate, force, perspective and location. A generic window-rain bed cannot automatically support outdoor woods, roof or splashing scenes.
4. After the final edit, run the full post-render AV scanner and existing continuity/signal checks. Watch the **entire exact master** and listen to its **entire soundtrack** with headphones; compare EVERY visual scene with heard material, loudness, perspective, rate, contact timing and transitions.
5. Any new visual alteration (e.g., a falling-rain overlay, respeeding, changed visible contact) invalidates earlier sound assumptions. Re-audition affected scenes with the final picture and document the effect's sound requirement, even when the source audio bytes are unchanged.
6. Any sound change invalidates prior full-master approval. Export, scan, rewatch and listen again. Record exact new SHA256.
7. Record full timecoded evidence under final_review.scene_audio_parity in the production manifest. Never invent reviewer identities, headphone auditions, contact times, observed material matches or audio-source hashes. If the file cannot actually be heard and watched, it is **NOT APPROVED**.
8. Before publishing through YouTube, Zernio, Upload-Post, any API, or a manual upload, run:
   python video/satisfying_studio/quality_gate.py release PATH/TO/production.json
   Any nonzero result means **STOP: DO NOT PUBLISH**. Technical scan success by itself is never publication approval. Explicit owner permission for public publishing remains separately required.

## Automated enforcement
scene_audio_parity_gate.validate_scene_audio_parity is called within the existing quality_gate.py release path, AFTER the standard exact-master/full-headphone/shot review, signal QA, physics and quality checks.

The required final_review.scene_audio_parity v1 evidence contains:
- Approved=true, unresolved_issues=[], exact reviewed_master_sha256 and reviewed_av_scan_sha256
- Genuine reviewer/method, full-video watch and entire headphone listen, re-review after last picture AND audio changes, detailed whole-film observations
- sound_sources entries with ID, actual audio file under project tree and matching SHA256, original source URL, commercial-safe individual license, recorded material, action and environment
- scene_checks one-to-one with all planned shots, exact 24 fps start_frame and end_frame, visible/audible material/action/environment, sound source IDs, per-scene real listening and visual observations, material, environment, intensity and texture checks plus every scene transition
- Full salient_visible_events lists with exactly corresponding synchronized_sound_events: unique event ID, frame of visible action, frame of heard onset within <=1 frame, source ID, recorded heard action, force/material/intensity match and real audition notes
- If truly ambient-only: a substantial no_distinct_audible_events_reason and ambient_only_suitable=true, not a claim that all audible events are synchronized
- Effect relevance flag visual_effects_affect_sound; if true then actual effect_sound_reevaluation_notes, effect_sound_reevaluation_passed=true and audio_reviewed_after_effects=true

Automatic rejections include: missing/partial scene, stale master or AV scan SHA256, missing sound provenance, mismatched material/environment/intensity, missing audible-event cue, >1-frame timing drift, missing headphone replay, missing transitions, new visual effects without audio reassessment, or any unresolved blocker.

## Limits: do not falsely claim sound was verified by code
The validator can check declared frame timing, hashes, source files, field completeness and self-consistency. It CANNOT detect the true physical source of a sound by waveform alone, establish that all natural raindrop events are covered, prove someone listened with headphones or award premium artistic quality. Human/AV-capable editorial inspection remains essential and claims cannot be fabricated. No existing standalone cloud posting connector is technically forced through GitHub; connected publishers must be operated only after explicit preflight approval.

## Regression command
cd video/satisfying_studio && python -m unittest -v test_scene_audio_parity_gate test_quality_gate
CI jobs satisfying-studio-gates and satisfying-studio-av-review-tests must pass.
The earlier 22-scene rain video remains UNAPPROVED until scene-specific Foley is rebuilt, reauditioned and the new exact export passes.
