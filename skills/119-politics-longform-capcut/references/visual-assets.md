# 시각 자산

대본 승인 뒤 C 작업자 한 명이 수행한다. 입력은 승인 대본의 `ASSEMBLY_ONLY_SEED`와
필요한 카드 목록이다. 출력은 이 회차 `Resources`의 지원 이미지·그래픽뿐이다.
source, narration, root, target, CapCut draft, `episode_cards.json`을 수정하지 않는다.

## 필요한 경우만 제작

`visual_asset_ref`가 있고 실제 자산이 없을 때만 만든다.
같은 visual ID·문구·style profile·SHA의 PASS 자산이 있으면 재생성하지 않는다.

## HTML/CSS 설명카드 기본 경로

다음은 `DEMOCRATIC_BLUE_CENTER_INFO_CARD_V1` HTML/CSS 설명카드를 기본으로 한다.

```text
작가 나레이션이 재생되는 설명 구간
챕터와 챕터 사이의 주장·사실·수치·차이 설명
다음 원본 영상 전 핵심 질문 정리
```

제작 흐름:

```text
투군이 확정한 top_label·headline·info_blocks·footer_text
→ 고정 HTML/CSS 템플릿 복제
→ 문구 주입
→ 1920×1080 PNG 렌더
→ Resources
```

HTML 자체를 CapCut에 넣지 않는다. 카드마다 새 디자인·외부 이미지 검색·AI 이미지 생성·
다중 시안을 기본 실행하지 않는다.

기본 스타일:

```text
canvas       = 1920×1080
background   = 짙은 민주블루 그라데이션
main_panel   = 중앙 집중형 짙은 남색 패널
headline     = 흰색 1~2줄 + 핵심어 노란색
info_blocks  = 2~4개
footer_strap = 한 줄
portrait     = OFF
news_capture = OFF
logo         = OFF
```

## 화면 안전영역

- 하단 자막 슬롯을 쓰는 카드에서는 하단 30%에 핵심 문구·도형·인물·로고를 두지 않는다.
- source/narration SRT와 논평은 평균 15자/줄, 최대 2줄이므로 그 높이를 침범하지 않는다.
- 무음 단순 챕터 카드는 3초이며 챕터 번호·제목·질문만 둔다.
- 설명 정보가 많은 카드를 무음 3초 챕터 카드로 축소하지 않는다.

## 검증

파일 존재·decode·1920×1080·SHA·overflow·하단 안전영역은 로컬 script로 검사한다.
기술 PASS 뒤 같은 검사를 Codex에게 반복시키지 않는다.
실제 화면의 가독성과 인상은 최종 `VISUAL_GATE`가 소유한다.
