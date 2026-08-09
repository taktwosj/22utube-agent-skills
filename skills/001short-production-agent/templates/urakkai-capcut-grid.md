# 우라까이 캡컷 표 — <episode_id>

`URAKKAI_CAPCUT_GRID_REQUIRED_ROWS`

> 승인 후보의 target 시간을 가로축으로, 실제 CapCut 논리 레이어를 세로축으로 기록한다. 모든 시간 칸을 채운다.

| 레이어 / target 시간 | <00:00.000–00:02.000> | <00:02.000–00:05.000> |
|---|---|---|
| VIDEO | <source 구간과 실제 사용할 화면> | <source 구간과 실제 사용할 화면> |
| T1 | <승인 후보 T1> | <승인 후보 T1> |
| T2 | <승인 후보 T2> | <승인 후보 T2> |
| A9 TTS | <실제 읽을 문장 / 해당 없음 — 이유> | <실제 읽을 문장 / 해당 없음 — 이유> |
| A9_TEXT | <A9과 같은 표시 문구 / 해당 없음 — 이유> | <A9과 같은 표시 문구 / 해당 없음 — 이유> |
| A10 원본화자발언 | <source range + retain/mute/duck + 발화> | <source range + retain/mute/duck + 발화> |
| A10_TEXT_WHITE | <primary speaker 문구 / 해당 없음 — 이유> | <primary speaker 문구 / 해당 없음 — 이유> |
| A10_TEXT_YELLOW | <other speaker 문구 / 해당 없음 — 이유> | <other speaker 문구 / 해당 없음 — 이유> |
| STATE | <현재 상황 문구 / 해당 없음 — 이유> | <현재 상황 문구 / 해당 없음 — 이유> |
| A11 | <SFX와 배치 / 해당 없음 — 이유> | <SFX와 배치 / 해당 없음 — 이유> |
| A12_RESERVED_EMPTY | <예약 비움 — 자동 조립 금지> | <예약 비움 — 자동 조립 금지> |
| SCREEN | <화면 효과와 baked text 처리> | <화면 효과와 baked text 처리> |

실제 산출물에서는 꺾쇠 placeholder를 제거하고 각 시간 헤더를 실측 `start–end`로 바꾼다. bare `없음`, `비움`, `UNVERIFIED`는 실패다.
