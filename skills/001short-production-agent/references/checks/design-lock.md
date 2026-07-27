# 최종 설계 잠금 검증

실제 `design_handoff`, source identity, 승인 timeline 입력을 열어 validator가 schema와 SHA-256 증거로 확인한다. 보고문이나 상태 문자열은 증거가 아니다. 세 파일과 승인 순서가 일치해야 `FINAL_DESIGN_LOCKED`다.
