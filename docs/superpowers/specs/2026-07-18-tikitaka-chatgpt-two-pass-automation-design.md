# Tikitaka ChatGPT 2차 검수 자동화 설계

## 목표

`00-tikitaka` Stage 1 설계가 기존 ChatGPT 프로젝트 `쇼츠대본분석`에서
Round 1 독립 검수와 Round 2 증거 감사를 거친 뒤에만
`SCRIPT_HANDOFF_GATE`로 이동하게 한다. 사용자가 Shorts URL을 제공하면
같은 자동화 경로로 `20_script/design_blueprint.md`까지 실제 검증한다.

## 현재 상태

- 스킬 문서와 단일 계약에는 2회 검수 규칙이 작성되어 있다.
- `tikitaka_harness_runner.py`는 완성된 검수 산출물을 검사할 수 있다.
- 라이브 프로젝트 공통 지침은 저장소의 라우터 지침과 일치한다.
- 라이브 프로젝트에는 Shorts 단일 계약 파일이 없어
  `SOURCE_CONTRACT_MISSING`이 발생한다.
- 패킷 생성, 응답 메타데이터 검증, 최종 게이트 작성은 아직 수동이다.

## 선택한 방식

브라우저 전송만 Codex의 로그인된 Chrome 제어를 사용하고, 재현 가능한
파일·해시·응답 검증은 Python CLI가 담당한다.

API나 별도 로그인 프로필을 사용하지 않는다. 프로젝트에 계약 파일을
한 번 연결한 뒤, 에피소드마다 새 프로젝트 대화 하나를 만들고 두 회차를
같은 대화에서 처리한다.

## 구성요소

### `chatgpt_review_workflow.py`

다음 하위 명령을 제공한다.

- `build-round1`: 현재 설계 산출물로 Round 1 패킷 생성
- `record-response --round 1|2`: 저장한 원문 응답의 라우팅, 회차,
  cycle ID, packet ID, 전송 해시, 종료 상태를 검증
- `build-round2`: Round 1 원문, Codex 결정표, 수정 설계와 게이트 결과로
  Round 2 패킷 생성
- `finalize-gate`: Round 2의 실제 권고가 `PASS_RECOMMENDED`일 때만
  `chatgpt_review_gate.json` 생성

### 해시 규칙

패킷은 LF로 정규화한다. `sent_packet_sha256` 계산에서는 현재 패킷
헤더에 있는 첫 번째 최상위 `sent_packet_sha256:` 줄만 제외한다.
Round 2 안에 인용된 Round 1 응답의 해시 줄은 보존한다.

완성 파일의 `packet_sha256`과 `response_sha256`은 저장된 원본 바이트
전체를 대상으로 계산한다.

### 응답 검증

각 응답은 다음 항목을 패킷과 정확히 일치시켜야 한다.

- `ROUTE=SHORTS`
- `review_round`
- `review_cycle_id`
- `packet_id`
- `sent_packet_sha256`
- 마지막 `external_review_status: PENDING_CODEX_REVIEW`

Round 2는 응답 본문에서 직접 읽은 권고가 `PASS_RECOMMENDED`일 때만
통과한다. JSON 게이트에 적힌 값만 신뢰하지 않는다.

### Codex 결정표

Round 1 제안은 `ADOPTED`, `PARTIALLY_ADOPTED`, `REJECTED`,
`PENDING_EVIDENCE` 중 하나로 모두 판정한다. `PENDING_EVIDENCE`가 남거나
제안 수와 결정 수가 다르면 Round 2 패킷을 만들지 않는다.

### 브라우저 경계

Python CLI는 ChatGPT에 로그인하거나 브라우저를 직접 조작하지 않는다.
Codex가 로그인된 Chrome으로 정확한 프로젝트를 열어 패킷을 전송하고,
새 응답 원문을 보존한 뒤 CLI 검증을 실행한다. 프로젝트를 열 수 없거나
응답을 복사할 수 없으면 `WAIT_CHATGPT_PROJECT_REVIEW`로 중단한다.

## 데이터 흐름

```text
timeline_design_gate PASS
-> build-round1
-> ChatGPT Project Round 1
-> record-response --round 1
-> Codex 결정표 작성
-> 채택 변경 반영 및 무효화된 설계 게이트 재실행
-> build-round2
-> ChatGPT Project Round 2
-> record-response --round 2
-> finalize-gate
-> tikitaka_harness_runner
-> SCRIPT_HANDOFF_GATE PASS
-> 20_script/design_blueprint.md
```

## 실패 상태

- 계약 파일 누락: `SOURCE_CONTRACT_MISSING`
- 프로젝트/로그인/새 응답 문제: `WAIT_CHATGPT_PROJECT_REVIEW`
- 응답 메타데이터 불일치: `WAIT_CHATGPT_PROJECT_REVIEW`
- 미결 Codex 판단: `WAIT_CODEX_REVIEW_DECISIONS`
- Round 2 수정·증거 요구: `WAIT_CHATGPT_REVIEW_REPAIR`
- 패킷 또는 응답 변조: 해시 불일치로 FAIL

## 범위

포함:

- 2회 검수 패킷과 게이트 자동화
- 라이브 프로젝트에 단일 Shorts 계약 연결
- 기존 하네스의 fail-closed 검증 강화
- Git 소스와 로컬 Codex 런타임 동기화
- 실제 Shorts URL 1개로 설계도 생성 검증

제외:

- ChatGPT API 사용
- 음성, SRT, CapCut, 렌더, 업로드 패키지 생성
- 정치 롱폼 계약 변경
- 기존 사용자 변경이나 TOP5 관련 파일 수정

## 성공 조건

- 신규 단위 테스트와 관련 회귀 테스트가 모두 통과한다.
- Round 1과 Round 2의 패킷·원문·결정표·게이트가 실제 에피소드에 남는다.
- Round 2가 `PASS_RECOMMENDED`가 아니면 하네스가 반드시 중단한다.
- 로컬 Codex의 `00-tikitaka`가 Git 완성본과 해시 일치한다.
- 실제 URL의 `20_script/design_blueprint.md`가 설계 단계 검증을 통과한다.
