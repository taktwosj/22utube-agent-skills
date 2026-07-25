# 오디오·자막 검증

역할별 오디오를 실제 파일과 ffprobe validator로 검증해 duration·codec·audio stream 증거로 기록한다. SRT cue는 측정 시작·끝 및 계약의 `subtitle_roles`·`caption_bindings`와 일치해야 한다. 유료 호출·문구 재작성은 금지이며 입력이 없으면 WAIT, 불일치는 FAIL이다.
