# 06_SlCAxcySf6A_MARA_STAGE03_URAKKAI_REV1

## 잠정 결론

**선택 추천안: `한국 친구가 못 견딘 두 가지`（전제 전면 교체）**

본 개정본은 `11_STAGE04_REVISION_ORDER_20260806.md`와 `13_CLAUDE_URAKKAI_REVISION_20260806.md`를 반영한 개정 초안이다. 舊안의 "입국장에서 압수당했다"는 전제를 뒷받침할 화면이 원본에 0컷이었다(전 Beat가 자동차 안 셀피). 원본에 실재하는 "한국 친구 사례"를 축으로 전제를 완전히 교체했다.

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
| episode_id | `SlCAxcySf6A` |
| 원본 표시명 | 벨기에의 에어컨·아이스커피 부족을 한국과 비교하는 여성 |
| 원본표 | `01_SlCAxcySf6A_ORIGINAL_CAPCUT_GRID.md` |
| 원본 media SHA-256 | `792230fe795b29466a901b99878c6ea7843afb9c97b3ca1902f0d4e84b197cf9` |
| 원본 길이 | `58.645s` |
| target 길이 | `[EST] 34~40초` |
| 댓글 자료 | `NOT_PROVIDED` |
| 사용자 승인 | `WAIT` |

## 1. 원본이 가진 힘

### MARA_MESSAGE

> **사람이 어느 문화에 적응했는지는 좋아하는 것보다, 고향에 돌아왔을 때 무엇이 없어서 견디기 힘든지에서 드러난다.**

## 2. 개정 사유

舊안의 핵심 전제(입국장에서 습관을 압수당했다)를 뒷받침할 화면이 원본에 없다. 전 Beat가 자동차 안 셀피이며 공항·입국장·세관 장면은 0컷이다. 갱신본 훅 조건("화면만 보아도 무엇이 달라졌는가")을 충족하지 못한다. 원본에 실재하는 "한국 친구가 벨기에에서 겪은 문화충격" 사례로 전제를 교체했다 — 손가락으로 항목을 세는 동작(SB04)이 체크리스트를 화면으로 지지한다.

## 3. 선택안 서사 계약

| 항목 | 설계 |
|---|---|
| 주인공 | 한국 생활에 익숙해진 뒤 고향 벨기에로 돌아온 여성 |
| 목표 | (교체) 한국 친구가 벨기에에서 못 견딘 두 가지를 설명한다 |
| 미해결 질문 | 한국 친구가 벨기에에서 못 견딘 게 뭐였을까 |
| 반전 | 그 목록을 지금 읽고 있는 사람이 그녀 자신이다 |
| 결말 | 고향은 하나도 안 바뀌었다. 친구의 목록을 넘겨받은 건 그녀였다 |
| 한 줄 | **한국 친구가 못 견딘 두 가지, 이제 제 목록이 됐습니다.** |
| resolution_type | `TRANSFORM_CANDIDATE` |
| creative_label（비계약） | `REVERSE_CULTURE_IDENTITY_REVEAL` |

## 4. SOURCE_OBSERVATION / FICTIONAL_RECONSTRUCTION 경계

| 분류 | 내용 | 사용 규칙 |
|---|---|---|
| SOURCE_OBSERVATION | 한국 친구의 벨기에 문화 충격 설명 | 원본표 근거 |
| SOURCE_OBSERVATION | 벨기에의 에어컨 부족과 한국의 보편성 비교 | 원본표 근거 |
| SOURCE_OBSERVATION | 아이스커피가 없다는 직접 설명 | 원본표 근거 |
| SOURCE_OBSERVATION | 에스프레소+얼음+우유 주문 거절 경험 | 원본표 근거 |
| SOURCE_OBSERVATION | 아이스라떼를 들고 걷는 행복 표현 | 원본표 근거 |
| ~~FICTIONAL_RECONSTRUCTION: 입국장에서 습관을 압수한다는 설정~~ | **삭제** — 화면 근거 0컷, 새 전제 채택으로 대체 | 서사 수정안 반영 |
| ~~FICTIONAL_RECONSTRUCTION: 에어컨과 아이스라떼를 생존 장비로 의인화~~ | **삭제** — 같은 사유 | 서사 수정안 반영 |
| ~~FICTIONAL_RECONSTRUCTION: 고향에서 생존시험을 치른다는 구조~~ | **삭제** — 같은 사유 | 서사 수정안 반영 |
| FICTIONAL_RECONSTRUCTION | 몇 년 뒤 고향에서 친구의 목록을 넘겨받았다는 서사적 결론 | 창작 설정 — 신규 등재. 원본표는 친구 사례·본인 경험을 각각 사실로 제시할 뿐, "목록 승계"라는 연결은 창작 해석 |

## 5. 구조 변형 계약

```text
source_order_signature=원본표의 SB 오름차순
target_order_signature=SB02 > SB05 > SB03 > SB04 > SB01 > SB06
source_structure_pattern=SP_JUDGMENT_MOTIVE_REFRAME
remake_structure_pattern=DST_PROOF_FIRST_ASSUMPTION_AUDIT
resolution_type=TRANSFORM_CANDIDATE
execution_strategy=full_tts  # 舊 narration_plus_speaker에서 전환 — 고정 앵글이라 원본음 손실 없음, 길이 압축 자유
baked_order_semantics=NONE
dialogue_dependency=CONTEXTUAL  # 단독 화자, 사례→결론 연결
```

## 6. Target VIDEO order + CapCut 세로 설계

| Target | Source range | 화면 | A9 |
|---|---|---|---|
| TB01 | `00:05.5–00:14` | 한국 친구 방문 사례 설명 | 한국 친구가 벨기에에 왔을 때, 못 견디겠다고 한 게 두 가지 있었습니다. |
| TB02 | `00:38–00:50` | 컵 조합 손동작·답답한 표정 | 첫째, 시원한 곳이 없다. 둘째, 얼음 넣은 커피를 안 판다. |
| TB03 | `00:14–00:28` | 에어컨 없는 집·식당 설명 | 그때 그녀는 웃었습니다. 그 정도로 뭘. |
| TB04 | `00:28–00:38` | 손가락으로 사례 열거 | 한국에서는 지하철도 집도 당연히 시원했으니까요. |
| TB05 | `00:00–00:05.5` | 강한 불만 표정·삽입컷 | 그리고 몇 년 뒤, 고향에 돌아온 그녀는 카페에서 이렇게 말하고 있었습니다. |
| TB06 | `00:50–00:58.6` | 웃으며 아이스라떼 얘기 | 에스프레소에 얼음이랑 우유만 넣어주시면 되는데요. 고향은 그대로였고, 친구의 목록을 넘겨받은 건 그녀였습니다. |

### 편집 원칙

- source range는 서사 수정안 값을 그대로 사용했다. 舊안의 4-8-2 target 순서와 완전히 다르다.
- 고정 앵글(자동차 셀피)이므로 원본음을 버려도 시각적 손실이 없다.

## 7. 전체 A9 작가 나레이션

> 한국 친구가 벨기에에 왔을 때, 못 견디겠다고 한 게 두 가지 있었습니다.
> 첫째, 시원한 곳이 없다.
> 둘째, 얼음 넣은 커피를 안 판다.
> 그때 그녀는 웃었습니다. 그 정도로 뭘.
> 한국에서는 지하철도 집도 당연히 시원했으니까요.
> 그리고 몇 년 뒤, 고향에 돌아온 그녀는 카페에서 이렇게 말하고 있었습니다.
> 에스프레소에 얼음이랑 우유만 넣어주시면 되는데요.
> 고향은 하나도 안 바뀌었습니다. 친구의 목록을 넘겨받은 건 그녀였습니다.

## 8. T1·T2·A9_TEXT·STATE

```text
T1: 한국 친구가 못 견딘 두 가지
T2: 이제 제 목록이 됐습니다
```

### A9_TEXT (6개, 컷 수와 동일)

- `못 견딘 두 가지`
- `시원한 곳이 없다`
- `얼음 커피도 없다`
- `그땐 웃었다`
- `몇 년 뒤 고향에서`
- `이제 제 목록`

### STATE (6개, 컷 수와 동일)

- `친구 방문 사례 설명`
- `컵 조합 손동작`
- `에어컨 없는 집·식당`
- `손가락으로 사례 열거`
- `불만 표정·삽입컷`
- `웃으며 아이스라떼`

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

원안(A10_RETAINED_SYNC)에서 TTS_ONLY_MUTE_SOURCE로 전환했다. 고정 앵글이라 원본음을 버려도 손실이 없고 길이 압축이 자유로워진다. 지시서 1-6절 대상 회차 목록(02·03·05·07·08)에는 06이 명시돼 있지 않으나, 06도 이번 개정으로 TTS_ONLY 오디오 정책으로 전환되므로 clear_anchors 블록을 함께 추가했다. 이 판단은 보고서 하단 "자체 판단 목록"에 별도로 표기한다.

## 10. 취약점·실패 조건

- 전 Beat가 자동차 안 셀피 고정 앵글이므로 단순 컷 재배열만 하면 시각 변화가 약하다. TB05의 "두 가지" 그래픽 강조 등 정보 전달용 효과는 허용하되 남발하지 않는다.
- "몇 년 뒤 고향에서 목록을 넘겨받았다"는 서사적 연결이며 경계표에 창작으로 등재했다.
- 원본표의 coarse beat 경계는 ±1초 수준이므로 현재 source range를 확정된 값으로 보고하지 않는다.

## 11. Stage 04 독립성 자체 검토

| 검토축 | 상태 | 근거 |
|---|---|---|
| 메시지 독립성 | PASS 후보 | 새 전제가 원본 요약이 아님 |
| 서사 독립성 | PASS 후보 | 화면 근거 있는 전제로 재구성 |
| 정보 순서 변형 | PASS 후보 | `SB02 > SB05 > SB03 > SB04 > SB01 > SB06` |
| 사실·창작 경계 | PASS 후보 | 舊 창작 3건 삭제, 신규 창작 1건 등재 |
| 사용자 승인 | WAIT | 승인 전 확정 금지 |

## 12. 사용자 승인 체크포인트

1. 전제 전면 교체(입국장 압수 → 친구 목록 승계)가 이 원본에 맞는가.
2. 전체 A9 나레이션 문체·감정 강도가 맞는가.
3. 제안한 target VIDEO order와 TTS_ONLY 전환으로 Stage 05 설계를 진행해도 되는가.

```text
CURRENT_STATUS=WAIT_USER_URAKKAI_APPROVAL
NEXT_ON_APPROVAL=STAGE_05_FINAL_DESIGN_LOCK
NEXT_ON_REVISION=STAGE_03_SAME_DRAFT_REWORK
```
