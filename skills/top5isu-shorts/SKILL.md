---
name: top5isu-shorts
description: Use when the user explicitly says top5isu, 탑5이슈, TOP5 쇼츠, 순위 쇼츠, 군림보 쇼츠, or gunlimbo, or asks to use the top5isu CapCut root template for a Korean Shorts project. Do not use for political longform, generic shrt white Shorts, or script-only Tikitaka work unless top5isu, TOP5, or 군림보 is explicitly named.
---

# top5isu Shorts

## Purpose

This skill is the single user-facing router for the `top5isu` Shorts lane. It
owns profile selection and the immutable production contract, not script
authorship or CapCut completion claims.

## Ownership

- `top5isu-shorts`: choose `top5` or `gunlimbo`, lock `top5isu_v1`, and create
  `top5isu_build_contract_v1`.
- `00-tikitaka`: own Stage 1 source analysis, hooks, script, 설계도, and script
  handoff.
- `000short-production-agent`: execute the approved contract, assemble CapCut,
  validate production assets, and own `FINAL_LOCK`.

Do not modify `00-tikitaka` to add top5isu production behavior.
Do not modify `111-politics-longform` or import politics-specific rules.
Do not let this skill declare `FINAL_LOCK`.

## Entry Gate

Trigger only when the user explicitly selects this lane with `top5isu`, `TOP5`,
`순위 쇼츠`, `군림보`, or `gunlimbo`.

Profile routing:

```text
ranking, 순위, TOP5, 5위부터 1위 -> style_profile=top5
story, 감동, 반전, 군림보       -> style_profile=gunlimbo
both or unclear                 -> WAIT_USER_PROFILE
```

Read only the selected profile reference:

- `style_profile=top5`: `references/top5-profile.md`
- `style_profile=gunlimbo`: `references/gunlimbo-profile.md`

## Stage Routing

### Script-only request

For `대본만`, `대본까지`, `티키타카`, or `설계도만`:

1. Require `00-tikitaka` for Stage 1.
2. Preserve its `WAIT_REPORT1_APPROVAL_TTS_DECISION` boundary.
3. Do not invoke production work.

### CapCut or full request

For `캣컵까지`, `캐컷까지`, `CapCut`, `끝까지`, or `업로드까지`:

1. Require a valid Stage 1 handoff from `00-tikitaka`.
2. Require `report1_approved=true` and an explicit voice/audio route.
3. Create and validate `top5isu_build_contract_v1`.
4. Route production to `000short-production-agent` with
   `template_profile=top5isu_v1`.

The explicit top5isu contract is the root-template authority for this lane. It
overrides the generic production default without changing that default for
other Shorts.

## Fail-Closed Template Rules

The contract must contain:

```text
template_profile=top5isu_v1
fallback_allowed=false
clone_required=true
root_template_mutation=false
fresh_project_id_required=true
fresh_timeline_id_required=true
```

If the archive, manifest, profile adapter, or proof is missing, stop. Never use
`shrt white` or a previous episode as a substitute.

Failure codes:

- `FAIL_TOP5ISU_ARCHIVE_INTEGRITY`
- `FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN`
- `FAIL_TOP5ISU_ADAPTER_MISSING`
- `FAIL_TOP5ISU_TRACK_MAPPING`
- `FAIL_SPEAKER_SEGMENT_MUTED`

## Template Contract

Read `references/top5isu-template-contract.md`. Required visual locks:

```text
required_tracks=IMAGE_EFFECT_PRESETS,TTS,T2,T1,LOGO
protected_tracks=LOGO,T1,T2,TTS
image_effect_count_required=7
sample_media_policy=replace_all
logo_full_duration=true
image_ui_y=-600
image_json_transform_y=-0.15625
canvas=1080x1920
```

The UI and JSON coordinate values are a locked pair. Do not write `-600`
directly into JSON transform fields.

## Audio Contract

Default SuperTone profile:

```text
VOICE_ID=otFXhy6zBa2LQ8AYSWUeDB
MODEL=sona_speech_2
PITCH_SHIFT=0
PITCH_VARIANCE=1
SPEED=1
```

Never write API keys to the skill, reports, manifests, or logs.

Audio normalization policy:

```text
method=ffmpeg loudnorm
target_integrated_lufs=-14
preimport_measurement_required=true
final_export_remeasure_required=true
```

Do not assume CapCut `target_loudness` metadata uses LUFS units. Normalize
audio files before import and remeasure the exported video before a final audio
claim.

For `top5`, source audio is muted unless a verified quote is explicitly kept.
For `gunlimbo`, preserve approved speaker segments and use TTS only for
explanation. See the selected profile reference.

## Handoff

Read `references/handoff-contract.md`. The Stage 1 package remains owned by
`00-tikitaka`; this skill adds a style contract without rewriting the script.

Required production inputs:

- `report1_handoff.json`
- `script_handoff_gate.json` with PASS
- `timeline_design.json`
- `block_map.json`
- `tts_copy_text.txt`
- `top5isu_build_contract.json`

If any required input is missing, stop before assets or CapCut.

## Validation

Run, in order:

1. `scripts/validate_top5isu_contract.py`
2. `scripts/validate_top5isu_package.py`
3. `000short-production-agent/scripts/validate_top5isu_track_mapping.py`
4. `scripts/validate_top5isu_capcut_draft.py`
5. Actual local CapCut visual/playback review
6. Final-export loudness measurement

Static JSON or media-link PASS is not visual/playback PASS. A DRAFT result is
not upload ready.

## Portable Path Rules

- Resolve the factory root from the active workspace.
- Keep OneDrive manifests relative.
- Keep the OneDrive archive immutable.
- Edit only a local clone with fresh IDs.
- Reject foreign Windows or macOS user-profile absolute paths in portable packages.
- Reject `.bak` files in portable packages.
- Do not edit a local CapCut draft while CapCut is open.
