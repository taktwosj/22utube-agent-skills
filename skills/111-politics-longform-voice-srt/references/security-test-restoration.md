# 111 보안 검사 복구 대응표

기준 비교: PR #12 이전 `b0be9080`의 111 테스트 86개와 현재 공유
110→111 계약. 단순 테스트 개수 대신 통제 목적이 어느 단계에서 집행되는지 기록한다.

| 이전 통제 목적 | 현재 집행 위치 | 대표 회귀 테스트 | 판정 |
|---|---|---|---|
| schema/status/episode/producer/next stage 고정 | 111 `gate_lock.py` exact top-level 검사 | `test_wrong_schema_blocks`, `test_status_must_be_locked`, `test_wrong_episode_blocks`, `test_producer_must_be_110`, `test_next_stage_must_be_111` | 유지 |
| 잠금 입력 누락·악성 경로·SHA 변조 차단 | 111 evidence exact set + episode 상대경로 + SHA | `test_missing_required_evidence_blocks`, `test_absolute_evidence_path_blocks`, `test_parent_traversal_blocks`, `test_tampered_review_file_blocks` | 유지 |
| 잠금 후 대본 변조·승인본/잠금본 불일치 차단 | 111 script SHA + byte identity | `test_locked_script_hash_mismatch_blocks`, `test_locked_script_must_equal_approved_script` | 유지 |
| unresolved/high/quote mismatch/deferred 0 강제 | 110과 111이 검수문 5개 카운터를 모두 0으로 검사 | `test_nonzero_review_summary_blocks`, `test_unresolved_high_blocks`, `test_deferred_tts_blocks` | 복구·강화 |
| 검수 보고서 위반 수와 실제 항목 합계 일치 | 110·111이 exact check set, list/count/total을 각각 검사 | `test_report_check_violation_cannot_hide_behind_zero_total`, `test_report_check_count_must_match_violation_list`, `test_report_boolean_count_is_rejected`, `test_report_missing_security_check_is_rejected`, `test_report_extra_check_is_rejected` | 복구·강화 |
| 외부 검수자와 실행자 분리 | `review_origin`, `recorded_by`, approval executor 비교 | `test_review_origin_must_match_authority`, `test_executor_cannot_record_own_review`, 110 `TestSelfApproval` | 유지 |
| 사용자 승인 출처·검수/승인 event 분리 | `user_message` 강제, event ID 분리·결합 | `test_inferred_user_approval_is_rejected`, `test_review_and_user_events_must_differ`, 110 `test_shared_event_id_is_rejected` | 복구·강화 |
| Claude 대체 경로 오용 차단 | CLAUDE 우선, CODEX_CLI는 `CLAUDE_CALL_FAILED` 보고서 경로·SHA·대본 SHA가 있을 때만 허용 | `test_codex_cli_fallback_passes_same_contract`, `test_codex_cli_without_failure_evidence_blocks`, 110 동명 테스트 | 통일 |
| source packet 신뢰성 | 110 source SRT review PASS + 사용자 음성 확인 receipt + SRT SHA를 packet과 lock에 결합, 111 재검증 | `test_source_srt_review_wait_status_blocks`, `test_source_srt_review_receipt_errors_block`, `test_source_srt_review_packet_binding_mismatch_blocks`, 110 `test_source_srt_quality_gate.py` | 신규 강화 |
| segment 순서·중복 ID·kind·chapter mapping | 111이 self-declared 구조 JSON을 신뢰하지 않고 110의 단일 markdown parser와 source reference/declared count 검증 결과를 SHA로 잠금 | 110 `test_md_parser.py`, `test_verify_integration.py`; root `test_110_lock_passes_111_gate_without_translation` | 소유권 이동 |
| hook/label이 다른 segment를 참조하거나 발명되는 문제 | 별도 hook/label 사본을 script lock에서 제거. 최종 markdown 전체를 단일 byte SHA로 잠가 downstream이 별도 문구를 만들 수 없게 함 | `test_post_lock_evidence_edit_is_rejected_by_111`, 110 quote/source/packet binding 테스트 | 표현 제거·통제 유지 |
| editorial decision key 오탈자·false 우회 | self-asserted boolean 묶음을 제거하고 실제 110 verification exact check set + 독립검수 + 사용자 승인으로 대체 | 가짜 보고서·missing/extra check·approval/review provenance 테스트 | 대체·강화 |
| `tts_params` key·형식·값·runtime override 차단 | 111 별도 `tts_params_lock_v1.json`, exact fields, non-empty string, numeric type, speed/variance > 0, script SHA 결합 | `test_tts_lock_rejects_*`, `test_runtime_speed_mismatch_raises`, `test_tts_lock_must_match_script_sha` | 복구·강화 |
| render target 무결성 | 110 script lock에서 제거하고 112 입력/템플릿 계약의 소유로 유지 | 112 production input/template gate | 올바른 단계로 이동 |

`CODEX_SUBAGENT`는 공유 계약에서 제거했다. 110이 실제로 생성할 수 있는 검수자 값은
`CLAUDE`와 `CODEX_CLI`뿐이며 111도 같은 두 값만 허용한다.

현재 111 테스트 수는 92개다. 테스트 수 증가 자체를 안전성 근거로 삼지는 않으며,
위 표의 통제 목적과 110→111 실제 통합 테스트 통과를 병합 조건으로 사용한다.
