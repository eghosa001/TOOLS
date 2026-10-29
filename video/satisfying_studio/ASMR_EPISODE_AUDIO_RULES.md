# ASMR episode continuity and sound-design rules (2026-10-29)

Applies only to `video/satisfying_studio/**`. Read with `AGENTS.md` and `QUALITY_STANDARD.md`. This responds to the rejected 3-minute *Satisfying Texture Lab* edit. It does not modify history/documentary rules.

## Editorial format

Choose one **editorial format**, as documented in [POPULAR_ASMR_BENCHMARK_2026-10-29.md](POPULAR_ASMR_BENCHMARK_2026-10-29.md): focused single material, process transformation, comparison, themed multi-trigger compilation, or surreal world. A video may use **more than one material** when variety itself is a designed part of the format (for example, comparing the cracking sounds of surfaces). The requirement is a recognizable sensory promise and deliberate sound/action transitions, not the same substance throughout. Never substitute unrelated stock clips just to reach a runtime.

Use a clear **sensory grammar**, not repeated footage: establish action or challenge, show the material's response, allow the tactile payoff, then advance the same process, comparison, theme or world. Use natural shot lengths and a deliberate rhythm. A 180-second video needs 180 seconds of distinct, edited material; no five-second demo loops and no arbitrary filler or substitutions when sources are missing.

A shot list must define original concept, selected `editorial_format`, `editorial_thesis`, visual `interaction`, per-shot material identity (which **may vary**), planned transitions, real recorded source or editable Blender asset, rights, exact duration in frames and approving editor. In a deliberate comparison, different materials need distinct sounds. Grade shots to support the chosen narrative, not to fake identical lighting across environments.

## Sound is first-class, not a soundtrack slapped on afterward

1. Choose real original or CC0/CC BY 4.0 material-specific close-mic recordings. Audit licence and hashes. Never use a five-second sound recording on endless repeat to fill a long film.
2. For **each actual contact visible in the finished frame sequence**, place a specific close sound at the true visual contact frame (tolerance max one frame), such as soft wet compression, adhesive release, light tool scrape, bubble, crackle or material-specific small click. No unrelated impacts and no guesswork via AI or file names.
3. Layer primary action, fine texture and subtle room air only where they improve presence. Preserve transient edges, microdetail and intentional quiet moments; do not blanket the entire mix with noise, forced music or an overbearing ambient bed.
4. Review the complete film on headphones: no abrupt jumps, clicks, distorted peaks, audio dropouts, compressor pumping, excessive repetition or dislocated stereo. Compare both *sound and image* with **independently researched popular format examples**, plus user-provided references only where relevant. Record exact accessible viewing/listening evidence, and never fabricate an audible comparison from video metadata.
5. The clean working master is 48 kHz stereo PCM; encode release audio as AAC 256 kb/s stereo at 48 kHz. Inspect true peak and integrated loudness as **technical warning/fail checks only**—these do not certify artistic Foley quality. Aim for true peak at or below -1 dBTP, without aggressive dynamic compression. A single integrated LUFS target cannot guarantee good ASMR.
6. A human editor must separately sign off both the sync and audible texture of **the exact final SHA256**. If that hasn't happened, label the file *technical export, not approved*.

## Production tooling

- `production/make_three_minute_texture_lab.py` is a fail-closed compatibility wrapper. Its previous diverse-montage and five-second `-stream_loop -1` Foley logic has been removed.
- `production/build_cohesive_episode.py episode_manifest.json output.mp4` builds only from pre-edited 720x1280/24fps takes and a cue sheet tied to their exact contact frames. It has **no stock download, filler, clip loop or background sound loop**.
- This builder requires the actual recording sources and an editor-authored manifest; it does not pretend to conjure 180 seconds of quality visuals or real Foley without those assets. Existing `quality_gate.py` artistic signoff still applies.
- For a new episode, begin with a **3–5 second sound-and-motion test** (approved by ear and eye), then a 20–30 second sequence **in the selected profile**, then the full-length master appropriate to that format. Avoid costly full renders until the small proof sounds natural.

## Episode JSON contract

```json
{
  "material_family": "translucent jelly",
  "duration_seconds": 180,
  "fps": 24,
  "manual_timeline_approved": true,
  "foley_manifest": "foley.json",
  "shots": [
    {
      "file": "takes/shot01.mp4",
      "sha256": "SHA256_OF_APPROVED_UNIQUE_TAKE",
      "duration_frames": 432,
      "material_family": "translucent jelly",
      "interaction": "gentle gel compression",
      "source_url": "https://ORIGINAL_ASSET_PAGE_OR_SOURCE",
      "license": "original"
    }
  ]
}
```

Above is a **schema illustration, not a valid release plan**; all shots must add up to 4,320 frames and cover multiple distinct interactions within the same family. Each Foley cue uses the existing `audio_mix.py` fields `file`, `sha256`, `source_url`, `license`, `frame`, `gain_db`, `max_length_seconds` **plus** `material_family`, `interaction`, `visual_contact_frame`, and `auditioned_in_context: true`. Each cue must correspond to an observed contact in the matching picture shot.

**Rejected baseline:** *Satisfying Texture Lab — 3 minutes* had mixed material families and looped five-second Foley; it remains **not independently approved**. Do not silently rename or re-export it as a remaster.
