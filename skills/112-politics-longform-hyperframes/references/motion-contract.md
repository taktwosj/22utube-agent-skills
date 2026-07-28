# HyperFrames 정치롱폼 모션 계약

이 문서는 레퍼런스 영상의 실측 어휘와 현재 빌더의 seek-safe 구현값을 분리해
기록한다. 제안값이나 육안 추정값은 계약값으로 승격하지 않는다.

## 금지 규칙과 이유

- CSS `animation: infinite`와 `alternate`를 금지한다. seek 결과가 프레임마다
  달라져 결정적 렌더가 깨지기 때문이다. (출처: `_sources/HANDOFF.json` →
  `forbidden`, `doctrine_conflicts`)
- idle 흔들림·부유·glow pulse·반복 scan beam을 금지한다. 모션은 상태를
  수행해야 하며 숨쉬듯 반복하면 안 된다. 레퍼런스의 idle 애니메이션도 0이었다.
  (출처: `_sources/HANDOFF.json` → `doctrine_conflicts`;
  `_sources/motion_analysis.md` → `정지 구간의 실제 상태`)
- 반복 대신 paused GSAP timeline의 단발 트윈을 사용한다. 긴 구간의 배경 변화도
  세그먼트 전체에서 한 번만 진행한다. (출처: `_sources/HANDOFF.json` →
  `doctrine_conflicts.resolution`; `_sources/build_hyperframes_project.py` →
  `chapter1_motion_timeline_js`, `composition_html`)
- 첫 프레임에는 골격과 의미 요소가 있어야 하며 비트에서는 상태만 바꾼다.
  `opacity 0↔1`로 골격을 토글하지 않는다. (출처: `_sources/HANDOFF.json` →
  `diagnosis_v8`, `plan_v8.P1`, `gates_v8`)

## 비트 앵커링

CHAPTER 1의 `cue_sec`는 확정 자막의 절대 시각이고 `local_sec`는 논리 세그먼트
안의 고정 위치다. 임의 stagger 계산으로 비트 시각을 만들지 않는다.
(출처: `_sources/build_hyperframes_project.py` → `CH1_MOTION_BEATS` 주석)

| 세그먼트 | 고정 비트 `이름=절대초/로컬초` | 근거 |
|---|---|---|
| seg5 | OPEN=97.56/0.0, HOOK=100.02/2.459, BEAT=104.90/7.339 | `_sources/build_hyperframes_project.py` → `CH1_MOTION_BEATS[5]` |
| seg8 | OPEN=129.32/0.0, BUILD-1=138.24/8.918, BUILD-2=148.46/19.138, PIVOT=170.14/40.818 | `_sources/build_hyperframes_project.py` → `CH1_MOTION_BEATS[8]` |
| seg10 | OPEN=206.52/0.0, BUILD-1=214.04/7.518, BUILD-2=225.40/18.878, ACCENT=236.24/29.718, HOLD=250.04/43.518 | `_sources/build_hyperframes_project.py` → `CH1_MOTION_BEATS[10]` |
| seg12 | OPEN=297.08/0.0, BUILD=312.70/15.617, COMPLETE=326.24/29.157, ACCENT=333.32/36.237 | `_sources/build_hyperframes_project.py` → `CH1_MOTION_BEATS[12]` |

ENDING도 확정 cue에 국면을 고정한다.

| 국면 | 시작 `절대초/로컬초` | 근거 |
|---|---:|---|
| P1 | 829.28/0.0 | `_sources/build_hyperframes_project.py` → `ENDING_MOTION_BEATS.P1-START` |
| P2 | 848.04/18.76 | `_sources/build_hyperframes_project.py` → `ENDING_MOTION_BEATS.P2-BOX-1` |
| P3 | 870.86/41.58 | `_sources/build_hyperframes_project.py` → `ENDING_MOTION_BEATS.P3-BOX-1` |
| P4 | 889.10/59.82 | `_sources/build_hyperframes_project.py` → `ENDING_MOTION_BEATS.P4-BOX-1` |
| P5 | 905.60/76.32 | `_sources/build_hyperframes_project.py` → `ENDING_MOTION_BEATS.P5-BOX-1` |
| END | 916.48/87.20 | `_sources/build_hyperframes_project.py` → `ENDING_MOTION_BEATS.END` |

## 진입 어휘

- 진입은 페이드 + 살짝 확대 + 살짝 위로다. before 프레임은 흐리고 작고
  어긋나 있으며 화면 밖 슬라이드는 사용하지 않는다.
- 그룹은 요소를 0.06~0.08초 간격으로 순차 진입시킨다.
- 텍스트는 흐림에서 진함으로 바뀌고 소속 그룹이 완성될 때 함께 올라온다.
- 한 장면 안에서는 등장한 요소를 다시 숨기지 않는다.
- 장면 내용 교체는 배경을 유지한 채 중앙 내용만 0.07초, 2프레임 하드 스왑한다.

이 어휘와 수치는 `_sources/motion_analysis.md` → `이벤트 판독`, `등장 어휘`의
실측을 그대로 옮겼다.

## 타이밍과 easing

### 레퍼런스 실측

| 항목 | 실측값 | 근거 |
|---|---:|---|
| 요소당 진입 | 0.2~0.3초 | `_sources/motion_analysis.md` → `우리 것과 비교` |
| 스태거 | 0.06~0.08초 | `_sources/motion_analysis.md` → `등장 어휘` |
| 모션 이벤트 | 22개, 길이 min 0.07초·중위 0.30초·max 2.23초 | `_sources/motion_analysis.md` → `측정값` |
| 정지 구간 | min 0.07초·중위 1.02초·max 6.47초 | `_sources/motion_analysis.md` → `측정값` |
| 움직이는 시간 | 8.8초, 18%; 정지 82% | `_sources/motion_analysis.md` → `측정값` |
| easing | 첫 20%에 피크 후 감쇠, `power2.out`~`power3.out`, 오버슈트 없음 | `_sources/motion_analysis.md` → `이징` |

### 현재 채택 구현

| 동작 | duration·stagger·easing | 근거 |
|---|---|---|
| 상태 전이 | 현재 0.32초, 완료 0.28초, `power2.out` | `_sources/build_hyperframes_project.py` → `_motion_state_timeline_lines` |
| 골격 선 그리기 | 0.72초, stagger 0.04초, `power2.out` | `_sources/build_hyperframes_project.py` → `chapter1_motion_timeline_js` |
| 진행표 현재점 | 확대 0.26초 뒤 복귀 0.32초, `power2.out`, 최대 scale 1.04 | `_sources/build_hyperframes_project.py` → `chapter1_motion_timeline_js` |
| 연결선 빛점 | 이동 2.2초 `none`, 소거 0.18초 `power1.out` | `_sources/build_hyperframes_project.py` → `chapter1_motion_timeline_js` |
| 후킹 밑줄·색 | 밑줄 0.32초 `power2.out`; 색 정착 0.28초 `power1.out` | `_sources/build_hyperframes_project.py` → `chapter1_motion_timeline_js` |
| ENDING 국면 전환 | 총 0.30초, 이전·다음 0.12초 겹침; 상승 `power2.out`, 하강 `none` | `_sources/build_hyperframes_project.py` → `ENDING_PHASE_TRANSITION_SEC`, `ENDING_PHASE_OVERLAP_SEC`, `_ending_phase_transition_timeline_lines` |

현재 상태 전이 0.28~0.32초와 `power2.out`은 레퍼런스의 요소 진입 0.2~0.3초,
실측 중위 0.30초에 근접하므로 변경하지 않는다.
(출처: `_sources/HANDOFF.json` → `reference_motion.verdict`)

## 채택하지 않은 것

### 그룹 재정렬

레퍼런스는 멤버가 추가될 때 기존 요소도 이동해 전체를 다시 중앙 정렬한다.
정치롱폼 화면에는 채택하지 않는다. 레퍼런스 카드는 동등한 병렬 항목이지만,
현재 박스 위치는 좌=원인·우=결과, 좌상=확인·우측=검증이라는 의미를 갖는다.
기존 요소를 재정렬하면 읽기가 흔들린다. (출처: `_sources/HANDOFF.json` →
`reference_motion.not_adopted`; `_sources/motion_analysis.md` → `이벤트 판독`)

### 반복 idle 효과

미세 플로팅, glow pulse, scan beam 반복은 채택하지 않는다. 모두 무한 반복이 되어
seek 결정성을 깨고, 레퍼런스도 정지 비율 82%와 idle 0을 보였다.
(출처: `_sources/HANDOFF.json` → `doctrine_conflicts`;
`_sources/motion_analysis.md` → `측정값`, `정지 구간의 실제 상태`)

## 미측정

- 진입 시작 scale의 정확한 값. `0.94`는 육안 판독에 따른 제안값일 뿐 실측값이
  아니다. (출처: `_sources/motion_analysis.md` → `미확인`)
- 진입 시작 y 오프셋의 정확한 값. `10px`도 요소 경계 상자 측정 전의 추정값이므로
  계약에 사용하지 않는다. (출처: `_sources/motion_analysis.md` → `미확인`)
