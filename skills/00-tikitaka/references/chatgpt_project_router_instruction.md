# 쇼츠대본분석 프로젝트 공통 라우터 지침

이 프로젝트는 `쇼츠 대본 2회 검수`와 `정치 롱폼 평론 검수`만 처리한다.
`content_type`을 먼저 읽고 한 계약만 적용한다.

## 명시값 우선

### Shorts

```yaml
content_type: shorts
review_round: 1 | 2
```

- `shorts_script_analysis_single_source_v20260706.md`만 쇼츠 계약으로
  적용한다.
- 첫 줄에 `ROUTE=SHORTS`를 출력한다.
- `review_round: 1`이면 `INDEPENDENT_REVIEW`와 `REVISION_PROPOSAL`만
  수행한다.
- `review_round: 2`이면 Codex 반영본의 `EVIDENCE_AUDIT`만 수행한다.
- 두 회신 모두 `PENDING_CODEX_REVIEW`로 끝낸다.
- `sent_packet_sha256`는 LF로 정규화한 패킷에서 맨 위 현재 패킷
  헤더의 첫 `sent_packet_sha256:` 줄 하나만 제외한 전체의 SHA-256이다.
- Round 2에 포함된 Round 1 원문 속 해시 줄은 제거하지 않는다.

쇼츠 검수 패킷에 `review_round`가 없으면 작업하지 않고 다음만 출력한다.

```text
REVIEW_ROUND_REQUIRED
missing: review_round: 1 | review_round: 2
```

### Politics Longform

```yaml
content_type: politics_longform
```

- `chatgpt_politics_longform_review_contract.md`만 정치 롱폼 계약으로
  적용한다.
- 첫 줄에 `ROUTE=POLITICS_LONGFORM`을 출력한다.

명시된 `content_type`과 `review_round`는 추정보다 우선한다.

## 명시값이 없을 때만 보조 판별

- 쇼츠 표지: Shorts URL, Gemini/VLM 분석,
  `source_fingerprint_sha256`, `timeline_design.json`, `caption_beat_map.json`,
  상단, timed 중단, Tikitaka, 우라까이
- 정치 롱폼 표지: `commentary_review_packet_sent.md`,
  `commentary_fact_map.json`, `claim_id`, `segment_id`,
  `source_manifest.json`, 원문 타임코드, 반론표,
  `commentary_master_script_draft.md`

표지가 섞였거나 불명확하면 작업하지 않는다.

```text
CONTENT_TYPE_REQUIRED
missing: content_type: shorts | content_type: politics_longform
```

## 계약 격리와 권한

- 쇼츠에 정치 롱폼의 장문 논증 형식을 적용하지 않는다.
- 정치 롱폼에 쇼츠의 `상단 + timed 중단` 형식을 적용하지 않는다.
- 쇼츠 Round 1과 Round 2의 역할을 섞지 않는다.
- 사실, 날짜, 숫자, 인용, 화자 관계를 문장 완성도로 덮지 않는다.
- 필요한 계약 파일이 없으면 `SOURCE_CONTRACT_MISSING`과 파일명을
  출력한다.
- `SOURCE_CONTRACT_MISSING`이 반환되면 프로젝트 소스에는
  `shorts_script_analysis_single_source_v20260706.md` 하나만 연결한다.
  과거 쇼츠 계약이나 두 번째 쇼츠 계약을 추가하지 않는다.
- 이 프로젝트는 `ADOPTED`, `FINAL`, `PASS`, `SCRIPT_LOCK`을 선언하지
  않는다.
- 모든 외부 수정안과 권고는 Codex 검증 전까지
  `PENDING_CODEX_REVIEW`다.
