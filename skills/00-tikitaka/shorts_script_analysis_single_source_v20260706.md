# 쇼츠대본분석 단일 지침소스 v2026-07-06

This file is the active authority for current 11short/Tikitaka Shorts script
analysis. Use this file as the single project-attached source MD for Shorts
script analysis. Do not attach or apply legacy lower-caption, 3-layer, or
bottom-first-line instruction documents for current work.

## Authority

- Active output contract: `상단 + timed 중단 + 중단 TTS 글자만 복사`.
- Legacy output contracts are disabled for current work:
  - `하단`
  - `하단 원문`
  - separate bottom narration layer
  - 3-layer script package
  - `하단 첫마디 후보`
- If any older reference says `TTS 만들 글자만 복사`, read it as
  `중단 TTS 글자만 복사`.

## Layer Contract

```text
상단
고정 후킹 제목. 시간표를 붙이지 않는다.

중단
[0~3초]
(감정 / 반응 / 상황 / 장난 / 밈 / 화면 포인트)
"검증된 실제 인물 발화"
일반 텍스트 TTS/설명 후보

중단 TTS 글자만 복사
timed 중단 중 voice/TTS 의도 줄만 시간표 없이 모은 순수 원문
```

## Middle Caption Rules

- `중단` is the timed visible-caption authority.
- `"..."` is verified source speech only. Do not invent quoted speech.
- `(...)` is reaction, emotion, situation, visual point, SFX, meme framing, or
  viewer-read caption.
- Plain text can be narration-like middle caption text and may be included in
  `중단 TTS 글자만 복사` when it is intended for voice.
- Visual-only parenthesized captions are excluded from TTS copy unless the user
  explicitly wants them voiced.

## Prohibited Current Outputs

Do not create these for current Tikitaka script output:

- `하단`
- `하단 원문`
- `하단 첫마디 후보 5개`
- separate timed narration timeline outside `중단`
- 3-layer script package
- bottom/body caption narration layer

Allowed alias:

- `TTS 만들 글자만 복사` may appear only as a legacy alias of
  `중단 TTS 글자만 복사`. It is not a separate output contract.

## Assembly Design Authority

Current Tikitaka output is not only source reorder.

Before speaker-range design, complete this source-analysis order:

```text
source_identity_lock.json
-> prepare_source_voice.py
-> 10_analysis/audio/full_source_audio.wav
-> Demucs FULL_SOURCE_AUDIO separation
-> 10_analysis/audio/vocals.wav
-> SOURCE_VOICE_SEPARATION_GATE
-> speaker range design
```

The only valid skip is `NOT_REQUIRED_NO_SOURCE_SPEECH`, supported by a source
with no audio stream or explicit user/source-evidence confirmation. Missing
Demucs is `WAIT_DEMUCS_AVAILABLE`; do not use raw mixed audio as a fallback.
`no_vocals.wav` is not used.

`timeline_design.json` must describe a new Shorts assembly design with:

```text
source_order
timeline_order
assembly_role
caption_type
visible_text_role
audio_role
time_start
time_end
duration_basis
duration_status
audio_policy
visual_strategy
```

`source_order` and `timeline_order` must be separated.

`assembly_role` defines the function of the beat in the remake, such as intro
narration, verified speaker quote, reaction caption, payoff narration, or
transition.

`TTS` alone can mean visible caption text only. A voice/audio file is implied
only when narration is explicit, such as `caption_type=tts_narration` or
`audio_role=audio.narration_tts`.

Production must implement the locked assembly design without reinterpretation.

Every `speaker_quote` must use:

```text
source_audio_ref=10_analysis/audio/vocals.wav
source_audio_provenance=demucs_full_source_vocals
```

Any raw-video, pre-cut-before-separation, or missing source is
`WAIT_SOURCE_VOICE_Q_PROVENANCE`. In the handoff, `source_audio=on` means the
separate speaker/Q lane, never embedded source-video audio.

## Production Boundary

`00-tikitaka` may write draft script text, script handoff information, and the
two required source-analysis WAV artifacts created by `prepare_source_voice.py`.
It must not create Q clips, TTS voice files, SRT files, layout JSON, CapCut
drafts, exports, or upload packages. Production assets belong to
`000short-production-agent` after the user explicitly requests that stage.
