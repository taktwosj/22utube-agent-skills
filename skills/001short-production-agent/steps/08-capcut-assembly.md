# 08 CapCut 조립
`FINAL_DESIGN_LOCKED`와 `AUDIO_CAPTION_VALIDATED` 증거, 편집 잠금, CapCut 종료, 근본 ZIP, 미디어/CFR, 필수 트랙을 먼저 확인한다. 승인 timeline·오디오 입력은 build contract로 고정하고 실제 경로와 SHA-256을 기록한다. 실패하면 오류 경로로 중단한다.

통과 후 immutable `shrt_white_base_v2` ZIP을 staging에만 풀고 `scripts/build_v2_contract_project.py`가 15개 `track_id` anchor로 기계 조립한다. source root는 수정하지 않으며, working copy의 schema·root/timeline parity·ID mirror·material reference·역할별 readback을 `scripts/validate_v2_contract_project.py`가 통과한 뒤에만 최종 프로젝트로 승격한다. 실패한 staging은 제거하고 `CAPCUT_STATIC_VALIDATED`를 기록하지 않는다.
