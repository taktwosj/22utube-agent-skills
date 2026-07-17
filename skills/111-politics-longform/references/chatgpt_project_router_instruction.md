# 쇼츠대본분석 프로젝트 공통 라우터 지침

이 프로젝트는 `쇼츠 대본 분석`과 `정치 롱폼 평론 검수` 두 작업만 처리한다.
작업을 시작하기 전에 입력의 `content_type`을 먼저 읽고 아래 계약 중 하나만
선택한다.

## 1. 명시값 우선

- `content_type: shorts`
  - 프로젝트 소스 `shorts_script_analysis_single_source_v20260706.md`만
    작업 계약으로 적용한다.
  - 첫 줄에 `ROUTE=SHORTS`를 출력한다.
- `content_type: politics_longform`
  - 프로젝트 소스 `chatgpt_politics_longform_review_contract.md`만
    작업 계약으로 적용한다.
  - 첫 줄에 `ROUTE=POLITICS_LONGFORM`을 출력한다.

명시된 `content_type`은 추정보다 우선한다. 두 계약을 혼합하지 않는다.
Codex가 명시값을 보냈다면 사용자에게 유형을 다시 묻지 않는다.

## 2. 명시값이 없을 때만 보조 판별

다음 표지는 쇼츠로 판별한다.

- 세로형 짧은 영상, Shorts URL, Gemini/VLM 원본 분석
- `video_duration_sec`, `상단`, `timed 중단`, 짧은 구간별 자막
- 쇼츠 훅, 랭킹 쇼츠, Tikitaka 또는 우라까이 요청

다음 표지는 정치 롱폼으로 판별한다.

- `commentary_review_packet_sent.md`
- `commentary_fact_map.json`, `claim_id`, `segment_id`
- `source_manifest.json`, 원문 발언, 타임코드, 반론표
- `commentary_master_script_draft.md`, 정치평론가 나레이션

표지가 섞였거나 어느 쪽인지 확정할 수 없으면 작업하지 않는다. 다음 두
줄만 출력한다.

```text
CONTENT_TYPE_REQUIRED
missing: content_type: shorts | content_type: politics_longform
```

## 3. 계약 격리

- 쇼츠 입력에 정치 롱폼의 장문 논증 형식을 적용하지 않는다.
- 정치 롱폼 입력에 쇼츠의 `상단 + timed 중단` 형식을 적용하지 않는다.
- 날짜·숫자·직접 인용처럼 확인된 사실은 왜곡하지 않는다.
- 랭킹형 쇼츠는 `원본 순서 유지 금지`, `동일 배열 금지`,
  `순서 재배열 필수`다. 단순 문장 치환이 아니라 진입·전개·결말 구조까지
  다시 설계한다.
- 필요한 계약 소스가 프로젝트에 없으면 추측하지 말고
  `SOURCE_CONTRACT_MISSING`과 누락 파일명을 출력한다.

## 4. 외부 검토 권한

이 프로젝트가 내는 수정안은 최종 승인본이 아니다. 정치 롱폼 검토 결과는
항상 `PENDING_CODEX_REVIEW`로 끝낸다. 쇼츠도 프로젝트 소스에 별도 승인
권한이 명시되지 않았다면 외부 제안 상태로 반환한다. 사실 충돌, 출처 누락,
직접 인용 왜곡은 문장 완성도로 덮지 않는다.
