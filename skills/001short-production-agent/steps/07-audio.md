# 07 오디오·자막 잠금

우라까이표의 실제 사용 행만 준비한다.

- A9가 있으면 실제 나레이션 파일을 검증하고 같은 시간·문장의 A9_TEXT를 만든다.
- STATE_LASER만 있으면 TTS 엔진을 호출하지 않는다. STATE는 음성 없는 상황설명문이다.
- A10이 있을 때만 Demucs로 원본 전체를 한 번 분리하고, 확정된 VIDEO 순서대로 화성 stem을 재배열한다.
- A10이 비움이면 Demucs와 A10 오디오 준비를 건너뛴다.
- A11은 실제 효과음이 있을 때만 사용한다. A12는 항상 비운다.
- A9_TEXT와 STATE_LASER는 한 줄 15자 이하, 최대 2줄이다.

실제 오디오 파일의 codec·duration·SHA-256과 자막 cue 정합을 검증한 뒤에만 `AUDIO_CAPTION_VALIDATED`로 진행한다.
