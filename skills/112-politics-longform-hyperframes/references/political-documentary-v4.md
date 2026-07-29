# Political Documentary Broadcast V4

`politics_documentary_broadcast_v4`는 V3를 대체하지 않는 명시적 선택형 episode
시각 레이어다. 기본 프로필은 계속 V3이며, V4 선택값을 제거하고 다시 빌드하면
즉시 V3로 돌아가야 한다.

## Profile authority

```text
PROFILE_ID=politics_documentary_broadcast_v4
PROFILE_AUTHORITY=assets/political-documentary-v4.json
EXTENDS=politics_documentary_broadcast_v3
DEFAULT=false
ROLLBACK=politics_documentary_broadcast_v3
```

공용 template lock과 `style_tokens.json`은 수정하지 않는다. V4는 episode CSS, SVG,
visual timeline, build manifest, audio manifest에만 주입한다. build manifest에는 V4
JSON의 SHA-256과 rollback profile ID를 기록한다.

## Chapter state contract

챕터 시작·전환 화면은 정치 또는 도시 배경 이미지 위에 흰색 대형 제목과 청록색
핵심어를 배치한다. 01~04 챕터 박스는 연결되어야 하며 각 시점의 상태는 다음
세 가지 중 하나다.

- `current`: 청록 발광, 1.06배 확대, 점등된 테두리
- `complete`: 완료 표식과 68% 수준의 차분한 명도
- `waiting`: 어두운 대기 상태

본문에서는 좌측 챕터 rail과 현재 챕터 강조를 유지한다. 좌측 rail은 우측 의미
요소가 바뀌어도 고정되어야 한다.

## Semantic visual timeline

우측 요소마다 다음 필드를 visual timeline과 DOM `data-*`에 함께 기록한다.

```text
start_ms
end_ms
semantic_role
active_state
```

`start_ms`는 해당 SRT 문장의 발화 시작과 ±150ms 이내여야 한다. 활성 구간에서는
대상 요소를 1.06배 확대하고, 별도 glow ring을 켜고, 아이콘을 한 번만 pulse하며,
연결 화살표 진행도를 전진시킨다. 이미 등장한 비활성 요소는 40~55%로 감광한다.
다음 요소는 자기 발화 전에는 보여주지 않는다. 모든 박스를 첫 프레임부터 동시에
보이거나 마지막 요소만 장면 전체에서 강조하면 실패다.

의미 색상은 사람이나 정당이 아니라 문장의 증거 상태에만 배정한다.

| semantic_role | color | marker |
|---|---|---|
| `verified_fact` | cyan | 없음 |
| `allegation_unverified` | orange | `의혹` 또는 `미확인` 필수 |
| `rebuttal_conflict_risk` | red-orange | 없음 |
| `conclusion_alternative` | cyan 또는 green | 없음 |

의혹을 금색으로 긍정 강조하거나 인물·정당별로 색을 고정하면 실패다.

## Source-video focus lines

집중선은 투명 SVG, Canvas, 투명 PNG 중 하나만 사용한다. 흰색 사각 배경을
두지 않는다. 중심은 핵심 인물 또는 사물에 맞추고 중앙 보호 반경을 비워 얼굴을
가리지 않는다. 자막과 출처 표기 영역도 침범하지 않는다.

```text
scale entrance=200ms
fade window=600..1200ms
repeat=key scenes only
```

## Audio normalization

TTS와 원본 영상 발화 클립은 각각 FFmpeg `loudnorm` 2-pass를 적용한다.

```text
I=-14 LUFS
TP<=-1 dBTP
LRA<=11
```

각 클립의 입력/출력 Integrated LUFS, True Peak, LRA, 적용 gain을 manifest에
기록한다. 정규화된 음성 클립으로 voice bus를 만든 다음 BGM ducking과 SFX mix를
적용한다. BGM과 SFX를 개별적으로 -14 LUFS로 올리지 않는다. 최종 master와 실제
렌더 출력의 오디오는 다시 측정하며, 덕킹 이후 무조건 gain을 더하지 않는다.
AAC 인코딩 뒤 True Peak가 -1 dBTP를 넘지 않도록 profile의 작은 음수
`final_encode_headroom_db`만 final master에 적용할 수 있다.

gain 절댓값이 profile 한계를 넘거나 출력 True Peak가 한계를 넘으면 자동 PASS하지
않고 `FAIL_AUDIO_GAIN_OUTLIER`로 중단한다.

## Dynamic evidence gates

파일 존재만으로는 아래 게이트를 통과할 수 없다.

- `PASS_CHAPTER_ACTIVE_STATE`: 실제 렌더에서 01~04가 각각 current인 서로 다른 프레임
- `PASS_SEMANTIC_VISUAL_SYNC`: 같은 장면의 세 시점 프레임과 visual timeline/SRT 오차
- `PASS_SOURCE_VIDEO_FOCUS_LINES`: 실제 렌더의 적용 전·중·후 프레임과 투명 overlay
- `PASS_AUDIO_LOUDNESS_NORMALIZATION`: 클립별 2-pass receipt와 실제 렌더 오디오 재측정

모든 evidence frame은 렌더 MP4에서 추출하고, SHA-256과 추출 시각을 evidence
manifest에 기록한다.
