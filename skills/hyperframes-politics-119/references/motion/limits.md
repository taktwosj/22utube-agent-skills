# 모션 상한과 금지

사용자 확정 2026-09-16 (Q2~Q5). 코드가 강제하는 항목에는 멈춤 코드를 적었다.

## 빈도·시간

| 규칙 | 값 | 어기면 |
|:--|:--|:--|
| 장면(약 10초)당 기본 모션 | 1~2개 (유형이 정한다) | — |
| 장면당 강조 | 최대 1개 | `MOTION_ACCENT_TOO_MANY` |
| 장면 강조 합계 | 1.0초 이하 | `MOTION_ACCENT_BUDGET` |
| Shake | 0.28초 · 진폭 18px(상하 6 · 회전 0.5°), 챕터당 1회 | `MOTION_CHAPTER_LIMIT` |
| 유형이 허용하지 않은 강조 | 금지 | `MOTION_FX_NOT_ALLOWED` |

챕터 횟수는 **한 번에 여러 장면을 만들 때만** 센다. `render_scenes.py --root <root> S05` 처럼 장면 하나만 다시 만들면 세지 못한다. 챕터 전체를 다시 만들 때 확인한다.

## 대체·제한 (결정 사유)

- **13 Tracking** — `letterSpacing` 트윈은 쓰지 않는다(리플로). 한글 어절을 나눠 `x` 로만 민다 → [word-slide](effects/word-slide.md).
- **글자 떠오름** — 0.50초. 값 하나(`presets.FLOAT_SECONDS`)로 전 장면이 같이 바뀐다(2026-09-16 사용자 선택).
- **24 Line Boil** — 제외. `motion-doctrine` 의 상시 흔들림 금지에 예외를 만들지 않는다.
- **37 RGB Split** — 제외. 색을 어긋나게 겹치는 효과는 눈이 아파 쓰지 않는다(2026-09-16 사용자 지시). 이전 결정(시안·흰색 0.15초)을 대체한다.
- **35 Camera Shake** — 0.28초 감쇠. 좌우만 떨면 미끄러져 보여 상하·미세 회전을 같이 준다. 세기는 `presets.SHAKE` 한 곳에서 바꾼다(2026-09-16 사용자가 '중' 선택). 다른 강조와 같은 장면에 쓰지 않는다.

## 항상 금지

- 상시 반복 모션: breathe · float · drift · glow pulse · CSS 무한 `@keyframes`. 31 Parallax 는 진입 때 한 번만.
- `Math.random`. 모든 모션은 일시정지 GSAP 타임라인 하나에 절대 시각으로 등록한다(seek-safe).
- 트윈 속성은 `x` · `y` · `scale` · `rotate` · `opacity` · `filter` · `clip-path` 만. `letterSpacing` · `width` · `top` 금지.
- 글자 · 도식 · 크롬은 띠 사이 `#safe`(y 189~891) 안에 둔다. 29 Snap Zoom 은 1.04 까지만 키운다.
- 같은 요소의 같은 속성에 트윈을 이어 붙이지 않는다. 연속 동작은 `keyframes` 한 개로 쓴다(`hyperframes check --strict` 의 `overlapping_gsap_tweens`).
