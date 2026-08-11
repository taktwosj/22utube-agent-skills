# 오디오·자막 검증

역할별 오디오를 실제 파일과 ffprobe validator로 검증해 duration·codec·audio stream 증거로 기록한다. 명시된 production mode·audio policy·audio source만 허용하고 자동 stem 전환을 금지한다. SRT cue는 Bxx source time과 B→V mapping receipt, `subtitle_roles`, `caption_bindings`와 전단사로 일치해야 한다. 정상 cue에 AI 검토를 반복하지 않는다. zero-caption은 timeline·lock·SRT·receipt가 모두 비었을 때만 PASS다.
