# Satisfying Studio — free commercially licensed real-world footage & hybrid production

**Effective 30 October 2026. Owner explicitly supersedes the earlier CGI-only restriction for this ASMR project.** This licence policy applies only under `video/satisfying_studio`. It does not relax history/documentary asset rules or the independent audiovisual release standard.

## Allowed production paths
- **LICENSED_STOCK:** editor-selected real-world stock video + original human-directed sequence + genuine matched sound design + licensed provenance. A stock-only compilation is NOT inherently eligible for YouTube monetization; obtain substantial original creative value before publication.
- **HYBRID:** same licence and sound rules, using source-cleared stock footage with separately authored original Blender sequences/graphics, compositing, and original transitions.
- **CGI_ONLY:** retain every Blender authoring recipe and existing test. The existing 47-format catalogue and legacy CGI scene assembler do not suddenly certify stock footage; do not change an existing manifest silently.

## Source allowlist (individual clip checks mandatory)
1. **Pexels Licence** — https://www.pexels.com/legal-pages/license/ ; https://help.pexels.com/hc/en-us/articles/360042295214-Can-I-use-the-photos-and-videos-for-a-commercial-project . Free commercial use, adaptation permitted, no required credit. Respect identifiable people, trademarks, endorsement and redistribution restrictions.
2. **Pixabay Content License** — https://pixabay.com/service/license-summary/ and https://pixabay.com/service/terms/ . Commercial use and adaptation permitted. No standalone resale/distribution, including merely resizing, cropping or recolouring; combination must meaningfully create a new work.
3. **Mixkit Video Free License** — https://mixkit.co/license/ ; https://mixkit.co/free-stock-video/ . Individual clip must be under **Video Free License**. **Video Restricted License is NOT allowed** for this commercial channel.
4. **CC0/public domain** — use authenticated original and verify exact CC0/public-domain declaration at the item page, not a search label.
5. **CC BY 4.0** or other explicit commercial-permitted attribution licenses — only if the original author, licence URL, modification statement, and attribution are stored and reproduced in video description as required. If attribution cannot be complied with, reject.

Never rip another ASMR creator's YouTube video, use watermarked preview/proxy clips, assume Creative Commons from a keyword, mislabel footage as original 3D, or publish media with unclear rights. Original creator rights and release/privacy/trademark issues require separate screening. Free-to-download does NOT automatically mean commercially permitted.

## Source ledger per shot
Each selected shot requires stable individual source page; contributor if available; source publication/platform; **exact checked licence + licence URL + checked date**; original clip SHA256; original filename, codec/fps/resolution; exact source trim; changes; corresponding output timeline span; saved frame samples; permitted use evaluation; audio source URL and licence; recording-to-visible-gesture appropriateness; credit/rights flags. Do not include unverifiable source records as clean.

An exact video is accepted for render only after the agent has **manually authored its narrative sequence and transitions**; source selection, rights matching and audio judgment must not be random/fully unattended. Keep the full source visible when an object or gesture would be cropped. No stretching, looping or adding unrelated sounds to pad runtimes.

## Audiovisual release protection
- The same 9/10 owner quality target remains, including macro clarity, visual detail, shot pacing, exposure, continuity, sound naturalness, physical gesture match, and entire-video review. **No automatic 9/10 from a successful FFmpeg command**.
- Real in-shot, synchronous audio is preferred if audible and appropriate. If stock has silent or no sound, editor selects same-material/movement real field recordings (e.g., sand poured onto sand), not procedurally invented audio or mislabeled impact sounds. Aim for each audible contact within one frame when discrete. Continuous flows should match the *whole ongoing action*.
- No unintended near-silent passage >=0.45s after final encode. No borrowed YouTube benchmark footage, non-consensual voice, excessive crop, fake camera physics, hard soundtrack jumps, or repeated five-second fillers.
- Verify actual video 24fps final frame count, H264/48k stereo audio, full decode, zero black/freeze issues, final AV scan and recorded genuine headphone/visual review before publication.
- YouTube reused/inauthentic-content policy: https://support.google.com/youtube/answer/1311392 . Stock rights DO NOT guarantee monetization. Prefer meaningful original Blender inserts, purposeful sound design and distinctive creative sequencing, not low-effort stock compilations; disclose stock sources honestly in channel workflow.
- Preserve editor-approved preview and final source/rights ledger. No owner footage required. Provide a low-data mobile copy and Google Drive link whenever practical.

## Available, already retrieved original stock resources
- Five Pexels sandfall clips from successfully downloaded action [40895058027](https://github.com/eghosa001/TOOLS/actions/runs/40895058027), including close sand cup pour, hand flow, airborne sand and beach sifting. Exact source pages and SHA256 in the archived `source_provenance.json`.
- Six additional original Zen-garden/sand-process clips from action [40899906637](https://github.com/eghosa001/TOOLS/actions/runs/40899906637), including direct Zen-garden pour and catching falling grains.
- Two authentic CC0 recorded sand pours from action [40895602308](https://github.com/eghosa001/TOOLS/actions/runs/40895602308); both original OGG recordings and source attributions are kept. Source pages: https://freesound.org/people/nicoproson/sounds/627070/ and https://freesound.org/people/martinimeniscus/sounds/199332/ .
- Rerun `.github/workflows/asmr-licensed-stock-sand-60s.yml` to bring these existing cloud media assets into an **original hand-directed** 60-second technically verified REVIEW candidate. Download assets in GitHub cloud, not on the user's phone. Never auto-publish; replace expiring source-run artifacts with a licensed source cache or a new rights-verified download when needed.

## Status
An initial 60s Sandfall Ritual was actually assembled and technically reviewed on 30 Oct 2026 (seven edited shots, real CC0 sand Foley). It is an **unapproved artistic candidate** pending complete headphones and source-clip creative/monetization review. Only the source policy is approved by the owner's request, not the video quality.


## Source-hash intake validator and additional confirmed 30s take (30 October 2026)

Use `python video/satisfying_studio/production/licensed_footage_gate.py <full_source_ledger.json> --assets-root <original_licensed_source_directory>` before manually producing a stock/hybrid release. This small **free/offline** program checks local source SHA256, corresponding publisher-domain licence, prohibited Mixkit Restricted/noncommercial labels, real source clip trim bounds, duplicate excerpt reuse, human-authored shot notes, Foley licence and source SHA256. It returns **rights/timing intake**, never subjective video approval or guarantee of YouTube monetization. `--release` fails until evidence-bound human full-picture/headphone review exists. The existing 47 CGI-specific scripts remain separate.

**New 30s portrait shot candidate, four distinctive real Pexels takes:** source and timecode ledger [`releases/SAND_FOUR_POURS_30S_SOURCE_LEDGER_2026-10-30.json`](releases/SAND_FOUR_POURS_30S_SOURCE_LEDGER_2026-10-30.json), source IDs 8347918, 8348030, 6550977, 17230362; CC0 recorded sand sounds 627070 and 199332. Reproduce that **already directed** original cut using `production/render_four_pours.py --assets-dir <licensed_staged_assets> --out-dir <new_output_dir>`. No new media is downloaded by the renderer: the existing GitHub Actions asset archives are reused. Full 30s actual MP4 was produced and technically decoded, but is **NOT independently headphone-reviewed or 9/10 approved**.

- **30s HD Google Drive review:** https://drive.google.com/file/d/1pCDv-TGNS1jABCKTBj4YTS55FgRZ1owk/view?usp=drivesdk
- **30s data-saving mobile review:** https://drive.google.com/file/d/1rWCQJiXCcxrF9Z_6R0-D8qJgyMgj_msi/view?usp=drivesdk
- **60s seven-shot Sandfall Ritual candidate HD:** https://drive.google.com/file/d/1N1h5ouervs9WZGQ8_Pk7u44nyKB-FEZt/view?usp=drivesdk
- **60s mobile:** https://drive.google.com/file/d/15HLJOIJdUltzaURJ98FUqPIrTw2SoPkE/view?usp=drivesdk

**Neither video is yet an original eight-minute master or any of four finished approved campaign Shorts.** These free sources are faster and more photographic than the rejected glass-marble CGI candidate, but the material-action timing, 9/10 target and YouTube original-value concerns still need true watching/listening and human review before public publishing.


## Enhanced stock Foley release gate (31 October 2026)

The old stock license intake booleans alone are **not sufficient for release**.
Run the existing production/licensed_footage_gate.py with --release and --assets-root.

- The manifest must specify master_file (relative MP4) and master_sha256. The release gate now recomputes the file hash, probes actual encoded H264/24fps 720p/1080p video plus 48kHz stereo AAC audio, and verifies the locked timeline duration.
- Every shot needs one or more **observed** contact_checks. Each cue records shot-local integer visual_contact_frame and audio_onset_frame (maximum one frame apart), sound_source_index referring to a verified hashed licensed recording, material_family, interaction, identical visual_intensity and audio_intensity, energy_match, timbre_harshness_match, auditioned_with_picture and substantial audition_notes. Each referenced sound_sources[] recording must declare the actually recorded material as recorded_material (matching its shot) and recorded_action; never relabel a gravel or water recording as slime. Intensity labels: delicate, gentle, moderate, forceful, impact.
- Every shot needs continuous_texture_covered and substantive texture_coverage_notes. Audio must actually fit the visible material, force and rests; no artificial noise beds, fillers or arbitrary loops.
- Actual final encoded audio is decoded to test no >=0.45-second near-silence at or below -55dBFS. This numerical scan is **not** a substitute for listening and cannot judge what the action should sound like.
- final_review must be tied to the exact master hash, identify a reviewer and substantively document genuine full-picture, headphone, and phone-speaker sound checks. A true flag without a genuine inspection is not permission to release.

A research shortlist of 12 individually linked stock footage candidates and five CC0 recorded Foley candidates is saved at research/commercial_stock_asmr_candidates_2026-10-31.json. These are candidates only, with no original download hashes or human sonic signoff yet; they are **not** published or approved master files. Source provenance, transformations and third-party rights must still be checked and preserved.

Qwen3-TTS is not a proven non-speech Foley generator. Never label previously sourced or Stable Audio generated sound as Qwen sound. Qwen analysis cannot replace real material-appropriate recorded Foley or manual picture-and-sound verification.
