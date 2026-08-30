# 09 사용자 수동 최종화

`CAPCUT_STATIC_VALIDATED` 뒤 자동화는 `WAIT_USER_CAPCUT_CHECK`에서 끝난다. `AGENT_PRIMARY_CLEAN_SOURCE` 또는 `USER_FALLBACK_CLEAN_SOURCE` VIDEO-only swap/reassembly은 Stage08 계약으로 끝낼 수 있지만, CapCut 화면 확인·다듬기·승인, render, upload는 사용자가 직접 수행한다.

자동화는 `USER_VISUAL_CHECKED`, `CAPCUT_POST_OPEN_REVALIDATED`, `USER_APPROVED`, `RENDER_VALIDATED`, `WAIT_UPLOAD_APPROVAL`, `upload_ready`, 또는 `uploaded`로 상태를 진행하거나 그 결과를 주장하지 않는다. 사용자 확인 없이 render·upload evidence를 만들거나 다시 검증하지 않는다.
