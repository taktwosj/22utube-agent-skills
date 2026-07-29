# 정치 다큐 기본 디자인 프리셋

## 권위

```text
PROFILE_ID=politics_documentary_broadcast_v3
PROFILE_AUTHORITY=../assets/political-documentary-defaults.json
VISUAL_REFERENCE=../assets/political-documentary-reference-frames.json
DEFAULT=LOCKED
OVERRIDE=LATEST_EXPLICIT_USER_INSTRUCTION_ONLY
```

사용자가 다른 디자인을 명시하지 않으면 이 프리셋을 사용한다. 공용 템플릿
`style_tokens.json`은 바꾸지 않고 episode CSS·SVG·`design.md`에만 적용한다.
구체적인 화면 밀도와 배치는 [visual-reference-frames.md](visual-reference-frames.md)의
승인 시안을 최우선 기준으로 삼는다.

## 영상 디자인

- 방향: 게임 HUD·사이버펑크·네온 UI를 제거한 방송사 정치 다큐멘터리 톤.
- 우선순위: 신뢰감, 긴장감, 가독성, 여백, 정렬, 타이포그래피.
- 배경: 딥 네이비 `#071426`에서 블랙으로 이어지는 낮은 대비 그라데이션.
- 패널: `#0D2038`. 기본 텍스트 `#F3F6FA`. 보조 텍스트 `#9EB0C4`.
- 포인트: 시안 `#21C7D9`. 선택 강조: 머스터드 `#F4C542`.
- 노란색은 현재 선택 항목과 핵심 문장에만 사용하고 한 화면 3곳을 넘기지 않는다.
- 본문 좌측 챕터 내비게이션은 25~27%, 우측 콘텐츠는 73~75%를 사용한다.
- 12컬럼 그리드와 자막 안전영역을 지키고 두꺼운 사각 외곽선을 사용하지 않는다.
- 서체는 최대 2종. 붓글씨, 검은 외곽선, 중복 그림자, 강한 글로우를 금지한다.
- 대각선 장식은 제거하고, 필요한 구조선은 낮은 불투명도로 2~3개만 둔다.
- 큰 챕터 숫자는 배경에 5~8% 불투명도로만 사용한다.
- 제목은 굵고 단정한 고딕 또는 현대적 명조로 최대 2줄 이내에 둔다.
- 상단은 좌측 `CHAPTER N`, 중앙 챕터 제목, 우측 CTA로 고정한다.
- `CHAPTER N`은 기존 대비 약 1.7배, 중앙 제목은 약 1.35~1.5배 확대한다.
- 좌측 목록은 bullet 없이 번호로 바로 시작한다. 활성 행은 금색 세로선과 번호,
  흰색 제목만 강조하고 행 전체를 박스로 감싸지 않는다.
- 나레이션 장면의 구조 선택은
  [narration-visual-grammar.md](narration-visual-grammar.md)를 따른다.

## 고정 표기

```text
SOURCE_POSITION=LEFT_TOP
SOURCE_LABEL=ACTUAL_YOUTUBE_CHANNEL_NAME
SOURCE_INTERNAL_ID_VISIBLE=false
SOURCE_DATE=UPLOAD_DATE
HEADER_COMMENT_POSITION=RIGHT_TOP
COMMENT_LINE_1=댓글로 의견 부탁드립니다.
COMMENT_LINE_2=구독과 좋아요 부탁드립니다.
HEADER_COMMENT_ON_CHAPTER_FRAMES=true
BOTTOM_RIGHT_COMMENT=false
FINAL_CTA_END_CARD=true
```

`원본 S12`처럼 내부 source ID를 화면에 노출하지 않는다. 실제 유튜브 채널명과
업로드 날짜를 쓴다. 댓글·구독 문구는 본문보다 낮은 우선순위로 챕터 화면 상단
우측에 두고 우측 하단에는 반복하지 않는다. 영상 마지막에는 같은 두 문장을 중앙에
배치한 전용 CTA 엔딩 화면을 한 번 사용한다.

## 모션

- 배경 페이드 0.3초.
- 챕터 라벨과 제목은 아래에서 12~20px 이동하며 페이드 인.
- 선택지는 0.08~0.12초 간격으로 순차 등장.
- 선택 포인트는 한 번만 점등.
- 바운스, 회전, 강한 확대, 반복 점멸, 네온 글로우를 금지한다.
- 첫 프레임의 주요 정보는 숨기지 않고 seek-safe하게 만든다.

## 썸네일 전달 형식

항상 아래 5항목을 이 순서와 이름으로 전달한다.

```text
추천 이미지 인물 3명:
후킹 단어 3개:
메인 문구 1:
보조 문구 2:
디자인:
```

- 추천 이미지 인물은 정확히 3개를 제시한다. 동일 핵심 인물을 세 번 추천해도 된다.
- 동일 인물 3개일 때는 정면·결연한 표정·연설 장면처럼 컷 성격을 다르게 제시한다.
- 후킹 단어는 정확히 3개다.
- 메인 문구는 하나, 보조 문구는 최대 두 줄이다.
- 메인 문구는 영상의 첫 결론과 같은 방향으로 쓴다.
- 16:9, 딥 네이비 배경, 흰색 본문, 핵심 단어만 머스터드로 강조한다.
- 게임 HUD, 붓글씨, 두꺼운 외곽선, 과도한 네온을 사용하지 않는다.

## 완료 점검

```text
게임 HUD·사이버펑크 인상 0
노란색 강조 지점 화면당 3개 이하
실제 유튜브 채널명·업로드 날짜 표시
내부 source ID 노출 0
댓글·구독 고정 문구 상단 우측, 전용 엔딩 화면 일치
제목·부제·선택 그래픽·하단 문장 위계 명확
불필요한 테두리·네온·대각선 장식 0
승인 문구·타이밍 임의 변경 0
썸네일 전달 5항목 순서 일치
```
