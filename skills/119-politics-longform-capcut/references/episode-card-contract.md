# Episode cards contract

A/B/C/D의 실제 승인 산출물만 다음 파일로 compile한다.

```text
{episode_dir}/50_capcut_project/episode_cards.json
```

`episode_cards.json`이 유일한 조립 Source of Truth다.
`USER_FINAL_ASSEMBLY_GRID.md`는 이 파일을 읽기 쉽게 변환한 READ-ONLY 뷰다.

## Card types

```text
INTRO
CHAPTER_CARD
SOURCE_VIDEO
NARRATION_IMAGE
NARRATION_VIDEO
TEXT_EXPLAINER
ENDING
```

## 필수 불변식

- 첫 카드는 `INTRO`, start=0, duration=5,000,000us다.
- 다음 카드 start는 이전 카드 end와 정확히 같다.
- 빈 시간·추정 패딩을 만들지 않는다.
- 무음 `CHAPTER_CARD`는 3,000,000us이고 lower mode는 `NONE`이다.
- `SOURCE_VIDEO`는 source identity, 실제 channel/date, source range를 가진다.
- 전체 project duration은 마지막 카드 end와 같다.
- 모든 카드는 한 primary video lane에서 선언 순서대로 이어진다.
- 챕터 사이 이미지와 나레이션이 모두 OFF이면 SOURCE_VIDEO를 직접 연결한다.

## 하단 단일 슬롯

내부 모드는 다음 중 하나다.

```text
SOURCE_TTS
NARRATION_TTS
VIDEO100_EXPLAINER
NONE
```

사용자 표현 매핑:

```text
SRT + SOURCE_AUDIO    → SOURCE_TTS
SRT + NARRATION_AUDIO → NARRATION_TTS
COMMENTARY_2LINE      → VIDEO100_EXPLAINER
NONE                  → NONE
```

같은 시간대에 하나만 허용한다.

## 전체 자막 15자×2줄 계약

모든 `SOURCE_TTS`, `NARRATION_TTS`, `VIDEO100_EXPLAINER`에 적용한다.

```text
TARGET_CHARS_PER_LINE = 15
MAX_LINES             = 2
TARGET_CHARS_PER_CUE  = 30
HARD_MAX_LINE_CHARS   = 18
```

표시 글자 수는 줄 앞뒤 공백을 제외하고 내부 공백·문장부호를 포함해 센다.

- 3줄 이상: `CAPTION_MAX_LINES_EXCEEDED`
- 평균 15자 초과: `CAPTION_AVERAGE_LINE_LENGTH_EXCEEDED`
- 한 줄 18자 초과: `CAPTION_LINE_HARD_LIMIT_EXCEEDED`
- `VIDEO100_EXPLAINER`가 정확히 2줄이 아님:
  `COMMENTARY_REQUIRES_EXACTLY_2_LINES`
- 빈 줄 또는 작업 메모: FAIL

긴 SRT는 원문을 축약하지 않고 시간상 연속된 cue로 나눈다.
`VIDEO100_EXPLAINER`는 PRE-119가 30자 안에서 정확한 두 줄로 작성한다.

## 권장 카드 예

```json
{
  "card_id": "C003",
  "card_type": "SOURCE_VIDEO",
  "target_start_us": 8000000,
  "target_duration_us": 27477000,
  "source_file": "C:/local/S03.mp4",
  "source_start_us": 242000000,
  "source_duration_us": 27477000,
  "source_identity_ref": "S03_LOCK",
  "source_channel": "MBCNEWS",
  "source_date": "2026.08.02",
  "original_audio_mode": "embedded",
  "lower_mode": "VIDEO100_EXPLAINER",
  "lower_text": "정책 방향은 같았지만\n시행 준비는 충분했나",
  "why_this_segment": "주장과 집행 준비의 차이를 제시"
}
```

## 미디어 이동성

`source_file`, `image_file`은 build machine 입력이다.
영상·오디오는 회차 고유 Media 폴더로 복사하고 한 번의 relink를 사용한다.
정적 이미지는 project Resources에 embed한다.
portable 정본은 root contract·root ZIP·manifest·cards·hash·report다.
