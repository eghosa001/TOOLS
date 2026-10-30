# Original CGI ASMR — measurable audiovisual QA and human signoff

Applies **only** to `video/satisfying_studio/`, for every one of the 47 registered
formats. The studio must make all original 3D picture, source licensed Foley and
perform all checks. The owner does **not** supply filmed footage, recorded Foley,
a performer or expensive video-generation credits.

## Engineering checks applied to the *encoded master*

`production/post_render_av_review.py` invokes
`production/av_signal_quality.py` for every registered `format_id`, both on
a 3–12s CGI audition and on the final film. Every result is bound to the exact
master's SHA256. FFmpeg provides full-length audio decode, EBU R128 loudness and
true-peak analysis. Separately, FFmpeg decodes video for blackout/freezes and
samples CGI frames for brightness, contrast, clipped highlights/shadows and
local image gradients. Both video and audio streams must decode.

**Blocking signal defects** for registered CGI masters:

- No measurable soundtrack, near-silent interval >=0.45s, or unsupported source;
- True peak **above −1 dBTP** or integrated loudness over −8 LUFS or below −50 LUFS.
  These are studio safety/excess thresholds, not a platform-mandated target;
- Video/audio duration difference **over 100 ms**;
- Incorrect actual output contract: H.264 video at 24 fps and AAC stereo at
  48 kHz for this existing studio pipeline, with native aspect/final resolution
  also checked by `quality_gate.py`;
- Missing decoded sampled frame information or absent/invalid format-specific
  signal QA, changed master hash, or scan belonging to another format.

**Investigation flags, not automatic artistic failures:**

- True peak above −2 dBTP preferred engineering headroom;
- Integrated loudness above −13 or below −32 LUFS. Delicate, impact and
  atmospheric ASMR legitimately differ; audition on headphones AND phone.
- EBU loudness range over 17 LU (aggressive dynamics), or under 1 LU for
  materials whose audible force should evolve;
- Unusually low average exposure, flat sampled gradients, many crushed shadow
  pixels, lost highlights or too many low-detail frames;
- Potential black/frozen imagery, including intentional dark/suspended scenes.

A featureless dark frame cannot be declared visually unacceptable from its
statistics alone, and busy noisy textures do not prove a film is photorealistic.
The studio requires an actual visual review of modelling, geometry, fine
surface details, deformation, tool-to-material contact, cuts, light, scale and
framing. No arbitrary noise can be added to bypass silence warnings.

## Format-aware direction for all 47 genres

`python video/satisfying_studio/production/av_signal_quality.py --list-profiles`

This produces exactly **47 distinct entries** derived from the authoritative
`formats/catalogue.json`: each includes the actual texture, gesture,
simulation solver, audio source class, plus genre-specific director guidance for
physical realism, Foley and camera clarity. Fragile wax and glass must have
realistic shard geometry; soft jelly needs volume and rebound; clicks need
non-clipping mechanical travel; fluids need real SPH, not floating spheres;
simulated performers need evaluated 3D body/jaw movement and lawful usable
voice; environmental effects need convincing true 3D motion. All entries are
CGI only, and all are labelled *not quality approved* until actually reviewed.

## Exact shot-to-sound synchronization

The sound editor is responsible for auditioning every license-verified source
stem against the actual CGI. `SOUND_DYNAMICS_AND_INTENSITY.md` requires:

- Audible onset within **one actual image frame** of contact;
- Actual material timbre and tool size, not an attractive but unrelated sound;
- Proportionate visual speed/force and audible energy, attack and tail;
- Natural variation for changes of motion, without harshly amplified small
  gestures or identical generic stems pasted across different materials;
- Full-source rights and hashes, with the specific cue ID and contact timestamp.

**The signal scanner cannot itself determine real physical contact from
decoded pixels, reliably classify actual Foley timbre or perform a real
headphone audition.** It never sets `audio_action_sync_verified=true`,
awards a 9/10 score or approves a new video. The human review in
`quality_gate.py` remains mandatory, per-shot and exact-master SHA bound.
Satisfying signal thresholds alone are insufficient for release.

## End-to-end commands (no media or services purchased)

Create, render and record a new original CGI source in the standard 3D studio,
source sounds from the cached licensed library and align them to the shot.
Build one original 5-second picture+audio audition. Then run:

```bash
# After 5-second MP4 is created
python video/satisfying_studio/production/post_render_av_review.py \
    /path/to/project/render/preview_with_foley.mp4 \
    --format wax-cracking \
    --output-json /path/to/project/render/post_render_preview_scan.json

# Frame/exposure and real full-track R128 sound metrics per CGI category
python video/satisfying_studio/production/av_signal_quality.py \
    --list-profiles
```

To authorize a CGI pilot in `quality_gate.py preview`, the reviewer must first
sign off on the **actual audition** and enter the SHA256 of the corresponding
preview scan in `preview_review.reviewed_preview_scan_sha256`.
After the film is finished, `production/assemble_reviewed.py` and
`quality_gate.py run-final` automatically issue final scans with the registered
format profile. At release, the completed full-film picture-and-headphone review
must reference `final_review.reviewed_av_scan_sha256`, include genuine visual,
auditory, intensity and contact observations and score all nine quality
criteria at least **9/10**.

The owner-approved publishing decision is separate. All formats start
**UNAPPROVED**. Audit software cannot certify a 47-format catalogue as 47
premium movies; each deserves individually rendered, watched and heard proof.

## Cost-efficient CI

The ASMR format workflow uses a free GitHub runner with FFmpeg and generated
**synthetic test fixtures only**, which are never reused in production or
represented as ASMR. CI checks all 47 source-specific QA entries, FFmpeg's
actual encoded 3-second stereo sample, extreme loudness/peak/inaudibility,
source/format mismatch, stale scan and audio/video alignment, plus the
existing audiovisual review gates. No owner video/audio uploads, Kaggle credits,
paid image generators or extra web research are necessary for these tests.
