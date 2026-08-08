# URAKKAI 아티팩트 계약 (Stage 05 → 08)

빌더는 `production_plan.json`을 읽지 않는다. 실제 권위 체인은
`source_identity` → `approved_timeline` + `build_manifest` → `design_lock_evidence` →
`audio_lock` + `caption_lock` + `final.srt` → `build_config` → `build_episode_capcut.py`
이며, 아래 항목은 전부 스키마에 없거나 이름만으로는 드러나지 않아 실제 회차에서 빌드를 세웠던 것들이다.

## 1. 순서 서명

`build_manifest.urakkai.locked_permutation`은 **최종 타임라인 배열 순서**와 같아야 한다.
원본 시간 순서가 아니다. 둘이 같으면 재배열이 없는 것이므로 URAKKAI가 성립하지 않는다.
불일치 시 `E_LOCKED_ORDER` / `TIMELINE_ORDER_SIGNATURE_MISMATCH`.

## 2. `source_audio[]` 필수 필드

| 필드 | 값 | 없으면 |
|---|---|---|
| `clip_id` | 대응하는 VIDEO 클립과 **같은 id** (`V01`…) | `E_AUDIO_BINDING` |
| `mode` | `on` \| `duck` \| `mute` | `E_AUDIO_BINDING` |
| `source_sha256` | **원본 영상**의 sha256 (오디오 파일 sha가 아니다) | `E_AUDIO_BINDING` |
| `source_range_us` / `target_range_us` | 대응 VIDEO 클립과 동일 | `E_AUDIO_BINDING` |
| `capcut_source_range_us` | 선택. 생략하면 `target_range_us`가 쓰인다 | — |

`capcut_source_range_us`가 타임라인 기준인 이유: A10에 물리는 파일은 **승인 순서로 재배열한 뒤
분리한 stem**이고 그 길이는 최종 타임라인과 같다. 원본 시간축을 넣으면
`SOURCE_RANGE_EXCEEDS_MEDIA`가 난다.

## 3. A10 stem 이중 구속

`audio_policy=A10_RETAINED_SYNC`에서 A10은 항상 외부 분리 stem이다. CapCut 내장 보컬 분리는 증거가 아니다.

- Demucs는 **재배열한 오디오**에 돌린다. 원본에 돌린 stem을 재배열하면 안 된다
- `audio_lock.audio_path`는 `vocal_stem_manifest`의 `vocals_path`와 정확히 같아야 한다
  (`AUDIO_CAPTION_VOCAL_STEM_*_PATH_MISMATCH`)
- `audio_lock.measured_duration_us`는 최종 타임라인 길이와 정확히 같아야 한다
  (`STAGE07_AUTHORITY_MISMATCH`). 샘플 단위로 패딩·트림해서 맞춘다

## 4. 자막 레이어

`caption_lock.cues[]`의 `layer`는 자막이 놓이는 트랙 역할이다: `STATE` / `A10_TEXT` / `A9_TEXT`.

- **다른 layer끼리는 시간이 겹쳐도 된다.** 상황 설명과 화자 발언이 동시에 떠 있는 게 정상이다
- 같은 layer 안에서는 겹칠 수 없다 (`AUDIO_CAPTION_CUE_OVERLAP`)
- `layer`를 생략하면 전체 큐가 한 줄로 취급되어 예전처럼 비겹침이 강제된다
- STATE와 A10_TEXT 문구는 **전부** `caption_lock`과 `final.srt`에 큐로 존재해야 한다
  (`SUBTITLE_BINDING_CUE_MISSING`, `SUBTITLE_TEXT_NOT_IN_LOCKED_SRT`)
- `caption_lock.cues` 배열 순서와 `final.srt` 블록 순서가 위치로 대응한다

## 5. 승인 타임라인에 빠뜨리기 쉬운 행

- `SCREEN_EFFECT`, `SCREEN_WHITE` 행이 없으면 빌더가 **조용히** 해당 템플릿 트랙을 비운다.
  둘 다 `0`부터 총 길이까지 한 행으로 넣는다
- `A10` 행이 없으면 `APPROVED_SEGMENT_ROLE_MISSING:A10`

## 6. 문구 길이

`shrt_white_base_v2` 시드는 자리표시자라 폭·줄바꿈 설정이 없고, 빌더는 문자열만 갈아끼우며
CapCut은 자동 축소·줄바꿈을 하지 않는다. 공백 제외 기준 줄당 상한:

| 역할 | 상한 | 초과 시 |
|---|---|---|
| T1 | 10 | `CAPTION_LINE_TOO_LONG` |
| T2 | 12 | `CAPTION_LINE_TOO_LONG` |
| A10_TEXT / A9_TEXT | 16 | `CAPTION_LINE_TOO_LONG` |
| STATE | 8 | `STATE_TEXT_TOO_LONG` / `STATE_CUES_INVALID` |

넘으면 문구를 줄이거나 명시적 `\n`을 넣는다. 멀티라인 큐는 `final.srt`에서 지원된다.

## 7. 워크플로 상태

`state.json.status`는 빌드 직전에 정확히 `AUDIO_CAPTION_VALIDATED`여야 한다.
다르면 `STAGE07_STATE_INVALID`(기대값과 실제값을 함께 출력한다).

## 8. 재잠금

승인 설계를 고쳐 다시 잠글 때는 `validate_design_lock.py --relock`을 쓴다.
플래그 없이 기존 증거 위에 쓰면 `DESIGN_LOCK_EVIDENCE_EXISTS`로 닫힌다.

## 9. 미디어 연결

빌더가 소재를 `<project>\Resources\media\`로 복사하고 `##_draftpath_placeholder_…##`
상대경로를 심는다. **사용자가 CapCut에서 미디어를 다시 연결할 일이 없다.**
A10 오디오는 `a10_vocal_stem.<ext>`라는 이름으로 복사되며 내용은 외부에서 분리한 Demucs vocal stem이다.
