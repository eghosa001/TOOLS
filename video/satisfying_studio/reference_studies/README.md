# ASMR reference evidence library — 29 October 2026

## Current status

**11 named YouTube references catalogued; all 11 connected source video-analysis reports recovered, comprising 429 timestamped scenes. 0/11 independently decoded and watched frame-by-frame or listened to in full by this session.** This is not a completed viewing report. The distinction is essential: public title/view count, a third-party scene-analysis excerpt, a video frame census, and an actual independent audiovisual review are four different types of evidence.

- [source_analysis_index.json](source_analysis_index.json) is the summary of all **429 scenes from 11 completed connected video analyses** including approximate timing, reported sound types and notable timestamp gaps. See [SCENE_AUDIO_FINDINGS_2026-10-29.md](SCENE_AUDIO_FINDINGS_2026-10-29.md) for practical production comparisons. The full reports are in [scenes/](scenes/) as one JSON per video.\n- [reference_library.json](reference_library.json) is the maintained, machine-readable source registry. Each reference records exact YouTube URL, format classification, source provenance, evidence level, known timestamped moments, metadata dates, and unverified gaps.
- [frame_audio_audit.py](frame_audio_audit.py) is an **offline, no-paid-AI, frame-by-frame signal analyzer**. For any playable source copy the editor has rights to inspect, it measures **every decoded frame** (luminance/contrast/motion) and every time-aligned audio interval (RMS/peak), with raw evidence in `frame_metrics.csv.gz`, candidate edits/onsets, a SHA256, and summary JSON. This is computational analysis, **not** claiming a human or vision-language model understood every frame or listened to the sound.
- The connected Higgsfield source contains **completed scene-level visual and reported sound analysis for all eleven videos**, which has now been preserved in GitHub as 429 scenes. This is stronger than metadata alone but is **not frame-level source playback**. Some longer reports have gaps or time contradictions, explicitly counted in the index.
- Access to connected Higgsfield analysis reports succeeded for all 11 references on 29 October 2026; this did not expose the underlying original video file or original audio bytes. GitHub Actions access smoke test [40874004648](https://github.com/eghosa001/TOOLS/actions/runs/40874004648) failed to retrieve even public video metadata for YouTube Short `S47YZ2C7nv4`: YouTube required sign-in. No source frames were downloaded. Connected vidIQ credit was exhausted on 29 Oct 2026, and the service reported refresh date **26 Nov 2026**. No paid media-generation tools or video credits were used.

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
- **Repair/process** — stress-ball repair **11-scene analysis with narrated repair arc** and prior 50.37M-view metric; `j2TVdltvJ_k`.
- **Focused tactile ritual** — kinetic sand **5 scenes of slicing, scooping, nail strikes, chopping and scraping** with prior 24.34M-view metric; `Cv19w_2-rMc`.
- **Escalation or comparison** — archived **46 and 42 scenes** respectively covering the layered-material formats; `lzHMQWgZjaI` and `vTB989TPw_A`.
- **Long relaxation** — clay butter and no-talking slime **51 and 123 provider-reported scenes**, with explicit timeline gaps; `hUSNOEnXdyg` and `LhMwd0JzTXA`.

**All 429 scene descriptions are now accessible for future production research, but no source has an independently verified frame-by-frame audiovisual signoff yet.** This library makes future analysis reproducible and truthfully bounded. Use the documented popular examples as creative references, **not as footage/audio assets**.


## Additional verified Blender/3D CGI source discovery — 30 Oct 2026

The original **11 reference videos / 429 provider scenes / 0 independently played originals** remains an unchanged historical count. A new, separate [3D CGI benchmark dossier](3D_CGI_BENCHMARKS_2026-10-30.md) lists seven genuine original Blender/CGI creator videos based on their public YouTube descriptions and verified public publication records. This list adds **zero** completed full-frame/ear-and-eye reviews; source videos have not been captured, and sound performance cannot be certified from descriptive metadata. Peer-side CGI contact/temporal comparisons are required before making claims of parity. Keep the list distinct from both the four user's creative ASMR samples and physical real-life sensory videos.
