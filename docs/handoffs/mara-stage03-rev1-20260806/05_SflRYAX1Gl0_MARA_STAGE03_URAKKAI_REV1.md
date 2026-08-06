# 05_SflRYAX1Gl0_MARA_STAGE03_URAKKAI_REV1

## 잠정 결론

**선택 추천안: `도둑을 잡으러 온 두 사람`**

본 개정본은 `11_STAGE04_REVISION_ORDER_20260806.md`와 `13_CLAUDE_URAKKAI_REVISION_20260806.md`를 반영한 개정 초안이다. 설계 자체는 양호했다. 훅 2초가 본문 구간 안에 그대로 들어 있던 문제와 "독일인" 미확인 서술만 고쳤다.

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
| episode_id | `SflRYAX1Gl0` |
| 원본 표시명 | 두 여성이 한국의 물건 방치 문화를 보고 놀라는 영상 |
| 원본표 | `01_SflRYAX1Gl0_ORIGINAL_CAPCUT_GRID.md` |
| 원본 media SHA-256 | `4ef11f17414221138f4fffe234da509534859aa80e9f50a144f117bb44acc895` |
| 원본 길이 | `45.547s` |
| target 길이 | `[EST] 32~38초` |
| 댓글 자료 | `NOT_PROVIDED` |
| 사용자 승인 | `WAIT` |

## 1. 원본이 가진 힘

### MARA_MESSAGE

> **신뢰가 높은 공간에서는 가장 강한 자물쇠가 물리 장치가 아니라 타인의 물건을 건드리지 않는 집단 규범처럼 보일 수 있다.**

## 2. 개정 사유

설계 자체는 좋다. 훅으로 쓴 `00:34–00:36` 2초 구간이 본문 舊 TB06(`00:30–00:38.8`) 안에 그대로 포함돼 있어 훅 beat 전체 반복 문제가 있었다. 본문 구간을 훅 이전/이후로 2분할했다.

## 3. 선택안 서사 계약

| 항목 | 설계 |
|---|---|
| 주인공 | 한국의 물건 방치 문화를 믿지 못하는 두 사람 |
| 목표 | 사람이 자리를 비우면 물건이 사라지는지 직접 증명한다 |
| 미해결 질문 | 누가 먼저 방치된 물건에 손을 댈까 |
| 반전 | 미끼를 늘리고 주변을 살펴도 범인은커녕 구경하는 사람도 나타나지 않는다 |
| 결말 | 가장 강한 자물쇠는 남의 물건에 관심을 두지 않는 태도였다 |
| 한 줄 | **도둑을 잡으러 온 두 사람, 범인이 나타나지 않았다.** |
| resolution_type | `TRANSFORM_CANDIDATE` |
| creative_label（비계약） | `INVESTIGATION_WITHOUT_CRIME` |

## 4. SOURCE_OBSERVATION / FICTIONAL_RECONSTRUCTION 경계

| 분류 | 내용 | 사용 규칙 |
|---|---|---|
| SOURCE_OBSERVATION | 비밀번호 장치 확인 | 원본표 근거 |
| SOURCE_OBSERVATION | 휴대폰을 두고 자리를 비우는 문제를 토론 | 원본표 근거 |
| SOURCE_OBSERVATION | 10년 된 휴대폰 농담 | 원본표 근거 |
| SOURCE_OBSERVATION | 야외에 가방·수건·옷이 다수 놓인 장면 | 원본표 근거 |
| SOURCE_OBSERVATION | 아무도 훔쳐가지 않는 것 같다는 반응 | 원본표 근거 |
| FICTIONAL_RECONSTRUCTION | 두 사람을 탐정으로 설정, 물건을 의도적 미끼로 해석 | 창작 설정 |
| FICTIONAL_RECONSTRUCTION | "독일인" | 창작 설정 — 신규 등재. 원본표는 `두 여성`까지만 확인되며 국적은 미확인 |

## 5. 구조 변형 계약

```text
source_order_signature=원본표의 SB 오름차순
target_order_signature=SB05(00:34-36) > SB01 > SB04 > SB02 > SB03 > SB05(00:30-34,00:36-38.8) > SB06
source_structure_pattern=SP_CLAIM_OR_QUESTION_TO_EVIDENCE_CHAIN
remake_structure_pattern=DST_PROOF_FIRST_EVIDENCE_RECONSTRUCTION  # 舊 산문: 대량 증거 훅 → 놀란 탐정 소개 → 약한 미끼 → 잠금장치 조사 → 도난 가설 → 더 큰 증거 → 범인 부재의 결론
resolution_type=TRANSFORM_CANDIDATE
execution_strategy=full_tts
baked_order_semantics=NONE
dialogue_dependency=NONE
```

## 6. Target VIDEO order + CapCut 세로 설계

| Target | Source range | 화면 | A9 |
|---|---|---|---|
| TB01 | `00:34–00:36` | 석축 위 물건 더미 | 이 많은 물건이 밖에 놓였는데, 사건은 일어나지 않았습니다. |
| TB02 | `00:00–00:05.6` | 놀란 두 사람 얼굴 | 두 사람은 그 이유를 직접 확인해 보기로 했습니다. |
| TB03 | `00:24.2–00:30` | 낡은 휴대폰 클로즈업 | 첫 번째 미끼는 10년 된 휴대폰. 너무 약한 미끼일 수 있었죠. |
| TB04 | `00:05.6–00:15.9` | 비밀번호 장치 | 그래서 잠금장치와 주변 동선까지 확인했습니다. |
| TB05 | `00:15.9–00:24.2` | 손짓하며 토론 | 고향이라면 자리를 비운 순간 사라질 거라고 했습니다. |
| TB06 | `00:30–00:34` + `00:36–00:38.8` | 주변을 둘러봄 → 물건 더미 재확인 | 그런데 현장에는 휴대폰보다 훨씬 큰 미끼가 이미 쌓여 있었습니다. |
| TB07 | `00:38.8–00:45.5` | 넓은 공간, 아무도 손대지 않음 | 범인은 나타나지 않았습니다. 가장 강한 자물쇠는 비밀번호가 아니라, 남의 물건에 관심 없는 사람들이었습니다. |

### 편집 원칙

- TB06은 훅(TB01, `00:34–36`)과 겹치지 않도록 2개 sub-range로 분할했다.
- source range는 서사 수정안 값을 그대로 사용했다.

## 7. 전체 A9 작가 나레이션

> 이 많은 물건이 밖에 놓였는데, 사건은 일어나지 않았습니다.
> 두 사람은 그 이유를 직접 확인해 보기로 했습니다.
> 첫 번째 미끼는 10년 된 휴대폰. 너무 약한 미끼일 수 있었죠.
> 그래서 잠금장치와 주변 동선까지 확인했습니다.
> 고향이라면 자리를 비운 순간 사라질 거라고 했습니다.
> 그런데 현장에는 휴대폰보다 훨씬 큰 미끼가 이미 쌓여 있었습니다.
> 범인은 나타나지 않았습니다. 가장 강한 자물쇠는 비밀번호가 아니라, 남의 물건에 관심 없는 사람들이었습니다.

## 8. T1·T2·A9_TEXT·STATE

```text
T1: 도둑을 잡으러 온 두 사람
T2: 범인이 나타나지 않았다
```

### A9_TEXT (7개, 컷 수와 동일)

- `사건인데 안 일어남`
- `이유를 확인하기로`
- `미끼는 10년 폰`
- `잠금장치 확인`
- `고향이면 사라진다`
- `더 큰 미끼 발견`
- `범인은 없었다`

### STATE (7개, 컷 수와 동일)

- `물건 더미`
- `놀란 두 사람`
- `낡은 휴대폰`
- `비밀번호 장치`
- `손짓하며 토론`
- `주변 재확인`
- `아무도 안 건드림`

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

- "독일인"은 원본표에서 확인되지 않는다. 4절 경계표에 창작으로 등재했으며, A9 대본에서도 국적 표현을 뺐다.
- 한국 전체에서 도난이 없다는 사실 주장으로 확장하면 안 된다. 결말은 "이 장면에서 그렇게 보였다"는 창작적 해석으로 제한한다.
- 원본표의 coarse beat 경계는 ±1초 수준이므로 현재 source range를 확정된 값으로 보고하지 않는다.

## 11. Stage 04 독립성 자체 검토

| 검토축 | 상태 | 근거 |
|---|---|---|
| 메시지 독립성 | PASS 후보 | 원본 요약이 아닌 새 관점 사용 |
| 서사 독립성 | PASS 후보 | 주인공·미해결 질문·반전·결말 재구성 |
| 정보 순서 변형 | PASS 후보 | 훅·본문 range 분리 완료 |
| 사실·창작 경계 | PASS 후보 | "독일인" 창작 등재 완료 |
| 사용자 승인 | WAIT | 승인 전 확정 금지 |

## 12. 사용자 승인 체크포인트

1. 훅 분리(2개 sub-range)가 이 원본에 맞는가.
2. "독일인" 삭제/창작 표기가 맞는가.
3. 제안한 target VIDEO order로 Stage 05 설계를 진행해도 되는가.

```text
CURRENT_STATUS=WAIT_USER_URAKKAI_APPROVAL
NEXT_ON_APPROVAL=STAGE_05_FINAL_DESIGN_LOCK
NEXT_ON_REVISION=STAGE_03_SAME_DRAFT_REWORK
```
