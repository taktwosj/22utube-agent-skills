# shrt_white_base_v3 canonical track matrix

Stage 05가 역할과 시간을 승인하고 Stage 08 builder는 아래 15개 물리 트랙에 기계적으로 배치한다. 트랙을 추가하거나 합치지 않는다.

| Index | Track | Contract |
|---:|---|---|
| 0 | VIDEO | SOURCE_VIDEO_PROVISIONAL의 `source.mp4` 또는 CLEAN_VISUAL_READY의 `clean_video.mp4`; embedded audio mute |
| 1 | SCREEN_EFFECT | 화면 효과 seed |
| 2 | SCREEN_WHITE | 전체 길이 흰 화면 seed |
| 3 | SOURCE_CREDIT | 전 구간 출처 표기; 선언 없으면 비움 |
| 4 | STATE_GLITCH | 예약 비움; 물리 트랙 유지 |
| 5 | STATE_LASER | `LASER_CUT` 상황설명 |
| 6 | A10_TEXT_WHITE | primary speaker 발언 |
| 7 | A10_TEXT_YELLOW | 그 외 확인된 화자 발언 |
| 8 | A9_TEXT | TTS 자막 |
| 9 | T2 | 승인된 T2 원문 그대로 |
| 10 | T1 | 승인된 T1 원문 그대로 |
| 11 | A9 | TTS 음성 |
| 12 | A10 | 검증된 Demucs vocal stem |
| 13 | A11 | 화면전환·반전·와우 SFX |
| 14 | A12_RESERVED_EMPTY | 반드시 비움; BGM은 이 계약 범위 밖 |

STATE의 의미 글자 수는 공백만 제외하고 15자 이하여야 한다. STATE가 없는 회차도 유효하다. `SPEAKER`는 A10_TEXT로만, `SITUATION` 또는 `STATE`는 STATE로만 라우팅하며 `UNASSIGNED` 화자는 추측하지 않고 WAIT 또는 FAIL 처리한다.
