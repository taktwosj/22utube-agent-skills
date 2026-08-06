# 01_dz0ev1nz1eg_MARA_STAGE03_URAKKAI_REV1

## 잠정 결론

**선택 추천안: `73개국에서 한 번도 안 한 행동`**

본 개정본은 `11_STAGE04_REVISION_ORDER_20260806.md`(계약 필드 지시서)와 `13_CLAUDE_URAKKAI_REVISION_20260806.md`(서사 수정안)를 반영해 02판을 개정한 초안이다. 사용자 승인 전이며, 확정 표현은 사용하지 않는다.

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
| episode_id | `dz0ev1nz1eg` |
| 원본 표시명 | 서울 도착 직후 청계천을 찾은 여행자 동행인 |
| 원본표 | `01_dz0ev1nz1eg_ORIGINAL_CAPCUT_GRID.md` |
| 원본 media SHA-256 | `e3884922f9af58b5204ca90e819250d415850a20506f7ab916f7c64201a0b556` |
| 원본 길이 | `32.555s` |
| target 길이 | `[EST] 30~35초` — 실제 보이스 생성·측정 전 잠금 금지 |
| 댓글 자료 | `NOT_PROVIDED` |
| 사용자 승인 | `WAIT` |

## 1. 원본이 가진 힘

### MARA_MESSAGE

> **여행의 최고의 순간은 더 많이 보는 데서 오지 않고, 더 이상 다음 장소로 서두르지 않아도 된다고 느끼는 순간에서 온다.**

### 실제 와우포인트

73개국 이상을 다닌 여행자들의 사진이 전부 서서 찍은 것이었는데, 앉아서 찍은 첫 사진이 서울에서 나왔다.

### 감정 이동

`빠르게 소비하는 여행 → 반복되는 습관 인식 → 서울에서의 예외 → 처음 앉음`

## 2. 개정 사유

기존 반전("작은 물길이 여행을 멈췄다")은 감상이지 반전이 아니다. 시청자가 뒤집힐 정보가 없다. 서사 수정안은 "처음 장면의 의미가 결말에서 달라짐" 유형으로 컨셉을 교체했다: 73개국의 사진은 전부 서서 찍은 것이었고, 앉아서 찍은 첫 사진이 서울에서 나왔다.

## 3. 선택안 서사 계약

| 항목 | 설계 |
|---|---|
| 주인공 | 73개국 이상을 이동해 온 여행 동행인 두 사람 |
| 목표 | (기존 유지) 서울에서도 계속 다음 장소로 이동한다 |
| 장애 | 도착 피로, 낯선 장소명, 늘 서서 이동해 온 습관 |
| 미해결 질문 | 73개국 동안 한 번도 안 한 행동이 무엇일까 |
| 반전 | 두 사람의 여행 사진은 전부 서서 찍은 것이었는데, 앉아서 찍은 첫 사진이 서울에서 나왔다 |
| 결말 | 서울이 준 첫 명소는 장소가 아니라, 앉아도 된다는 자세였다 |
| 한 줄 | **73개국에서 한 번도 안 한 행동을, 서울에서 처음 했습니다.** |
| resolution_type | `TRANSFORM_CANDIDATE` |
| creative_label（비계약） | `EMOTIONAL_REFRAME` |

## 4. SOURCE_OBSERVATION / FICTIONAL_RECONSTRUCTION 경계

| 분류 | 내용 | 사용 규칙 |
|---|---|---|
| SOURCE_OBSERVATION | 두 사람이 함께 여행하며 셀피 촬영 | 원본표 근거 |
| SOURCE_OBSERVATION | "73개국 이상" 화면 문구 | 원본표 근거 |
| SOURCE_OBSERVATION | 서울 도착 직후·청계천 방문 자막 | 원본표 근거 |
| SOURCE_OBSERVATION | 물에 발을 담그는 화면과 긍정 반응 | 원본표 근거 |
| SOURCE_OBSERVATION | 수로 주변에 앉은 사람들 (SB05) | 원본표 근거 |
| FICTIONAL_RECONSTRUCTION | 두 사람을 부부/동행 관계로 규정하는 설정 | 창작 설정 — 실제 사실로 보고 금지 |
| FICTIONAL_RECONSTRUCTION | 항상 다음 일정을 서두른다는 성격, 73개국 내내 서서 찍었다는 습관화 해석 | 창작 설정 — 실제 사실로 보고 금지 |
| FICTIONAL_RECONSTRUCTION | 서울에서 처음 앉아서 사진을 찍었다는 의미 부여 | 창작 설정 — 실제 사실로 보고 금지 |
| ~~FICTIONAL_RECONSTRUCTION: 현지인이 신발을 벗었다는 서술~~ | **삭제** — 원본표 SB05는 "수로 주변에 앉은 사람들"까지만 확인되며 신발을 벗었다는 서술은 미확인. 대본에서 제외했다 | 서사 수정안 반영 |

## 5. 구조 변형 계약

```text
source_order_signature=원본표의 SB 오름차순
target_order_signature=SB01a > SB03 > SB01b > SB02 > SB05 > SB04 > SB06
source_structure_pattern=SP_CAUSAL_PROGRESSION_TO_PAYOFF
remake_structure_pattern=DST_PAYOFF_FIRST_CAUSAL_BACKFILL  # 舊 산문: 감각적 결과 훅 → 감정 결과 선공개 → 여행자 정체 공개 → 도착 맥락 → 작은 장애 → 현지인의 행동 단서 → 공간의 의미 회수
resolution_type=TRANSFORM_CANDIDATE
execution_strategy=full_tts
baked_order_semantics=NONE
dialogue_dependency=CONTEXTUAL  # 발음 시도와 반응이 느슨하게 연결
```

## 6. Target VIDEO order + CapCut 세로 설계

| Target | [EST] 시간 | Source range | VIDEO | A9 | STATE |
|---|---|---|---|---|---|
| TB01 | 0:00–0:02 | `00:00–00:01.6` | 물에 들어간 발만. 얼굴 숨김 | 73개국을 돌아온 두 사람의 사진에는 공통점이 하나 있었습니다. | 발만 보이는 클로즈업 |
| TB02 | 0:02–0:05 | `00:10–00:13` | 청계천 이름을 발음하려다 막히는 표정 | 전부 서서 찍은 사진이라는 것. | 발음 시도하는 표정 |
| TB03 | 0:05–0:10 | `00:01.6–00:06.6` | 여행 몽타주·걷는 장면 | 다음 장소가 늘 기다리고 있었으니까요. | 여행 몽타주 |
| TB04 | 0:10–0:14 | `00:06.6–00:10` | 서울 거리·버스 | 서울에 도착한 첫날 계획도 같았습니다. | 서울 거리 이동 |
| TB05 | 0:14–0:20 | `00:23.5–00:28.5` | 물가에 앉은 사람들 | 그런데 이름조차 읽기 어려운 이 물길에서, 사람들은 아무도 서 있지 않았습니다. | 물가에 앉은 사람들 |
| TB06 | 0:20–0:28 | `00:16–00:23.5` | 청계천 전경 | 두 사람은 73개국 만에 처음으로 신발을 벗고 앉았습니다. | 청계천 전경 |
| TB07 | 0:28–끝 | `00:28.5–00:32.5` | 웃는 셀피 | 서울이 준 첫 명소는 장소가 아니라, 앉아도 된다는 자세였습니다. | 웃는 셀피 |

### 편집 원칙

- source range는 서사 수정안 값을 그대로 사용했다. 임의로 바꾸지 않는다.
- 정확 source in/out은 Stage 05에서 프레임 경계를 잠근 뒤 확정한다. SB01 내부의 발 장면/몽타주 경계는 프레임 재확인이 필요하다.

## 7. 전체 A9 작가 나레이션

> 73개국을 돌아온 두 사람의 사진에는 공통점이 하나 있었습니다.
> 전부 서서 찍은 사진이라는 것.
> 다음 장소가 늘 기다리고 있었으니까요.
> 서울에 도착한 첫날 계획도 같았습니다.
> 그런데 이름조차 읽기 어려운 이 물길에서, 사람들은 아무도 서 있지 않았습니다.
> 두 사람은 73개국 만에 처음으로 신발을 벗고 앉았습니다.
> 서울이 준 첫 명소는 장소가 아니라, 앉아도 된다는 자세였습니다.

## 8. T1·T2·A9_TEXT·STATE

```text
T1: 73개국에서 한 번도 안 한 행동
T2: 서울에서 처음 했습니다
```

### A9_TEXT (7개, 컷 수와 동일)

- `사진의 공통점`
- `전부 서서 찍음`
- `다음 장소가 있었다`
- `서울 첫날도 같은 계획`
- `아무도 서 있지 않다`
- `처음으로 앉았다`
- `앉아도 된다는 허락`

### STATE (7개, 컷 수와 동일)

- `발만 보이는 클로즈업`
- `발음 시도하는 표정`
- `여행 몽타주`
- `서울 거리 이동`
- `물가에 앉은 사람들`
- `청계천 전경`
- `웃는 셀피`

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

새 A9는 TB01~TB07 전 컷에 존재한다. 원본 발화를 CapCut 음원으로 쓰지 않는다. 원본 VIDEO는 전부 mute하고 A9 새 작가 나레이션만 사용하며 A10·A11·A12는 비운다.

- 실제 보이스를 생성해 길이를 측정하기 전 target time과 자막 경계를 확정하지 않는다.

## 10. 취약점·실패 조건

- SB01 내부 발 장면과 여행 몽타주의 정확한 경계는 Stage 05 전 프레임 단위로 재확인이 필요하다.
- 신발을 벗었다는 서술은 경계표 4절에서 삭제했다. 이후 어떤 구간에도 다시 넣지 않는다.
- 원본표의 coarse beat 경계는 ±1초 수준이므로 현재 source range를 확정된 값으로 보고하지 않는다.

## 11. Stage 04 독립성 자체 검토

| 검토축 | 상태 | 근거 |
|---|---|---|
| 메시지 독립성 | PASS 후보 | 새 반전(습관·예외)이 원본 요약이 아님 |
| 서사 독립성 | PASS 후보 | 주인공·미해결 질문·반전·결말 재구성 |
| 정보 순서 변형 | PASS 후보 | `SB01a > SB03 > SB01b > SB02 > SB05 > SB04 > SB06` |
| A9 독립 대본 | PASS 후보 | 새 작가 나레이션 |
| VIDEO-대본 정렬 | CONDITIONAL PASS | Stage 05 프레임 경계 잠금 필요 |
| 사실·창작 경계 | PASS 후보 | 신발 서술 삭제로 경계 정합성 개선 |
| 사용자 승인 | WAIT | 승인 전 확정 금지 |

## 12. 사용자 승인 체크포인트

1. 새 반전(사진 습관·예외)이 이 원본에 맞는가.
2. 전체 A9 나레이션의 문체와 감정 강도가 맞는가.
3. 제안한 target VIDEO order로 Stage 05 설계를 진행해도 되는가.

```text
CURRENT_STATUS=WAIT_USER_URAKKAI_APPROVAL
NEXT_ON_APPROVAL=STAGE_05_FINAL_DESIGN_LOCK
NEXT_ON_REVISION=STAGE_03_SAME_DRAFT_REWORK
```
