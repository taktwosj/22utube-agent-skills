```text
BLOCKED_PENDING_SOURCE_RECHECK
- 화면 인물이 1인인가 2인인가
- Lv.1 / Lv.999 표기가 상승 순번인가 (순번이면 재배열 금지)
이 두 건 확인 전 Stage 05 진행 금지
```

# 02_jenrMvVbYcE_MARA_STAGE03_URAKKAI_REV1

## 잠정 결론

**선택 추천안: `김치 앞에서 겁쟁이였던 남자`（1인 2막 구조, 프레임 확인 전 미확정）**

본 개정본은 `11_STAGE04_REVISION_ORDER_20260806.md`와 `13_CLAUDE_URAKKAI_REVISION_20260806.md`를 반영한 개정 초안이다. 기존 "두 번째 요원" 구조는 원본에 존재 근거가 없는 인물을 전제로 하고 있었음이 검토에서 드러났다. 본 개정본은 1인 2막 구조를 권장안으로 제시하나, 화면 인물 수와 Lv 표기 확인 전에는 어느 구조도 확정할 수 없다.

```text
owner_skill=001short-production-agent
stage=03_MARA_CREATIVE_URAKKAI
SOURCE_MEDIA_STATUS=VERIFIED
ORIGINAL_CAPCUT_GRID_STATUS=READY_FOR_REVIEW
MARA_MESSAGE_STATUS=DRAFT_READY
CREATIVE_PREMISE_STATUS=BLOCKED_PENDING_SOURCE_RECHECK
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
| episode_id | `jenrMvVbYcE` |
| 원본 표시명 | 김치 봉지·병을 폭발물처럼 다루는 반응 편집 |
| 원본표 | `01_jenrMvVbYcE_ORIGINAL_CAPCUT_GRID.md` |
| 원본 media SHA-256 | `fc9faf96ee954800e2c7b59d4597207a5e493bd05a5b930992ceb1481a074950` |
| 원본 길이 | `35.712s` |
| target 길이 | `[EST] 27~32초` |
| 댓글 자료 | `NOT_PROVIDED` |
| 사용자 승인 | `WAIT` |

## 1. 원본이 가진 힘

### MARA_MESSAGE

> **준비가 과해 보이는 순간에도 위험을 이해한 사람만이 침착하게 끝낼 수 있다.**

### 감정 이동

`비웃음 → 긴장 → 안도 → 자만 → 즉시 응징되는 코미디`

## 2. 개정 사유

기존 설계 전체가 "첫 번째 요원 vs 두 번째 요원" 대비였는데, 원본표 Beat 분할표는 SB01~SB06 전부 `남성` 1인이며, 원본표 3절은 "인물들 사이의 가족관계"를 미확인으로 명시했다. 화면 자막은 "엄마 왜 그래요?"다. 두 번째 인물의 존재 근거가 없다. 기존 경계표는 "두 인물을 같은 조직의 요원으로 설정"만 창작으로 분류해 인물이 2인이라는 사실 자체를 전제해 버린 문제가 있었다.

권장 수정: 1인 2막 구조. 매뉴얼을 지킨 그가 성공한 뒤, 방심한 같은 그가 3분 뒤에 당한다.

## 3. 선택안 서사 계약

| 항목 | 설계 |
|---|---|
| 주인공 | 발효식품 앞에 선 한 남자 (1인, 프레임 확인 전 미확정) |
| 목표 | 압력이 찬 김치를 사고 없이 개봉한다 |
| 미해결 질문 | 겁쟁이처럼 보이던 그가 정말 겁쟁이였을까 |
| 반전 | 매뉴얼을 지켜 성공한 그가, 3분 뒤 방심하여 같은 인물에게 당한다 |
| 결말 | 김치가 살려준 건 용감한 그가 아니라, 3분 전의 겁 많던 그였다 |
| 한 줄 | **김치 앞에서 겁쟁이였던 남자가, 3분 뒤에 옳았습니다.** |
| resolution_type | `TRANSFORM_CANDIDATE` |
| creative_label（비계약） | `COMEDIC_RULE_PROOF` |

## 4. SOURCE_OBSERVATION / FICTIONAL_RECONSTRUCTION 경계

| 분류 | 내용 | 사용 규칙 |
|---|---|---|
| SOURCE_OBSERVATION | 부푼 김치 봉지 | 원본표 근거 |
| SOURCE_OBSERVATION | 냄비뚜껑을 방패로 들고 가위로 절단 | 원본표 근거 |
| SOURCE_OBSERVATION | 봉지의 가스가 빠지며 첫 시도 성공 | 원본표 근거 |
| SOURCE_OBSERVATION | 김치병을 손으로 열다 내용물이 쏟아짐 | 원본표 근거 |
| FICTIONAL_RECONSTRUCTION | 김치 연구소·안전교육이라는 세계관 설정 | 창작 설정 |
| FICTIONAL_RECONSTRUCTION | 1차 성공 후 자만했다는 동기 | 창작 설정 — 신규 등재 |
| ~~FICTIONAL_RECONSTRUCTION: 두 인물을 같은 조직의 요원으로 설정~~ | **삭제** — 인물 수 미확인 상태에서 2인 전제를 경계표에 등재하는 것 자체가 사실 승격 오류였다 | 서사 수정안 반영 |

## 5. 구조 변형 계약

```text
source_order_signature=원본표의 SB 오름차순
target_order_signature=SB06a > SB01 > SB02 > SB03 > SB04 > SB05 > SB06b
source_structure_pattern=SP_STATE_DEPENDENT_PROCESS_TO_RESULT
remake_structure_pattern=DST_RESULT_FIRST_PROCESS_REENTRY  # 舊 산문: 실패 결과 0.7초 훅 → 안전장비 소개 → 위험 증거 → 절차 실행 → 성공 → 자만한 재도전 → 최종 응징
resolution_type=TRANSFORM_CANDIDATE
execution_strategy=full_tts
baked_order_semantics=UNVERIFIED  # Lv.1/Lv.999 동시 표기. 상승 순번이면 재배열 시 거짓 정보. 확인 전 재배열 확정 금지
dialogue_dependency=NONE
```

## 6. Target VIDEO order + CapCut 세로 설계

| Target | Source range | 화면 | A9 |
|---|---|---|---|
| TB01 | `00:28.2–00:29.2` | 김치가 손 위로 쏟아지는 0.8초 | 이 사고는 3분 전에 이미 예고돼 있었습니다. |
| TB02 | `00:00–00:04` | 냄비뚜껑·가위·부푼 봉지 | 그는 김치 봉지 하나를 열려고 방패와 절단 도구를 준비했습니다. |
| TB03 | `00:04–00:10` | 부푼 봉지, 긴장한 표정 | 우스워 보이지만 이유가 있었습니다. 부푼 봉지 안은 이미 압력이 차 있었으니까요. |
| TB04 | `00:10–00:18.2` | 방패 뒤에서 가위 끝만 | 그는 얼굴을 최대한 멀리 두고 가위 끝만 내밀었습니다. |
| TB05 | `00:18.2–00:21.7` | 바람 빠지고 도구 내려놓음 | 가스가 빠지고, 첫 번째 김치는 조용히 끝났습니다. |
| TB06 | `00:21.7–00:28.2` | 유리병을 맨손으로 돌림 | 그리고 그는 방패를 내려놨습니다. 병 하나쯤은 맨손이면 된다고 생각했죠. |
| TB07 | `00:29.2–00:35.7` | 쏟아짐, 수습 | 김치가 살려준 건 용감한 그가 아니라, 3분 전의 겁 많던 그였습니다. |

### 편집 원칙

- source range는 서사 수정안 값을 그대로 사용했다.
- 위 target order와 1인 2막 전제는 화면 인물 수 확인 전까지 잠정안이다. 2인으로 확인되면 경계표에 `FICTIONAL_RECONSTRUCTION: 등장인물이 2인이라는 설정`을 등재하고 원 구조(두 요원 대비)로 되돌린다.

## 7. 전체 A9 작가 나레이션

> 이 사고는 3분 전에 이미 예고돼 있었습니다.
> 그는 김치 봉지 하나를 열려고 방패와 절단 도구를 준비했습니다.
> 우스워 보이지만 이유가 있었습니다. 부푼 봉지 안은 이미 압력이 차 있었으니까요.
> 그는 얼굴을 최대한 멀리 두고 가위 끝만 내밀었습니다.
> 가스가 빠지고, 첫 번째 김치는 조용히 끝났습니다.
> 그리고 그는 방패를 내려놨습니다. 병 하나쯤은 맨손이면 된다고 생각했죠.
> 김치가 살려준 건 용감한 그가 아니라, 3분 전의 겁 많던 그였습니다.

## 8. T1·T2·A9_TEXT·STATE

```text
T1: 김치 앞에서 겁쟁이였던 남자
T2: 3분 뒤에 옳았습니다
```

### A9_TEXT (7개, 컷 수와 동일)

- `3분 전 예고된 사고`
- `방패와 가위 준비`
- `이미 압력 찬 상태`
- `가위 끝만 내밀다`
- `첫 김치 조용히 끝`
- `맨손이면 충분하다 생각`
- `3분전 겁쟁이가 살렸다`

### STATE (7개, 컷 수와 동일)

- `쏟아지는 순간`
- `냄비뚜껑과 가위`
- `부푼 봉지`
- `방패 뒤 절단`
- `바람 빠짐`
- `병 뚜껑 맨손 개봉`
- `수습하는 손`

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

원본 VIDEO는 전부 mute한다. A9 새 작가 나레이션만 사용하고 A10·A11·A12는 비운다.

## 10. 취약점·실패 조건

- **선행 확인 2건 — 확정 전 필수:**
  1. 화면 인물이 1인인가 2인인가. 2인이면 기존 두 요원 구조도 가능하다.
  2. `Lv.1` / `Lv.999` 표기가 상승 순번인가. 순번이면 재배열 시 `Lv.999`가 먼저 나와 거짓 정보가 된다.
- 원본의 Lv.1/Lv.999 게임 UI를 그대로 중심 장치로 쓰면 원본 메시지에 가까워진다.
- 원본표의 coarse beat 경계는 ±1초 수준이므로 현재 source range를 확정된 값으로 보고하지 않는다.

## 11. Stage 04 독립성 자체 검토

| 검토축 | 상태 | 근거 |
|---|---|---|
| 메시지 독립성 | PASS 후보 | 새 반전(자기 자신에게 당함)이 원본 요약이 아님 |
| 서사 독립성 | CONDITIONAL | 인물 수 확인 전 미확정 |
| 정보 순서 변형 | PASS 후보 | `SB06a > SB01 > SB02 > SB03 > SB04 > SB05 > SB06b` |
| baked_order_semantics | BLOCKED | Lv 표기 확인 필요 |
| 사용자 승인 | WAIT | 승인 전 확정 금지, 프레임 확인 선행 |

## 12. 사용자 승인 체크포인트

1. 1인 2막 구조와 2인 대비 구조 중 어느 쪽으로 프레임을 확인할지.
2. 위 두 건 확인 후 결말과 A9 나레이션이 맞는지.
3. 제안한 target VIDEO order를 프레임 확인 후 Stage 05로 넘길지.

```text
CURRENT_STATUS=WAIT_USER_URAKKAI_APPROVAL
NEXT_ON_APPROVAL=STAGE_05_FINAL_DESIGN_LOCK（단, BLOCKED_PENDING_SOURCE_RECHECK 2건 해소 후에만）
NEXT_ON_REVISION=STAGE_03_SAME_DRAFT_REWORK
```
