# CartoonStudio — HIGH-QUALITY CHARACTER REQUIREMENTS (25 October 2026)

**Production policy:** Do not use the retired procedural clay or Quaternius/KayKit low-detail models. They were only technical experiments; they are not approved as the show's finished character art.

**Current genuine verified asset:** Blender Studio **Rain, historical v2.6** redistributed by Packt's *Realizing 3D Animation in Blender* educational archive. The source ZIP is pinned using the Git object's actual SHA-1 and SHA-256 is recorded after download. A real Blender 4.0.2 audit successfully inspected 50,563 faces, 71 mesh objects, 2,215 pose bones, 240 shape keys, 19 actions, and existing clothing/hair/skin textures. The full asset has a separate true-mesh Cycles visual-quality inspection. Rain v2.6 is **not** Rain v3, and one imported rig is **not** 15 finished characters.

## Primary recommendations, reviewed from the actual publishers

| Candidate | Official source | Cost/license | Rig and face | Production status |
|---|---|---|---|---|
| Rain v3 | https://studio.blender.org/characters/rain/v3/ | Free CC BY, give credit | Production IK/FK and facial layered controls, Blender 4.1+ | **Not downloaded** in this pipeline. Historic Rain v2.6 from Packt is technically verified |
| Snow v4 | https://studio.blender.org/characters/snow/v4/ | Free CC BY, give credit | Production IK/FK and facial layered controls, Blender 4.1+ | **Not downloaded**: official site download link/auth not validated for CI |
| Ellie (Sprite Fright) | https://studio.blender.org/characters/ellie/v1/ | Free CC BY | Professional character; older CloudRig | **Not imported**: designed for Blender 3.3–3.6 |
| Jay (Sprite Fright) | https://studio.blender.org/characters/jay/v1/ | Free CC BY | Professional rig | **Not imported**: designed for Blender 3.3–3.6 |
| Sprite + Elder Sprite | https://studio.blender.org/characters/ | Free CC BY | Character rigs, some facial and loop controls | **Not imported**: Blender 3.3–3.6 compatibility check required |
| Forest Animals | https://studio.blender.org/characters/forest-animals/v1/ | Free CC BY | Six different scene creatures; no included animations reported | **Not imported**; not automatically ready for talking |
| Canino3d free cartoon girl | https://sketchfab.com/3d-models/free-stylized-cartoon-girl-rigged-character-dcaa822909ae4e04ad7eb85bc371a8c4 | CC BY per Sketchfab | Listing claims ~57k triangles and >100 facial blend shapes | **Not imported**; authenticated download needed, verify actual GLB/file licence |
| Canino3d cartoon man | https://sketchfab.com/3d-models/free-cartoon-game-man-character-rigged-a69c8962f4a14ea89bf623d716a81411 | CC BY per Sketchfab | Listing claims ~105k tris and >100 face targets | **Not imported**; authenticated download needed |
| Blender-chan | https://amarilloarts.itch.io/blender-chan | CC0 public free version, check source | ~453k triangles and rig, but special Auto-Rig Pro tooling | Not imported; anime appearance not matched to intended show |
| EMA | https://theunseenvulga.itch.io/3d-character-riggedema | CC0 per creator | Hand-painted ~76k triangles, game rig | Not imported; manual itch download required |

The **actual binary** and compatibility gate takes precedence over screenshots, promotional thumbnails, labels of “high quality” or reported rig statistics. Never silently substitute a failed download with another artist's low-poly model.

## Character consistency and intellectual property

Lelli, Brin and Odo were originally designed as stylized nonhuman creatures. Rain and Snow are stylized **human** characters. They should not silently replace the three original heroes without establishing a deliberate new visual identity; this research is a replacement candidate library, not a change to dialogue/canon. User can approve new model-to-key mapping once reviewed. Do not depict third-party copyrighted series characters or imitate their protected designs. CC BY requires preserving artist and model attribution in episode credits and channel descriptions.

## Production gate for all 15 actual model keys

1. **Distinct models**: 15 actual different model identities, no repeats/recolours counted as separate models.
2. **Real source**: separate downloadable file + full source URL, artist, licence and credit; no scraped gated assets, credential sharing, or unauthorized mirror licence changes.
3. **Mesh and materials**: successful Blender actual-file inspection, no critical missing diffuse or hair texture, good rendered face + full body at 1280×720.
4. **Skeletal animation**: actual compatible rig, working action/pose, no assumption that rig controllers survive GLB export to Godot.
5. **Talking face**: real mouth/eye shapes or validated bone face controls, tested against audible generated/spoken WAV samples and unchanged dialogue.
6. **Rendering**: a complete 3-second preview MP4 inspected before requesting full episode. Never automate preview or full render simply from a GitHub push.
7. **Story**: preserve all original 74 dialogue lines and their speaker order. **No update to** `video/story.json` without the user's explicit request.
8. **Assets**: package big .blend files as GitHub Actions artifacts or Kaggle inputs, not inside the public source repository. Do not put Kaggle API tokens in chat, notebook or repo.

## What is actually running today

- `video/fetch_real_studio_rig.py`: downloads real historical Rain archive and verifies pinned source bytes.
- `video/high_quality_rig_audit.py`: opens an existing Blender rig without executing external Python scripts; reports faces, bones, shape keys, actions and external textures.
- `video/render_real_studio_rig_still.py`: checks actual Blender materials in a CPU Cycles **still**, not a video preview.
- `video/export_professional_blend_to_glb.py`: experimental glTF skeleton+face export for the saved Kaggle notebook. An export must pass a structural test before it may be described as ready for Godot; the native .blend remains master.
- `.github/workflows/cartoonstudio-professional-rigs.yml`: current real rig and studio-still QA.
- `.github/workflows/cartoonstudio-professional-glb-bridge.yml`: experimental native rig to GLB test.
- Old Quaternius production and manual video workflows have been deleted to prevent accidentally rendering the rejected low-detail characters. No Kaggle run has been started.

**Not completed:** 15 reviewed high-quality models, automatic rig retargeting, approved identity-to-model mapping, reliable facial lip sync in exported GLB, a high-quality MP4 or finished episode. Never claim otherwise.

## Verified eight-character native master milestone — 25 October 2026

The **latest source library** is from [GitHub Actions run 40230434307](https://github.com/eghosa001/TOOLS/actions/runs/40230434307); artifact name `cartoonstudio-eight-original-blender-studio-rig-masters`. It contains eight different **real author-created original Blender** assets: Rain, Cat, Dog, Sprite, butterfly, ladybug, snail and spider. It also packages **41 first-party original texture files and 58 auxiliary files** (some are rigging scripts/node dependencies), rather than old low-poly substitutes or newly generated models.

The follow-up audit [run 40230523698](https://github.com/eghosa001/TOOLS/actions/runs/40230523698) successfully opened all eight original Blender files. **Seven of eight** have the required Blender rig libraries present. Dog's native file still references an unpublished `dog_faceposelib.anim.blend`; Cat and Dog also reference optional `paper_01.tif` maps not found in the source. Rain's `<UDIM>` texture paths require tile-aware interpretation; real files like `1001` are shipped. Do **not** interpret the seven-rig result as seven finished talking actors: butterfly and others may have very few or no facial shape keys, and lip-sync/action tests are outstanding.

The original Cat/Dog base-colour TIFF source maps **were recovered** after fixing the ZIP extractor, which previously discarded TIFF files. The alternative `cat-studio-restored.glb` / `dog-studio-restored.glb` files are labelled **reference-colour review assets**, not original textured film models. They retain the original skeleton/morph binary but were observed to have loose/detached teeth and incomplete facial rest presentation. Do not use them unreviewed in an episode. The first-party texture **native Blender** models remain preferred.

The legacy manual Kaggle renderer is now blocked with a high-quality manifest/approved-asset gate, so a manual GitHub Actions selection cannot silently fall back to the rejected procedural cast. This is protective, not a completed new production renderer.

**Current actual status:** 8 unique imported author-created Blender masters, 7 native rigs with no missing linked .blend libraries, 3 high-detail GLBs structurally verified in Godot (Rain, Cat and Dog), 0 approved model-to-series-key mappings, 0 video previews with this new cast, and 7 further distinct professional characters still required to reach 15. The 74 original dialogue lines are unchanged. The public studio art is CC BY, requiring creator attribution.

## 17 genuinely distinct first-party Blender Studio rigs sourced and reviewed

**25 October 2026 new accepted source inventory, not approved screen cast.**

The original actor source set has now expanded from eight to **17 unique 3D source identities**: the previously inspected Rain, Cat, Dog, Sprite, Butterfly, Ladybug, Snail and Spider; two DOGWALK characters Pinda and Chocomel (Blender 4.5); and seven Singularity creatures: Critter, Double Mohawk, Multi Frog, Manta Ribs, Double Eye, Plump Fly and Coral Boi (Blender 5.1). All were obtained directly from actual original Blender Studio authored production files, not the retired low-quality procedural pack or duplicate recolours. Published Blender Studio Splash sources are under CC BY (credits required). This is **17 different originally authored source assets**, not seventeen similarly detailed speaking protagonists.

- Native DOGWALK source-to-artist-material asset build [40233130603](https://github.com/eghosa001/TOOLS/actions/runs/40233130603) passed. Separate Pinda/Chocomel .blend files with original packed shader textures and actual rendered preview imagery. Independent fresh-process rig reload [40233055636](https://github.com/eghosa001/TOOLS/actions/runs/40233055636) passed, proving the Blender native libraries really reopen separately.
- Native Singularity seven-actor source and visual extraction [40232793948](https://github.com/eghosa001/TOOLS/actions/runs/40232793948) passed for all seven. Source extracted via Blender 5.1.2: these are valid original rigs, but most are outer-space/background creatures and no speech visemes or human/child anatomy are promised.
- The assembled [17-character asset library](https://github.com/eghosa001/TOOLS/actions/runs/40233910527) passed. The GitHub artifact is large (~1.1 GB) because it contains original *native* .blend libraries and their textures. The quick [visual review board](https://github.com/eghosa001/TOOLS/actions/runs/40234096515) is a separate small download with nine actual render photos and the complete 17-name metadata registry. The eight older source characters have separately inspected meshes/rigs but are not yet in this modern-only nine-image contact sheet.
- In the actual rendered photos the five *Singularity* background creatures besides Critter and Plump Fly often appear extremely small, so the **framing and presentation still need retesting** before approving production use. Main speaking cast consistency is NOT resolved.
- The GLB conversions of DOGWALK models successfully passed Godot skeleton tests but **render white**, losing the native Blender artists' complex shaders. These degraded GLBs are rejected for the final show, retaining the original native .blend asset masters instead.
- Measured mouth-controller motion in the imported Cat and Dog GLB rigs via [40233744745](https://github.com/eghosa001/TOOLS/actions/runs/40233744745). The named facial pose bones moved, but the evaluated mesh did **not** deform: Blender rig drivers and facial control relationships were not preserved through GLB. Therefore these GLBs are NOT ready for believable speech.
- The exported Rain GLB contains a true nonempty `mouth_open` morph target (2026-10-25 local accessor inspection), but the isolated morph target mostly affects gums and tongue; visually correct talking lips require additional testing in native Blender. This is a partial control, NOT full lip sync.

**Production-policy reality:** There are now >=15 actual separately-authored professional native models available to evaluate. This does not make the episode pipeline production-ready: 17 character identities are not mapped to the canonical 15, many lack speaking face, original studio costumes are not necessarily stylistically consistent, and none has passed a full 74-line lip-synced episode render. The legacy low-poly pipeline remains blocked. Don't fabricate or promise a Pixar-grade talking cartoon just because a GitHub native asset/geometry test passed. User must approve the new hero visual identity before replacing Lelli, Brin and Odo in public episodes.


## 25 October 2026 continuation — genuine native assets, story review and speaking-face tests

The `TOOLS` repository now has a **verified 17-distinct-model artist-created source inventory**: eight older Blender Studio character masters plus two original DOGWALK characters (Pinda and Chocomel) and seven original Singularity creatures. This is a source-identity inventory, not a claim that all 17 are equally detailed, identical in style, or ready to talk.

- **Actual native character downloads, no procedural fallback:** [17-model assembly run 40233910527](https://github.com/eghosa001/TOOLS/actions/runs/40233910527) passed; the large asset artifact contains original native .blend files and provenance. [Compact visual review run 40234096515](https://github.com/eghosa001/TOOLS/actions/runs/40234096515) contains real static renders of the nine modern characters.
- **Standalone reusable actor tests:** Pinda and Chocomel successfully reopen in a fresh Blender process with original materials [40233055636](https://github.com/eghosa001/TOOLS/actions/runs/40233055636). Seven Singularity originals also independently reopen with skinned meshes and no missing necessary shader image files [40234435191](https://github.com/eghosa001/TOOLS/actions/runs/40234435191).
- **Real seven-character visual gallery:** [40235722377](https://github.com/eghosa001/TOOLS/actions/runs/40235722377) generated a compact seven-character contact sheet from actual Blender renders. **Critter and Plump Fly are visually legible;** the other small Singularity background creatures need revised framing to assess their suitability and should not be counted as polished talking leads.
- **First high-quality episode review:** [40236330123](https://github.com/eghosa001/TOOLS/actions/runs/40236330123) checked every line in the existing 74-line story and created exact JSON timing cues and captions without touching `video/story.json`, canon, Kaggle, or rendering. The script also supports future episodes with different dialogue lengths.
- **Strict native mouth morphology:** [40236424472](https://github.com/eghosa001/TOOLS/actions/runs/40236424472) measured actual shape-key geometry rather than trusting bone/key names. Of the original eight native Blender Studio actors, **only Rain** has a verified non-corrective direct mouth-opening shape; other lip/teeth/mouthbag corrections are *not* equivalent to speech visemes.
- **Native jaw skeletal deformation:** [40236624723](https://github.com/eghosa001/TOOLS/actions/runs/40236624723) shows the original Sprite deforming mesh vertices with its `DEF-Jaw` bone (74 sampled vertices moved, largest displacement 0.006875 world units). Cat/Dog direct jaw-bone tests found no such weighted jaw controls; scripted rig face controllers may still exist but have not been verified for automated dialogue.
- **Further speaker screening:** The original Singularity Critter face/jaw test is prepared in `.github/workflows/cartoonstudio-critter-native-speech-test.yml`. Its results must be checked independently before counting a third actor that can open its mouth.

### Safe next episode path

1. Present the true original Blender-rendered **character review board** for identity approval. Lelli, Brin and Odo's turquoise/ochre/coral shapes, clothing and personalities are canon, so a different imported design cannot be silently installed as that existing hero.
2. Select **three actual speech-capable high-quality rigs**, preferably reusing proven original mouth/Jaw controls. Test one real recorded spoken line per actor and compare visual mouth movement. An existing rig with no working mouth controls is a **supporting character**, not a talking lead.
3. Stage the approved three actors and licensed garden scenery in **native Blender**, retaining artist materials and existing actions. Do not automatically switch to washed-out/white GLBs when shader export loses fidelity.
4. Provide **exact unchanged story JSON and asset mapping**, then manually run **a three-second preview** only on user request. No full render without user review and explicit approval of that preview.
5. Continue using commercially usable CC BY with publisher/creator attribution; never include the Kaggle token in public files, chats or notebooks.

**Not done:** official speaking-actor visual approval, exact lip-sync with audio, professional preview MP4, full episode render. Automated CI structural tests are not finished 3D video.


**Critter speech test result (run 40236781064):** Successfully inspected the actual Blender Studio Critter native rig, with 16 shape keys and 57 jaw/mouth-named pose controllers. **Zero actual mouth-opening/phoneme shape keys** and **zero confirmed mesh-deforming weighted jaw bones** under the tested pose. Therefore Critter should NOT be counted as a verified talking lead. It remains a high-detail speaking-unverified supporting-character candidate. Source test: https://github.com/eghosa001/TOOLS/actions/runs/40236781064 .

**Confirmed measurable mouth actuation remains two native studio actors** (Rain `mouth_open` blend shape; Sprite `DEF-Jaw` bone), each still lacking validated multi-phoneme synchronized facial speech. Do not promote any additional actor simply because its file has many bones or its artist demo shows a mouth.


## 25 October 2026 — spoken-WAV-to-native character geometry evidence

[Real native spoken-audio test 40237611334](https://github.com/eghosa001/TOOLS/actions/runs/40237611334) **completed successfully as an independent engineering diagnostic**, not a production video render. A temporary diagnostic synthesizer spoke the exact existing first Brin dialogue sentence; canonical voice settings and all 74 dialogue lines remained unchanged. The native rigs were keyframed for 93 frames at 24 FPS, and high-amplitude voice samples were compared against actual evaluated mesh vertices.

- **Sprite:** Original native DEF-Jaw and original skinned mesh moved with the WAV signal in 8/8 tested high-amplitude samples. A separate native Blender rehearsal copy, WAV and JSON geometry evidence are archived. This proves audio-reactive jaw movement, **not** phoneme visemes, accurate lip contact or a finished animated performance.
- **Rain historic v2.6:** The raw source has a geometrically nonzero mouth_open key, but 0/8 evaluated loud-voice samples showed mesh motion. **Audio-driven speech is NOT verified.** Do not equate raw shape-key data with a visible lip.
- **Pinda:** 27 mouth-named controllers, no verified noncorrective speech shape or directly weighted jaw deformation under the original-native conservative test; **speech unverified**.
- **Chocomel:** 5 mouth-named controllers; original DEF-jaw test produced zero sampled vertex motion; **speech unverified**.
- **Critter:** The independent earlier negative result still stands ([40236781064](https://github.com/eghosa001/TOOLS/actions/runs/40236781064)).
- **Identity/continuity:** No character-to-Lelli/Brin/Odo mapping, visual redesign, series voice or story file was approved or changed. No Kaggle cells, episode preview or full render were triggered.
- **New research candidate, outside the core 17:** [VitruvianGodot](https://github.com/ibrews/VitruvianGodot) publishes a genuine CC0 human head with FACS shapes. It is **not** yet a third fully rigged talking lead; face geometry, body compatibility, Mixamo animation licensing and series-style consistency each require independent checks. Do not count the non-canon head in the original 17-model source tally.

See the [93-frame native audio-driven rig evidence and DOGWALK mouth reports](https://github.com/eghosa001/TOOLS/actions/runs/40237611334). A successful GitHub workflow means the stated engineering checks passed; it is not a finished MP4.


### 25 October 2026 — third verifiably moving high-detail facial asset, matching rigged body (NOT canon)

The [original CC0 Vitruvian head morph test 40238204680](https://github.com/eghosa001/TOOLS/actions/runs/40238204680) **passed** with the actual published 10 MB head GLB pinned at source commit bdecdcd537b4031fdd0fb299b7e4f93f084fffa0. On the real imported 17,161-vertex face mesh, Blender counted **26 existing source morph targets**, including 5 actual independently deforming mouth controls. Of 1,717 evaluated vertex samples, the Mouth_Large_Opened control moved **841**, Jaw_Lower **802**, aa_02 **1,310**, ow_08 **266**, and p_b_m_21 **189**. An actual spoken WAV envelope also moved the existing source open-mouth morph. Original author-created source geometry was used; no generated face or hand-made alternative was substituted.

The proof artifact has genuine Blender-rendered neutral and open-mouth **PNG stills**, the WAV, a separate native head audition copy, and numeric source/licence evidence. **Speech viseme existence does not prove phoneme-accurate alignment or finished acting.**

The follow-up [matching body and face run 40238554194](https://github.com/eghosa001/TOOLS/actions/runs/40238554194) also **passed**: the separately published real body GLB imported with a **52-bone existing armature, 57,531 skinned body vertices**, and the original face retained all five measured deforming mouth shapes. Both an original neutral full-body still and an open-mouth full-body still were rendered without any video or episode production. No missing external material image file paths were detected by this structural Blender check.

**Important limitation:** The head was **not yet attached to the body rig by Blender armature parenting** in this isolated import test. The source *Godot* project already attaches the head/hair to the body's Head bone using a BoneAttachment3D; reusing that original implementation or explicitly validated Blender equivalent is the next technical step. The actor is a stylized/realistic **human**, **not an authorized redesign of any nonhuman Sunpatch Court hero**. Original body animations include Mixamo material whose commercial/redistribution terms need separate review; only the source CC0 head/textures are expressly attested in the upstream NOTICE. Do not silently promote to a third fully episode-ready lead or count it as a new accepted canonical hero. The original 17-source professional cast inventory remains unchanged.

**Engineering readiness:** Sprite WAV-driven jaw = measured pass; Vitruvian source face = independently verified real multiple visemes and WAV-open; Rain WAV evaluation = fail; Pinda/Chocomel direct mouth screen = negative. No character mapping approved, 74 original lines unchanged, zero Kaggle episode previews and zero full episode MP4s.


## 25 October 2026 continuation — completed native bone following, original body actions and source material tests

**All three new non-episode engineering gates passed.** They do not authorize a Kaggle episode render, a cast redesign or distribution of third-party native animation files.

1. **Actual original head attached and driven from Mixamo skeleton:** [Run 40240205191](https://github.com/eghosa001/TOOLS/actions/runs/40240205191) passed. Blender correctly resolved the body glTF bone name to `mixamorig:Head`. A Child Of bone-follow attachment preserved the original neutral position and then moved **202 sampled original head vertices**, with up to **0.0525387 Blender world-unit movement**, when the 52-bone body head was posed. This checks actual evaluated mesh geometry, not merely a parent-pointer field.
2. **Real speech recognizer cues drive existing FACS mouth shapes:** The same run generated real English diagnostic spoken WAV audio from the first canonical line **without rewriting it**, used MIT-licensed [Rhubarb 1.14.0](https://github.com/DanielSWolf/rhubarb-lip-sync) to recognize **15 cues covering A-F**, and keyframed **101 frames** at 24 FPS into the original existing source face morphs. The result includes two real Blender-rendered PNG frames and a JSON evidence record. This is a **working automated viseme timing pipeline**, not independent proof of attractive phoneme lip readability in a finished film.
3. **Original body motion genuinely works:** [Run 40240458533](https://github.com/eghosa001/TOOLS/actions/runs/40240458533) passed a stronger check after actual action playback, not just a stored animation name. The genuine source `Walk_mixamo_vitruvian` action showed **0.61992 Blender units maximum evaluated bone-position movement** and **6.09785 radians maximum sampled bone-rotation change** across sampled frames. Existing original body actions were not overwritten.
4. **Restore high-detail original materials:** [Run 40240663507](https://github.com/eghosa001/TOOLS/actions/runs/40240663507) passed. Downloaded **seven actual published original CC0 face/body albedo, normal, roughness and mouth PNG maps** from pinned first-party VitruvianGodot source. Verified real images and installed them in **three matching real imported face/body/mouth material instances**, then rendered a genuine PBR comparison PNG. This Blender Principled conversion is a **viewing approximation**, not a claim of exact Godot's MatMADNESS/SSS shader parity or a finished beauty shot.

**Artifact access:** [original attached face and speech morph review](https://github.com/eghosa001/TOOLS/actions/runs/40240458533), [real source PBR face/body material review](https://github.com/eghosa001/TOOLS/actions/runs/40240663507). Only audit JSON and small rendered PNG evidence are provided; raw third-party .glb/.blend and Mixamo animation packages were not redistributed in these artifacts.

**Commercial licence separation:** The source project's [NOTICE](https://github.com/ibrews/VitruvianGodot/blob/main/NOTICE.md) expressly identifies the CharMorph-based source face and `vit_*.png` textures as CC0; the code/shaders are MIT. [Adobe's Mixamo FAQ](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html) permits its content to be used royalty free to create commercial *films*, but this must **not** be interpreted as permission to resell, expose or redistribute raw source motion files.

**Unresolved approvals are not programming bugs:** Vitruvian is an original high-detail *human* candidate; Lelli, Brin and Odo are established original nonhuman characters. No mapping of this imported human onto those heroes has been authorized. Natural facial appeal, facial/body visual alignment in a polished video, hair animation, 1280×720 cinematic scene appearance and full episode lip sync must still be approved from an actual short user-requested production preview, not structural CI alone. There is no authorized rendered episode MP4 and no canon changes.

**Working development scripts:** `video/assemble_vitruvian_original_actor.py` attaches the existing original head to its original body rig and maps genuine Rhubarb cues onto the original FACS shapes, `video/apply_original_vitruvian_pbr.py` restores original high-res skin/mouth PBR source maps, and corresponding isolated no-episode workflows run on repository changes. Existing `video/story.json` with its exact 74 original dialogue entries remains unchanged.


### Final integrated character rehearsal verification (no episode render)

[GitHub Actions run 40240991555](https://github.com/eghosa001/TOOLS/actions/runs/40240991555) **PASSED the complete combined engineering QA** after pulling the real original third-party rig/face and **all seven pinned original CC0 PBR maps**. In one Blender scene it checked source FACS morphs, preserved neutral bone attachment, physically moving head/skinned mesh, original `Walk_mixamo_vitruvian` action deformation, actual spoken WAV-derived Rhubarb viseme tracks and two real textured still renders.

**Measured evidence:** 52 existing body bones; **202 sampled head vertices moved** from a real skeleton head rotation, max 0.0525387 Blender units; published Walk body action max sampled bone translation **0.61992** Blender units and rotation **6.09785** radians; **15 automatically recognized Rhubarb mouth cues across six shapes**, keyframed for **101 frames**; **seven published source CC0 skin/normal/roughness/mouth image maps** reconnected to **three actual imported author-materials** in the same test scene.

[Download the exact integrated audit evidence and two original-textured Blender screenshots](https://github.com/eghosa001/TOOLS/actions/runs/40240991555/artifacts/12616873397).

Important: this proof **does not** imply that the existing main-story characters were mapped to this human source candidate, that artist-grade close-up viseme animation or hair simulations were visually approved, or that 1280×720 episode-quality MP4 exists. It is a defensible **technical** head/body/speech/material integration milestone. Original `video/story.json` blob SHA remains `aa2620ce8dcb7114f6bd1a0d0afe1cf307c61020`; no Kaggle render, story edit or character-canon change occurred. Raw third-party Mixamo animations were not released in GitHub artifacts.


### Final remaining engineering fixes — original rigged hair, real Godot dynamics and honest nonhuman-cast screening

These improvements are **not an episode render** and **not permission to redesign** the series.

- **Original source Hair Tool rig imported and tested:** [GitHub run 40241817681](https://github.com/eghosa001/TOOLS/actions/runs/40241817681) passed on the actual published original 52-bone body, CC0 FACS head, and 6-bone rigged hair GLB, with **511,454 existing skinned hair mesh vertices**. Rotating the real body head bone moved 151 sampled original hair vertices by up to **0.0554059 Blender units** and restored the original resting position. No hair geometry was fabricated or source rig substituted.
- **Hair incorporated into the *same* full speaking human test:** [GitHub run 40242038974](https://github.com/eghosa001/TOOLS/actions/runs/40242038974) passed for original body/face/hair + 7 authentic first-party CC0 PBR maps, actual 52-bone action movement, original 101-frame/15-cue Rhubarb mouth animation and two real stills. The combined script now requires original rigged hair to move and return to neutral before reporting integration success. [Integrated evidence and preview stills](https://github.com/eghosa001/TOOLS/actions/runs/40242038974/artifacts/12617019757).
- **Source Godot hair physics itself genuinely executes:** [GitHub run 40242458725](https://github.com/eghosa001/TOOLS/actions/runs/40242458725) passed with the **actual upstream MIT-licensed HairSpring GDScript**, the published original complete GLB trio and real Godot. Across **100 physics steps**, four simulated chain joints, **14 original body collision spheres**, a head rotation of up to **0.27998 radians**, hair-bone rotation up to **1.22108 radians** and hair-tail movement up to **0.23735 units** were measured. Both published original Idle/Walk source animations loaded. [Godot physics report](https://github.com/eghosa001/TOOLS/actions/runs/40242458725/artifacts/12617109884). This verifies the source skeleton and numerical simulation, but not pixel-perfect dynamics or a user-reviewed animated shot.
- **Remaining six distinct Singularity background creatures were honestly screened:** [GitHub run 40242210117](https://github.com/eghosa001/TOOLS/actions/runs/40242210117) passed audits for Double Mohawk, Multi Frog, Manta Ribs, Double Eye, Plump Fly and Coralboi. None of six showed a directly deforming mouth morph or directly weighted moving jaw bone under the conservative tests. They do **not** become verified speech leads merely because all original meshes render. Complex original rig face controllers could require separate driver exploration. [Original-mesh mouth geometry findings](https://github.com/eghosa001/TOOLS/actions/runs/40242210117/artifacts/12616154553).
- **New source-only QA implementations:** `video/audit_original_vitruvian_hair.py`, `video/test_actual_godot_hair_spring.gd`, `video/audit_other_singularity_speech.py`, plus corresponding GitHub Actions. The existing `video/assemble_vitruvian_original_actor.py` now attaches and verifies true original rigged hair and source PBR in the same FACS speech audition. Assets are fetched from pinned original author sources; only small numeric test evidence, still images and cue data are uploaded.

**Remaining product acceptance gates, not failures that software can silently resolve:** Lelli, Brin and Odo are the user's established nonhuman designs. Vitruvian is a genuinely rigged/talking human technical candidate, not an approved replacement. No set of three nonhuman visually-canonical mouth-synchronized speaking rigs has yet been approved and installed, and existing low-detail procedural fallbacks remain prohibited. The automated lip-sync geometry gate does **not** establish visually natural speech, colour/hair rendering parity, polished children's-story cinematography, or finished 720p/24fps playback. Those decisions require a reviewed technical performance and then an **explicitly user-requested** 3-second episode preview before any full episode. No `story.json` content or original voices were changed; **no Kaggle preview/full episode or episode MP4 was launched**.
