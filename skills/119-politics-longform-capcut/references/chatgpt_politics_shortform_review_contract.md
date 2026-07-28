# ChatGPT 정치 롱폼 파생 숏폼 후보 검수 계약

## 라우팅

```yaml
content_type: politics_shortform
truth_mode: fact_first
```

첫 응답 줄은 `ROUTE=POLITICS_SHORTFORM`이다.

## 목적

승인된 정치 롱폼에서 맥락이 독립적으로 이해되고 첫 3초가 강한
45~70초 연속 원본 구간을 1~3개 제안한다. 유효 후보가 적으면 억지로
3개를 채우지 않는다. 안전한 후보가 없으면 `NO_SAFE_CANDIDATE`를 반환한다.

## 필수 입력

- 승인된 정치 롱폼 원고
- fact map
- source transcript와 원본 timecode
- source_id와 segment_id 대응표
- 원고 승인 또는 검수 게이트

승인 원고, fact map, 원문 자막, timecode 중 하나라도 없으면
`SOURCE_CONTRACT_MISSING`을 반환한다.

## 후보 규칙

- 후보 하나는 하나의 `source_id`에 속한 45~70초 연속 구간이다.
- 실제로 연속된 `segment_id`만 사용한다.
- 첫 3초 훅과 핵심 인용은 원문 발화를 그대로 보존한다.
- 인물, 날짜, 숫자, 직책, 범죄·수사·법원 표현은 fact map과 대조한다.
- 앞뒤 맥락을 잘라 의미가 달라지면 후보에서 제외한다.
- 새 주장, 새 인용, 요약 대사, 상단 문구, TTS 문안은 만들지 않는다.
- 이 단계에서는 원본 순서를 바꾸거나 여러 구간을 재조립하지 않는다.

## 출력

후보별로 다음 형식을 사용한다.

```text
### PS001
- source_id:
- segment_ids:
- source_start:
- source_end:
- duration_sec:
- first_3_sec_hook:
- core_quote:
- why_it_works:
- risk_level: low | medium | high
- risk:
- evidence:
- context_before:
- context_after:
- recommendation: RECOMMENDED | USABLE_WITH_CAUTION | REJECT
```

`evidence`에는 `claim_id`, transcript cue 또는 원본 timecode를 기록한다.
마지막 줄은 `external_review_status: PENDING_CODEX_REVIEW`다.

## 권한 경계

`119-politics-longform-capcut`은 후보 1~3개와 정확한 원본 범위를 검증한다.
Codex와 사용자가 후보를 선택한 뒤에만 `001short-production-agent`가 상단, timed 중단,
조립 역할, TTS와 원본음성 정책을 설계한다. `001short-production-agent`가 원본 범위를
바꿔야 한다면 `DESIGN_REOPEN_REQUIRED`로 반환한다.

ChatGPT는 후보 추천과 위험 표시만 수행한다. `FINAL`, `PASS`, `ADOPTED`,
후보 잠금을 선언하지 않는다.
