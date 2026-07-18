# top5isu_v1 Adapter

This adapter is selected only by an approved `top5isu-shorts` build contract.
It does not replace the normal production default.

## Identity Lock

```text
template_profile=top5isu_v1
reference_project_name=top5isu
derived_from_reference_project=true
fallback_allowed=false
```

Clone the verified `top5isu` root project. Never repair an old episode draft
into the next episode and never fall back to `shrt white`. A fallback attempt is
`FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN`.

## Track Lock

Preserve the reference-project row order exactly:

```text
IMAGE_EFFECT_PRESETS
TTS
T2
T1
LOGO
```

The logo spans the full timeline. Replace the seven sample image segments with
episode assets while retaining their approved image effects. Sample media must
not remain active.

## Coordinate Lock

The CapCut UI value and draft JSON value are different representations:

```text
image_ui_y=-600
image_json_transform_y=-0.15625
```

Writing `-600` directly into `clip.transform.y` is a hard failure.

## Audio Lock

Resolve semantic audio lanes independently of visible CapCut row names:

```text
audio.narration_tts=A_TTS
audio.speaker_source=A_SOURCE
audio.sfx=A_SFX
audio.bgm=A_BGM
```

Do not reuse the generic `shrt white` A9-A12 row mapping. Normalize source and
generated audio with `ffmpeg loudnorm` to `-14 LUFS` before import, retain the
measurement report, and remeasure the final export before any final claim.

Run `scripts/validate_top5isu_track_mapping.py` before draft assembly and the
`top5isu-shorts` package/draft validators after assembly.
