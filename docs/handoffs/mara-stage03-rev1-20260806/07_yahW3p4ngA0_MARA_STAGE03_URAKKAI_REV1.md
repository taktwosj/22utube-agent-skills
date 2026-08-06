# 07_yahW3p4ngA0_MARA_STAGE03_URAKKAI_REV1

## 잠정 결론

**선택 추천안: `한국 식당이 문을 닫자` — 거의 원안 그대로.**

본 개정본은 `11_STAGE04_REVISION_ORDER_20260806.md`와 `13_CLAUDE_URAKKAI_REVISION_20260806.md`를 반영한 개정 초안이다. 8개 회차 중 가장 잘 짜인 설계로 평가됐다. 계약 필드 6종만 채우고 서사는 거의 그대로 유지한다.

```text
owner_skill=001short-production-agent
stage=03_MARA_CREATIVE_URAKKAI
SOURCE_MEDIA_STATUS=VERIFIED
ORIGINAL_CAPCUT_GRID_STATUS=READY_FOR_REVIEW
MARA_MESSAGE_STATUS=DRAFT_READY
CREATIVE_PREMISE_STATUS=DRAFT_READY
NOVELIZED_SCRIPT_STATUS=DRAFT_READY
FICTION_BOUNDARY_STATUS=LABELED
VIDEO_REORDER_STATUS=PROPOSED_NOT_FRAME_LOCKED
AUDIO_POLICY=TTS_ONLY_MUTE_SOURCE
URAKKAI_STATUS=WAIT_USER_URAKKAI_APPROVAL
REVISION=REV1_20260806
```

## 0. Source of Truth

| 항목 | 값 |
|---|---|
| episode_id | `yahW3p4ngA0` |
| 원본 표시명 | 작은 도시에서 한국 식당을 찾았지만 집에서 한국 음식을 먹는 여성 |
| 원본표 | `01_yahW3p4ngA0_ORIGINAL_CAPCUT_GRID.md` |
| 원본 media SHA-256 | `c61fa34c6c359042ab049f9700302c126221dde09936e0c3ef9673b167b7d08a` |
| 원본 길이 | `40.811s` |
| target 길이 | `[EST] 30~36초` |
| 댓글 자료 | `NOT_PROVIDED` |
| 사용자 승인 | `WAIT` |

## 1. 원본이 가진 힘

### MARA_MESSAGE

> **문화는 특정 장소가 열어줘야만 누릴 수 있는 것이 아니라, 음식·상·방송 같은 작은 의식을 스스로 재현할 때 집 안에서도 살아난다.**

## 2. 개정 사유

거의 고치지 않는다. 닫힌 문과 열린 거실이 하나의 시각적 대구로 닫히는 구조가 이미 강하다. 계약 필드(resolution_type, DST/SP 매핑, execution_strategy, baked_order_semantics, 대화 의존성, clear_anchors)만 신설·교체한다.

## 3. 선택안 서사 계약

| 항목 | 설계 |
|---|---|
| 주인공 | 작은 도시에서 한국 음식을 갈망하는 여성 |
| 목표 | 오늘 안에 한국 음식을 먹는다 |
| 미해결 질문 | 도시의 유일해 보이는 한식당이 닫혔다면 오늘의 갈망은 끝날까 |
| 반전 | 집에서 라면·김치·한국 방송을 준비해 손님 한 명짜리 식당을 직접 연다 |
| 결말 | 도시의 한국 식당은 닫혔지만 그녀의 거실에서는 한국이 문을 열었다 |
| 한 줄 | **한국 식당이 문을 닫자, 그녀가 거실을 열었습니다.** |
| resolution_type | `TRANSFORM_CANDIDATE` |
| creative_label（비계약） | `SELF_CREATED_SOLUTION` |

## 4. SOURCE_OBSERVATION / FICTIONAL_RECONSTRUCTION 경계

| 분류 | 내용 | 사용 규칙 |
|---|---|---|
| SOURCE_OBSERVATION | 인구 약 6만이라는 화면 자막 | 원본표 근거 |
| SOURCE_OBSERVATION | 한국 식당 간판 발견 | 원본표 근거 |
| SOURCE_OBSERVATION | 문이 닫힌 장면과 "닫았어요" 자막 | 원본표 근거 |
| SOURCE_OBSERVATION | 한국 음식을 먹고 싶다는 반복 | 원본표 근거 |
| SOURCE_OBSERVATION | 집에서 라면·김치 식사와 한국 방송 시청 | 원본표 근거 |
| FICTIONAL_RECONSTRUCTION | 식당이 도시의 유일한 한식당이라는 설정 | 창작 설정. 최종 대본에서는 "단 하나처럼 보였다"로 유지 |
| FICTIONAL_RECONSTRUCTION | 집 식사를 1인 식당 개업으로 재구성, 사장·요리사·손님을 모두 맡는 설정 | 창작 설정 |

## 5. 구조 변형 계약

```text
source_order_signature=원본표의 SB 오름차순
target_order_signature=SB04b > SB07a > SB02 > SB03 > SB04a > SB05 > SB06 > SB07b
source_structure_pattern=SP_DUAL_PAYOFF_SYNTHESIS
remake_structure_pattern=DST_PAYOFF_FIRST_DUAL_SYNTHESIS  # TB01(닫힌 문)과 TB02(집 식당 예고)가 서로 다른 두 결과를 연속 선공개하는 이중 payoff 구조
resolution_type=TRANSFORM_CANDIDATE
execution_strategy=full_tts
baked_order_semantics=NONE
dialogue_dependency=NONE
```

## 6. Target VIDEO order + CapCut 세로 설계

| Target | Source range | 화면 | A9 |
|---|---|---|---|
| TB01 | `00:20–00:24` | 닫힌 문·실망한 표정 | 어렵게 찾아간 한국 식당은 문을 닫고 있었습니다. |
| TB02 | `00:36–00:38` | 거실 상차림 1초 예고 | 그런데 그날 밤, 다른 한국 식당이 문을 열었습니다. |
| TB03 | `00:03–00:09` | 도시 거리·셀피 | 인구 6만의 도시에서 그녀의 목표는 하나였습니다. |
| TB04 | `00:09–00:16` | 간판 발견·기쁜 표정 | 오늘 안에 한국 음식을 먹는 것. 마침 식당도 찾았죠. |
| TB05 | `00:16–00:20` | 입구 확인 | 하지만 문은 열리지 않았습니다. |
| TB06 | `00:24–00:28` | 갈망하는 얼굴 | 그렇다고 오늘까지 닫을 수는 없었습니다. |
| TB07 | `00:28–00:36` | 라면·김치 준비 | 그녀는 집으로 돌아가 냄비를 올렸습니다. 손님도 한 명, 요리사도 한 명이었습니다. |
| TB08 | `00:38–00:40.8` | 거실 TV·상 | 도시의 한국 식당은 닫혔지만, 그녀의 거실에서는 한국이 문을 열었습니다. |

### 편집 원칙

- source range는 서사 수정안 값을 그대로 사용했다. 舊안과 거의 동일하다.

## 7. 전체 A9 작가 나레이션

> 어렵게 찾아간 한국 식당은 문을 닫고 있었습니다.
> 그런데 그날 밤, 다른 한국 식당이 문을 열었습니다.
> 인구 6만의 도시에서 그녀의 목표는 하나였습니다.
> 오늘 안에 한국 음식을 먹는 것. 마침 식당도 찾았죠.
> 하지만 문은 열리지 않았습니다.
> 그렇다고 오늘까지 닫을 수는 없었습니다.
> 그녀는 집으로 돌아가 냄비를 올렸습니다. 손님도 한 명, 요리사도 한 명이었습니다.
> 도시의 한국 식당은 닫혔지만, 그녀의 거실에서는 한국이 문을 열었습니다.

## 8. T1·T2·A9_TEXT·STATE

```text
T1: 한국 식당이 문을 닫자
T2: 그녀가 거실을 열었습니다
```

### A9_TEXT (8개, 컷 수와 동일)

- `식당 문이 닫혔다`
- `다른 식당이 열렸다`
- `작은 도시, 목표 하나`
- `간판 발견, 기쁨`
- `문은 안 열렸다`
- `오늘까진 포기 못해`
- `냄비를 올리다`
- `거실에서 한국 열림`

### STATE (8개, 컷 수와 동일)

- `닫힌 문·실망`
- `거실 상차림 예고`
- `도시 거리·셀피`
- `간판 발견`
- `입구 확인`
- `갈망하는 얼굴`
- `라면·김치 준비`
- `거실 TV·상`

## 9. 오디오 정책

```text
AUDIO_POLICY=TTS_ONLY_MUTE_SOURCE
clear_anchors=A9,A9_TEXT,A12
capcut_a12=EMPTY
video_volume=0
a10=EMPTY
a11=EMPTY
a9_segments>=1
```

## 10. 취약점·실패 조건

- "도시의 유일한 한국 식당"은 원본만으로 확정되지 않는다. 최종 대본에서는 "단 하나처럼 보였다" 또는 "어렵게 찾은 식당"으로 유지한다.
- 원본표의 coarse beat 경계는 ±1초 수준이므로 현재 source range를 확정된 값으로 보고하지 않는다.

## 11. Stage 04 독립성 자체 검토

| 검토축 | 상태 | 근거 |
|---|---|---|
| 메시지 독립성 | PASS 후보 | 새 관점·감정 보상 사용 |
| 서사 독립성 | PASS 후보 | 주인공·미해결 질문·반전·결말 재구성 |
| 정보 순서 변형 | PASS 후보 | `SB04b > SB07a > SB02 > SB03 > SB04a > SB05 > SB06 > SB07b` |
| 계약 필드 | PASS 후보 | DST/SP/execution_strategy/baked/dialogue/clear_anchors 전부 신설 |
| 사용자 승인 | WAIT | 승인 전 확정 금지 |

## 12. 사용자 승인 체크포인트

1. 원안 그대로의 서사가 이 원본에 맞는가.
2. 전체 A9 나레이션 문체·감정 강도가 맞는가.
3. 제안한 target VIDEO order로 Stage 05 설계를 진행해도 되는가.

```text
CURRENT_STATUS=WAIT_USER_URAKKAI_APPROVAL
NEXT_ON_APPROVAL=STAGE_05_FINAL_DESIGN_LOCK
NEXT_ON_REVISION=STAGE_03_SAME_DRAFT_REWORK
```
