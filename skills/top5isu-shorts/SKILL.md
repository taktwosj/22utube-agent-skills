---
name: top5isu-shorts
description: Standalone end-to-end factory for Korean TOP5, ranking, 군림보, and gunlimbo Shorts. Use for script design, TTS/audio, images, CapCut project creation, validation, and final reporting in the top5isu template lane. Do not mix this lane with generic Tikitaka or shrt white production.
---

# top5isu Standalone Shorts Factory

## Factory Identity

```text
standalone_factory=true
external_skill_handoff=forbidden
single_entrypoint=$top5isu-shorts
template_profile=top5isu_v1
fallback_allowed=false
```

This skill owns the complete TOP5·군림보 lane. It does not route script design,
production, CapCut assembly, or validation to another skill. Keep implementation
files inside this skill and split them by responsibility instead of adding more
user-facing skills.

## Commands

```text
$top5isu-shorts TOP5 쇼츠 끝까지
$top5isu-shorts 군림보 쇼츠 끝까지
$top5isu-shorts TOP5 설계도만
$top5isu-shorts 군림보 CapCut 프로젝트까지
```

The operator needs to remember only `$top5isu-shorts`.

## Profile Router

```text
TOP5, 탑5, 탑파이브, 순위, 랭킹, 5위부터 1위 -> style_profile=top5
군림보, gunlimbo, 군림보형 이야기                    -> style_profile=gunlimbo
both or unclear                                      -> WAIT_USER_PROFILE
```

Read only the selected profile:

- `style_profile=top5`: `references/top5-profile.md`
- `style_profile=gunlimbo`: `references/gunlimbo-profile.md`

Do not apply Tikitaka stages, handoff files, shrt-white coordinates, or generic
Shorts caption lanes to either profile.

## Internal Lifecycle

One skill owns all stages:

```text
INTAKE
-> SCRIPT_DESIGN
-> AUDIO_ASSETS
-> CAPCUT_PROJECT
-> FINAL_REPORT
```

Create an episode with `scripts/create_top5isu_episode.py`. Fixed directories:

```text
00_source
10_analysis
20_script
30_audio
40_assets
50_capcut_project
90_reports
```

### INTAKE

- Lock `style_profile=top5|gunlimbo`.
- Record topic, source URLs/files, requested stop point, upload target, and facts
  requiring verification.
- Do not invent rankings, prices, revenue, dates, quotes, or source facts.
- Resolve the active factory root before writing an episode.

#### CLEAN_VIDEO_REWORK

When the operator supplies a clean video derived from an existing Short after
captions, subtitles, or other text overlays were removed, keep it in this skill
as `intake_mode=clean_video_rework`. Do not treat it as an unrelated new source.

1. Save `source_short_ref`, `derived_from_existing_short=true`, and the clean
   video path in `10_analysis/clean_video_rework_manifest.json`.
2. Require `captions_removed=true`, `text_overlays_removed=true`, actual visual
   review, OCR overlay check, and playable-media ffprobe.
3. Run `scripts/validate_top5isu_rework_intake.py`.
4. If visual/OCR cleanliness is not proven, stop at
   `WAIT_CLEAN_VIDEO_REVIEW`; do not silently reject or replace the supplied
   clean source.
5. After PASS, reuse the existing episode intent and rebuild script, audio,
   assets, and CapCut project from the supplied clean video.

### SCRIPT_DESIGN

Read `references/script-contract.md` and create:

```text
20_script/design_blueprint.md
20_script/script.json
20_script/tts_copy_text.txt
20_script/top5isu_build_contract.json
```

Run `scripts/validate_top5isu_blueprint.py` and
`scripts/validate_top5isu_contract.py`. If the user explicitly says `끝까지`, the
approved scope covers the internal stages, but factual ambiguity, missing source
evidence, or an undecided required audio route remains a WAIT blocker.

### AUDIO_ASSETS

Read `references/production-contract.md`.

- Generate or accept the selected narration and preserve the full audio.
- Default SuperTone profile:

```text
VOICE_ID=otFXhy6zBa2LQ8AYSWUeDB
MODEL=sona_speech_2
PITCH_SHIFT=0
PITCH_VARIANCE=1
SPEED=1
```

- Never print or serialize API keys.
- Normalize with `ffmpeg loudnorm` to `-14 LUFS` before import.
- `final_export_remeasure_required=true`.
- Replace every sample image; image effect count remains seven.
- TOP5 uses source-backed rank facts. 군림보 preserves approved speaker audio.

### CAPCUT_PROJECT

The target is a real local editable CapCut project, not a JSON-only report.

1. Validate the immutable root package with
   `scripts/validate_top5isu_package.py`.
2. Clone the verified root project `top5isu`; never edit the root.
3. Require fresh project and timeline IDs.
4. Replace all sample media and relink only current episode files.
5. Preserve exact track order:

```text
IMAGE_EFFECT_PRESETS,TTS,T2,T1,LOGO
```

6. Preserve `image_ui_y=-600` and
   `image_json_transform_y=-0.15625` as a locked pair.
7. Resolve audio lanes as `A_TTS`, `A_SOURCE`, `A_SFX`, and `A_BGM`.
8. Run `scripts/validate_top5isu_track_mapping.py` and
   `scripts/validate_top5isu_capcut_draft.py`.
9. Register/open the local draft and perform actual visual/playback review.
10. Do not claim project completion from static JSON alone.

#### Operator Manual Edit Policy

After the operator opens CapCut, manual edits, duration changes, track additions,
text corrections, and timing adjustments are normal production work:

```text
manual_edit_policy=MANUAL_EDIT_EXPECTED
manual_edit_difference_is_failure=false
current_draft_reread_required=true
```

Do not compare the edited project to an old snapshot and raise a problem merely
because values changed. Re-read the current `draft_content.json` and current
project metadata. Use `validate_top5isu_capcut_draft.py --manual-edit-expected`
to report the observed current state without failing on user-created structural
differences. Only unreadable/missing project data or an explicit new safety
blocker may stop re-entry.

Any attempt to use `shrt white` stops with
`FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN`.

### FINAL_REPORT

Read `references/report-contract.md`. `FINAL_LOCK` requires:

- blueprint PASS
- contract PASS
- template package PASS
- track mapping PASS
- CapCut draft PASS
- real local project path and fresh IDs
- actual visual/playback review
- no sample media or `.bak` residue
- final export loudness measurement when an export exists
- `90_reports/assembly_report.md` with `# 조립도 보고서`
- exact `CapCut 프로젝트명`, project folder name, and local project path
- final `## 캣컵복사하기` block whose last non-empty line is the exact project name
- `scripts/validate_top5isu_assembly_report.py` PASS

The assembly report is written after CapCut assembly and must end with the exact
CapCut project file/folder name so the operator can copy it directly. Later
operator edits are `MANUAL_EDIT_EXPECTED` and do not invalidate the report solely
because duration, tracks, text, or timing changed; re-read the current draft and
issue a revised report only when requested.

Upload, publish, schedule, and delete actions always require explicit operator
approval. A project file is not an upload approval.

## Template Locks

Read `references/top5isu-template-contract.md`.

```text
required_tracks=IMAGE_EFFECT_PRESETS,TTS,T2,T1,LOGO
protected_tracks=LOGO,T1,T2,TTS
image_effect_count_required=7
sample_media_policy=replace_all
logo_full_duration=true
image_ui_y=-600
image_json_transform_y=-0.15625
canvas=1080x1920
clone_required=true
root_template_mutation=false
fresh_project_id_required=true
fresh_timeline_id_required=true
```

## Profile Locks

### TOP5

- Fixed narration order: greeting -> topic explanation -> 5 -> 4 -> 3 -> 2 -> 1 -> close.
- Each rank is an independent `ranking_item`.
- Verify every amount, statistic, date, and ranking basis.
- TTS is primary; source audio is muted unless a verified quote is selected.

### 군림보

- Story order: setup -> complication -> emotional turn -> close.
- Preserve approved speaker segments and keep them audible.
- TTS explains around source speech and must not replace the key speaker line.
- `speaker_segments_preserved=true` and `speaker_mute_forbidden=true`.

## Validation Order

```text
1. validate_top5isu_rework_intake.py when a clean-video rework manifest exists
2. validate_top5isu_blueprint.py
3. validate_top5isu_contract.py
4. validate_top5isu_package.py
5. validate_top5isu_track_mapping.py
6. validate_top5isu_capcut_draft.py
7. actual CapCut visual/playback review
8. validate_top5isu_assembly_report.py
9. final export loudness measurement when applicable
```

Static validation is not visual validation. An openable draft is not upload
ready. If any gate fails, repair only inside this skill and rerun the failed and
downstream gates.

## Portable and Safety Rules

- Keep OneDrive manifests relative and the root archive immutable.
- Reject foreign absolute user-profile paths and `.bak` files.
- Do not edit a local CapCut draft while CapCut is open.
- Never output secrets, cookies, tokens, or authentication files.
- Do not publish automatically without explicit approval.
