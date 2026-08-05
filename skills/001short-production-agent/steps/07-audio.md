# 07 오디오
원본 배경음 성분은 제거한다. A12는 비운다. 화자·동물·포인트 음성은 A10, TTS는 A9, 효과음은 A11에만 배치한다. 실제 오디오 파일을 ffprobe로 확인하고 duration·codec·stream을 기록한다. SRT cue와 승인된 A9·A10 오디오 구간이 일치할 때만 `AUDIO_CAPTION_VALIDATED`다.

원본 화자 음성을 남기는 경우에는 `references/source-vocal-separation.md`를 읽고 실제 Demucs stem `vocals.wav`만 A10에 넣는다. CapCut 보컬 유지 설정만으로는 배경음 제거 완료가 아니다.
