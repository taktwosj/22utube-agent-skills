# 08_D6K9UI3a1kQ_MARA_STAGE03_URAKKAI_REV1

## 잠정 결론

**선택 추천안: `서울 최고 야경의 정체`**

본 개정본은 `11_STAGE04_REVISION_ORDER_20260806.md`와 `13_CLAUDE_URAKKAI_REVISION_20260806.md`를 반영한 개정 초안이다. 8개 회차 중 컨셉이 가장 강하다고 평가됐다. 간판 노출 시점과 마지막 주간 컷만 고쳤다.

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
STAGE05_LOCK_ITEM=GS25_SIGNAGE_CROP_COORDINATES
```

## 0. Source of Truth

| 항목 | 값 |
|---|---|
| episode_id | `D6K9UI3a1kQ` |
| 원본 표시명 | 한강변 GS25 편의점과 야경을 소개하는 남성 |
| 원본표 | `01_D6K9UI3a1kQ_ORIGINAL_CAPCUT_GRID.md` |
| 원본 media SHA-256 | `0d5e134033093f0b833ce37a155fd4fc87e28f31cbee588a3b9b7ee8ec2830ae` |
| 원본 길이 | `58.793s` |
| target 길이 | `[EST] 32~38초` |
| 댓글 자료 | `NOT_PROVIDED` |
| 사용자 승인 | `WAIT` |

## 1. 원본이 가진 힘

### MARA_MESSAGE

> **장소의 가치는 가격표나 간판이 아니라, 평범한 소비에 어떤 경험이 함께 붙어오는지에서 결정된다.**

## 2. 개정 사유

컨셉(고급 전망대처럼 보였던 곳이 편의점이었다)은 그대로 유지한다. 두 가지만 고쳤다: (1) 反전 전 구간에서 GS25 간판이 노출되면 설계 전체가 무너지므로 간판 노출 시점을 명확히 통제, (2) 결말 컷에 낮 셀피가 섞여 있어 야경으로 닫히지 않던 문제를 주간 컷 제외로 수정.

## 3. 선택안 서사 계약

| 항목 | 설계 |
|---|---|
| 주인공 | 서울에서 저렴하게 밤을 보내려는 여행자 |
| 목표 | 비싼 입장료 없이 한강 야경과 휴식 공간을 동시에 찾는다 |
| 미해결 질문 | 라면 조리기·좌석·한강 전망을 모두 가진 장소의 정체는 무엇일까 |
| 반전 | 고급 전망대처럼 소개된 장소의 간판이 중반에 GS25로 드러난다 |
| 결말 | 그의 인생 최고 장소는 별 다섯 개 호텔이 아니라 편의점이었다 |
| 한 줄 | **서울 최고 야경의 정체, 입장권은 라면 한 그릇.** |
| resolution_type | `TRANSFORM_CANDIDATE` |
| creative_label（비계약） | `LOCATION_IDENTITY_REVEAL` |

## 4. SOURCE_OBSERVATION / FICTIONAL_RECONSTRUCTION 경계

| 분류 | 내용 | 사용 규칙 |
|---|---|---|
| SOURCE_OBSERVATION | 한강·다리·도시 야경 | 원본표 근거 |
| SOURCE_OBSERVATION | GS25 외관과 간판 | 원본표 근거 |
| SOURCE_OBSERVATION | 라면 조리기·서서 먹는 공간 | 원본표 근거 |
| SOURCE_OBSERVATION | 실내 좌석과 야외 테이블 | 원본표 근거 |
| SOURCE_OBSERVATION | 음료·맥주를 마실 수 있다는 설명 | 원본표 근거 |
| SOURCE_OBSERVATION | 인생 역대 최고 편의점이라는 평가 | 원본표 근거 |
| FICTIONAL_RECONSTRUCTION | 저렴한 밤 장소를 찾고 있었다는 목표, 입장권·드레스코드 비교 장치 | 창작 설정 |
| FICTIONAL_RECONSTRUCTION | 시청자가 루프탑 바라고 추리하도록 만드는 정보 통제 | 창작 설정 |

## 5. 구조 변형 계약

```text
source_order_signature=원본표의 SB 오름차순
target_order_signature=SB06 > SB08a > SB04(간판 제외) > SB05 > SB02 > SB03 > SB07 > SB08b(주간 컷 제외) > SB01(주간 컷 제외)
source_structure_pattern=SP_VISUAL_CONTRAST_TO_PROOF
remake_structure_pattern=DST_PAYOFF_FIRST_CONTRAST_RECOMPOSITION  # 舊 산문: 정체를 숨긴 야경 훅 → 테이블 증거 → 조리기·좌석 단서 → GS25 공개 → 장소 맥락 → 이용법 → 최종 가치 평가
resolution_type=TRANSFORM_CANDIDATE
execution_strategy=full_tts
baked_order_semantics=LOCAL_REAUTHORABLE  # GS25 간판이 baked이나 순번 의미는 없음. 노출 시점 통제 필요
dialogue_dependency=NONE
```

## 6. Target VIDEO order + CapCut 세로 설계

| Target | Source range | 화면 | A9 |
|---|---|---|---|
| TB01 | `00:30–00:36` | 한강·다리 야경만. 간판 없음 | 이 남자는 서울에서 가장 비싸 보이는 야경을 가장 싸게 찾아냈습니다. |
| TB02 | `00:48–00:52.5` | 야외 테이블·강변 좌석 | 입장권도 드레스코드도 없이, 빈 테이블까지 있었습니다. |
| TB03 | `00:14–00:24` | 라면 조리기·서서 먹는 공간. **간판 크롭 제외** | 안에는 라면 조리기와 바로 먹을 수 있는 자리가 있었고 |
| TB04 | `00:24–00:30` | 실내 좌석·창밖 야경 | 추우면 실내에서도 같은 밤을 기다릴 수 있었습니다. |
| TB05 | `00:04.1–00:08` | GS25 간판 전체 공개 | 그리고 이 장소의 정체가 드러났습니다. GS25 편의점. |
| TB06 | `00:08–00:14` | 한강 앞 셀피 | 전망대도 루프탑 바도 아니었습니다. |
| TB07 | `00:40.5–00:48` | 음료·매장·한강 전경 | 필요한 건 음료 한 캔이나 라면 한 그릇뿐이었습니다. |
| TB08 | `00:52.5–00:58` | 야경·테이블·도시 불빛 | 평범한 소비에 한강의 밤이 따라왔습니다. |
| TB09 | `00:00–00:02.5` | 야경 셀피만. **주간 컷 제외** | 그의 인생 최고 장소는 별 다섯 개 호텔이 아니라, 별것 없어 보이던 편의점이었습니다. |

### 편집 원칙

- **Stage 05 잠금 항목:** TB03(`00:14–00:24`)의 GS25 간판 크롭 좌표. TB05(`00:04.1–00:08`)보다 먼저 간판이 화면에 노출되면 반전 구조 전체가 무너진다. 정확한 크롭 좌표는 Stage 05에서 프레임 단위로 확정하며, 확정 전에는 이 구간의 편집을 진행하지 않는다.
- TB09는 舊안의 `00:00–00:04.1`에서 `00:00–00:02.5`로 축소했다. 원본표 SB01에는 `낮의 짧은 셀피 삽입`이 포함되어 있어 결말이 야경으로 닫히지 않는 문제가 있었다. 주간 컷을 제외한 구간만 사용한다.
- source range는 서사 수정안 값을 그대로 사용했다.

## 7. 전체 A9 작가 나레이션

> 이 남자는 서울에서 가장 비싸 보이는 야경을 가장 싸게 찾아냈습니다.
> 입장권도 드레스코드도 없이, 빈 테이블까지 있었습니다.
> 안에는 라면 조리기와 바로 먹을 수 있는 자리가 있었고
> 추우면 실내에서도 같은 밤을 기다릴 수 있었습니다.
> 그리고 이 장소의 정체가 드러났습니다. GS25 편의점.
> 전망대도 루프탑 바도 아니었습니다.
> 필요한 건 음료 한 캔이나 라면 한 그릇뿐이었습니다.
> 평범한 소비에 한강의 밤이 따라왔습니다.
> 그의 인생 최고 장소는 별 다섯 개 호텔이 아니라, 별것 없어 보이던 편의점이었습니다.

## 8. T1·T2·A9_TEXT·STATE

```text
T1: 서울 최고 야경의 정체
T2: 입장권은 라면 한 그릇
```

### A9_TEXT (9개, 컷 수와 동일)

- `가장 비싼 야경을`
- `가장 싸게 찾았다`
- `라면도 먹을 수 있다`
- `실내에서도 같은 밤`
- `정체는 GS25`
- `전망대도 바도 아님`
- `필요한 건 한 캔`
- `평범한 소비, 한강의 밤`
- `별것 없어 보인 최고`

### STATE (9개, 컷 수와 동일)

- `한강·다리 야경`
- `야외 테이블`
- `라면 조리기 (간판 크롭 제외)`
- `실내 좌석·창밖 야경`
- `GS25 간판 공개`
- `한강 앞 셀피`
- `음료·매장·전경`
- `야경·테이블·불빛`
- `야경 셀피만 (주간 컷 제외)`

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

- **Stage 05 잠금 항목:** GS25 간판 크롭 좌표 (TB03 구간). 반전 전 간판이 보이면 설계 전체가 무너지므로 실제 프레임을 확인해 크롭이 가능한지 검증해야 하며, 불가능하면 "정체 추리" 대신 "라면 한 그릇의 가치 역전" 안으로 복귀한다.
- TB09 축소(`00:00–00:02.5`)로 주간 컷 혼입을 막았으나, 실제 프레임에서 해당 구간에도 주간 컷이 남아 있는지 Stage 05에서 재확인이 필요하다.
- 원본표의 coarse beat 경계는 ±1초 수준이므로 현재 source range를 확정된 값으로 보고하지 않는다.

## 11. Stage 04 독립성 자체 검토

| 검토축 | 상태 | 근거 |
|---|---|---|
| 메시지 독립성 | PASS 후보 | 원본 요약이 아닌 새 관점 사용 |
| 서사 독립성 | PASS 후보 | 주인공·미해결 질문·반전·결말 재구성 |
| 정보 순서 변형 | PASS 후보 | 정체 공개 시점을 중반으로 이동 |
| baked_order_semantics | CONDITIONAL PASS | 간판 크롭 좌표 Stage 05 확정 필요 |
| 사용자 승인 | WAIT | 승인 전 확정 금지 |

## 12. 사용자 승인 체크포인트

1. 간판 노출 시점 재배치(TB03 크롭, TB05 공개)가 이 원본에 맞는가.
2. 결말 주간 컷 제외가 맞는가.
3. 제안한 target VIDEO order로 Stage 05 설계(간판 크롭 좌표 확정 포함)를 진행해도 되는가.

```text
CURRENT_STATUS=WAIT_USER_URAKKAI_APPROVAL
NEXT_ON_APPROVAL=STAGE_05_FINAL_DESIGN_LOCK（GS25_SIGNAGE_CROP_COORDINATES 확정 포함）
NEXT_ON_REVISION=STAGE_03_SAME_DRAFT_REWORK
```
