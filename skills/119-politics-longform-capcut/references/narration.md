# 나레이션

대본 승인 뒤 B 작업자 한 명이 수행한다. 입력은 승인 대본의 나레이션 문장이다. 출력은
이 회차의 narration audio/video와 narration SRT뿐이다. source, Resources, root, target,
CapCut draft, `episode_cards.json`을 수정하지 않는다.

## 순서

1. 기존 Supertone 설정이 있으면 119 내부에서 사용해 승인된 나레이션 문장만 합성한다.
2. 생성 직후 파일 존재, audio stream, duration을 확인한다.
3. 실제 audio를 시간축 정본으로 강제 정렬한다.
4. 정렬 결과로 narration SRT를 만든 뒤 문장 누락·중복·역순·시간 겹침을 확인한다.

직접 경로의 `NARRATION_TTS`는 119가 생성하고 승인 대본에 맞춰 정렬한 narration SRT를
사용한다. 사용자가 기존 111 SRT를 직접 제공했다면 선택 입력으로 가져올 수 있지만 111의
실행, lock, receipt, 산출물은 필수 조건이 아니다.

## 실패와 재개

활성 문장 또는 파일의 API·audio integrity·alignment·SRT 검사에서 구체적 실패가 난 부분만
다시 실행한다. 정상인 합성 파일은 재생성하지 않는다. 실제 narration media와 SRT가
재개점이며 별도 receipt나 checkpoint를 만들지 않는다.

완료 시 join owner에게 실제 경로, duration, SHA-256, SRT cue만 전달한다.
