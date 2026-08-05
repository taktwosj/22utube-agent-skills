# 02 원본 설계도
원본을 보지 않은 제작자도 벤치마킹 쇼츠를 재현할 수준으로 작성한다.

먼저 `references/shorts-structure-taxonomy.md`의 4축을 판정한다. 소재·화면 템플릿·전달 방식·원본 서사 구조를 서로 대신 쓰지 않는다. 이 단계는 관찰만 하며 우라까이·TTS·개선 판단은 Stage 03으로 넘긴다.

- 장면·원본 구간·문구·음성·효과·좌표를 기록하며 사용자 취향 변경은 넣지 않는다.
- 임의의 5초·1초 등 정률 구간으로 자르지 않고 자막 등장·퇴장, 화자·대사 전환, 차량·인물 행동, 효과음·화면 처리 변화 시점으로 구조를 나눈다.
- `SOURCE_OBSERVATION`, `SCREEN_LABEL`, `SCREEN_CLAIM`, `TRANSCRIPT`, `UNVERIFIED`를 구분한다. 화면 제작자 설명이나 화자 라벨을 독립 검증된 사실로 승격하지 않는다.
- 화자·욕설·창문음·현장음·편집 SFX·BGM이 원본에서 명확하지 않으면 `UNVERIFIED`로 남긴다.
- 텍스트는 문구뿐 아니라 1080×1920 기준 위치·bbox·정렬·줄 수·대표색·외곽선/배경·등장 구간을 기록한다.
- `templates/original-capcut-grid.md`를 복사해 `original-blueprint.md`의 CapCut 세로줄 원본표를 작성한다. `ORIGINAL_CAPCUT_GRID_REQUIRED_ROWS`: `T1`, `T2`, `A9 TTS`, `A9_TEXT`, `A10 작가 나레이션`, `A10 화자발언 1`, `A10 화자발언 2`, `A10 화자발언 3`, `STATE 상황설명문구`를 모든 source 구간 열에 반드시 작성한다.
- 각 칸에는 원본 문구·발화·시간·화면 상태 또는 근거 있는 부재 사유를 넣는다. bare `없음`, `비움`, `UNVERIFIED`만 쓰지 않는다. title evidence가 없으면 `미확정 — 제목 evidence 필요`, 화자 ID가 없으면 `화자발언 N (인물 미확정)`과 해당 발화를 쓴다.
- `A9 TTS`는 원본 작가 나레이션 재현 대본이고 새 WAV가 아니다. `A9_TEXT`는 같은 원문을 한 줄 15자 이하로 줄바꿈만 하며, 원문 의미를 줄이거나 바꾸지 않는다. `STATE 상황설명문구`는 현재 행동·감정·관계를 나타내는 짧은 비문장 문구로 쓴다.
- 변화 구간마다 `source_beat_id`, `story_function`, `dialogue_dependency`, `baked_order_semantics`, `hook_candidate`를 기록하고 `source_order_signature`를 만든다.
- 원본 설계도에서 해석·평가·개선안은 제외하고 Stage 03 1차 추천으로 분리한다.
