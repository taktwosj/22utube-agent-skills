# 03_JER7q6xk4eI_MARA_STAGE03_URAKKAI_REV1

## 잠정 결론

**선택 추천안: `한국 도착 11분`**

본 개정본은 `11_STAGE04_REVISION_ORDER_20260806.md`와 `13_CLAUDE_URAKKAI_REVISION_20260806.md`를 반영한 개정 초안이다. 기존 훅이 "화장실이 첫 관광지"라는 결론을 먼저 말해버려 이후 39초 동안 미해결 질문이 없었다. 훅을 표지판 앞에서 멈춘 얼굴로 교체했다.

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
| episode_id | `JER7q6xk4eI` |
| 원본 표시명 | 처음 한국에 도착한 여성의 공항철도 이용기 |
| 원본표 | `01_JER7q6xk4eI_ORIGINAL_CAPCUT_GRID.md` |
| 원본 media SHA-256 | `1283a64e427a3b9fef720a42c7a080135af3308b0b58464275b5d80b128b27fc` |
| 원본 길이 | `57.920s` |
| target 길이 | `[EST] 36~42초` |
| 댓글 자료 | `NOT_PROVIDED` |
| 사용자 승인 | `WAIT` |

## 1. 원본이 가진 힘

### MARA_MESSAGE

> **낯선 나라의 첫인상은 관광지가 아니라, 지친 사람도 혼자 목적지에 도착하게 해주는 시스템에서 만들어진다.**

## 2. 개정 사유

기존 훅(TB01)이 "화장실이 첫 관광지"라고 결론을 먼저 말한 뒤 TB08에서 같은 정보를 반전으로 다시 썼다. 그 사이 39초 동안 미해결 질문이 없어 훅이 답을 선소비하는 구조였다. 훅을 `표지판 앞에서 멈춘 얼굴`로 교체하고, 훅 구간과 본문 구간이 겹치지 않도록 재구성했다.

## 3. 선택안 서사 계약

| 항목 | 설계 |
|---|---|
| 주인공 | 잠을 거의 자지 못하고 한국에 혼자 도착한 첫 여행자 |
| 목표 | 아무한테도 안 묻고 서울행 열차를 찾을 것 |
| 미해결 질문 | 도착 11분째 그녀는 왜 아직 공항을 못 나가고 있을까 |
| 반전 | 미션을 끝낸 뒤 그녀가 가장 오래 들여다본 곳은 열차 화장실이었다 |
| 결말 | 관광지에 닿기도 전에, 한국은 이미 점수를 따냈다 |
| 한 줄 | **한국 도착 11분, 그녀는 아직 공항을 못 나갔습니다.** |
| resolution_type | `TRANSFORM_CANDIDATE` |
| creative_label（비계약） | `MISSION_COMPLETE_UNEXPECTED_SCORE` |

## 4. SOURCE_OBSERVATION / FICTIONAL_RECONSTRUCTION 경계

| 분류 | 내용 | 사용 규칙 |
|---|---|---|
| SOURCE_OBSERVATION | 혼자 길을 찾아야 한다는 화면 자막 | 원본표 근거 |
| SOURCE_OBSERVATION | 버스·철도 표지와 직통열차 발견 | 원본표 근거 |
| SOURCE_OBSERVATION | 발권기에서 표 구매·출력 | 원본표 근거 |
| SOURCE_OBSERVATION | 열차 좌석·화장실·창밖 풍경에 대한 반응 | 원본표 근거 |
| FICTIONAL_RECONSTRUCTION | 공항을 탈출 게임·단서 미션으로 설정 | 창작 설정 |
| FICTIONAL_RECONSTRUCTION | 화장실을 첫 관광지·평가장소로 해석 | 창작 설정 |
| FICTIONAL_RECONSTRUCTION | "밤새 비행기에서 못 잔" 상태 | 창작 설정 — 신규 등재. 원본표 STATE는 `도착 선언·피로`까지만 확인되며 "밤새 비행기·한숨도 못 잔"은 원본 미확인 |

## 5. 구조 변형 계약

```text
source_order_signature=원본표의 SB 오름차순
target_order_signature=SB02(00:12-14) > SB01 > SB02(00:07.6-12) > SB03 > SB04 > SB05 > SB06a > SB06b > SB07
source_structure_pattern=SP_STATE_DEPENDENT_PROCESS_TO_RESULT
remake_structure_pattern=DST_RESULT_FIRST_PROCESS_REENTRY  # 舊 산문: 의외의 최종 평가장소 훅 → 성공 증거 → 도착으로 회귀 → 미션·단서 → 발권 → 탑승 → 화장실 반전 → 창밖으로 감정 해소
resolution_type=TRANSFORM_CANDIDATE
execution_strategy=full_tts
baked_order_semantics=NONE
dialogue_dependency=NONE
```

## 6. Target VIDEO order + CapCut 세로 설계

| Target | Source range | 화면 | A9 |
|---|---|---|---|
| TB01 | `00:12–00:14` | 표지판 앞에서 멈춘 얼굴 | 한국 도착 11분, 그녀는 아직 공항을 못 나가고 있었습니다. |
| TB02 | `00:00–00:07.6` | 수하물·무빙워크 셀피 | 밤새 비행기에서 못 잔 채로, 목표는 하나였습니다. |
| TB03 | `00:07.6–00:12` | 홀에서 표지판 찾기 | 아무한테도 안 묻고 서울행 열차를 찾을 것. |
| TB04 | `00:16–00:23.5` | 색상 표지·직통열차 카운터 | 첫 단서는 색깔, 두 번째는 직통열차라는 글자였습니다. |
| TB05 | `00:23.5–00:31.7` | 매표창구·발권기 | 마지막 관문은 처음 보는 발권기. |
| TB06 | `00:31.7–00:40.2` | 표 출력 → 플랫폼 → 탑승 | 표 한 장이 나왔고, 미션은 거기서 끝난 줄 알았습니다. |
| TB07 | `00:40.2–00:46` | 좌석·통로 확인 | 그런데 열차에 타자 그녀가 확인하기 시작한 건 좌석이 아니었습니다. |
| TB08 | `00:46–00:49.5` | 화장실 공개 | 한국에서 그녀가 가장 오래 들여다본 첫 장소는, 열차 화장실이었습니다. |
| TB09 | `00:51.2–00:57.9` | 창밖 수변·편안한 셀피 | 관광지에 닿기도 전에, 한국은 이미 점수를 따냈습니다. |

### 편집 원칙

- 훅 `00:12–00:14`는 본문 TB03 `00:07.6–00:12`와 겹치지 않는다.
- 본문 TB08은 `00:40.2–00:49.5`로 훅 구간(`00:49.5–00:51.2`, 舊 TB01)과 분리했다.
- source range는 서사 수정안 값을 그대로 사용했다.

## 7. 전체 A9 작가 나레이션

> 한국 도착 11분, 그녀는 아직 공항을 못 나가고 있었습니다.
> 밤새 비행기에서 못 잔 채로, 목표는 하나였습니다.
> 아무한테도 안 묻고 서울행 열차를 찾을 것.
> 첫 단서는 색깔, 두 번째는 직통열차라는 글자였습니다.
> 마지막 관문은 처음 보는 발권기.
> 표 한 장이 나왔고, 미션은 거기서 끝난 줄 알았습니다.
> 그런데 열차에 타자 그녀가 확인하기 시작한 건 좌석이 아니었습니다.
> 한국에서 그녀가 가장 오래 들여다본 첫 장소는, 열차 화장실이었습니다.
> 관광지에 닿기도 전에, 한국은 이미 점수를 따냈습니다.

## 8. T1·T2·A9_TEXT·STATE

```text
T1: 한국 도착 11분
T2: 아직 공항을 못 나갔습니다
```

### A9_TEXT (9개, 컷 수와 동일)

- `도착 11분째`
- `밤새 못 잔 채 도착`
- `혼자 열차 찾기`
- `단서는 색깔·글자`
- `낯선 발권기`
- `표 나왔다, 끝?`
- `좌석 아닌 걸 확인`
- `첫 관광지는 화장실`
- `관광 전에 이미 반함`

### STATE (9개, 컷 수와 동일)

- `표지판 앞 멈춘 얼굴`
- `수하물·무빙워크`
- `표지판 찾는 중`
- `색상 표지·카운터`
- `매표창구·발권기`
- `표 출력·탑승`
- `좌석·통로 확인`
- `화장실 공개`
- `창밖 풍경·셀피`

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

- "밤새 비행기에서 못 잔"은 원본 미확인 창작이며 4절 경계표에 등재했다. 제작 보고에서 원본 사실로 승격하지 않는다.
- 화장실 훅을 너무 길게 보여주면 중간 미션의 보상이 사라진다. 1~2초 반응만 사용하고 전체 공간 공개는 TB08에서 처음 완성한다.
- 원본표의 coarse beat 경계는 ±1초 수준이므로 현재 source range를 확정된 값으로 보고하지 않는다.

## 11. Stage 04 독립성 자체 검토

| 검토축 | 상태 | 근거 |
|---|---|---|
| 메시지 독립성 | PASS 후보 | 새 관점·감정 보상 사용 |
| 서사 독립성 | PASS 후보 | 훅이 답을 선소비하지 않도록 재구성 |
| 정보 순서 변형 | PASS 후보 | 훅·본문 range 분리 완료 |
| A9 독립 대본 | PASS 후보 | 새 작가 나레이션 |
| 사실·창작 경계 | PASS 후보 | "밤새 못 잔" 창작 등재 완료 |
| 사용자 승인 | WAIT | 승인 전 확정 금지 |

## 12. 사용자 승인 체크포인트

1. 훅 교체(표지판 앞 멈춤)가 이 원본에 맞는가.
2. 전체 A9 나레이션 문체·감정 강도가 맞는가.
3. 제안한 target VIDEO order로 Stage 05 설계를 진행해도 되는가.

```text
CURRENT_STATUS=WAIT_USER_URAKKAI_APPROVAL
NEXT_ON_APPROVAL=STAGE_05_FINAL_DESIGN_LOCK
NEXT_ON_REVISION=STAGE_03_SAME_DRAFT_REWORK
```
