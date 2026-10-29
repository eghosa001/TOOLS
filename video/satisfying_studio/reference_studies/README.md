# ASMR reference evidence library — 29 October 2026

## Current status

**11 named YouTube references catalogued. 0/11 independently watched frame-by-frame and listened to in full by this session.** This is not a completed viewing report. The distinction is essential: public title/view count, a third-party scene-analysis excerpt, a video frame census, and an actual independent audiovisual review are four different types of evidence.

- [reference_library.json](reference_library.json) is the maintained, machine-readable source registry. Each reference records exact YouTube URL, format classification, source provenance, evidence level, known timestamped moments, metadata dates, and unverified gaps.
- [frame_audio_audit.py](frame_audio_audit.py) is an **offline, no-paid-AI, frame-by-frame signal analyzer**. For any playable source copy the editor has rights to inspect, it measures **every decoded frame** (luminance/contrast/motion) and every time-aligned audio interval (RMS/peak), with raw evidence in `frame_metrics.csv.gz`, candidate edits/onsets, a SHA256, and summary JSON. This is computational analysis, **not** claiming a human or vision-language model understood every frame or listened to the sound.
- The four original reference descriptions were **previously summarized by a third-party scene-analysis source**, and approximate scene times have been preserved. Their actual frames, original audio signals, exact timings and full scene list remain unavailable. The other seven have **publicly verifiable metadata only**.
- GitHub Actions access smoke test [40874004648](https://github.com/eghosa001/TOOLS/actions/runs/40874004648) failed to retrieve even public video metadata for YouTube Short `S47YZ2C7nv4`: YouTube required sign-in. No source frames were downloaded. Connected vidIQ credit was exhausted on 29 Oct 2026, and the service reported refresh date **26 Nov 2026**. No paid media-generation tools or video credits were used.

## Required future real viewing protocol

1. Obtain access to **the exact public video source** through an authorized player, or receive a user-supplied local MP4. Do not evade sign-in, DRM, or permissions. Record video ID, creator, retrieval date, filename, file SHA256, fps, resolution, duration and rights to analyze. Never commit the creator's raw video/audio or full-size frame thumbnails to the repository.
2. Run `python -m pip install numpy`; ensure FFmpeg/FFprobe are available. Run:
   ```bash
   python video/satisfying_studio/reference_studies/frame_audio_audit.py \
     /local/authorized/reference.mp4 \
     video/satisfying_studio/reference_studies/reviews/VIDEO_ID \
     --reference-id VIDEO_ID
   ```
3. Independently **view/listen to the actual video** while checking the complete frame-derived timeline. For every distinct shot and every material-contact event, record exact `start_frame`, `end_frame`, material type, camera/framing/light, hand/tool/material motion, onset/texture/tail of each sound, how it corresponds to contact, and transitions. Also note hooks, pacing changes, repeated motifs, defects, and ending/loop structure. Use headphones for Foley judgments.
4. Never assign a quality score or claim audio synchronization by relying on waveform transients alone: motion peaks may be camera cuts, audio peaks may be music, and visual contact may be quiet.
5. Save editorial findings into `reviews/VIDEO_ID/reviewer_notes.md` and `reviews/VIDEO_ID/confirmed_events.json` **only after actual viewing**, with editor, date, method, source SHA256, and explicit review completion. Preserve original/source quotations sparingly. Write transferable principles, not copied footage/compositions or prohibited copyrighted audio.
6. Update `reference_library.json` evidence flags and times from reviewed file; **no review flag from title, search snippet, thumbnail, scene summary or script alone**. Then cite actual reviewed examples in future production manifests. Replace stale and weak references as better current examples appear.

## How to use the research now

The current index can support **concept selection and format research**, with conservative confidence labels:
- **Surreal reveal** — previously reported tube-to-object transformations; original reference `kKOJZbthcyo`.
- **Focused gel texture** — previously reported pour/press/spread sequence; `S47YZ2C7nv4`.
- **Material contrast** — previously reported crack/tear variation; `7gV-0be8WqE`.
- **Environment-based surreal** — previously reported multi-environment POV transitions; `XJ1SaNX4s8I`.
- **Repair/process** — 50.37M-view stress-ball-repair **title and public metrics only**; `j2TVdltvJ_k`.
- **Focused tactile ritual** — 24.34M-view kinetic sand **title and public metrics only**; `Cv19w_2-rMc`.
- **Escalation or comparison** — 100-layer and 1-vs-100-layer public titles; `lzHMQWgZjaI` and `vTB989TPw_A`.
- **Long relaxation** — clay butter and slime no-talking **titles and descriptions only**; `hUSNOEnXdyg` and `LhMwd0JzTXA`.

**No individual source here has an independently verified frame-by-frame audiovisual signoff yet.** This library makes future analysis reproducible and truthfully bounded. Use the documented popular examples as creative references, **not as footage/audio assets**.
