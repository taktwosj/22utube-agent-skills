# 00-tikitaka Harness Mode Lock Report

## 결론

이번 문제는 대본 품질 문제가 아니라 실행 증거 부재 문제였다. `SCRIPT_LOCK: PASS` 같은 문구는 모델의 말만으로 인정하면 안 되며, 파일·로그·콜백·검증표가 없으면 무조건 `DRAFT` 또는 `NOT_LOCKED`로 고정해야 한다.

## 원인

- 로컬 런타임 `00-tikitaka` 스킬이 공유 원본보다 짧은 구버전이었다.
- 기존 규칙은 5작가 모드와 SCRIPT_LOCK을 요구했지만, 최종 보고 문구를 `job_state.json`, `validation_report.json`, `evidence_pack.json`, `visual_gate.md` 같은 외부 증거에 묶는 fail-closed 장치가 부족했다.
- 그래서 실제 에이전트/하네스/n8n 실행 없이도 답변에서 `PASS`처럼 보이는 문구를 쓸 수 있었다.

## 수정 범위

- source skill: `{UTUBE_ROOT}/codex_skills_source/00-tikitaka/SKILL.md`
- local runtime skill: `%USERPROFILE%/.codex/skills/00-tikitaka/SKILL.md`
- new runner: `{UTUBE_ROOT}/codex_skills_source/00-tikitaka/scripts/tikitaka_harness_runner.py`
- local runner: `%USERPROFILE%/.codex/skills/00-tikitaka/scripts/tikitaka_harness_runner.py`

## 추가된 LOCK 규칙

`SKILL.md`에 `[LOCK] HARNESS / SCRIPT_LOCK / FINAL REPORTING RULE` 섹션을 추가했다.

핵심 규칙:

- 말로 된 완료는 완료가 아니다.
- `SCRIPT_LOCK: PASS`, `HARNESS: PASS`, `n8n: DONE`, `최종본`, `완료했습니다`, `검수 완료`, `락 걸었습니다`, `배포 가능`은 증거 없이는 금지다.
- `work_order.md`, `execution_spec.md`, `implementation_log.md`, `persona_outputs/`, `script_gate_report.json`, `validation_report.json`, `evidence_pack.json`, `harness_trace.log`, `visual_gate.md`, `job_state.json`이 필요하다.
- n8n은 execution id, callback log, webhook response, output artifact, 또는 `job_state.json`의 `n8n.status=DONE` 증거가 있어야 실행으로 인정한다.
- 하나라도 없으면 `DRAFT`, `NOT_LOCKED`, `NOT_RUN`, `UNVERIFIED`, 또는 `FAILED`로 보고한다.

## 추가된 러너

명령:

```powershell
py -3 {UTUBE_ROOT}\codex_skills_source\00-tikitaka\scripts\tikitaka_harness_runner.py {work_dir} --job-id {job_id}
```

생성/갱신 파일:

- `job_state.json`
- `validation_report.json`
- `evidence_pack.json`
- `visual_gate.md`
- `harness_trace.log`

동작:

- 증거가 없으면 `final_report_allowed=false`
- n8n 증거가 없으면 `n8n: NOT_RUN`
- 5작가 산출물이 5개 미만이면 `5작가 모드: NOT_RUN`
- script gate 증거가 없거나 pass count/hard veto 조건이 맞지 않으면 `Script Gate: FAILED` 또는 `NOT_RUN`
- 모든 증거가 통과할 때만 `SCRIPT_LOCK: SCRIPT_LOCKED`

## 검증 결과

빈 증거 폴더 테스트:

```text
EXIT=2
SCRIPT_LOCK: NOT_LOCKED
최종 상태: DRAFT
완료 보고 가능 여부: NO
```

모든 증거가 있는 모의 폴더 테스트:

```text
EXIT=0
SCRIPT_LOCK: SCRIPT_LOCKED
최종 상태: SCRIPT_LOCKED
완료 보고 가능 여부: YES
```

로컬 런타임 테스트:

```text
EXIT=2
SCRIPT_LOCK: NOT_LOCKED
최종 상태: DRAFT
완료 보고 가능 여부: NO
```

로컬/원본 `SKILL.md` SHA256 해시가 일치했다.

## 백업 / 롤백

수정 전 백업:

```text
{UTUBE_ROOT}/codex_skills_source/_backups/tikitaka_harness_mode_20260608-131936/source_SKILL.md
{UTUBE_ROOT}/codex_skills_source/_backups/tikitaka_harness_mode_20260608-131936/local_SKILL.md
```

롤백 방법:

```powershell
Copy-Item "{UTUBE_ROOT}\codex_skills_source\_backups\tikitaka_harness_mode_20260608-131936\source_SKILL.md" "{UTUBE_ROOT}\codex_skills_source\00-tikitaka\SKILL.md" -Force
Copy-Item "{UTUBE_ROOT}\codex_skills_source\_backups\tikitaka_harness_mode_20260608-131936\local_SKILL.md" "%USERPROFILE%\.codex\skills\00-tikitaka\SKILL.md" -Force
```

## 남은 주의

현재 채팅은 이미 시작된 런타임 컨텍스트라 스킬 재로드가 보장되지 않는다. 새 채팅 또는 런타임 새로고침 후부터 강화된 `00-tikitaka` 규칙이 안정적으로 적용된다.
