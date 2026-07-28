# 04 우라까이 2회 검토 개선

`URAKKAI`에서만 검토 개선 loop를 정확히 2회 실행한다.

1. Loop 1: 현재 승인 후보를 first-party Claude OAuth의 Claude Opus `--effort low`로 검토한다. Hermes가 훅 명확성·장면 이해도·이탈 지점·대사 중복·감정 연결 의견을 평가하고 후보를 개선한다.
2. Loop 2: Loop 1 개선본을 같은 범위로 다시 검토한다. Hermes가 다시 개선한 뒤 baseline·Loop 1·Loop 2 후보 중 계약을 지키는 최상안을 확정한다.

Claude는 조언자다. source/target range, segment ID, 장면 수, 실제 오디오 timing의 권위는 Hermes가 유지한다. 실패한 loop만 동일 입력의 Hermes 서브에이전트 검토 1회로 대체한다. 두 loop의 입력·출력 hash, 채택·반려, 개선점과 최종 선택 사유를 `20_script/external-review.md`와 `20_script/external-review.json`에 기록한다. 토큰·쿠키·conversation/session ID는 기록하지 않는다. 두 loop 증거가 모두 없으면 `WAIT_EXTERNAL_REVIEW`에서 멈춘다.
