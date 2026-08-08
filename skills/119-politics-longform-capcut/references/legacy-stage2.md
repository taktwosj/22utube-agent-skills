# 레거시 Stage 2

사용자가 기존 Stage 2 산출물 사용을 명시한 회차만 이 문서를 읽는다. 직접 대본 경로에는
이 산출물, 영수증, preflight를 만들거나 요구하지 않는다.

## 입력

```text
episode_id / active_writer_machine / lock_owner
20_script/design_blueprint_approved.json
20_script/design_blueprint_approved.md
10_analysis/timeline_design_approved.json
90_reports/external_review_gate.json
10_analysis/speech_boundary_lock.json
10_analysis/roughcut_edl_locked.json
10_analysis/source_labels_locked.json
20_locked_clips/locked_clips_manifest.json
```

공식 Stage 2의 `speech_boundary_lock.boundaries`를 정상 schema로 받는다. 오래된 산출물의
`clips`는 legacy 호환 입력일 수 있지만, 공식 `boundaries`가 있고 `clips`가 없다는 이유만으로
정상 입력을 실패 처리하지 않는다. ASR cue는 편집 컷을 지배하지 않으며 실제 컷에서 표시
자막만 split 또는 clamp한다.

## Preflight

```powershell
python scripts/validate_politics_capcut_inputs.py `
  --episode-dir <episode_dir> `
  --report <episode_dir>\90_reports\capcut_stage2_preflight_v1.json `
  --active-writer-machine <home_windows|office_windows|macmini> `
  --lock-owner <owner>
```

`PASS`가 아니면 `WAIT_STAGE2_INPUTS`다. preflight는 읽기 전용이며 CapCut 프로젝트,
미디어, 잠긴 원본을 바꾸지 않는다. 실패한 입력 하나만 고쳐 같은 preflight를 다시 실행한다.
PASS 뒤 `INPUT_ROUTE=LEGACY_STAGE2_PREFLIGHT`와 `STAGE2_PREFLIGHT=PASS`를 보고한다.

검증된 Stage 2 산출물을 소비하는 기존 공식 builder 또는 adapter를 사용한다. 직접 경로의
A–D join을 요구하지 않고 `episode_cards.json`을 손으로 만들지 않는다. 공식 adapter가
`episode_cards.json`을 출력한 경우에만 이를 확인하고 [capcut-assembly.md](capcut-assembly.md)의
Build 절부터 진행한다. 사용할 공식 adapter가 없으면 `WAIT_LEGACY_CARD_ADAPTER`로 멈춘다.
