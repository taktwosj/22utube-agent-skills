# 03_CAPCUT_LAYOUT_CONTRACT

## Purpose

CapCut PASS is based on real draft files and normalized draft validation, not report wording.
This contract separates the script-writing role from the CapCut production role:

- `00-tikitaka`: `상단`, timed `중단`, `중단 TTS 글자만 복사`, verified `"화자발언"`, `(상황설명)`, 우라까이, 랭킹 재배열.
- `000short-production-agent`: CapCut project creation, template selection, T1/T2/T3/T4/T5/T6 role order, A-track audio insertion, and `draft_content.json` validation.

## Template Selection Gate

- Generic 11short/쇼츠공장 production has no third silent format default. The
  current official presets are the two defaults in
  `manifests/capcut-template-set.json`.
- Current named presets:
  - `black` / `블랙기본` / `블랙템플릿`: black-band layout draft base.
  - `insta white` / `인스타템플릿` / `인스타 템플릿`: Instagram/Reels draft base.
- Future presets such as `정치템플릿` may be added. If the user names a new template, use that exact user-selected template and record it in the manifest.
- Do not recreate a selected template manually from the old normal fallback. A draft that was not based on the selected preset fails the template gate.
- `인스타기본` is legacy/reference-only. Current factory routing uses `인스타템플릿` unless the user explicitly names a different real CapCut template.

## CapCut T-track Contract

`T1/T2/T3` are not work-stage names. They are the internal CapCut text-track order.
Keep this order in every selected template (`black`, `insta white`, or a future
user-named template):

```text
T1 = 소제목1
T2 = 소제목2
T3 = TTS / 나레이션 자막
T4 = 화자발언1, verified source speech only, visible as " "
T5 = 화자발언2, verified source speech only, visible as " "
T6 = (현장상황 / 행동 / 감정설명)

V7 = 템플릿 배경 / 랭킹중간 / 전환용 클립
V8 = 실제 영상 짜집은 source clip
A9 = 원본음성 / BGM / 랭킹 기본 배경음
A10 = TTS / 효과음 / 나의 사전 설정 효과음
```

Rules:

- Do not change the role or order of `T1~T6` to make room for audio, BGM, SFX, or imported media.
- Insert original audio, TTS, BGM, ranking BGM, and SFX only on A-tracks (`A9/A10` or additional audio rows). Never write audio/video segments into T-tracks.
- After adding audio, re-open the actual `draft_content.json` and verify track order and track type. If `T1~T6` order/role/segment identity changed, FAIL.
- `T4/T5` may contain only source-verified speech/subtitle/STT/OCR. Do not invent quoted speech.
- `T6` may overlap `T3/T4/T5` when it explains the same visual moment.
- No `하단`, `하단 원문`, bottom-caption, or bottom-TTS layer is allowed.
- Bracketed timecodes such as `[00:00-00:03]` are operator markers and must never become visible text.

## Template Style Preservation Gate

- A selected preset/template must be cloned or derived from that actual local CapCut draft. Do not rebuild the look by hand from a generic three-text fallback.
- For every active text role, preserve the template material/segment style and layout fields by default. Only the text content and timing may change unless the user explicitly asks for a style change.
- The post-CapCut gate must compare role rows against the selected template or approved reference for at least: font family/id, font size, fill color, outline/stroke, background or box style, transform/scale, x/y position, alignment, opacity, animation/effect references, and full-duration top-title timing where applicable.
- Any unapproved font, color, position, animation, grouping, or row-role change is a hard layout failure.
- Remove stale placeholder source media that is not part of the selected template master. Preserve required template master structures such as `subdraft`, `Resources/combination`, `materials.drafts`, sticker/effect rows, and preset audio placeholder relationships. If placeholder audio paths remain, report `portable_bundle=false` until the resource bundle is verified.

## Instagram Template Style Baseline

- Canvas: 1080x1920 vertical.
- Start from `인스타템플릿`/`인스타 템플릿`; never start from a blank project when Instagram was selected.
- Replace placeholder media with real source clips on `V8`.
- Preserve template font, color, position, animation, BGM, SFX, and safe-area layout.
- `T1/T2`: fixed top subtitle/title rows, centered, template font preserved.
- `T3`: TTS/narration caption, green-family or template-defined TTS style, black outline/stroke when template uses it.
- `T4/T5`: speaker-separated verified source speech only, color-separated by speaker when template provides it.
- `T6`: parenthesized situation/action/emotion caption.

## Instagram Template Master - 2026-06-28

Official CatCup template masters:

```text
black
insta white
```

Use these two CapCut sample projects as current defaults.
`insta white` is the display name of local draft folder
`260625-ig-contortion-top3-urakkai-instagram-tts`. Do not use
`260625-ig-contortion-top3-urakkai-instagram-tts-fixed`; it contains
`Default`/`T1`/`T2` placeholders and an invalid 98-second stale template tail.

Required creation mode:

- Copy the whole CapCut draft folder from the template master first.
- Preserve `draft_content.json`, `draft_info.json` when present,
  `draft_meta_info.json`, `draft_virtual_store.json`, `subdraft`,
  `Resources/combination`, preset audio placeholder relationships, sticker/effect
  rows, and the existing track/z-order structure.
- Replace only current job media and content: `source.mp4`, visible text,
  timing, and job-specific TTS/audio assets.
- Keep the 10-track master structure and 4 editable text tracks unless the user
  explicitly approves a new template version.
- Treat the internal `test.mp4` in both default projects as placeholder media.
  Generated work must replace it with the job source video.
- Do not rebuild Instagram drafts by creating a new JSON with only
  `source.mp4 + PNG frame + text`. That is a fake lookalike draft and fails the
  template gate.
- If `##_draftpath_placeholder_##` audio paths remain, report
  `portable_bundle=false` until `Resources/combination` and all dependent
  resources are bundled and verified. Do not claim cross-machine portability
  while placeholder audio paths are unresolved.

## Black Template Style Baseline

- Canvas: 1080x1920 vertical.
- Start from `블랙템플릿`; never start from a blank project when Black was selected.
- Keep the top/bottom black bands.
- `T1/T2`: white bold centered text inside the top black band.
- `T3/T6`: inside the visible video-safe area; do not cover important action.
- Ranking/TOP-N jobs insert `랭킹중간` or the selected separator clip between rank/item sections, with 0.2~0.4 second precision for transition points.

## FFmpeg Render-Match Contract

FFmpeg cannot create editable CapCut `T1~T6` projects. It may only render a final MP4 that visually matches the selected CapCut template.

Required render target:

```text
1080x1920
30fps
h264 + aac
source audio preserved unless the plan explicitly lowers/mutes it
TTS/BGM/SFX added only as audio layers
no visible timecodes
no bottom-caption layer
no unverified quoted speech
```

Use this JSON shape for FFmpeg workers:

```json
{
  "target": "instagram_or_black",
  "canvas": { "width": 1080, "height": 1920, "fps": 30 },
  "template": {
    "name": "인스타템플릿",
    "mode": "ffmpeg_render_match"
  },
  "tracks": [
    { "id": "T1", "role": "top_title_1" },
    { "id": "T2", "role": "top_title_2" },
    { "id": "T3", "role": "tts" },
    { "id": "T4", "role": "source_speech_1" },
    { "id": "T5", "role": "source_speech_2" },
    { "id": "T6", "role": "situation_emotion" },
    { "id": "V7", "role": "template_background_or_transition" },
    { "id": "V8", "role": "source_clip" },
    { "id": "A9", "role": "source_audio_bgm_or_ranking_bgm" },
    { "id": "A10", "role": "tts_sfx_or_preset_effect" }
  ],
  "segments": [
    {
      "start": 0.0,
      "end": 3.0,
      "source": "source.mp4",
      "source_in": 12.4,
      "source_out": 15.4,
      "texts": [
        { "track": "T1", "text": "소제목1" },
        { "track": "T2", "text": "소제목2" },
        { "track": "T6", "text": "(현장상황 설명)" }
      ]
    }
  ],
  "audio": {
    "keep_source_audio": true,
    "tts": [],
    "bgm": []
  }
}
```

## Ranking Separator Preset

- Ranking/TOP-N drafts must insert the CapCut preset/template or separator clip named `랭킹중간` between rank/item sections after the ranking order has been remixed.
- `capcut_timeline_manifest.json` must record the inserted separator positions and the rank/item boundaries they separate.
- Absence of `랭킹중간`/selected ranking separator between ranking beats fails the ranking placement gate.
- Ranking transition timing must be refined from the 1-second scan bucket to `0.2` to `0.4` second precision or frame-difference precision and recorded in `source_scene_transitions_precision.json`.

## Normalized Draft

Normalize draft JSON before validation:

```text
draft_content.json
-> capcut_draft_normalizer
-> capcut/normalized_draft.json
-> harness validation
```

Both raw `draft_content.json` and `normalized_draft.json` should remain available for audit.

## Video Track

- CapCut cut assembly must follow `$env:UTUBE_ROOT/11short/CAPCUT_CUT_ASSEMBLY_CONTRACT.md`.
- Do not create exact split-only clips. Generate `cut_manifest.json`, export handle clips, and place each handle clip as an independent CapCut clip with the initial visible trim set to the exact `visible_start_ms~visible_end_ms` range.
- `source_order` is the original source order. `timeline_order` is the CapCut placement order. Do not conflate them.
- Required proof before CapCut PASS: `cut_manifest.json`, `proof/clip_durations.csv`, `proof/timeline_order.txt`, `proof/contact_sheet.jpg`, `proof/capcut_assembly_report.json`, and exported `clips/S*_handle_*.mp4` files.
- The full original `source.mp4` must remain in the CapCut media bin as `original_source_media` with `imported_to_capcut_media=true` and `has_audio_stream=true`.
- Do not replace the original media-bin source with split clips, extracted audio, pre-renders, or generated footage.

## Bottom Text

Current 11short production forbids bottom text:

- no bottom caption
- no bottom subtitle
- no bottom legacy slot
- no bottom TTS script layer
- no source line as bottom caption

## Audio

- All audio additions belong on A-tracks, not T-tracks.
- If TTS is not requested, source audio can be kept.
- If TTS is requested, `voiceover_body.mp3` as one continuous track fails.
- TTS must be split by segment: `audio_000.mp3`, `audio_001.mp3`, etc.
- `spoken_scene` original speech/emotional audio must not be covered by TTS.
- Mixed scenes should use `keep_original` or `lower_original` unless there is a clear reason to mute.

## CapCut Registration

Required files:

- `draft_content.json`
- `draft_meta_info.json`
- `draft_virtual_store.json`
- `capcut/normalized_draft.json`

Registration checks must record checked CapCut root paths and whether the draft is visible in local CapCut.

The post-CapCut openability gate must also verify:

- the draft folder exists under the active CapCut project root
- the reported `draft_name` matches the registered draft folder/name
- `draft_content.json`, `draft_meta_info.json`, and `draft_virtual_store.json` parse as JSON
- referenced media/material paths exist on disk
- no selected-template placeholder media remains on the active timeline
- the real `source.mp4` is imported into the media bin when source media is required
- role-separated `T1~T6` text tracks exist as editable CapCut text segments
- audio/BGM/TTS/SFX exist only on A-tracks, not on T-tracks
- no video, audio, or media item was accidentally written into a text track
- draft duration and media duration are plausible against ffprobe/source
- Instagram/Reels drafts record
  `catcup_reference_layout_profile=insta_white_template_master_v1`
  and `catcup_reference_project=insta white`
- Black-template drafts record
  `catcup_reference_layout_profile=black_template_master_v1`
  and `catcup_reference_project=black`
- Instagram/Reels drafts are not based on the `-fixed` draft and contain no
  visible `Default`, `T1`, or `T2` placeholder text
- Template-backed drafts retain `subdraft`, `Resources/combination`, 10 total
  tracks, 4 text tracks, template-frame media, and master-derived draft
  materials unless a new template version was explicitly approved
- Every source-video segment must keep mandatory media enhancement settings:
  `QualityEnhance=HD`, `smart_color_adjust=30-50`, `clear=30-50`,
  `sharpen=30-50`, and `particle=5-30` visible-slider value. Adjacent
  source-video segments must differ by at least `5` points for
  `smart_color_adjust`, `clear`, and `sharpen`.
- Any draft with active audio must have CapCut loudness normalize enabled at
  `-14 LUFS`.
- if placeholder audio paths remain, the report says `portable_bundle=false`
  and does not claim Mac/Windows/Claude/Hermes portability

If any openability check fails, report the draft as `FAIL_OPENABILITY` or `WAIT_REPAIR`; do not give only the CapCut name as if the project is ready.
