# Episode cards contract

A/B/C/D의 실제 승인 산출물만 다음 파일로 compile한다.

```text
{episode_dir}/50_capcut_project/episode_cards.json
```

`episode_cards.json`이 유일한 조립 Source of Truth다. `USER_FINAL_ASSEMBLY_GRID.md`는 READ-ONLY 뷰다.

## Top-level 필수값

```text
schema=politics-longform-episode-cards.v1
execution_mode=ASSEMBLY_ONLY
episode_id
project_name
cta_like_subscribe=ON|OFF
cards[]
```

CTA는 회차 전체 ON/OFF만 지원한다. 카드별 값은 top-level과 같아야 한다. 혼합값은 `CTA_POLICY_MIXED_UNSUPPORTED`다.

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

- 첫 카드는 root content boundary와 일치하는 `INTRO` 또는 start=0의 `SOURCE_VIDEO`다.
- 다음 카드 start는 이전 카드 end와 정확히 같다.
- 빈 시간·추정 패딩을 만들지 않는다.
- 무음 `CHAPTER_CARD`는 3,000,000us이고 lower mode는 `NONE`이다.
- `INTRO` 외 모든 카드는 비어 있지 않고 `chapter_title`과 동일한 `chapter_label`을 가진다. builder는 이를 해당 챕터 종료까지 상단에 표시한다.
- `SOURCE_VIDEO`는 source identity, channel/date, source range와 비어 있지 않은 `source_display_label`을 가진다. 화면 출처는 `출처 {source_display_label}` 한 줄뿐이며 channel/date는 provenance metadata다.
- 전체 duration은 마지막 카드 end와 같다.
- 모든 카드는 한 primary video lane에서 선언 순서대로 이어진다.
- 챕터 사이 이미지와 나레이션이 모두 OFF이면 SOURCE_VIDEO를 직접 연결한다.

## 하단 단일 슬롯

내부 모드:

```text
SOURCE_TTS
NARRATION_TTS
VIDEO100_EXPLAINER
NONE
```

사용자 표현:

```text
SRT + SOURCE_AUDIO    → SOURCE_TTS
SRT + NARRATION_AUDIO → NARRATION_TTS
COMMENTARY_2LINE      → VIDEO100_EXPLAINER
NONE                  → NONE
```

같은 시간대에 하나만 허용한다.

## build 전 preflight

```powershell
python scripts/run_politics_assembly_preflight.py `
  --cards <episode_cards.json> `
  --report <episode_dir>\90_reports\assembly_preflight_v1.json `
  --grid <episode_dir>\50_capcut_project\USER_FINAL_ASSEMBLY_GRID.md
```

PASS report는 cards SHA와 실제 SRT/raw transcript SHA, GRID SHA를 묶는다. 이후 입력이 바뀌면 builder가 거부한다.
