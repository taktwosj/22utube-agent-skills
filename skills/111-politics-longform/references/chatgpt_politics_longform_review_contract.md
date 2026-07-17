# ChatGPT 정치 롱폼 마스터 원고 2회 검수 계약

이 계약은 정치 롱폼의 `commentary_master_script_draft.md`를 ChatGPT 프로젝트에서
두 번 검수할 때 적용한다. 하단 2줄 평론용 외부 검토 계약과 쇼츠 계약을 섞지
않는다.

## 1. 게이트 분리

```text
MASTER_COMMENTARY_REVIEW_GATE: 마스터 원고의 2회 ChatGPT 검수
EXTERNAL_LOWER_COMMENTARY_GATE: 하단 2줄 평론의 시간순 외부 검토
```

`MASTER_COMMENTARY_REVIEW_GATE`의 파일은 모두
`20_script/master_commentary_review/` 아래에 둔다.
`EXTERNAL_LOWER_COMMENTARY_GATE`가 사용하는
`commentary_review_packet_sent.md`,
`commentary_review_packet_manifest.json`,
`commentary_review_packet_returned.md`,
`commentary_review_receipt.json`, `external_review_gate.json`은 재사용하지 않는다.
두 게이트의 PASS는 서로를 대신하지 않는다.

## 2. 권한

ChatGPT는 독립 검수자다. 외부 모델은 최종 승인 파일을 만들지 않는다.
두 회차의 모든 반환 상태는 `PENDING_CODEX_REVIEW`다. ChatGPT의
`PASS_RECOMMENDED`는 검수 권고일 뿐 `PASS`, `FINAL`, `ADOPTED` 또는
`commentary_master_script_approved.md` 생성을 뜻하지 않는다.

Codex는 Round 1의 모든 `suggestion_id`에 exactly one 결정을 기록한다.

```text
ADOPTED
PARTIALLY_ADOPTED
REJECTED
PENDING_EVIDENCE
```

각 결정에는 `decision_reason`이 필요하다. `PENDING_EVIDENCE`가 하나라도 남으면
Round 2를 보내거나 마스터 검수 게이트를 통과시키지 않는다. 사용자의 명시적
승인 전에는 `commentary_master_script_approved.md`를 만들지 않는다.

## 3. 공통 근거

두 회차는 다음 내용을 근거로 삼는다.

- `core_question`: 영상 전체가 답할 핵심 질문
- `commentary_master_script_draft.md`: 마스터 원고 전문
- `commentary_fact_map.json`: `claim_id`별 사실, 해석, 반론, 판단
- `source_manifest.json`: 실제 출처, 날짜, URL과 근거 역할
- 원문 발언: `source_id`, `segment_id`, 타임코드와 정확한 문장
- timeline의 전체 `ordered_segment_ids`
- 아직 확인되지 않은 fact lock과 제작자가 이미 고정한 사실

필수 근거가 없으면 추정으로 채우지 않고 `CONTEXT_REQUIRED`,
`FACT_CHECK_REQUIRED`, `SOURCE_MISMATCH`, `FACT_LOCK_CONFLICT`,
`NEEDS_EVIDENCE` 중 하나로 표시한다.

근거 충돌 시 권한 순서는 원본 1차 자료, 기관 원문, 출처와 날짜가 확인되는 보도,
fact map, 검토 대상 원고, 외부 모델의 추론 순서다.

## 4. ROUND_1

입력 헤더:

```yaml
content_type: politics_longform
review_round: 1
packet_id: 고유 ID
sent_packet_sha256: Round 1 발송문 SHA-256
episode_id: 에피소드 ID
core_question: 영상 전체의 핵심 질문
target_duration_sec: 목표 길이
```

Round 1은 다음 두 역할만 수행한다.

1. `INDEPENDENT_REVIEW`: 초안을 고치기 전에 논증, 근거, 반론, 맥락을 진단한다.
2. `REVISION_PROPOSAL`: 진단된 문제에 한해서 수정안을 제시한다.

제안마다 다음 필드를 사용한다.

```yaml
suggestion_id:
segment_id:
claim_id:
source_id:
before:
after:
revision_type:
reason:
evidence:
counterargument:
derived_from:
inference_type:
confidence:
factual_impact:
risk:
verification_state:
```

`suggestion_id`는 회차 안에서 중복할 수 없다. 직접 인용과 작성자의 해석을
구분하고, 원문에 없는 의도나 배후를 사실처럼 추가하지 않는다. 원고 전체를
취향대로 재창작하지 않는다.

Round 1 반환 형식:

```text
ROUTE=POLITICS_LONGFORM
review_round: 1
packet_id: ...
sent_packet_sha256: ...

## INDEPENDENT_REVIEW
segment_id와 claim_id별 진단

## REVISION_PROPOSAL
suggestion_id별 수정 제안

## HARD_BLOCKERS
없으면 NONE, 있으면 필요한 근거

final_state: PENDING_CODEX_REVIEW
```

Round 1 직후 Codex는 원문, 출처, 날짜, 숫자와 fact lock을 다시 대조하고
`round1_codex_decisions.json`에 제안별 결정을 기록한다. 채택한 제안만 반영해
마스터 원고와 fact map을 수정한다.

## 5. ROUND_2

Round 2는 반드시 Round 1을 수행한 same conversation에서 이어간다.

```yaml
content_type: politics_longform
review_round: 2
same_conversation_id: required
packet_id: 새 고유 ID
parent_round1_return_sha256: Round 1 반환문 SHA-256
parent_decisions_sha256: Codex 결정표 SHA-256
```

새 대화, 갈라진 대화, 대화 ID가 확인되지 않는 경우
`SAME_CONVERSATION_REQUIRED`로 중단한다. 같은 대화라는 이유로 이전 첨부를
암묵적으로 기억한다고 가정하지 않는다. Round 2 패킷 자체에 다음 전문을 모두
다시 넣어 self-contained 상태로 만든다.

1. Round 1 전체 반환문
2. Codex 결정표 전체
3. 수정된 마스터 원고 전문
4. 수정된 fact map 전문
5. timeline segment 순서 전체
6. 핵심 질문

패킷에는 다음 앵커를 각각 한 번 넣는다.

```text
<!-- ROUND1_RETURN_FULL -->
<!-- CODEX_DECISIONS_FULL -->
<!-- REVISED_MASTER_SCRIPT_FULL -->
<!-- REVISED_FACT_MAP_FULL -->
<!-- TIMELINE_ORDER_FULL -->
<!-- CORE_QUESTION -->
```

Round 2는 다음 두 역할을 수행한다.

1. `EVIDENCE_AUDIT`: 채택된 수정의 사실, 인용, 날짜, 숫자, 해석을 다시 검증한다.
2. `FLOW_CONTINUITY_AUDIT`: 원고 전문이 핵심 질문을 향해 자연스럽게 이어지는지
   전체 흐름으로 검수한다.

`FLOW_CONTINUITY_AUDIT`는 최소한 다음을 확인한다.

- `ordered_segment_ids`가 Round 1과 동일하고 segment order drift가 없는가
- 각 구간의 마지막 문장이 다음 구간의 첫 주장으로 논리적으로 이어지는가
- 같은 주장을 반복하거나 반론을 두 번 처리하지 않는가
- 수정 때문에 주어, 시점, 출처 또는 핵심 질문이 바뀌지 않았는가
- 인트로, 본론, 반론, 판단의 역할과 강도가 자연스럽게 상승하는가
- 개별 문장은 좋아졌지만 전체 결론이 비약하는 문제가 없는가

Round 2 반환 형식:

```text
ROUTE=POLITICS_LONGFORM
review_round: 2
packet_id: ...
same_conversation_id: ...

## EVIDENCE_AUDIT
채택된 수정의 근거 재검증

## FLOW_CONTINUITY_AUDIT
구간 전환과 전체 논리 흐름 검수

recommendation: PASS_RECOMMENDED|REVISE_REQUIRED|EVIDENCE_REQUIRED
flow_continuity_status: PASS|FAIL
remaining_blockers: []
final_state: PENDING_CODEX_REVIEW
```

`REVISE_REQUIRED`, `EVIDENCE_REQUIRED`, 흐름 FAIL 또는 남은 blocker가 있으면
`WAIT_CHATGPT_REVIEW_REPAIR`다. 원고를 수정한 뒤 필요한 검수 회차를 다시 만들고
해시를 갱신한다.

## 6. 불변 파일 계약

```text
20_script/master_commentary_review/
├─ round1_packet_sent.md
├─ round1_manifest.json
├─ round1_returned.md
├─ round1_receipt.json
├─ round1_codex_decisions.json
├─ round2_packet_sent.md
├─ round2_manifest.json
├─ round2_returned.md
├─ round2_receipt.json
└─ master_commentary_review_gate.json
```

발송문과 반환문을 덮어쓰지 않는다. 각 manifest와 receipt는 실제 파일의 SHA-256을
고정한다. Round 2 manifest는 Round 1 반환문과 Codex 결정표의 SHA-256을 부모
해시로 고정한다. Round 1 receipt, Round 2 manifest, Round 2 receipt의
`conversation_id`는 모두 같아야 한다.

Round 1 manifest의 불변 권위는 원고와 fact map 전문을 포함한
`round1_packet_sent.md`다. Round 1 이후 수정되는 작업용
`commentary_master_script_draft.md`와 `commentary_fact_map.json`의 과거 해시를
현재 파일에 다시 요구하지 않는다. Round 2 manifest는 수정된 현재 원고, fact
map과 timeline의 파일 경로·SHA-256을 별도로 고정한다.

Round 1 receipt의 `suggestion_ids`와 Codex 결정표는 정확히 일대일이어야 한다.
누락, 중복, 알 수 없는 제안 ID, 빈 `decision_reason`은 실패다.
Round 1 manifest, Round 2 manifest, Round 2 receipt의
`ordered_segment_ids`가 하나라도 다르면 `SEGMENT_ORDER_DRIFT`다.

검증 명령:

```powershell
python scripts/validate_chatgpt_two_pass_review.py --review-dir "{episode}\20_script\master_commentary_review"
```

검증기가 만든 `MASTER_COMMENTARY_REVIEW_GATE=PASS`는 2회 검수 파일과 해시 연결이
정상이라는 뜻이다. 사용자 승인, 하단 2줄 외부 검토, 설계 승인 또는 CapCut 조립
PASS를 대신하지 않는다.

## 7. 금지

- Round 1과 Round 2를 한 응답에서 동시에 수행했다고 주장하지 않는다.
- Round 2를 새 대화에서 시작하지 않는다.
- Round 1 제안을 Codex 결정 없이 자동 채택하지 않는다.
- 하단 2줄 외부 검토 파일을 마스터 원고 2회 검수 파일로 재사용하지 않는다.
- 외부 반환문에 `final_state: FINAL`, `approval_status: PASS`,
  `commentary_master_script_approved.md` 생성 완료를 쓰지 않는다.
- 직접 인용 왜곡, 날짜·숫자 오류, 직책 오류, 미확인 범죄 단정이 있으면
  권고 PASS를 내지 않는다.
