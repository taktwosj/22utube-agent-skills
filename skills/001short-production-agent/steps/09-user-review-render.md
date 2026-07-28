# 09 사용자 확인·재검증·승인·렌더

`CAPCUT_STATIC_VALIDATED` 뒤 CapCut에서 사용자가 화면을 직접 확인하고 `USER_VISUAL_CHECKED`를 기록한다. CapCut을 닫은 뒤 같은 CapCut 검증 증거의 경로·SHA-256과 episode_id에 연결해 ID·경로·duration·참조를 다시 검사하고 `CAPCUT_POST_OPEN_REVALIDATED`를 기록한다. 재검증이 실패하면 승인하지 않고 08에서 근본 ZIP으로 재생성한다.

사용자 승인 `USER_APPROVED`는 위 두 이벤트 다음에만 기록한다. Stage09 review evidence는 세 이벤트를 정확한 순서로 담고, 첫 이벤트는 CapCut evidence SHA-256에, 다음 이벤트는 직전 이벤트의 canonical SHA-256에 연결해야 한다. validator는 review evidence 자체 SHA-256, episode_id, CapCut evidence 연결, 이벤트 순서·체인, 현재 프로젝트의 post-open 상태를 모두 다시 확인한다.

그 뒤 렌더 파일의 존재·크기·video stream·decode·duration을 확인한다. render evidence 출력은 명시한 승인 root 내부의 alias·hardlink 없는 신규 파일에만 쓴다. 모두 맞아야 `RENDER_VALIDATED`다. 업로드·게시·전송은 별도 승인 전 `WAIT_UPLOAD_APPROVAL`로 멈춘다.
