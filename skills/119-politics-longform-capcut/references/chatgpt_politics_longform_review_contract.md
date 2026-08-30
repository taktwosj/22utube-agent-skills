# ChatGPT 정치 롱폼 마스터 원고 2회 검수 계약

이 계약은 정치 롱폼 마스터 원고의 내용·근거·흐름·문자 품질을 두 번에 나눠
검사한다. 검수 결과는 사람이 바로 읽을 수 있는 Markdown으로 작성한다.

검수자에게 packet ID, SHA-256, manifest, receipt, 내부 경로를 작성시키지 않는다.
해시와 파일 연결은 Codex 자동화 계층이 별도로 관리한다.

## 공통 원칙

- 원문, fact map, 1차 자료를 우선한다.
- 사실, 인용, 날짜, 숫자, 화자, 법원·수사 판단과 해석을 구분한다.
- 자료가 부족하면 문장을 완성해 추정하지 말고 `NEEDS_EVIDENCE`로 표시한다.
- 원고의 블록 ID와 순서를 임의로 바꾸지 않는다.
- 보고서형 추상어보다 사람·행동·충돌·숫자·직접 질문을 우선한다.
- 전체 원고를 새로 쓰지 않는다. 문제가 있는 위치와 필요한 수정만 제안한다.
- 외부 검수자는 `FINAL`, `PASS`, `ADOPTED`, `SCRIPT_LOCK`을 선언하지 않는다.
- 모든 제안은 Codex 검증 전까지 `PENDING_CODEX_REVIEW`다.

## Round 1

입력 맨 위에 다음을 적는다.

```yaml
content_type: politics_longform
review_round: 1
```

### 기본 입력

- 마스터 원고
- commentary fact map
- 조사 자료
- 중심 질문 또는 중심 명제
- 변경 금지 항목과 블록 순서

원문 발언, source manifest, 추가 자료는 사실 확인에 필요한 경우에만 더한다.

### 역할

Round 1은 진단과 수정 제안만 수행한다.

- 중심 명제가 끝까지 증명되는지
- 사실과 해석이 섞였는지
- 근거 없는 인과·의도 추론·과장이 있는지
- 중요한 반론을 피하고 있는지
- AI식 일반론과 추상명사가 반복되는지
- 실제 발언의 감정과 문장 온도가 어긋나는지
- 오탈자, OCR 오인식, 고유명사·법률용어 오류가 있는지
- 깨진 특수문자, `<< d>>`, `�`, 깨진 자모, 중복 구두점이 있는지

### 출력

첫 줄:

```text
ROUTE=POLITICS_LONGFORM
```

이어서 다음 순서로 작성한다.

1. 총평
2. 중심 명제 판정
3. 블록별 진단
4. 강한 문장
5. 약한 문장
6. 정치적 균형과 반론
7. `NEEDS_EVIDENCE`
8. 번호가 붙은 수정 제안
9. 문자·오탈자 교정 목록

수정 제안은 다음 정도의 정보만 있으면 된다.

```text
### R1-01
대상: N003
문제: 선거 결과와 출연자의 해석이 사실상 동일시돼 있다.
수정 방향: “입증했다”를 “해석에 힘을 실었다”로 제한한다.
근거: fact map F07, 반론 C02
근거 상태: 충분
```

한 제안에 수십 개 필드를 만들거나 JSON으로 반환하지 않는다.

마지막 줄:

```text
PENDING_CODEX_REVIEW
```

## Codex 중간 결정

Codex는 Round 1 제안을 원문과 자료에 다시 대조하고 제안마다 정확히 하나를
결정한다.

```text
ADOPTED
PARTIALLY_ADOPTED
REJECTED
PENDING_EVIDENCE
```

결정표에는 제안 ID, 결정, 이유, 실제 반영 위치만 기록한다. 채택한 내용만 원고와
fact map에 반영한다. `PENDING_EVIDENCE`가 남아 있으면 Round 2로 넘어가지 않는다.

## Round 2

Round 1과 같은 ChatGPT 대화에서 이어서 진행한다.

입력 맨 위에 다음을 적는다.

```yaml
content_type: politics_longform
review_round: 2
```

### 입력

- Round 1 검수 결과
- Codex 제안별 결정표
- 수정 원고
- 수정 fact map
- 변경 요약
- 유지해야 할 블록 순서와 중심 질문

### 역할

Round 2는 새 창작이나 전면 개작이 아니라 수정 후 감사다.

- Round 1 문제가 실제로 해결됐는지
- 채택·부분 채택·기각 범위를 지켰는지
- 수정하면서 새로운 사실 오류가 생기지 않았는지
- 숫자, 날짜, 인용, 출처, 화자 귀속이 유지됐는지
- 해석이나 가능성을 확인 사실로 바꾸지 않았는지
- 문장별 수정 때문에 전체 논증과 결론이 무너지지 않았는지
- 오탈자, OCR, 깨진 문자와 특수기호가 남지 않았는지

### 출력

첫 줄:

```text
ROUTE=POLITICS_LONGFORM
```

이어서 다음 순서로 작성한다.

1. Round 1 지적 해결 여부
2. 사실·숫자·출처 감사
3. 새로 생긴 오류
4. 전체 흐름 감사
5. 문자·오탈자 감사
6. 남은 blocker
7. 검수 권고

검수 권고는 다음 셋 중 하나만 사용한다.

```text
PASS_RECOMMENDED
REVISE_REQUIRED
EVIDENCE_REQUIRED
```

마지막 줄:

```text
PENDING_CODEX_REVIEW
```

## Codex 최종 판단

외부 권고를 받은 뒤 Codex가 원문, fact map, 결정표, 수정 원고를 다시 대조한다.
외부 모델의 `PASS_RECOMMENDED`는 최종 승인이나 제작 잠금이 아니다. 근거·흐름·문자
품질에 blocker가 없을 때만 별도 내부 게이트가 다음 제작 단계로 넘긴다.
