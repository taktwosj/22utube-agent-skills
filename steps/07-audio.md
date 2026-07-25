# 07 오디오
원본 BGM은 가능하면 제거·감쇄한다. 화자·동물·포인트 음성은 A10, TTS는 A9, 효과음은 A11, 새 BGM은 A12에 설계된 구간만 배치한다. 실제 오디오 파일을 ffprobe로 확인하고 duration·codec·stream을 기록한다. SRT cue와 승인된 A9·A10 오디오 구간이 일치할 때만 `AUDIO_CAPTION_VALIDATED`다.
