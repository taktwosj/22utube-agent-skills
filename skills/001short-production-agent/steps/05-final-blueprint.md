# 05 최종 설계
Stage 04에서 승인된 원본표와 우라까이표만 반영한다. `references/shorts-structure-taxonomy.md`의 분류·우라까이·가단야 판단을 고정한다.

- `source_identity.json`, `approved_timeline.json`, `design_handoff.json`에는 4축 분류, source/target order signature, source/target beat 매핑, `remake_structure_pattern`, `resolution_type`, 와우포인트, 가단야 결과를 함께 기록한다.
- `TRANSFORM_APPROVED`는 실제 target VIDEO 순서가 source와 다르고 대화·인과·baked-in 순번 검수가 통과했을 때만 쓴다.
- `SAFE_UNCHANGED_FALLBACK`은 별도 clean-only 경로이고, `BLOCKED_REFERENCE`는 제작 단계로 보내지 않는다.

각 파일의 SHA-256과 승인 순서를 검증한다. 불일치하면 진행하지 않으며, 모두 일치할 때만 `FINAL_DESIGN_LOCKED`로 06에 인계한다.
