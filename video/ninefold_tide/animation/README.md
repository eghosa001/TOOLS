# The Ninefold Tide — frame-first 2D animation

This is the primary production path for the series. The Google Drive story, character and visual continuity documents are authoritative; approved drawings, pose sheets and exposure sheets are the source assets. Finished video is an **end product**, never a source.

The visual ambition is expressive, premium hand-drawn action animation with painted maritime backgrounds, original character designs and optional 3D layout. Do not copy other studios' characters, frames or costumes. A technical rendering or successful test is not a visual approval.

## Pipeline

1. Review the current Drive canon, shot direction, character/costume state, prop physics and art-index approval.
2. Build one shot package: E101/CAM03B is the pilot. Confirm camera, timing, acting objective and geography.
3. Draw approved keys and breakdowns. In-between drawings are explicit editorial art decisions, not morph-generated guesses.
4. Correct anatomy, hands, costume, expression, silhouette, timing and contact, then clean lines and paint every necessary drawing.
5. Composite separately painted environments, foreground rail, shadow, character and practical effects into a numbered PNG sequence. Verify every frame.
6. Pass human art/continuity/rights reviews, then encode an MP4 for editorial cutting. The episode cut also requires approved voice and mix.

Existing deterministic frame_factory.py can be used as an internal compositing aid after the drawing approvals. The production gate is animation/tools/shot_gate.py. The older pipeline.py can assemble an episode **only after each shot supplies the gated frame manifest**. It can no longer accept a video file as sufficient proof.

## Commands — no video credits or cloud download required

~~~bash
python -m pip install Pillow
python -m unittest discover -s video/ninefold_tide/animation/tools/tests -v

# Must fail until someone actually approves art and supplies real private image files.
python video/ninefold_tide/animation/tools/shot_gate.py check --manifest video/ninefold_tide/animation/shots/E101/CAM03B/brief/shot.json --stage intake

# Copy the manifest to your private shot directory; put real reviewed PNGs beside it.
# Use --asset-root for private source files, and choose intake, keys, frames or export.
python video/ninefold_tide/animation/tools/shot_gate.py check --manifest /private/E101/CAM03B/shot.json --stage keys

# After all numbered PNGs exist, generate an UNSIGNED hash ledger, then record
# its filename/checksum in the shot manifest before human frame-by-frame review.
python video/ninefold_tide/animation/tools/shot_gate.py index --manifest /private/E101/CAM03B/shot.json --output /private/E101/CAM03B/review/frame_ledger.json

# Only after every gate and named review passes:
python video/ninefold_tide/animation/tools/shot_gate.py export --manifest /private/E101/CAM03B/shot.json --output /private/E101/CAM03B/export/shot.mp4
~~~

The repository deliberately ships **no approved keys or footage**. Art, WAVs, Krita/OpenToonz projects, big PNGs and footage belong in the private Drive/workspace, not this public GitHub repository. Empty folders are structural placeholders.

Read PRODUCTION_RULES.md, DRIVE_SOURCE_OF_TRUTH.md, docs/shot_workflow.md and docs/quality_bar.md before making a shot.

## Artwork generated in ChatGPT or stored in Google Drive

The vector previz generator is **not** capable of rendering premium character art. Generate one standalone canon-correct 16:9 painting per key pose from the approved reference sheet, then import it with `animation/tools/art_intake.py` into a **PRIVATE** shot folder. Artwork imported from ChatGPT, Drive, a technical previz or an artist always remains `PENDING_HUMAN_ART_REVIEW`; it cannot satisfy any art-approval gate without named evidence. The tool preserves source hashes, refuses automatic cropping and tracks alternatives without silently selecting between them. The canonical story and character designs remain in the linked Google Drive, not in GitHub. See `docs/ARTWORK_GENERATION_AND_INTAKE.md` for the exact CAM03B canon-safe art brief, zero-credit commands and volume/cost rationale. Legacy and vector outputs remain **review/reference only**.
