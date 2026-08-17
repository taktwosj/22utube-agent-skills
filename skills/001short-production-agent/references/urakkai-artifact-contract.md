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

- `T1`, `T2`, `SCREEN_EFFECT`, `SCREEN_WHITE`는 각각 정확히 한 행이어야 하며,
  모두 `0`부터 타임라인 총 길이까지 유지한다. 누락·중복·부분 길이는 `FULL_SPAN_ANCHOR_INVALID`다
- `A10` 행이 없으면 `APPROVED_SEGMENT_ROLE_MISSING:A10`

## 6. 문구 길이

`shrt_white_base_v2` 시드는 자리표시자라 폭·줄바꿈 설정이 없고, 빌더는 문자열만 갈아끼우며
CapCut은 자동 축소·줄바꿈을 하지 않는다. 공백 제외 기준 줄당 상한:

| 역할 | 상한 | 초과 시 |
|---|---|---|
| T1 | 10 | `CAPTION_LINE_TOO_LONG` |
| T2 | 12 | `CAPTION_LINE_TOO_LONG` |
| A10_TEXT | 16 | `CAPTION_LINE_TOO_LONG` |
| A9_TEXT | 15, 최대 2줄 | `CAPTION_LINE_TOO_LONG` / `CAPTION_TOO_MANY_LINES` |
| STATE | 15, 최대 2줄 | `STATE_TEXT_TOO_LONG` / `CAPTION_TOO_MANY_LINES` / `STATE_CUES_INVALID` |

넘으면 문구를 줄이거나 명시적 `\n`을 넣는다. 멀티라인 큐는 `final.srt`에서 지원된다.

## 7. 워크플로 상태

`state.json.status`는 빌드 직전에 정확히 `AUDIO_CAPTION_VALIDATED`여야 한다.
다르면 `STAGE07_STATE_INVALID`(기대값과 실제값을 함께 출력한다).

## 8. 재잠금

승인 설계를 고쳐 다시 잠글 때는 `validate_design_lock.py --relock`을 쓴다.
플래그 없이 기존 증거 위에 쓰면 `DESIGN_LOCK_EVIDENCE_EXISTS`로 닫힌다.

## 9. 미디어 연결

빌더는 소재 경로를 패키지에 기록하지만, 사용자는 CapCut에서 미디어를 직접 다시 연결한다.
최종 빌드 보고서는 복사 가능한 `project_path`와 `media_source_path`를 모두 제공해야 한다.
A10 오디오는 `a10_vocal_stem.<ext>`라는 이름으로 복사되며 내용은 외부에서 분리한 Demucs vocal stem이다.

## 조립을 막는 구조 제약 (실측, 260817 유형 4에서 확인)

설계 단계에서 미리 맞춰라. 조립 직전에 걸리면 표·타임라인·잠금 전체를 다시 만들어야 한다.

### 1. 같은 Bxx를 두 번 쓸 수 없다

`validate_capcut_project.py`가 동일 `source_range`를 가진 VIDEO 세그먼트 두 개를 `DUPLICATE_SOURCE_RANGE`로 막는다.
콜드오픈에 쓴 구간을 뒤에서 회수용으로 다시 쓰는 설계는 **불가능하다.**

부분 구간(예: 한쪽만 33ms 늦게 시작)으로 피하려 하지 마라. `validate_audio_caption.py`의 caption-timing v2는
V열의 소스 범위를 **원본표 헤더에서** 다시 계산하므로 우라까이표에 적은 부분 구간과 어긋나
`CAPTION_TIMING_BUILD_MAPPING_MISMATCH`가 난다. V열의 소스 범위는 항상 Bxx 전체 범위여야 한다.

**해법**: 그 Bxx를 콜드오픈에만 두고 원래 자리에서 뺀다. 재배열은 남은 구간들로 만든다.

### 2. 자막 cue 하나는 V열 하나를 넘을 수 없다

caption-timing v2는 모든 cue가 정확히 한 개의 `mapping[]` 행(=V열)을 가리키고
cue의 소스 범위가 그 V의 소스 범위 안에 들어갈 것을 요구한다. `mapping[]`은 V열과 1:1이어야 하며
여분 행을 넣을 수 없다.

A9 나레이션이 여러 V열에 걸치면 **cue를 V 경계에서 쪼개라.** 이때:

- `validate_design_lock.py`는 `set(A9 cue_id) == set(A9_TEXT cue_id)`와 start/duration/text 일치를 요구한다.
  자막만 쪼개면 `A9_TEXT_PAIRING_MISMATCH`가 난다. **오디오 cue도 같이 쪼개라.**
- 연속 TTS wav를 V 경계에서 자른 조각들은 이어붙이면 원본과 비트 단위로 동일하므로 재생은 끊기지 않는다.
  자른 뒤 `numpy.array_equal`로 확인하고 넘어가라.
- 자를 지점은 **실제 발화 쉼**과 맞춰라. RMS로 무음 구간을 먼저 재고, 그 근처 V 경계를 고른다.
  V 경계 누적합이 발화 쉼에서 멀면 그 배열 자체가 잘못된 것이다.

### 3. T1/T2는 각 한 줄 12자, 줄바꿈 불가

`validate_design_lock.py`의 `MAX_LINE_LENGTH_BY_ROLE`가 T1/T2에 12자 제한을 건다.
동시에 `validate_capcut_grids.validate_locked_assembly`의 제목 비교는 **정규화 없는 완전일치**라
표 셀의 `<br>`가 타임라인의 `\n`과 매칭되지 않는다.

따라서 **T1과 T2는 각각 12자 이하 한 줄**이어야 한다. 제목 두 줄은 T1이 1줄, T2가 2줄이다.
A9_TEXT·A10_TEXT는 정규화 비교라 `<br>`를 써도 된다(A9_TEXT 15자, A10_TEXT 16자).

### 4. 표 A9 행은 파일명이 아니라 문구다

`A9`는 `A9_TEXT`·`A10_TEXT_*`·`STATE_*`와 같은 text role로 검사된다.
표의 A9 셀에 wav 파일명을 적으면 `TABLE_CELL_TEXT_MISMATCH`가 난다. 오디오 바인딩은 `audio_lock.role_files`가 한다.

### 5. 타임라인에 A10 오디오 행이 따로 있어야 한다

`role=A10` 세그먼트를 V열마다 하나씩(총 V개) 둔다. `A10_TEXT`와 `segment_id`가 겹치면
`APPROVED_TIMELINE_ACTUAL_MISMATCH`가 나므로 `A10_AUDIO_Vxx` 같은 별도 id를 쓴다.
`content_type`은 `SPEAKER`(스키마 enum: TITLE/TTS/SPEAKER/SITUATION/STATE), 색은 `color_role` WHITE/YELLOW.

### 6. A10 스템 길이는 타임라인 길이와 정확히 같아야 한다

`STAGE07_AUTHORITY_MISMATCH`는 `measured_duration_us == duration_us` 완전일치를 본다(URAKKAI 트림 경로 제외).
44.1kHz로 리샘플하면 µs가 딱 안 떨어질 수 있다. **48kHz 스템은 리샘플하지 말고 그대로 이어붙여라** —
48000 Hz에서는 µs 단위 길이가 정수로 떨어지고 음질 손실도 없다.
