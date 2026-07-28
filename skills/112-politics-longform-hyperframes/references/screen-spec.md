# HyperFrames 정치롱폼 화면 계약

이 문서는 현재 구현과 인수인계 자료에 수치 근거가 있는 화면값만 고정한다.
역사 설명이나 제안값이 현재 CSS 선언과 다르면 현재 구현값만 계약으로 사용한다.

## 캔버스와 안전영역

아래 좌표는 별도 표기가 없으면 1920×1080 캔버스의 픽셀 좌표다.

| 항목 | 계약값 | 근거 |
|---|---:|---|
| 캔버스 | 1920×1080, 30fps | `_sources/HANDOFF.json` → `canvas` |
| 불투명 상단 띠 | y=0~132, 높이 132 | `_sources/HANDOFF.json` → `safe_area.top_frame_opaque_px`, `zindex_lesson` |
| 텍스트 최소 y | 24 | `_sources/HANDOFF.json` → `safe_area.text_min_y` |
| 그래픽 안전영역 | x=500~1790, y=148~790 | `_sources/HANDOFF.json` → `safe_area.graphic` |
| 좌측 진행표 예약영역 | x=110~500 | `_sources/HANDOFF.json` → `safe_area.left_reserved` |
| 하단 예약영역 시작 | y=800 | `_sources/HANDOFF.json` → `safe_area.bottom_reserved_y_from` |

루트 composition도 `data-width="1920"`, `data-height="1080"`, `data-fps="30"`으로
이 값을 구현한다. (출처: `_sources/build_hyperframes_project.py` → root `index.html`)

## 후킹 배너

| 속성 | 계약값 | 근거 |
|---|---:|---|
| 위치·크기 | left 110, top 24, width 1700, height 92 | `_sources/build_hyperframes_project.py` → `.mg-hook-banner` |
| 내부 가로 padding | 4 | `_sources/build_hyperframes_project.py` → `.mg-hook-banner` |
| 폰트 | Pretendard Variable, 38px, weight 800 | `_sources/build_hyperframes_project.py` → `.mg-hook-line` |
| 행간·자간 | line-height 1.2, letter-spacing -0.8px | `_sources/build_hyperframes_project.py` → `.mg-hook-line` |
| 정렬 | 수직 중앙, 텍스트 좌측 | `_sources/build_hyperframes_project.py` → `.mg-hook-banner`, `.mg-hook-line` |
| 면 처리 | border 0, background none | `_sources/build_hyperframes_project.py` → `.mg-hook-banner` |
| 겹침 층 | z-index 40 | `_sources/build_hyperframes_project.py` → `.mg-hook-banner` |

텍스트 전체는 첫 프레임부터 표시하고 핵심어 밑줄만 cue에 맞춰 움직인다.
(출처: `_sources/HANDOFF.json` → `plan_v8.P6`)

## 스테이지

| 화면 | 위치·크기 | 내부 좌표계·상태 | 근거 |
|---|---|---|---|
| CHAPTER 1 상태유지 나레이션 | x=500, y=148, 1290×642; 끝점 x=1790, y=790 | stage가 642로 확장되어 CH1 배율 1.035 | `_sources/build_hyperframes_project.py` → `.mg-stage`, `.mg-stage svg`, `.mg-label`; `_sources/HANDOFF.json` → `safe_area._label_note` |
| CHAPTER 2~4 기존 나레이션 그래픽 | x=730, y=170, 1060×620 | 다이어그램은 아직 기존 화면 | `_sources/build_hyperframes_project.py` → `.nr-right`; `_sources/HANDOFF.json` → `status.not_done` |
| ENDING | x=110, y=148, 1700×642; 끝점 x=1810, y=790 | viewBox 1700×548, 세로 letterbox | `_sources/HANDOFF.json` → `ending.stage`; `_sources/build_hyperframes_project.py` → `ENDING_VIEWBOX`, `ENDING_STAGE_LAYOUT` |

ENDING은 챕터가 아니므로 진행표와 챕터 제목을 두지 않는다.
(출처: `_sources/HANDOFF.json` → `ending._`)

## 자막대

- 하단 자막용 예약영역은 y=800부터다. 나레이션 자막 텍스트는 `#FFD84A`,
  원본 화자 자막 텍스트는 `#FFFFFF`다. (출처: `_sources/HANDOFF.json` →
  `safe_area.bottom_reserved_y_from`, `layout.narration.bottom`, `layout.source_clip.bottom`;
  `_sources/build_hyperframes_project.py` → `.caption-narration`, `.caption-source`)
- `.lower-caption-band`의 정확한 x·y·width·height와 배경색은 세 참고자료에
  CSS 선언값이 없어 **미측정**이다. y=800은 자막대 자체 좌표가 아니라 예약영역
  시작점이다. (출처: `_sources/build_hyperframes_project.py` → `frame_layers`)

## z-index 토큰과 트랙 번호

| 토큰 | 값 | 층의 의미 |
|---|---:|---|
| `--z-media` | 1 | 영상·이미지 같은 미디어 |
| `--z-frame` | 20 | 잠긴 상·하단 프레임 |
| `--z-focus-lines` | 22 | 집중선 오버레이 |
| `--z-caption-band` | 30 | 하단 자막대 |
| `--z-metadata` | 40 | 출처·댓글·구독·후킹 배너 같은 메타데이터 오버레이 |
| `--z-caption-text` | 50 | 자막 텍스트 |

토큰 값은 `_sources/HANDOFF.json` → `zindex_lesson.tokens`에서 인용했다.

`data-track-index`는 HyperFrames 타임라인 순서이고 화면 겹침은 CSS `z-index`가
결정한다. 두 값은 무관하다. 커스텀 오버레이에 `z-index`를 생략하면
`top-frame`의 `--z-frame:20` 아래로 깔린다. 후킹 배너는 트랙 번호와 무관하게
`z-index:40`을 명시해야 한다. 배너 위치는 이 오진 과정에서 3회 시도됐다.
(출처: `_sources/HANDOFF.json` → `banner_position_history`, `zindex_lesson`)

## 라벨 타이포그래피

| 라벨 | 크기·두께 | 근거 |
|---|---:|---|
| CHAPTER 1 상태 노드 | 48px, weight 600 | `_sources/build_hyperframes_project.py` → `.mg-label` |
| ENDING 노드 | 48px, weight 600 | `_sources/build_hyperframes_project.py` → `.ending-label` |
| 기존 나레이션 핵심·보조·태그 | 64px·50px·48px, weight 700 | `_sources/build_hyperframes_project.py` → `.nr-key`, `.nr-sub`, `.nr-tag` |
| 진행표 기본·현재 | 26px weight 500 · 30px weight 700 | `_sources/build_hyperframes_project.py` → `.nr-rail .rlabel` |

노드 라벨의 화면상 하한은 48px이다. 과거 stage가 620에서 548로 축소되던
배율 0.884에서는 화면상 48px을 지키려고 viewBox 글자를 54.3px 이상으로 계산해
56px을 썼다. 현재 stage는 642로 확장되어 CH1 배율이 1.035가 되었으므로 보정이
필요 없어 48px로 복귀했다. (출처: `_sources/build_hyperframes_project.py` →
`.mg-label` 주석; `_sources/HANDOFF.json` → `safe_area._label_note`)

## 화면 밀도 규칙

- 국면 하나에는 요소·라벨을 3~4개까지만 둔다. 따라서 한 화면의 국면별 라벨
  상한은 4개다. cue 약 3개를 요소 1개로 환산해 필요한 국면 수를 정한다.
  (출처: `_sources/HANDOFF.json` → `density_rule._`)
- 4국면 이하는 골격 전체를 첫 프레임부터 예정 상태로 보이고 cue에서 상태만
  전이한다. seg8과 seg10의 4국면이 승인된 상한이며 seg25도 이 경계에 속한다.
  (출처: `_sources/HANDOFF.json` → `density_rule.phases_le_4`,
  `density_rule.scan.phases_4_caution`)
- 5국면 이상은 화면을 국면별로 분리하고 각 국면에 자기 요소 3~4개만 둔다.
  대상은 seg16(15cue), seg26(16cue), seg29(23cue)다.
  (출처: `_sources/HANDOFF.json` → `density_rule.phases_ge_5`)
- 8초 미만은 단일 비트만 사용하고 새 배너를 만들지 않는다. seg19는 3.1초라
  직전 배너를 승계한다. (출처: `_sources/HANDOFF.json` →
  `density_rule.under_8s`)
- seg29에서 라벨 18개를 한 화면에 둔 v9는 자리 부족으로 라벨 2개가 카드 밖에
  놓여 실패했다. 이 실패가 국면별 상한의 근거다.
  (출처: `_sources/HANDOFF.json` → `density_rule.why`, `ending_history.v9`)

## 미측정

- `.lower-caption-band`의 정확한 x·y·width·height와 배경색.
