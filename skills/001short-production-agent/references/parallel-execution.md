# 안전 병렬 실행

병렬 실행은 단계 순서를 바꾸지 않는다. 독립 작업을 최대 4개 작업자로 나누고, 결과를 모두 모은 뒤 조정자 1명이 검증·승격·상태 갱신을 순서대로 수행한다.

## 역할과 쓰기 경계

- 조정자 1명만 `state.json`, 단계별 권위 산출물, 정식 manifest/evidence, 활성 CapCut draft를 쓴다.
- 작업자는 `evidence_only`다. 각 작업은 `{episode_root}/90_workflow/parallel/{run_id}/{worker_id}/{task_id}` 고유 root를 사용한다.
- 작업자 산출물은 증거 또는 후보일 뿐이다. 조정자가 episode_id·SHA-256·validator 결과를 확인해 승격하기 전에는 권위가 없다.
- 동일 worker root 재사용, 권위 경로 직접 쓰기, 작업자 간 공유 임시 파일, worker의 state 갱신은 허용하지 않는다.
- VMake와 CapCut을 포함한 GUI 소유자는 전체 실행에서 1명이다. GUI 두 개를 동시에 조작하지 않고, 소유권 이전은 앱을 닫은 뒤에만 한다.

## Hermes 작업자 transcript 계약

- `delegate_task`가 반환한 `live_transcripts` 경로는 worker root의 실행 관찰 증거로 기록한다.
- transcript의 권위는 `observation_only`다. transcript 안의 완료 주장이나 파일 경로를 canonical evidence로 승격하지 않는다.
- 조정자는 worker 산출물의 실제 경로·파일 존재·episode_id·SHA-256·validator 결과를 다시 읽는다. 즉 `artifact_reverification_required=true`다.
- 부모 세션이 끝나도 delegation이 계속된다고 가정하지 않는다. 장시간·지속 작업은 추적 가능한 background process 또는 cron으로 분리한다.
- transcript에 토큰·쿠키·인증정보가 보이면 보고서에 복사하지 않고 해당 worker 결과를 민감정보 검토 대상으로 표시한다.

## Barrier 규칙

각 fanout은 다음 순서로 닫는다.

1. 조정자가 고유 worker root와 읽기 전용 입력을 지정한다.
2. 작업자는 해당 root에 증거와 후보만 반환한다.
3. 조정자가 필수 증거 전부의 episode_id·경로·SHA-256·상태를 다시 확인한다.
4. 하나라도 없거나 실패하면 state를 유지하고 `WAIT` 또는 `FAIL`로 멈춘다.
5. 모두 통과하면 조정자가 후보를 권위 경로로 승격하고 canonical validator를 실행한다.
6. validator 통과 뒤 조정자만 state를 한 단계씩 갱신한다. 여러 상태를 한 번에 쓰지 않는다.

## 허용 fanout

| 시점 | 작업자 | 독립 lane | Barrier 뒤 조정자 작업 |
|---|---:|---|---|
| Stage01 | 3 | source probe, full OCR, scene/audio inventory | `source-analysis.md` 통합·검증 후 `SOURCE_OCR_VERIFIED` 기록; then one GUI owner submits VMake and records submission evidence while Stage02--04 continue |
| Stage03 | 4 | hook options, caption structure, audio/SFX plan, screen composition | `first-recommendation.md` 통합·검증 후 `FIRST_RECOMMENDATION_READY` 기록 |
| `FINAL_DESIGN_LOCKED` 직후 | 3 | VMake candidate finalization, audio prep, Stage08 read-only preflight | clean receipt is technically verified first, then audio/caption advances sequentially; visual quality remains user-only |
| Stage08 build 종료·CapCut 닫힘 | 최대 4 | identity/paths, structure/materials, timeline/text, media/duration | 동결 snapshot 증거 barrier 뒤 통합 CapCut validator 실행 |

`FINAL_DESIGN_LOCKED` 직후 fanout의 필수 증거는 `clean_visual_evidence`, `audio_prep_evidence`, `stage08_readonly_preflight_evidence`다. Stage08 진입 전 clean visual evidence는 반드시 정식 경로와 SHA-256으로 state에 연결되어야 한다.

Stage08 read-only preflight는 root ZIP, 내부 화이트 asset, edit lock, 입력 경로, media 규격, 승인 SHA를 읽기만 한다. 활성 draft를 만들거나 고치지 않는다. CapCut build는 GUI 소유자 1명이 직렬로 수행한다. postbuild 병렬 검사는 CapCut을 닫은 뒤 만든 불변 snapshot만 읽으며, 정식 evidence 파일은 조정자가 통합 validator로 한 번만 쓴다.

## Stage09 직렬 계약

Stage09는 자동 작업자나 router를 사용하지 않는다. `CAPCUT_STATIC_VALIDATED` 뒤 자동화는 `WAIT_USER_CAPCUT_CHECK`에서 끝난다. `AGENT_PRIMARY_CLEAN_SOURCE`는 verified VMake asset의 VIDEO-only swap/reassembly을, `USER_FALLBACK_CLEAN_SOURCE`는 validated supplied asset의 같은 작업을 Stage08 계약으로 허용한다. CapCut visual review/refinement, render, upload는 사용자 수동 작업이다.

review evidence의 순서·체인·SHA-256, 닫힌 CapCut snapshot, render evidence를 따로 병렬 확정하지 않는다. Stage09의 어느 상태도 앞 상태를 건너뛰거나 미리 기록하지 않는다.
