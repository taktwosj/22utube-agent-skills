# 모션 40개 대조 — 정치119에서 무엇을 쓰는가

출처는 `buttercake_motion_templates.html` 의 40개 이름이다. 그 파일의 CSS 는 4초 무한 반복이라 그대로 쓰지 않는다. 이름·명세로만 쓴다.
`HA/` = `hyperframes-animation/`. 구현이 정치119에 있는 것만 링크가 이 스킬 안을 가리킨다.

## 쓰는 것

| # | 효과 | 어디에 | 구현·규칙 |
|:--|:--|:--|:--|
| 01 | Easing | 전 장면 | `HA/adapters/gsap-easing-and-stagger.md` |
| 02 | Overshoot | 칩·아이콘 | `HA/rules/spring-pop-entrance.md`. 제목 글자에는 안 씀 |
| 06 | Anticipation | timeline·flow·move | [effects/anticipation.md](effects/anticipation.md) |
| 07 | Follow-through | timeline·panel·부제 | [effects/follow-through.md](effects/follow-through.md) |
| 08 | Stagger | 전 장면 | `HA/rules/waterfall-entry.md`. 그룹 합계 0.5초 이하 |
| 09 | Motion Blur | 스냅 줌·빠른 진입 | `HA/rules/motion-blur-streak.md` |
| 10 | Motion Trails | 핀·패킷 이동 | `trail` (scene-presets.md) |
| 11 | Kinetic Typography | 오프닝·챕터 제목 | `HA/rules/kinetic-beat-slam.md` |
| 12 | Per-character | 제목 본문 | [effects/word-slide.md](effects/word-slide.md) — 한글은 어절 단위 |
| 13 | Tracking | — | **대체**. letterSpacing 금지 → 12 와 같은 파일 |
| 14 | Masked Text Reveal | — | **제외**. 걷어내기가 어색해 부드러운 떠오름으로 대체 (2026-09-16) |
| 15 | Write-on | 밑줄 강조 | `HA/rules/svg-path-draw.md` |
| 18 | Shape Morphing | 주장판 → 기록판 | `HA/rules/card-morph-anchor.md` |
| 19 | Trim Paths | 도식 연결선 | 같은 구현. `hf119/diagram/*` 이 이미 씀 |
| 21 | Radial Burst | flow 우회 순간 1회 | `HA/rules/particle-burst.md`. 0.4초 |
| 25 | Glow | 강조 어절 1회 | `HA/rules/asr-keyword-glow.md`. 상시 pulse 금지 |
| 29 | Snap Zoom | 결정 시점 1회 | `HA/rules/coordinate-target-zoom.md`. 1.04 까지 |
| 31 | Parallax | 진입 1회 | `HA/adapters/css-animations.md`. 상시 drift 금지 |
| 32 | 2.5D | 관계도·카드 | `HA/rules/split-tilt-cards.md`. 얕게 |
| 33 | Rack Focus | 관계도 초점 | `HA/rules/depth-of-field-blur.md` |
| 35 | Camera Shake | 대립 장면 | `HA/rules/multi-phase-camera.md`. 0.28초·진폭 18·챕터 1회 |
| 36 | Light Sweep | 문서·증거 카드 | `HA/rules/ambient-glow-bloom.md`. 한 번만 |

## CapCut 이 하는 것 (장면 안에서 안 씀)

26 Wipe Transition · 27 Match Cut · 28 Whip Pan · 30 Freeze Frame · 40 Speed Ramp.
40 은 소스 속도 변경이라 원본 특성 변경 금지에 걸린다. 속도를 바꾸지 않는다.

## 안 쓰는 것

03 Damped Oscillation · 04 Bounce · 05 Squash & Stretch · 16 Text Scramble · 17 Text Morphing ·
20 Repeater · 22 Liquid Motion · 23 Seamless Loop · 24 Line Boil · 34 Dolly Zoom ·
37 RGB Split · 38 Displacement Map · 39 Turbulent Displace.

사유: 03·04·05 는 정치 다큐 톤이 아니다. 16·17 은 사실·숫자 오독 위험. 23·24 는 상시 흔들림 금지. 37 은 눈이 아파 제외(둘 다 2026-09-16 사용자 확정). 38·39 는 인물 사진 왜곡. 나머지는 비용 대비 효과가 없다.

장면 유형별 조합은 [scene-presets.md](scene-presets.md), 상한은 [limits.md](limits.md).
