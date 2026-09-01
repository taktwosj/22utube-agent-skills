# 렌더 확인 경계

정상 Stage09 router에서 render는 사용자 수동이며 자동화는 `WAIT_USER_CAPCUT_CHECK`에서 멈춘다. 이 문서는 Stage09 자동 명령이 아니고, 사용자 확인 없이 `validate_render.py`를 호출하거나 render evidence를 만들지 않는다.

사용자가 화면 확인과 export를 각각 명시한 별도 MCP export job은 [승인 후 MCP export](../capcut-export-telegram-handoff.md)를 따른다. 그 job에서도 `MP4_CREATED`, `MP4_VALIDATED`, `MCP_ARTIFACT_AVAILABLE`, `REMOTE_FILE_RETRIEVAL`을 각각 검증하며 하나를 다른 하나로 승격하지 않는다.
