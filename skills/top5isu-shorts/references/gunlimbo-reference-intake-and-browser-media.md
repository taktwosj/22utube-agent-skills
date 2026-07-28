# Gunlimbo Reference Intake, Browser Image, and Audio QA

Use this procedure when the operator supplies a source Shorts URL plus several reference images and asks for a Gunlimbo remake.

## 1. Reference-collection mode

- While the operator is still sending images, save each original sequentially under the episode intake/reference folder.
- Record the operator's intended role verbatim, for example `노 저어`, `아 큰일 났다`, or `월드컵 내용 나올 때`.
- Keep creative reaction labels separate from verified direct quotations. Never rewrite a reaction label as something the public figure actually said unless a source verifies it.
- Reply briefly with the saved role and count; do not start drafting between every incoming image.
- When the operator says `이정도로해서 만들어`, treat reference collection as complete and proceed end-to-end without another confirmation. Preserve upload/publish approval as a separate gate.
- Build a manifest containing source path, dimensions, SHA-256, role, and whether the file is reference-only or approved for direct use.

## 2. Source facts when direct download is blocked

Use a layered fallback rather than guessing:

1. Read YouTube oEmbed for public title/author metadata.
2. In the managed browser, inspect `ytInitialPlayerResponse` only for non-sensitive metadata such as title, duration, dimensions, caption availability, and format presence.
3. Never print or persist signed stream URLs, cookies, browser target IDs, conversation URLs, or session values.
4. If source speech cannot be recovered, do not invent or reuse it. Set `source_speaker_mode=no_meaningful_source_speech`, `speaker_segments=[]`, and create new TTS from independently verified articles.
5. Separate operator-supplied comic staging from verified facts in `evidence_packet.json`.

## 3. ChatGPT image generation through managed CDP

- Use a normal logged-in ChatGPT conversation. Temporary ChatGPT conversations may explicitly disable image generation; detect that message immediately and restart in a regular conversation instead of waiting for the image timeout.
- Sanitize runner logs. Log only a generic tab index/title; never log full URLs, target IDs, conversation IDs, cookies, or session values.
- Before each prompt, verify the composer exists and the page is not already generating.
- After submission, inspect the DOM for one of three states: generating, generated-image candidate, or visible refusal/error. A refusal/error must stop or reroute immediately; it must not wait ten minutes as if generation were active.
- Final generated assets must be real ChatGPT PNG files. Reference screenshots guide role and composition; do not reproduce their watermarks, captions, or logos.
- For TOP55, center-safe crop and resize to exactly `966×794`; retain raw PNGs and unique SHA-256 hashes.
- If the local vision helper is unavailable, upload the generated contact sheet to a fresh regular ChatGPT conversation for structured visual QA. Structural QA remains mandatory regardless: dimensions, uniqueness, text/OCR check, file integrity, safe crop, and TOP55 frame preview.

## 4. TTS duration-repair and silence QA

- Generate Supertone with the Gunlimbo defaults explicitly set: approved voice, `sona_speech_2t`, speed `1`, pitch shift `0`, pitch variance `1`. Do not rely on an older helper's model default.
- Never print the API key or environment contents.
- Measure actual duration before repair. Writer repair may run at most twice.
- If two repairs oscillate between too long and too short, restore the better previously validated response, wrap it in the required sentinel envelope, and rerun `validate_top5isu_writer_response.py`. Do not silently use an unvalidated local rewrite.
- Inspect `silencedetect` output before locking duration. Shorten abnormal internal dead air longer than about one second while preserving a natural pause; do not trim spoken audio or change default speech speed merely to hit a target.
- Derive caption boundaries from actual speech pauses. Keep every caption page to at most two lines and preserve digits in visible captions.
- Final audio is not PASS until duration, SHA-256, integrated loudness, true peak, and subtitle end time are measured from the final file. Target Gunlimbo audio is `-14.0 LUFS`; report the measured value, not the filter's requested value.

## 5. CapCut handoff

- Use `top5isu_v2_top55` from episode creation onward. A new episode scaffold must not fall back to `top5isu_v1`.
- Keep the fixed v2 track order: `IMAGE_EFFECT_PRESETS, FRAME, LOGO, TTS_TEXT, SOURCE_TEXT, T2, T1`.
- Apply one real animation payload to every image and only one or two high-impact effects.
- Build a new versioned project, preserve the previous project, and verify the installed draft. Do not open CapCut, render, export, upload, or publish unless explicitly requested.
