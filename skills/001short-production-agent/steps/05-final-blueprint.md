# 05 최종 설계
외부 검토 중 원본으로 확인된 개선만 반영한다. 승인 설계를 `source_identity.json`, `approved_timeline.json`, `design_handoff.json`으로 고정하고 각 파일의 SHA-256과 승인 순서를 검증한다. 불일치하면 진행하지 않으며, 모두 일치할 때만 `FINAL_DESIGN_LOCKED`로 06에 인계한다.
