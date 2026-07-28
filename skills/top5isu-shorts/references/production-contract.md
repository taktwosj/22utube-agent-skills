# top5isu Standalone Production Contract

Production is internal to `top5isu-shorts` and targets a real editable CapCut project.

## Audio and Assets

- Preserve full narration; never trim audio to force a visual duration.
- Normalize imported narration with ffmpeg loudnorm at -14 LUFS.
- Re-measure the final export when one exists.
- Replace all sample media. Episode image count is dynamic; every image keeps
  exactly one transition animation, with one or two fire-effect peak images.
- TOP5 source audio is muted unless a verified quote is selected.
- Gunlimbo approved speaker segments remain audible and unmasked by TTS.
- For every gunlimbo source with meaningful speaker speech, extract the entire
  original source audio and run full-length vocal isolation before creating any
  `Q1`, `Q2`, or later quote clip. This is mandatory whenever the separation
  tool can run; never isolate already-cut quote fragments.
- Prefer `demucs_htdemucs_ft` two-stem separation. Approved equivalents are
  `demucs_two_stems` and `bs_roformer_vocals`.
- Cut every Q clip only from `vocals.wav`; never from the mixed source audio.
- Mute the original video audio in CapCut. Preserve narration on `A_TTS` and
  isolated quotes on `A_SOURCE`.
- Require `processed_before_speaker_clip_cut=true`,
  `q_clips_source=vocals_stem`, `original_video_audio_muted=true`,
  `residual_music_review=PASS`, and `voice_artifact_review=PASS`.
- If separation is unavailable or fails, stop at `WAIT_VOCAL_ISOLATION`; do not
  silently import music-contaminated Q clips.

## CapCut Clone

- Lock `template_profile=top5isu_v2_top55` and `fallback_allowed=false`.
- Validate the immutable `top5isu` root archive and manifest.
- Clone to a fresh local project with fresh project/timeline IDs.
- Never mutate the root archive or use a previous episode as a base.
- Required track order:
  `IMAGE_EFFECT_PRESETS,FRAME,LOGO,TTS_TEXT,SOURCE_TEXT,T2,T1`.
- Required audio lanes: `A_TTS,A_SOURCE,A_SFX,A_BGM`.
- Required root image transform: UI `0`, JSON `0.0`; frame and logo span the
  full duration.
- Every image requires an animation. One or two emotional peak indices use
  `불꽃 회오리`, `불꽃 스와이프`, or `불꽃 마법`.
- Reject `shrt white`, `.bak`, stale sample media, and foreign user-profile paths.

## Clean Video Rework

When the operator supplies a clean video derived from an existing Short with
captions, subtitles, logos, or other text overlays removed, use
`intake_mode=clean_video_rework` and preserve `source_short_ref` plus
`derived_from_existing_short=true`.

- Verify the file exists, is non-empty, and passes ffprobe.
- Require visual review and OCR overlay check to confirm text removal.
- Record `captions_removed=true` and `text_overlays_removed=true`.
- Run `scripts/validate_top5isu_rework_intake.py`.
- Missing visual/OCR proof is `WAIT_CLEAN_VIDEO_REVIEW`, not a reason to treat
  the file as an unrelated source.
- After PASS, rebuild against the current clean video while preserving episode
  provenance and operator intent.

## Operator Manual Edits

After the generated project is opened in CapCut, operator changes are expected.
Re-read the current draft and metadata. Duration, track, text, timing, cut, or
media differences from the generated snapshot are not failures by themselves.
Use `manual_edit_policy=MANUAL_EDIT_EXPECTED` and never restore old values unless
explicitly requested.

## Assembly Report

After CapCut assembly, write `90_reports/assembly_report.md`. It must include the
exact existing CapCut project name, folder name, file name, and local path. The
last non-empty line must be the exact project name under `## 캣컵복사하기`.
Run `scripts/validate_top5isu_assembly_report.py`; a text-only or nonexistent
project path is not production evidence.

## Secret Handling

Never print, serialize, persist, or report API keys, access tokens, cookies,
authentication files, or session credentials. Read approved credentials only
from the configured environment at execution time. Validator reports and
assembly reports must contain no secret values.

## Evidence

A project claim requires the local project path, current draft readback/hash,
validator reports, and assembly report. CapCut app visual/playback review is
required only when the operator explicitly requests it.
