# 07 오디오·자막 잠금

우라까이표의 실제 사용 행만 준비한다.

- A9가 있으면 실제 나레이션 파일을 검증하고 같은 시간·문장의 A9_TEXT를 만든다.
- STATE_LASER만 있으면 TTS 엔진을 호출하지 않는다. STATE는 음성 없는 상황설명문이다.
- `CAPTION_ONLY_MUTE_SOURCE`는 A9/A9_TEXT/A10/A10_TEXT/A11을 비우고 VIDEO를 0으로 둔다. 전체 길이의 `SILENCE` WAV는 SHA·duration 검증용으로만 잠그며 CapCut에 삽입하지 않는다.
- `SOURCE_ORDER_UNCHANGED_CLEAN_ONLY`는 원본 A10을 그대로 쓰며 Demucs를 실행하지 않는다.
- Demucs는 사용자가 선택한 두 stem 모드에서만 원본 전체를 한 번 분리한다. `SOURCE_ORDER_UNCHANGED_A10_RETAINED`는 검증된 전체 stem, `URAKKAI`는 확정 VIDEO 순서로 재조립한 stem을 쓴다.
- A11은 실제 효과음이 있을 때만 사용한다. A12는 항상 비운다.
- A9_TEXT와 STATE_LASER는 한 줄 15자 이하, 최대 2줄이다.

실제 오디오 파일의 codec·duration·SHA-256과 자막 cue 정합을 검증한 뒤에만 `AUDIO_CAPTION_VALIDATED`로 진행한다.
정상 cue는 Bxx source time과 B→V mapping을 재사용한 `caption_timing_evidence.json`으로 검증한다. AI·이미지 재검토는 오류 cue에만 사용한다. 자막이 없으면 timeline·lock·SRT·evidence가 모두 빈 상태여야 한다.
