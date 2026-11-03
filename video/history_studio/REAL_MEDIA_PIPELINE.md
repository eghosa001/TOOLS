# Facts Uncovered: current real-media-only production pipeline

This is the authoritative workflow for the Facts Uncovered historical YouTube channel. **No AI-generated images or video, CGI, synthetic reconstructions, synthetic 2D/3D scene rendering, generated diagrams or photo-to-video generation.** Use only real filmed footage, real photographs and scans of actual physical historical records, with verified permission for commercial use and editing. AI narration is a separate audio-licensing question, not permission to use AI visuals.

## Only active historical workflows

1. **Prepare approved sources.** Select historically accurate clips and photographs, verify camera/physical-document origin, commercial-use rights, derivative/editing rights and attribution. Keep original files and licence evidence.
2. **Build preview.** Use `.github/workflows/facts-uncovered-real-only-assembly.yml` with the GitHub release tag containing the media files and two JSON ledgers. The script `video/history_studio/real_only_assemble.py` validates all sources and cuts the selected actual film into a draft with existing narration. There is no AI image/video fallback.
3. **Quality gates.** `source_first_policy.py` requires genuine visual sources and verified licences. `video_motion_gate.py` requires at least 65% of the running time to show **genuine moving film**, not animated photos. These checks cannot independently guarantee copyright permission; an editor must verify the actual source.
4. **Review.** The produced MP4 is PREVIEW ONLY. Review every shot, narration alignment and attribution and approve the exact MP4 SHA-256. No automatic upload from the build workflow.
5. **Upload after approval.** The existing `.github/workflows/youtube-upload-direct.yml` invokes `youtube_direct/upload_to_youtube.py` and `youtube_direct/verify_real_only_release.py`. It requires the final approved MP4, both signed matching source ledgers, any verified real-photo thumbnail and authenticated ownership of Facts Uncovered. It cannot use OAuth credentials linked to an ASMR channel.
6. **CI verification.** `.github/workflows/history-video-motion-gate-tests.yml` verifies source rights, no synthetic visuals and upload safety.

## Files required in source footage GitHub release

Place all source assets in one release, with flat unique filenames and both `REAL_ONLY_SOURCE_MANIFEST.json` and `REAL_ONLY_MOTION_MANIFEST.json`. Every source shot has exact start and end seconds, unique ID, narration text, shot subject and reason, source page URL, creator, licence name and URL, attribution, commercial-use and edit permission, local source file name and SHA-256. Include independent genuine real-film/photograph origin verification. Source files must be real camera films, real camera photos or scans of physical originals; no generated material. Video shots can specify `source_in_seconds` to choose the approved original in-point.

The source manifest also needs an `audio` record with `local_path`, `sha256`, `source_description` and `commercial_rights_verified: true`. Narration duration must agree with the video timeline within one second. Audio must be suitable for commercial publication, including any TTS-model licensing and music.

The motion manifest mirrors the source shots, uses `CAMERA_FILM`/real-camera or physical-scan capture types and records the real filmed-motion share and individual rights evidence. Period-context, contemporary location and filmed reenactment clips must be labelled accurately. Do not call reenactment the original event.

**If original film footage does not exist:** use an appropriately licensed **live-action filmed** reconstruction, clearly described as a reenactment; otherwise use genuine photographs to explain the specific evidence, revise the episode or halt. Synthetic visuals are never a fallback.

## Release conditions

- Source and motion ledgers individually PASS; source-video timeline aligns with narration and each other.
- The final human editorial review references the exact MP4 checksum and confirms source relevance, audiovisual quality, source licensing and attribution.
- A claimed public-domain record still needs individual rights verification for the intended distribution territories.
- Commercial reuse rights make the material potentially suitable for publication, **not automatically monetizable**; YouTube's originality/reused-content rules still apply.
- A failed shot/license/source check blocks the release. Never replace a missing clip silently with an AI image, generic montage or auto-selected unrelated stock.

## Cleanup record: 3 November 2026

Removed **193 obsolete historical GitHub Actions workflows** from the active repository branch. These included redundant Titanic, Giza, Molasses, historical 3D shorts, photo-montage renderers, repair experiments, legacy publishing transports and old staging jobs. The code history is still available in Git for audit, not as an active production path.

The separate Ninefold Tide animation work, ASMR pipelines, Android work and football editing workflows were not removed. Historic documentary scripts, research, previous video results and source assets remain in the repository as reference material, not as approved finished media.

Do not restore a previous historical workflow without bringing it under this source-verification, genuine-footage and editorial-approval system.
