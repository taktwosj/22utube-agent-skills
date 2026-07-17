# 쇼츠대본분석 프로젝트 공통 라우터 지침

이 프로젝트는 쇼츠 분석과 정치 롱폼 마스터 원고 검수만 처리한다. 작업 시작 전에
입력의 `content_type`을 읽고 정확히 하나의 계약만 적용한다.

## 1. 명시값 우선

- `content_type: shorts`
  - `shorts_script_analysis_single_source_v20260706.md`만 적용한다.
  - 첫 줄에 `ROUTE=SHORTS`를 출력한다.
- `content_type: politics_longform`
  - `chatgpt_politics_longform_review_contract.md`만 적용한다.
  - `review_round: 1` 또는 `review_round: 2`가 반드시 있어야 한다.
  - 첫 줄에 `ROUTE=POLITICS_LONGFORM`을 출력한다.

명시된 유형은 추정보다 우선한다. 두 계약을 혼합하지 않는다.

## 2. 누락 처리

`content_type`이 없고 쇼츠와 정치 롱폼 중 하나로 확정할 수 없으면 작업하지 않고
다음만 출력한다.

```text
CONTENT_TYPE_REQUIRED
missing: content_type: shorts | content_type: politics_longform
```

정치 롱폼인데 `review_round`가 없으면 다음만 출력한다.

```text
REVIEW_ROUND_REQUIRED
missing: review_round: 1 | review_round: 2
```

정치 롱폼 Round 2인데 Round 1 대화의 `conversation_id`를 확인할 수 없거나 다른
대화에서 들어오면 다음만 출력한다.

```text
SAME_CONVERSATION_REQUIRED
required: Round 1과 동일한 ChatGPT conversation_id
```

## 3. 보조 판별

명시값이 없을 때 다음 표현은 쇼츠 후보 신호다.

- 세로형 영상, Shorts URL, Gemini/VLM 원본 분석
- `video_duration_sec`, 상단, timed 중단, 구간별 자막
- 쇼츠 훅, 티키타카, 우라까이

다음 표현은 정치 롱폼 후보 신호다.

- `commentary_master_script_draft.md`, `commentary_fact_map.json`
- `round1_packet_sent.md`, `round2_packet_sent.md`
- `claim_id`, `segment_id`, `suggestion_id`
- 정치평론가 나레이션, 마스터 원고, 전체 흐름 검수

보조 신호만으로 회차를 추정하지 않는다.

## 4. 격리 규칙

- 쇼츠 입력에 정치 롱폼의 논증·증거 감사 형식을 적용하지 않는다.
- 정치 롱폼 입력에 쇼츠의 상단·timed 중단 형식을 적용하지 않는다.
- 원본 순서 유지 금지, 동일 배열 금지, 순서 셔플 필수 같은 쇼츠 변환 규칙을
  정치 롱폼에 적용하지 않는다.
- 필요한 계약 파일이 없으면 추측하지 않고 `SOURCE_CONTRACT_MISSING`과 누락
  파일명을 출력한다.

## 5. 외부 검수 권한

정치 롱폼 Round 1과 Round 2의 반환은 항상 `PENDING_CODEX_REVIEW`다.
Round 1은 `INDEPENDENT_REVIEW`와 `REVISION_PROPOSAL`, Round 2는
`EVIDENCE_AUDIT`와 `FLOW_CONTINUITY_AUDIT`를 수행한다. Round 2는 같은 대화에서
이어지되 패킷 자체에 Round 1 반환문, Codex 결정표, 수정 원고, fact map,
timeline 순서와 핵심 질문의 전문을 다시 포함한다.

외부 모델은 `ADOPTED`, 최종 승인, 사용자 승인 또는
`commentary_master_script_approved.md` 생성을 선언하지 않는다.
