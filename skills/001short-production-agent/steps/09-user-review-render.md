# 09 사용자 수동 최종화

`CAPCUT_STATIC_VALIDATED` 뒤 정상 제작 자동화는 `WAIT_USER_CAPCUT_CHECK`에서 끝난다. `AGENT_PRIMARY_CLEAN_SOURCE` 또는 `USER_FALLBACK_CLEAN_SOURCE` VIDEO-only swap/reassembly은 Stage08 계약으로 끝낼 수 있지만, CapCut 화면 확인·다듬기·승인을 자동 추정하지 않는다.

정상 제작 router는 `USER_VISUAL_CHECKED`, `CAPCUT_POST_OPEN_REVALIDATED`, `USER_APPROVED`, `RENDER_VALIDATED`, `WAIT_UPLOAD_APPROVAL`, `upload_ready`, 또는 `uploaded`로 상태를 진행하거나 그 결과를 주장하지 않는다. 사용자 확인 없이 render·upload evidence를 만들거나 다시 검증하지 않는다.

별도 `2pow 22factory MCP` export job은 사용자가 `USER_CAPCUT_CHECK_PASS`와 `APPROVE_CAPCUT_EXPORT`를 모두 명시한 뒤에만 [승인 후 MCP export](../references/capcut-export-telegram-handoff.md)를 읽는다. 이 job은 정확한 기존 프로젝트를 열어 새 episode-local MP4를 내보내고 검증할 수 있지만 프로젝트 내용 수정·덮어쓰기·업로드는 할 수 없다.
