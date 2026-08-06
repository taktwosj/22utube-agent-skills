# 05 최종 설계
외부 검토 중 원본으로 확인된 개선만 반영한다. `references/shorts-structure-taxonomy.md`의 분류·우라까이·가단야 판단을 고정한다.

- `source_identity.json`, `approved_timeline.json`, `design_handoff.json`에는 4축 분류, source/target order signature, source/target beat 매핑, `remake_structure_pattern`, `resolution_type`, 와우포인트, 가단야 결과를 함께 기록한다.
- `TRANSFORM_APPROVED`는 실제 target VIDEO 순서가 source와 다르고 대화·인과·baked-in 순번 검수가 통과했을 때만 쓴다.
- `SAFE_UNCHANGED_FALLBACK`은 별도 clean-only 경로이고, `BLOCKED_REFERENCE`는 제작 단계로 보내지 않는다.
- `shrt_white_base_v2` 정본은 `scripts/compile_production_plan.py`로 승인된 `approved_timeline.json`을 실행 가능한 15트랙 production plan으로 컴파일한다. 대표 화자는 `A10_TEXT_WHITE`, 그 밖의 확정 화자는 `A10_TEXT_YELLOW`, 미확정 화자는 추측 없이 `A10_TEXT_UNASSIGNED`로 라우팅한다. `STATE`는 승인된 효과 하나만 `STATE_EFFECT_1~3`에, 전환·반전·와우 SFX는 승인된 seed만 `A11_SFX`에 배치한다.

각 파일의 SHA-256과 승인 순서를 검증한다. 불일치하면 진행하지 않으며, 모두 일치할 때만 `FINAL_DESIGN_LOCKED`로 06에 인계한다.
