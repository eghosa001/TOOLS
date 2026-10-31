# Ninefold Tide — reproducible Godot / Kaggle pre-video handoff

**Development status: technical rig workbench. No moving-video output and no final-art approval.**

This is the controlled replacement for treating multiple historical Phase ZIPs as separate current Godot projects. It does **not** delete the archived originals or turn approved design sheets into finished animation.

## Canon and ownership

- [Master Series Bible](https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit)
- [Character & Visual Design Bible](https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit)
- [Art Index](https://docs.google.com/document/d/1roYu1Frb2awFvwSI7mms2_llnag58qDVCmnUEfb5F24/edit)

Naya is **16, 164 cm**. Her stable design uses tightly braided black hair in a low practical knot, a storm-blue cropped work jacket, teal tunic, cream measurement tape, dark reinforced trousers, gripped boots, notebook and a brass-and-glass Reading Disc. No invented red scarf, magical abilities or unauthorized design substitutions.

## Technical baseline

The exact approved-reference-derived Naya source is reconstructed by overlaying Phase 20 on Phase 19. The separate Phase 24 harbour *review laboratory* is retained in its own Godot subproject so that it cannot overwrite the production dashboard or substitute review-only environment art for the final world.

| Input | SHA-256 | Purpose |
|---|---|---|
| `Ninefold_Phase19_Naya_ArtRig_Integration_Patch.zip` | `a4b2bd530c4751ab9751db98bfa001525763cc42a845f48467e89f63a5b0a7cb` | Source-derived Naya sprites, expressions, first rig |
| `Ninefold_Phase20_Joint_And_Rail_Grip_Patch.zip` | `a32865d216df556c9f22eae21309bd5fc648c3629ac9bacdf8280a7116f6d64b` | Parent-relative joints, underdraw, rail-contact IK |
| `Ninefold_Phase24_Curated_Godot_Project.zip` | `c6c824b3fd23ede6e7fe3e3c2966b555be9453e71725b8896a44201630581324` | Harbour painting comparison and separate IK review |

The assembler validates all archive SHA-256 values before extraction, checks file-path safety, verifies the **85** Phase20 art-source hash entries, checks the 28 Naya joint nodes and keeps the release flags closed. The project is *not* claimed to have 28 artist-approved joints or completed production model sheets. The first local source-patch build passed **16 existing Phase19/20 Python tests** and the assembler's **7 independent safety tests**.

## How to run the Kaggle handoff without your laptop

1. Upload `Ninefold_Private_Source_Inputs.zip` **once** to a **private** Kaggle Dataset and attach it as notebook Input. Keep the Dataset private; these are the owner's character drawings, not public GitHub assets.
2. Open `Ninefold_Kaggle_Godot_PreVideo.ipynb` as a Kaggle notebook. The notebook downloads the small `bootstrap.py` script from one explicit tested GitHub commit. If Kaggle Internet is disabled, it uses the exact same script supplied inside the private input pack, with a SHA-256 check.
3. Run assembly and offline tests. If you want **real** Godot engine validation in Kaggle, attach a trusted **Godot 4.7.2 Linux executable** as an additional private input and set its path in the notebook. The notebook will not claim engine validation if Godot is absent.
4. Inspect `BUILD_REPORT.json` and `ENGINE_REPORT.json` (if the engine check ran). Outputs are in `/kaggle/working/ninefold_review/`. No video is produced.

The notebook must be **rerun** to receive a different pinned commit. GitHub does not remotely update a Godot process already running on Kaggle. Pin a newer *tested* commit in the notebook after future rig changes; never fetch `main` without reviewing the resulting SHA.

## Executables and testing

From the checked-out code branch, with the three private ZIP files in `/path/to/private_inputs/`:

```bash
python video/ninefold_tide_2d/production_tools/bootstrap.py \
  --input-dir /path/to/private_inputs \
  --output-dir /tmp/ninefold_review
python -m unittest discover -s /tmp/ninefold_review/naya/tests -v
python video/ninefold_tide_2d/production_tools/bootstrap.py \
  --output-dir /tmp/ninefold_review --godot /path/to/godot --engine-test
```

The public GitHub Actions job runs safe assembler unit tests and *synthetic* Godot 4.7.2 IK checks. It cannot certify full private Naya artwork, appearance, sound or preview quality without the original private pack. The Kaggle notebook requires actual execution and inspection before Kaggle runtime verification can be claimed.

## Outstanding acceptance gates

- The Naya workbench still uses source-derived cutouts with incomplete concealed joint painting, and lacks a fully approved five-angle production rig.
- Review Naya's anatomy, braid consistency, clothing, expression changes, rail hand grip, foreground occlusion and silhouette at 1280px and phone sizes in real Godot screenshots.
- Approve natural dialogue, Foley and the final mix separately. No audio or lip-sync certification is implied here.
- Only after producer/artist signoff can a representative rig become a source template for Kito, Iri and the rest of the cast.

**Cost policy:** no paid model, paid GPU, new VPS or always-on laptop is required for preparation. GitHub Actions handles code-only geometry testing; Kaggle is for opt-in private-runtime testing. Kaggle Internet/GPU availability and import compatibility are not presumed.