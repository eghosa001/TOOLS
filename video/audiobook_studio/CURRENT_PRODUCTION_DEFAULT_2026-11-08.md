# Audiobook Studio — Start here in every new chat

**Owner decision: 8 November 2026. This is the current production default for original, illustrated Audiobook Studio fiction.** Read this **before generating art, audio or video**. It supersedes earlier *Audiobook Studio* instructions recommending GPU rentals, paid TTS services, full animation, slide-only drafts or Qwen/Ryan as the automatic narrator. It does **not** change the distinct Facts Uncovered/history, ASMR or universal-edit channel rules.

## What the owner actually wants

Produce the **finished video**, not a standalone image gallery or another hypothetical plan.

1. Use the **latest explicitly approved** complete episode script and its matching story bible, pronunciation notes and scene plan. Read the actual material. No invented scenes or shortened/padded script.
2. Illustrate it with **original 2D Chinese manhua / Chinese cultivation-webnovel art**, with consistent characters, clothing, geography and props. These are **STILL IMAGES**, not animated scenes. Do not add Blender, 3D, AI-video animation or parallax/depth tools.
3. Generate a consistent English **male Kokoro Michael** narration (voice `am_michael`) with natural delivery and accurate character-name pronunciation. This is the owner's newly accepted CPU-first voice for this audiobook track (replacing Qwen/Ryan as the default here). Target **1.25× synthesis speed** as a *working audition target*, not a runtime quota. Listen for comfortable, expressive language rather than multiplying several speed adjustments.
4. **Time every visual to the exact narration phrase it depicts**. No generic backdrop lasting through several unrelated ideas. The images must change with the narrated *meaning*, not an arbitrary fixed image interval.
5. Assemble from approved artwork and measured speech with **FFmpeg on CPU**: simple cuts/brief fades, optional restrained zoom, 1920×1080, 16:9, H.264/AAC MP4. No GPU procurement, paywall, waiting list or approval application.
6. Inspect actual images against the words, hear the MP4, verify video/audio streams, coverage, sync, rights and continuity; regenerate **only** failed assets and reuse accepted ones.
7. Deliver the **actual MP4 link on the owner's private Google Drive** as the primary result; only show separate images or prompts when the owner expressly requests them. Never claim an unfinished/unchecked file is finished, never auto-publish.

**Important distinction:** `image_gen` (built into ChatGPT) makes the still illustrations, with no external image-account authorization. **Google Drive stores completed artwork/MP4; it is not an image generator.** GitHub Actions' free Linux CPU can synthesize Kokoro and FFmpeg-assemble from private inputs. User does not need to provide additional GPU or third-party image-generator access. If a tool is blocked, use another authorized method; do not stall on researching platforms.

## Mandatory production stages and blocking checks

| Stage | Mandatory output | Stop when |
|---|---|---|
| Script lock | Approved episode TXT, SHA-256, source URL/version, full verbatim beat list | Missing original, wrong draft, missing paragraphs, invented sentences |
| Voice audition | Approved `am_michael` sample, natural-name tests in sentences, master speed, cached chunks | Wrong names, rushed/clipped words, unnatural rhythm |
| Visual beat map | One source-quoted narration passage for each shot; positive and negative visual requirements; references and timeline anchor | A shot cannot be justified by **the exact words spoken then** |
| Character/look bible | Persistent identity/style prompts and approved reference images | Same character changes face, age, robe, injuries or appearance |
| Art inspection | Pixel-inspected individual original images with source, image hash, licensing/provenance and editorial pass | Generic wallpaper, misleading current-vs-memory state, invented props, anatomical holes, text artifacts or wrong location |
| Audio-to-picture timing | Audio for each precise narration beat, measured actual seconds, one art file per beat, no gap/overlap | Guessing from word count or using a broad image across unrelated paragraphs |
| Video output | Real Full-HD MP4 with sound and measured duration, sampled frames and full listening review | Missing MP4, silent track, mismatched shot, irrelevant art, bad crop, clipping |
| Private review | Verified Google Drive MP4 and correction report; owner decides release | No Drive result or release authorization |

A program checking names/prompts/files/hashes **cannot prove** the artwork depicts the narration. Only actually inspecting the pixels and viewing/listening to the assembled sequence can grant editorial acceptance. **Fail closed** if review is uncertain.

### Visual errors the owner has rejected (generic rules)

- **Present versus flashback:** a vanished object cannot appear in the present simply because narration mentions its name; only show the complete original object in a specifically narrated former-era memory shot. Mark every scene's time period.
- **Internal spiritual injuries are not external open wounds** unless the actual script says otherwise. Cultivation diagrams must explain a real narrated mechanism without inventing unrelated magic wallpaper.
- **Character identity and attire must not drift.** Preserve the approved portrait, age, hair, injuries, rank, clothes, exact prop counts and the latest story's spatial continuity.
- **Setting must be exact.** Do not replace an alley with an unfinished building, temple courtyard with another period, or show a moon when the source says the sky is moonless.
- **Every separately narrated idea needs its actual matching picture at that point in the voice.** Record one image+spoken passage per meaningful beat, not one broad background across unrelated beats. Avoid generating image galleries or text-heavy storyboard grids as scene frames.
- **Read the PRIVATE continuity and exact shot restrictions** for the currently approved story from its linked private folder, not from a guessed description in this public repo.

## Current story: Eternal Dao of the Lost Epoch (D03)

This is the current starting series, **not** `The Graves That Answer`. Episode 1 = **Chapter 1, “The Wrong Sky,” and Chapter 2, “The Weight of an Old Name.”**

- Approved private D03 full manuscript (five volumes): https://docs.google.com/document/d/17vdwOPJcgi90u_Dj5rc_X78qz4TCj2k8nRVMKSfnbxQ/edit
- **Locked Episode 1 narration source:** https://docs.google.com/document/d/1FnoycxFSFwagkjz8RbWc1Ng9GTBtdkCAQ0aYtLd0MpI/edit
- **Locked original story-matched storyboard/cast/24 anchor beats:** https://docs.google.com/document/d/1vw0znZUigZs-q4ciu8-bGEFiJnRwTdEnltp0a63zF_E/edit
- Master bible V3: https://docs.google.com/document/d/1za_vABCRJ_yg6Qi-V_RYBjsw8j4au1WGc7RwHJqAvf4/edit\n- **PRIVATE story-specific visual continuity/negative constraints:** https://drive.google.com/file/d/100qqvX4uT9wjlmNBICS42J-kHgYmTeuz/view
- Verified D03 Episode 1 source count: **3,613 words including headings** per locked production handoff. Measure actual final duration from Kokoro, not the older 3,444-word D02 estimate.
- Last user-reviewed opening preview (reference **only**, not full episode or unconditional release approval): https://drive.google.com/file/d/1HdJjOXbHCSSnbKUVUP5qWEI-KlMbIUuu/view
- Approved private review folder: https://drive.google.com/drive/folders/1SInHPNbQ-660nNjftuirZbDi6oCRyET3

Private manuscripts, names, dialogue and character designs should **not** be committed to this public repo. Keep them in Drive or private production directories with hash-based provenance. Public GitHub holds workflow/instructions/code/test fixtures only.

## Voice settings and timing

- Default identity: **Kokoro / American male `am_michael`**, English `lang_code=a`, CPU inference. Earlier Qwen Ryan is an archived approved *alternative*, not the default for new Audiobook Studio episodes.
- User approved Michael's general timbre but repeatedly found `speed=0.91` and `1.10` too slow. Work at **approximately 1.25× effective speed** and hear the sample; adjust by the quality of *actual speech*, not by a filename or a target minute count. **Do not** synthesize at 1.25× and then also apply an additional `atempo=1.25` (that would be 1.56×). If post-processing speed is necessary, use pitch-preserving `atempo`, never more than 1.25× on top of source performance without re-audition; prefer re-synthesis.
- Pronunciation lexicon: Li Tianming, Mei Shun, Wen Qingshi, White Rain Temple, Old Pulse, Qi Refining, meridians, dantian, Golden Core, Bran, Lin, Warden, Phase Lock, Heavenly Lattice and lattice crowns. Test actual names in full sentences and correct the pronunciation **before** 25-minute generation.
- Chunk by meaningful, source-exact passages/sentences. Voice output should have natural breaths and dialogue attribution, not artificial dramatic silences or forced runtime.
- Synthesize and cache each beat's WAV by source+voice+speed hash; concatenate using the **actual duration** of each beat. Bind images to this chunk timeline, not rough word timing. Master near -16 LUFS / true peak <= -1.5 dBTP, verify by hearing and measurement.
- Each MP4 remains PRIVATE REVIEW; publish only after owner approval.

## What the assistant should do on a NEW CHAT request “Make the next audiobook video”

1. Read repo `AGENTS.md`, `video/audiobook_studio/AGENTS.md`, this file, and the existing master standards. Fetch private current story source and storyboard from Drive. Never ask the owner to repeat these links.
2. Select the next approved episode in story order; honor a newly specified title/episode if given. Do not resurrect superseded `The Graves That Answer` as the default.
3. Generate only missing original 2D stills **internally**, ensure consistency via prior character references, inspect *every image* against its exact spoken sentence and negative constraints, and keep source-linked QA evidence. Do **not** show art to the user unless expressly requested.
4. Generate/reuse Kokoro Michael narration, check names, read speed and actual waveform; build precise image/audio timeline, then FFmpeg assemble the complete video on CPU. Reuse valid assets, do not restart from scratch.
5. Validate video and audio, review first/middle/end plus every high-risk cut, full listen, upload verified MP4 privately to Google Drive, link **the video**, and accurately state any remaining approval gates. No wallpaper with generic narration and no placeholder “video.”
6. If a service needs paid signup or new authorization, do **not** recommend a GPU search; use built-in art and existing free CPU path. If a real blocker remains, state it specifically without claiming the video exists.

## Source priority and status

1. User's latest explicit direction and approved manuscript/bible (newer approval supersedes older tool defaults).
2. This **8 November** production override for video and narrator choice.
3. `AGENTS.md`, `WRITING_AND_PRODUCTION_STANDARD.md`, `manhua_pipeline/QUALITY_GATES.md`, `manhua_pipeline/README.md` for all *nonconflicting* safeguards.
4. Original v1.1 uploaded master rules (109 rules) and reusable 16-category quality scorecard for fiction text quality. Those docs' older initial Ryan recommendation is **not** a lock against the user's newer approved Kokoro direction.

**Release is never automatic. No artificial duration padding. No uploads of private script or visual spoilers into this public repo.**