# Gunlimbo TOP55 Image2 Production Lessons

Use this reference for gunlimbo/TOP55 productions built from a source URL plus operator-supplied reference images.

## 1. Separate facts from editorial reaction labels

- Save every operator reference image unchanged and create a manifest with file name, dimensions, SHA-256, intended role, and source URL/episode.
- Labels such as `노 저어` or `아, 큰일 났다` may be operator-directed emotion or scene intent rather than verified quotes.
- Record them as `creative_dialogue_labels` with `creative_dialogue_is_verified_quote=false` unless an authoritative source verifies the exact words.
- Use verified reporting for narration; use the labels only for expression, composition, or cut timing.

## 2. ChatGPT browser image generation

- Generate final production images in a regular logged-in ChatGPT conversation. Temporary ChatGPT conversations can refuse image generation; detect that response immediately and navigate to a regular fresh chat instead of waiting for the image timeout.
- Image runners must not log full conversation URLs, target/tab IDs, cookies, or session values. Log only a safe browser-profile label and job status.
- Keep operator images as composition references; do not copy their logos, watermarks, article text, or accidental scoreboards into the generated image.
- Request no text, numbers, logos, watermarks, or borders inside the image. Keep the main subject in the central 80% safe area.
- A common ChatGPT raw size is `1383×1137`; center-crop to the measured TOP55 window ratio, then resize to exactly `966×794`.
- Verify all expected raw/final files, decode every PNG, require unique final hashes, run OCR, and create TOP55 frame previews plus a contact sheet.

## 3. Supertone and subtitle handling

- Explicitly pin the approved voice, `sona_speech_2t`, speed, pitch shift, and pitch variance. Do not rely on a helper script's model default.
- Use the dedicated Supertone virtual environment when the system Python lacks the SDK; this is an execution detail, not a reason to change providers.
- Measure actual TTS duration before locking the timeline. Never trim the waveform to force a target duration.
- Run silence detection. If TTS contains an abnormal multi-second internal gap, shorten only that gap while preserving speech speed and wording, then remeasure loudness.
- Final pre-import audio should be measured, not inferred. Target `-14 LUFS`; store integrated loudness, true peak, duration, size, and SHA-256 in the TTS manifest.
- The CapCut builder CLI expects subtitle JSON as an object: `{"cues":[...]}`, not a bare array. Cues must be contiguous, start at zero, end at the measured audio duration, and contain at most two display lines.

## 4. TOP55 contract semantics

- In `top5isu_build_contract_v2`, `image_effect_count_required` means the number of root animation prototypes and remains `4`; it is not the derived episode's image count.
- Store the derived image count separately in the image plan/track mapping/readback. A seven-image project still uses four canonical root prototypes.
- For a seven-image episode, boundaries contain eight strictly increasing values and the last boundary is replaced by measured audio duration.
- Close CapCut before cloning/installing a project. Preserve existing projects rather than overwriting them.
- All media and effect paths in the installed draft must resolve under the installed project folder.

## 5. Draft readback

- Animation labels are nested at `materials.material_animations[].animations[].name`; do not look for `materials.video_animations` or a top-level animation `name`.
- Text material `content` is itself a JSON string; parse it and read its inner `text` field for T1, T2, SOURCE_TEXT, and subtitles.
- Verify track order, duration, image-material hashes, actual `966×794` material metadata, one animation per image, intended high-impact indices, subtitle count, title/source text, no sample/placeholder residue, no `.bak`, and final `draft_content.json` SHA-256.

## 6. Completion gate

A project is ready only when package, blueprint, writer/fact/policy/persona, audio/subtitle, Image2, contract, track-mapping, draft, assembly-report, and full regression tests pass. App playback, MP4 export, upload, and publication remain separate explicit approvals.
