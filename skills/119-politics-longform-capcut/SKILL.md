---
name: 119-politics-longform-capcut
description: Use only when a political-longform request explicitly contains CapCut, 캡컷, 119, or 119정치롱폼.
---

# 119 정치롱폼 CapCut 제작

119는 승인된 정치롱폼 설계를 실제 source·narration·visual·root 자산과 결합해
편집 가능한 로컬 CapCut 프로젝트로 조립한다.

사용자가 CapCut, 캡컷, 119, 119정치롱폼을 명시했을 때 사용한다.
명시 호출이 없으면 119로 자동 우회하지 않는다.

## 시작

1. `episode_id`, active writer, 사용자 요청 결과를 확인한다.
2. 승인된 대본이 없을 때만 [direct-script.md](references/direct-script.md)를 읽는다.
3. 승인 대본에 `[ASSEMBLY_ONLY_SEED]` 또는 `execution_mode=ASSEMBLY_ONLY`가 있으면
   이 문서의 `ASSEMBLY_ONLY` 직접 경로를 최우선으로 적용한다.
4. 현재 단계의 reference만 읽으며 관련 없는 reference 전체를 미리 읽지 않는다.

| 관찰 가능한 상태 | 읽을 문서 | 상태 |
|---|---|---|
| 대본 미승인 | `direct-script.md` | `CAN_DRAFT` 또는 `WAIT_SCRIPT_APPROVAL` |
| 승인 대본 + ASSEMBLY_ONLY_SEED | 이 문서 + 현재 책임 reference | `ASSEMBLY_ONLY_READY` |
| 직접 대본 승인·제공 | 이 문서의 직접 경로 | `DIRECT_SCRIPT_READY` |
| 기존 Stage 2 산출물 사용을 명시 | `legacy-stage2.md` | `LEGACY_STAGE2_PREFLIGHT` |
| 실패 단계가 불명확 | `resume-map.md` | 한 단계 선택 |

직접 경로의 최소 입력은 `episode_id`, 승인된 최종 대본,
출처 URL·원본 SRT·로컬 미디어 중 하나 이상이다.
직접 경로는 110·111, 외부 검토 영수증, review packet, 업로드 패키지에 의존하지 않는다.

## ASSEMBLY_ONLY 잠금

`ASSEMBLY_ONLY_SEED`는 투군 PRE-119가 다음을 확정했다는 뜻이다.

```text
카드 순서
CARD_TYPE
챕터 제목·훅
나레이션 대사
HTML/CSS 설명카드 문구
하단 SRT | COMMENTARY_2LINE | NONE
논평 2줄
CTA 정책
WHY_THIS_SEGMENT
```

119는 다음 런타임 값만 결합한다.

```text
실제 파일 경로
SHA-256
실제 duration
검증된 source range
source channel/date/speaker
narration audio/SRT
rendered image
target start/duration
```

이미 실제 PASS 산출물과 동일 identity·SHA·duration이 있으면 다시 조사·검증·생성하지 않는다.

허용되는 기본 흐름:

```text
기존 또는 필요한 A/B/C/D 자산
→ episode_cards.json
→ caption layout validator
→ USER_FINAL_ASSEMBLY_GRID.md
→ clean build
→ relink
→ save/close
→ readback
→ media resolution
→ visual gate
```

ASSEMBLY_ONLY 회차에서 금지:

```text
정치 이슈 재조사
승인 대본 재작성·재검토
기존 PASS source metadata·exact quote 재검증
목표 초를 맞추기 위한 강제 retime
Grid 필드 보완용 추가 조사
builder 기능개선·TDD·candidate code 수정
새 adapter·독립 code review
정상 PASS 단계 전체 재실행
build 후 active draft 직접 수술
```

현재 조립을 실제로 불가능하게 만드는 결함이면 자동 개발 작업으로 확장하지 않고
`ASSEMBLY_BLOCKED:<정확한 원인>`으로 중단한다.

## 승인 뒤 A–D

없는 필수 산출물만 만들고 기존 PASS 산출물은 재사용한다.

| 작업 | 읽을 문서 | 독점 출력 |
|---|---|---|
| A 출처·SRT·다운로드·로컬 컷 | `source-media.md` | source media와 source captions |
| B 나레이션·정렬·SRT | `narration.md` | narration media와 narration SRT |
| C HTML/CSS 설명카드 등 지원 시각 자산 | `visual-assets.md` | episode `Resources` 자산 |
| D 근본·target·CapCut 종료 준비 | `capcut-assembly.md` 준비 절 | 공식 resolver 결과 |

A–D는 다른 작업의 state·산출물·CapCut draft·`episode_cards.json`을 수정하지 않는다.
모두 준비된 뒤 join owner 한 명만 실제 산출물을 `episode_cards.json`으로 합친다.
`episode_cards.json`이 유일한 join이자 조립 Source of Truth다.

## 전체 하단 자막 화면 계약

다음 모든 하단 표시 자막에 동일하게 적용한다.

```text
SOURCE_TTS
NARRATION_TTS
VIDEO100_EXPLAINER
```

잠금값:

```text
TARGET_CHARS_PER_LINE = 15
MAX_LINES             = 2
TARGET_CHARS_PER_CUE  = 30
HARD_MAX_LINE_CHARS   = 18
```

- 평균 한 줄 15자를 목표로 하고 화면에는 최대 2줄만 표시한다.
- 표시 글자 수는 각 줄의 앞뒤 공백을 제외하고 내부 공백·문장부호를 포함해 센다.
- 두 줄이면 전체 표시 글자 수가 30자를 넘지 않게 한다.
- 자연스러운 조사·어절·호흡 경계에서 줄을 나눈다.
- 긴 문장을 글자 크기로 억지 축소하지 않는다.
- 30자를 넘으면 원문을 바꾸지 말고 시간상 연속된 다음 cue로 분할한다.
- 원본 SRT·직접인용은 축약·의역하지 않는다.
- `VIDEO100_EXPLAINER`는 정확히 2줄이어야 한다.
- 3줄 표시, 빈 줄, 작업 메모형 문구는 FAIL이다.
- SRT와 `VIDEO100_EXPLAINER`를 같은 시간대에 함께 표시하지 않는다.

빌드 전 `validate_politics_caption_layout.py`를 로컬로 실행한다.
정상 PASS 결과를 다시 Codex에게 읽혀 같은 검사를 반복시키지 않는다.

## 핵심 불변식

- 한 회차에는 active writer 한 명만 둔다.
- CapCut 또는 백그라운드 프로세스가 열려 있으면 draft를 만들거나 고치지 않는다.
- active pointer가 선택한 검증 완료 근본만 사용한다.
- 원본 MP4, Media 폴더, CapCut draft, cache, 계정 정보는 로컬에 둔다.
- portable JSON에는 사용자 프로필 절대경로와 cache 경로를 넣지 않는다.
- ASR cue가 편집 컷을 정하지 않는다. 실제 컷에서 자막을 split 또는 clamp한다.
- 목표 길이·원본/나레이션 비율은 사용자 절대 LOCK이 아니면 `[EST]`다.
- 실제 source와 narration duration을 사용한다.
- 업로드·썸네일·렌더는 사용자 명시 요청이 있는 별도 단계다.

## 실패와 재개

일반 직접 경로에서는 구체적 기술 실패가 발생했을 때
`첫 실패 재현 → 원인 최소 수정 → 같은 검사 재실행`으로 처리한다.

ASSEMBLY_ONLY에서는 자동 코드수정·기능개선으로 확장하지 않는다.
상위 조립 입력 오류는 상위 입력 또는 cards를 수정한 뒤 clean rebuild한다.
active draft의 CTA·텍스트·template·attachment·history를 연쇄 수술하지 않는다.

성공한 단계는 실제 identity·SHA·duration이 유지되면 다시 실행하지 않는다.
재개점이 불명확할 때만 [resume-map.md](references/resume-map.md)를 읽는다.

## 단계 문서

- 대본: [direct-script.md](references/direct-script.md)
- 출처 미디어: [source-media.md](references/source-media.md)
- 나레이션: [narration.md](references/narration.md)
- 시각 자산: [visual-assets.md](references/visual-assets.md)
- 조립·검증: [capcut-assembly.md](references/capcut-assembly.md)
- 카드 계약: [episode-card-contract.md](references/episode-card-contract.md)
- 재개 선택: [resume-map.md](references/resume-map.md)
- 기존 Stage 2 전용: [legacy-stage2.md](references/legacy-stage2.md)

근본 승격 작업을 명시적으로 요청받았을 때만
[root-bundle-contract.md](references/root-bundle-contract.md)를 읽는다.

## 완료 판정

직접 경로는 `STAGE2_PREFLIGHT`를 요구하거나 보고하지 않는다.

```text
DIRECT_SCRIPT_READY 또는 ASSEMBLY_ONLY_READY
ROOT_CONTRACT
CAPTION_LAYOUT
EPISODE_CARDS
USER_FINAL_ASSEMBLY_GRID
PROJECT_BUILD
MEDIA_RELINK
MEDIA_RESOLUTION
VISUAL_GATE
```

`MEDIA_RELINK=PASS`, `MEDIA_RESOLUTION=PASS`, `VISUAL_GATE=PASS`가 모두 있어야
CapCut 제작 완료다. 정적 JSON 검사나 GRID는 실제 화면 승인 증거가 아니다.
`MP4`와 `UPLOAD`는 실행하지 않았으면 `NOT RUN`이다.
