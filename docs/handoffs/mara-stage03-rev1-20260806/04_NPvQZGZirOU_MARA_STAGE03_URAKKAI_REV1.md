# 04_NPvQZGZirOU_MARA_STAGE03_URAKKAI_REV1

## 잠정 결론

**선택 추천안: `악역에게만 한국어를 배운 여자`（컨셉 유지, 훅만 교체）**

본 개정본은 `11_STAGE04_REVISION_ORDER_20260806.md`와 `13_CLAUDE_URAKKAI_REVISION_20260806.md`를 반영한 개정 초안이다. 컨셉은 원안을 그대로 유지한다. 훅이 결말과 동일한 2초 구간을 재사용하던 문제만 고쳤다. 이 회차는 실제 한국어 발화가 콘텐츠의 핵심이라 나레이션으로 덮지 않는다.

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
AUDIO_POLICY=A10_RETAINED_SYNC
URAKKAI_STATUS=WAIT_USER_URAKKAI_APPROVAL
REVISION=REV1_20260806
```

## 0. Source of Truth

| 항목 | 값 |
|---|---|
| episode_id | `NPvQZGZirOU` |
| 원본 표시명 | K-드라마로 한국어를 배운 여성이 한국인에게 말을 거는 영상 |
| 원본표 | `01_NPvQZGZirOU_ORIGINAL_CAPCUT_GRID.md` |
| 원본 media SHA-256 | `7ac6e570a8d8d2c05385c708178a7075793c04323e61793e1607ad7fe5bf29da` |
| 원본 길이 | `54.059s` |
| target 길이 | `[EST] 38~44초` |
| 댓글 자료 | `NOT_PROVIDED` |
| 사용자 승인 | `WAIT` |

## 1. 원본이 가진 힘

### MARA_MESSAGE

> **언어 실력은 완벽한 문법보다 낯선 사람에게 실제로 말을 거는 용기에서 증명된다.**

## 2. 개정 사유

기존 설계는 훅(舊 TB01)에서 결말과 같은 2초 구간(`00:46.0–00:48.0`)을 그대로 다시 썼다. 갱신본 조항상 훅 beat를 본문에서 그대로 반복하면 `URAKKAI_STRUCTURE_UNCHANGED`로 취급된다. 훅을 손동작 시연 컷 `00:38–00:38.8`로 교체하고, 본문 TB07은 결말 잔여 구간을 온전히 사용하도록 재배치했다.

## 3. 선택안 서사 계약

| 항목 | 설계 |
|---|---|
| 주인공 | K-드라마만으로 한국어를 익힌 여성 |
| 목표 | 실제 한국인 앞에서 자신의 한국어가 통하는지 확인한다 |
| 미해결 질문 | 드라마 악역 대사도 실제 한국어 시험에서 통할까 |
| 반전 | 평범한 인사 대신 위협적인 대사를 했지만 상대는 놀란 뒤 실력을 높게 평가한다 |
| 결말 | 시험은 통과했지만 다음 교재는 로맨스 드라마가 필요하다 |
| 한 줄 | **악역에게만 한국어를 배운 여자, 첫 실전 점수는?** |
| resolution_type | `TRANSFORM_CANDIDATE` |
| creative_label（비계약） | `PERFORMANCE_PAYOFF` |

## 4. SOURCE_OBSERVATION / FICTIONAL_RECONSTRUCTION 경계

| 분류 | 내용 | 사용 규칙 |
|---|---|---|
| SOURCE_OBSERVATION | K-드라마로 한국어를 배웠다는 설명 | 원본표 근거 |
| SOURCE_OBSERVATION | 실제 한국인을 찾아 말을 검 | 원본표 근거 |
| SOURCE_OBSERVATION | 부탁 후 드라마식 강한 문장 시연 | 원본표 근거 |
| SOURCE_OBSERVATION | 상대의 놀람·칭찬·마지막 작별 | 원본표 근거 |
| FICTIONAL_RECONSTRUCTION | K-드라마 악역들을 한국어 선생님으로 의인화 | 창작 설정 |
| FICTIONAL_RECONSTRUCTION | 길에서 만난 한국인을 즉석 시험관으로 임명 | 창작 설정 |
| FICTIONAL_RECONSTRUCTION | 상대 반응을 점수로 환산, 다음 교재가 로맨스라는 결말 농담 | 창작 설정 |

## 5. 구조 변형 계약

```text
source_order_signature=원본표의 SB 오름차순
target_order_signature=SB05a(00:38-38.8) > SB01 > SB02 > SB03 > SB04 > SB05 > SB06(잔여, 00:38.8-46) > SB05b(잔여)
source_structure_pattern=SP_INTERACTION_ESCALATION_TO_REVERSAL
remake_structure_pattern=DST_REVERSAL_FIRST_INTERACTION_RECOMPOSITION  # 舊 산문: 좋은 평가 반응 훅 → 이상한 교재 공개 → 시험 결심 → 시험관 발견 → 시험 조건 설명 → 대사 수행 → 점수·작별
resolution_type=TRANSFORM_CANDIDATE
execution_strategy=narration_plus_speaker
baked_order_semantics=NONE
dialogue_dependency=INDIVISIBLE_DIALOGUE_BUNDLE  # "한국분이세요?"→답, 시연→평가 묶음이 깨지면 실패
```

## 6. Target VIDEO order + CapCut 세로 설계

| Target | Source range | 화면 | A9 / 원본음 | A9 | A10 |
|---|---|---|---|---|---|
| TB01 | `00:38–00:38.8` | 손동작 크게 쓰는 0.8초. 대사는 안 들려줌 | A9 — 이 문장 하나가 오늘의 시험 문제였습니다. | ON | OFF |
| TB02 | `00:00–00:06` | 실내 셀피 | A9 — 그녀의 한국어 선생님들은 늘 누군가에게 복수하고 있었습니다. | ON | OFF |
| TB03 | `00:06–00:17` | 거리에서 계획 말함 | A9 — 교과서도 학원도 없이 악역 대사만 외운 그녀는 실전시험을 결심했습니다. | ON | OFF |
| TB04 | `00:17–00:24` | 상대에게 말 거는 장면 | **원본음 유지 / A9 없음** | OFF | ON |
| TB05 | `00:24–00:38` | 부탁·학습 경로 설명 | **원본음 유지 / A9 없음** | OFF | ON |
| TB06 | `00:38.8–00:46` | 드라마식 문장 시연 | **원본음 유지 / A9 없음** | OFF | ON |
| TB07 | `00:46–00:48` | 상대의 평가, 놀란 반응 | A9 — 잠시 정적 뒤에 돌아온 답은 칭찬이었습니다. | ON | OFF |
| TB08 | `00:48–00:54` | 웃으며 작별 | A9 — 시험은 통과했습니다. 다만 다음 교재는 로맨스가 필요해 보입니다. | ON | OFF |

### 편집 원칙

- TB04~TB06은 대화 의존성 `INDIVISIBLE_DIALOGUE_BUNDLE`로 묶여 있으므로 압축하지 않고 원본 길이를 유지한다.
- A9=ON과 A10=ON이 동시인 구간은 0개다.
- source range는 서사 수정안 값을 그대로 사용했다.

## 7. 전체 A9 작가 나레이션 (A9 구간만)

> 이 문장 하나가 오늘의 시험 문제였습니다.
> 그녀의 한국어 선생님들은 늘 누군가에게 복수하고 있었습니다.
> 교과서도 학원도 없이 악역 대사만 외운 그녀는 실전시험을 결심했습니다.
> (TB04~TB06 원본음 구간)
> 잠시 정적 뒤에 돌아온 답은 칭찬이었습니다.
> 시험은 통과했습니다. 다만 다음 교재는 로맨스가 필요해 보입니다.

## 8. T1·T2·A9_TEXT·STATE

```text
T1: 악역에게만 한국어를 배운 여자
T2: 첫 실전 점수는?
```

### A9_TEXT (5개 — 원본음 전용 컷 TB04~TB06은 A9 없음이므로 A9_TEXT 없음)

- `오늘의 시험 문제` (TB01)
- `선생님은 전부 악역` (TB02)
- `실전시험 결심` (TB03)
- `정적 뒤 칭찬` (TB07)
- `합격, 다음은 로맨스` (TB08)

### STATE (8개, 컷 수와 동일)

- `손동작 크게`
- `실내 셀피`
- `거리에서 계획 말함`
- `말 거는 장면`
- `부탁·설명`
- `드라마 대사 시연`
- `놀란 반응`
- `웃으며 작별`

## 9. 오디오 정책

```text
AUDIO_POLICY=A10_RETAINED_SYNC
A12=RESERVED_EMPTY
```

"한국분이세요?", 부탁 장면, 드라마식 한국어 문장, 상대의 평가·마지막 감사 발화를 유지 후보로 둔다. TB04~TB06은 A9 없이 A10만 사용한다. Stage 07에서 Demucs vocal stem과 VIDEO/A10 동기를 검증한다.

## 10. 취약점·실패 조건

- 클라이맥스(TB06)의 실제 한국어 문장을 A9가 덮으면 와우포인트가 사라진다. A9를 멈추고 검증된 vocal stem A10을 전면에 둔다.
- TB04~TB06을 다른 위치로 옮기면 질문→답 묶음이 깨진다. 대화 의존성 계약 위반.
- 훅(TB01, `00:38–00:38.8`)을 본문에서 제외했으므로 시연 동작의 시작 프레임이 잘리지 않는지 Stage 05에서 확인한다. TB06을 `00:38.8–00:46`으로 좁혔으므로 손동작 시연의 초입 0.8초가 자연스럽게 이어지는지 실제 프레임으로 재검증이 필요하다.
- 원본표의 coarse beat 경계는 ±1초 수준이므로 현재 source range를 확정된 값으로 보고하지 않는다.

## 11. Stage 04 독립성 자체 검토

| 검토축 | 상태 | 근거 |
|---|---|---|
| 메시지 독립성 | PASS 후보 | 새 관점·감정 보상 사용 |
| 서사 독립성 | PASS 후보 | 주인공·미해결 질문·반전·결말 유지, 훅만 교체 |
| 정보 순서 변형 | PASS 후보 | 훅·본문 range 분리 완료 |
| 대화 의존성 | PASS 후보 | INDIVISIBLE_DIALOGUE_BUNDLE 유지 |
| 사용자 승인 | WAIT | 승인 전 확정 금지 |

## 12. 사용자 승인 체크포인트

1. 훅 교체(손동작 0.8초)가 이 원본에 맞는가.
2. A9/A10 트랙 분리가 맞는가.
3. 제안한 target VIDEO order로 Stage 05 설계를 진행해도 되는가.

```text
CURRENT_STATUS=WAIT_USER_URAKKAI_APPROVAL
NEXT_ON_APPROVAL=STAGE_05_FINAL_DESIGN_LOCK
NEXT_ON_REVISION=STAGE_03_SAME_DRAFT_REWORK
```
