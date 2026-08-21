---
name: 112-politics-longform-hyperframes
description: Use when the user explicitly requests 112정치롱폼, 하이퍼프레임 정치롱폼, HyperFrames 정치롱폼, a politics longform HyperFrames template, composition preview, HTML video assembly, or HyperFrames MP4 validation.
---

# 112 Politics Longform HyperFrames

## Core Boundary

HyperFrames 정치롱폼만 소유한다. 아래 선언이 단일 lane 경계다.

```text
CapCut lane(119)=OUT_OF_SCOPE
KEEP_UNCHANGED=%USERPROFILE%\agent-skills\skills\119-politics-longform-capcut
KEEP_UNCHANGED=%USERPROFILE%\worktrees\agent-skills-000-politics-new\skills\000-politics-longform
HYPERFRAMES_FAILURE_AUTO_RUN_119=FORBIDDEN
MODIFY_119_OR_ITS_WORKTREE=FORBIDDEN
MODIFY_000_OR_ITS_WORKTREE=FORBIDDEN
NEW_SKILL=112-politics-longform-hyperframes
```

119 및 그 worktree를 수정하지 않는다. HyperFrames 실패 시 119를 자동 실행해
우회하지 않는다. 000-politics-longform, 000-politics-new와 그 worktree도 수정하지
않는다. 일반 정치롱폼 요청은 기존 lane으로 돌려보낸다.

## Required Reads

작업 전에 현재 factory의 `AGENTS.md`, `docs/YOUTUBE_PRODUCTION_WORK_ORDER.md`,
그리고 [template-contract.md](references/template-contract.md)를 읽는다. 에피소드 화면이나
썸네일 전달안을 만들 때는 [political-documentary-design-preset.md](references/political-documentary-design-preset.md)와
[narration-visual-grammar.md](references/narration-visual-grammar.md),
[visual-reference-frames.md](references/visual-reference-frames.md),
`assets/political-documentary-defaults.json`,
`assets/political-documentary-reference-frames.json`도 읽는다.
사용자가 V4를 명시하면 [political-documentary-v4.md](references/political-documentary-v4.md)와
`assets/political-documentary-v4.json`도 추가로 읽는다. 설치된
`hyperframes`, `hyperframes-cli`, `hyperframes-registry` 스킬이 있으면 정확한
syntax와 CLI 계약을 위해 읽는다. 없으면 설치를 추정하지 말고 실제
`npx.cmd hyperframes --help`와 프로젝트 선언 버전을 확인한다.

## Source Of Truth

```text
skill_git_authority=%USERPROFILE%\agent-skills\skills\112-politics-longform-hyperframes
PL_HYPERFRAMES_REPO=%USERPROFILE%\repos\politics-longform-hyperframes
template_default=${PL_HYPERFRAMES_REPO}\template
episode_project={episode}\60_hyperframes\project
default_visual_profile=assets/political-documentary-defaults.json
optional_visual_profile_v4=assets/political-documentary-v4.json
```

공용 템플릿은 episode 밖에 둔다. episode 프로젝트는 공용 템플릿을 복제하거나
명시적으로 참조한다. 과거 episode와 legacy draft를 템플릿으로 승격하지 않는다.

### 템플릿 정본 — OneDrive 사본 사용 금지

```text
FORBIDDEN_TEMPLATE={factory_root}\02_politics_longform\templates\politics-longform-template-v1
reason=LOCK_DRIFT
```

OneDrive 사본은 `compositions/source-video.html`이 lock과 불일치하고
실패 snapshot·`debug.log`·cache 잔재가 있다. 부분 패치하거나 제작 입력으로
쓰지 않는다. 반드시 repo 정본에서 신규 clean copy를 만든다.

P5 시작 직전 확인 항목:

```text
lock manifest 19/19 일치
style_tokens.json 일치
template_manifest.json 일치
OneDrive drift template 참조 0건
locked template 파일 변경 0건
복사본에 cache / debug.log / 실패 snapshot 포함 0건
```

### 에피소드 시각 레이어 — lock과 디자인 진화의 분리

lock은 공용 템플릿이 에피소드마다 조금씩 달라지는 drift를 막으려는 것이지,
에피소드 화면 디자인을 영구히 얼리려는 것이 아니다. 둘을 분리한다.

```text
공용 템플릿 파일        변경 0건. lock 그대로 (프레임·안전영역·자막 위치)
에피소드 시각 레이어    자유. 빌더가 주입하는 episode CSS / SVG로만 표현
```

에피소드 레이어에서 바꿔도 되는 것:

```text
색 팔레트 · 채도 · 명도
도형 · 모서리 반경 · 선 굵기
폰트 (로컬 임베드에 한함)
시각 부호 체계 (실선/점선/채움 등)
모션 · 이징 · 등장 순서
```

에피소드 레이어에서도 바꾸지 않는 것 — **공식값**:

```text
출처 표기 (좌측 상단)
댓글 · 구독 유도 문구
하단 자막의 위치와 스타일
```

`style_tokens.json`은 계속 lock 대상이다. 에피소드 조절은 이 파일을 고치지 않고
빌더가 주입하는 레이어에서 한다. 템플릿 사본의 파일을 편집해 디자인을 바꾸면
`FAIL_TEMPLATE_LOCK_DRIFT`다.

### 기본 디자인 프리셋 — 고정

```text
DEFAULT_VISUAL_PROFILE=politics_documentary_broadcast_v3
PROFILE_AUTHORITY=assets/political-documentary-defaults.json
PROFILE_SCOPE=EPISODE_VISUAL_LAYER_ONLY
PROFILE_OVERRIDE=LATEST_EXPLICIT_USER_INSTRUCTION_ONLY
```

사용자가 다른 디자인을 명시하지 않으면 이 프리셋을 그대로 적용한다. 게임 HUD,
사이버펑크, 네온 UI를 만들지 않는다. 딥 네이비 기반 방송사 정치 다큐 톤,
정렬·여백·타이포그래피 중심의 화면을 사용한다. 고정 색상, 레이아웃, 출처 표기,
댓글·구독 문구, 모션과 썸네일 전달 형식은
[political-documentary-design-preset.md](references/political-documentary-design-preset.md)를 따른다.
나레이션 장면은 대본의 의미에 따라 `FLOW_NODES`, `TIMELINE_PATH`, `CORE_ORBIT`,
`COMPARE_SPLIT`, `STEP_PROGRESS`, `QUOTE_SPOTLIGHT` 중 하나를 선택하고
[narration-visual-grammar.md](references/narration-visual-grammar.md)의 반복 방지와
발화 동기화 규칙을 따른다. 사각형 카드와 직선 화살표만 반복하지 않는다.
레이아웃과 화면 밀도는 사용자가 승인한 네 장의 시안을 담은
[visual-reference-frames.md](references/visual-reference-frames.md)를 최우선 시각 기준으로 삼는다.

공용 템플릿 lock을 고치지 않는다. 프리셋은 episode CSS·SVG·`design.md`에만
주입하고, 적용한 profile ID와 JSON SHA-256을 episode `design.md` 또는 build manifest에
기록한다. 명시적 사용자 변경 없이 색상·서체·CTA 문구·출처 위치를 임의 변경하면
`FAIL_DEFAULT_VISUAL_PROFILE_DRIFT`다.

### V4 반응형 화면·음량 프로필 — 명시적 선택만

```text
OPTIONAL_VISUAL_PROFILE=politics_documentary_broadcast_v4
PROFILE_AUTHORITY=assets/political-documentary-v4.json
EXTENDS=politics_documentary_broadcast_v3
DEFAULT_PROFILE_REMAINS=politics_documentary_broadcast_v3
ROLLBACK_PROFILE=politics_documentary_broadcast_v3
```

V4는 사용자가 명시한 episode에만 적용한다. V3 정본 JSON, 네 장의 reference frame,
공용 template lock은 수정하지 않는다. V4 선택값을 제거하고 episode를 다시 빌드하면
V3가 적용되어야 한다.

V4 본문은 좌측 chapter rail을 고정하고 우측 요소를 실제 SRT 발화에 따라 순차
반응시킨다. 각 요소의 `start_ms`, `end_ms`, `semantic_role`, `active_state`를 DOM과
visual timeline에 모두 기록한다. 발화 시작과 반응 시작 오차는 ±150ms 이내다.
색상·chapter 상태·집중선·금지 항목은
[political-documentary-v4.md](references/political-documentary-v4.md)를 따른다.

TTS와 원본 영상 발화에는 실제 FFmpeg `loudnorm` 2-pass를 적용한다. 음성 bus를
만든 뒤 BGM ducking과 SFX mix를 적용하고 final master 및 실제 렌더 오디오를
재측정한다. BGM과 SFX를 각각 -14 LUFS로 정규화하지 않는다. gain 또는 clipping
한계를 넘으면 `FAIL_AUDIO_GAIN_OUTLIER`다.

### 시각 부호 체계 요건

정치 롱폼은 확인된 사실과 화자의 해석을 화면에서 구분해야 한다.
표현 방법은 자유지만 구분 자체를 없애지 않는다.

```text
확인된 사실 / 미검증·해석 을 가르는 부호가 최소 1개 존재할 것
부호 없이 둘을 같은 형태로 표시 = FAIL_UNMARKED_INTERPRETATION
```

## Workflow

### P1 Preflight

1. factory root와 writer/lock을 확인한다.
2. 기존 119/000 경로의 변경 전 해시와 Git scoped status를 기록한다.
3. Node 22+, HyperFrames 버전, FFmpeg/FFprobe, 포트를 확인한다.
4. 3017이 사용 중이면 프로세스를 종료하지 않고 3018 이상을 선택한다.

### P2 Template Contract

1. 기존 episode는 읽기 전용 참고만 한다.
2. 테스트를 먼저 작성하고 필요한 파일 부재로 RED를 확인한다.
3. 세 composition과 공용 frame component를 생성한다.
4. `style_tokens.json`을 단일 조절값 권위로 사용한다.

### P3 Validate

다음 순서만 사용한다.

```powershell
python scripts/validate_template.py {template_path}
npx.cmd hyperframes lint
npx.cmd hyperframes check --strict --snapshots
npx.cmd hyperframes preview --port {available_port} --no-open --background
```

lint 실패 시 check를 실행하지 않는다. check 실패 시 사용자 preview를 요청하지
않는다. 저장된 과거 PASS 대신 현재 명령 출력을 사용한다.

V4 선택 시에는 episode sample/project에서 `scripts/normalize_v4_audio.py`로 음성을
실제 정규화하고, HyperFrames render MP4에서 evidence frame을 추출한 뒤
`scripts/validate_v4_evidence.py`를 추가 실행한다. 파일 존재만 보는 정적 검사는
V4 gate 증거가 아니다.

### P4 User Gate

preview URL이 실제로 응답하고 세 composition 첫 프레임을 확인할 수 있을 때만
`WAIT_USER_TEMPLATE_PREVIEW`를 출력한다. 사용자 명시 승인 전에는 template LOCK,
전체 episode 적용, MP4 render를 하지 않는다.

### P5 Episode Production

사용자가 승인·LOCK한 템플릿으로 별도 episode 작업을 시작한다. 승인 대본,
source range, WAV, SRT와 chapter 순서를 바꾸지 않고 HTML composition으로 구현한다.
사용자 별도 디자인 지시가 없으면 `politics_documentary_broadcast_v3`를 episode
시각 레이어에 적용한다. 출처에는 `S12` 같은 내부 ID가 아니라 실제 유튜브 채널명과
업로드 날짜를 표시한다. 썸네일 전달안은 프리셋의 고정 5항목 순서로 작성한다.
원본 영상 장면은 영상과 표정이 우선이며 흐름도나 장식 도형을 덮지 않는다.
나레이션 장면은 승인 대본 밖의 문구를 추가하지 않고 실제 SRT 발화 구간에 맞춰
시각 요소를 등장시킨다. preview 승인 전 render를 하지 않는다.

V4가 명시된 episode는 다음 네 gate가 실제 렌더·오디오 측정으로 모두 PASS해야 한다.

```text
PASS_CHAPTER_ACTIVE_STATE
PASS_SEMANTIC_VISUAL_SYNC
PASS_SOURCE_VIDEO_FOCUS_LINES
PASS_AUDIO_LOUDNESS_NORMALIZATION
```

## Hard Stops

| Condition | Status |
|---|---|
| HyperFrames 설치·실행 환경 때문에 preview 불가 | `WAIT_HYPERFRAMES_ENV` |
| 기존 프로젝트 수정이나 근본 원인 조사가 필요 | `WAIT_ROOT_CAUSE` |
| 파일 또는 검증 실패 | `FAIL` |
| 음성 gain 과다·clipping·측정 한계 실패 | `FAIL_AUDIO_GAIN_OUTLIER` |
| lint/check/preview 정상, 사용자 화면 확인 대기 | `WAIT_USER_TEMPLATE_PREVIEW` |

## Common Mistakes

- 기존 `119-politics-longform-capcut`을 HyperFrames로 인플레이스 전환하지 않는다.
- 오세훈 전용 이름·asset·절대경로를 공용 템플릿에 복사하지 않는다.
- 하나의 거대한 `index.html`에 모든 콘텐츠·스타일·동작을 넣지 않는다.
- 원격(remote) CDN·webfont·image·video·CSS·JS를 사용하지 않는다. 금지 대상은
  네트워크 의존이지 자원 종류가 아니다. 프로젝트 안에 파일로 들어와 오프라인에서
  렌더되면 폰트·라이브러리·이미지 모두 허용한다. GSAP도 CDN이 아니라
  `assets/vendor/gsap.min.js`로 vendor해서 쓴다. 판정 기준은
  "렌더 중 네트워크 요청 0건"이다.
- 첫 프레임을 빈 화면으로 만드는 등장 애니메이션을 사용하지 않는다.
- 자막 두 종류를 같은 시점에 겹치지 않는다.
- 출처 자리에 `원본 S12` 같은 내부 source ID를 노출하지 않는다.
- 댓글·구독 문구를 임의로 줄이거나 다른 문구로 바꾸지 않는다.
- 붓글씨, 두꺼운 외곽선, 반복 점멸, 대각선 네온 장식을 기본값으로 사용하지 않는다.
- 나레이션 장면을 사각형 카드와 직선 화살표만으로 연속 구성하지 않는다.
- 의미를 무시하고 장식 다양성만을 위해 도형을 늘리지 않는다.
- 외부 이미지 생성을 기본 공정에 넣지 않는다. 인물 누끼는 승인 시안과 같은
  히어로 장면에 한해 기존 소스나 사용자 제공 자산으로 허용한다.
- 가짜 Studio token UI나 지원되지 않는 control을 만들지 않는다.

## Validation Tool

`scripts/validate_template.py`는 공용 파일, composition, token group, DOM role,
중복 ID, remote asset과 placeholder asset을 검사한다. 실행 결과가 0이 아니면
HyperFrames lint/check로 진행하지 않는다.

V4에서는 `scripts/normalize_v4_audio.py`가 clip/voice bus/final master의 2-pass
loudnorm과 manifest를 만들고, `scripts/validate_v4_evidence.py`가 실제 렌더에서
추출한 chapter·semantic·focus frame 및 렌더 오디오 재측정값을 검증한다.
