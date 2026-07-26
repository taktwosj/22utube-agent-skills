---
name: 112-politics-longform-hyperframes
description: Use when the user explicitly requests 112정치롱폼, 하이퍼프레임 정치롱폼, HyperFrames 정치롱폼, a politics longform HyperFrames template, composition preview, HTML video assembly, or HyperFrames MP4 validation.
---

# 112 Politics Longform HyperFrames

## Core Boundary

HyperFrames 정치롱폼만 소유한다. 기존 CapCut 제작 스킬을 대체하지 않는다.

```text
KEEP_UNCHANGED=C:\Users\arajun\agent-skills\skills\111-politics-longform
KEEP_UNCHANGED=C:\Users\arajun\worktrees\agent-skills-000-politics-new\skills\000-politics-longform
NEW_SKILL=112-politics-longform-hyperframes
CapCut fallback=FORBIDDEN
```

`111-politics-longform`, `000-politics-longform`, `000-politics-new`와 그 CapCut
worktree를 수정하지 않는다. HyperFrames 실패를 CapCut 자동 실행으로 우회하지
않는다. 사용자가 일반 정치롱폼이나 CapCut을 요청하면 기존 lane으로 돌려보낸다.

## Required Reads

작업 전에 현재 factory의 `AGENTS.md`, `docs/YOUTUBE_PRODUCTION_WORK_ORDER.md`,
그리고 [template-contract.md](references/template-contract.md)를 읽는다. 설치된
`hyperframes`, `hyperframes-cli`, `hyperframes-registry` 스킬이 있으면 정확한
syntax와 CLI 계약을 위해 읽는다. 없으면 설치를 추정하지 말고 실제
`npx.cmd hyperframes --help`와 프로젝트 선언 버전을 확인한다.

## Source Of Truth

```text
skill_git_authority=C:\Users\arajun\agent-skills\skills\112-politics-longform-hyperframes
PL_HYPERFRAMES_REPO=C:\Users\arajun\repos\politics-longform-hyperframes
template_default=${PL_HYPERFRAMES_REPO}\template
episode_project={episode}\60_hyperframes\project
```

공용 템플릿은 episode 밖에 둔다. episode 프로젝트는 공용 템플릿을 복제하거나
명시적으로 참조한다. 과거 episode와 CapCut draft를 템플릿으로 승격하지 않는다.

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

## Workflow

### P1 Preflight

1. factory root와 writer/lock을 확인한다.
2. 기존 111/000 경로의 변경 전 해시와 Git scoped status를 기록한다.
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

### P4 User Gate

preview URL이 실제로 응답하고 세 composition 첫 프레임을 확인할 수 있을 때만
`WAIT_USER_TEMPLATE_PREVIEW`를 출력한다. 사용자 명시 승인 전에는 template LOCK,
전체 episode 적용, MP4 render를 하지 않는다.

### P5 Episode Production

사용자가 승인·LOCK한 템플릿으로 별도 episode 작업을 시작한다. 승인 대본,
source range, WAV, SRT와 chapter 순서를 바꾸지 않고 HTML composition으로 구현한다.
preview 승인 전 render를 하지 않는다.

## Hard Stops

| Condition | Status |
|---|---|
| HyperFrames 설치·실행 환경 때문에 preview 불가 | `WAIT_HYPERFRAMES_ENV` |
| 기존 프로젝트 수정이나 근본 원인 조사가 필요 | `WAIT_ROOT_CAUSE` |
| 파일 또는 검증 실패 | `FAIL` |
| lint/check/preview 정상, 사용자 화면 확인 대기 | `WAIT_USER_TEMPLATE_PREVIEW` |

## Common Mistakes

- 기존 `111-politics-longform`을 HyperFrames로 인플레이스 전환하지 않는다.
- 오세훈 전용 이름·asset·절대경로를 공용 템플릿에 복사하지 않는다.
- 하나의 거대한 `index.html`에 모든 콘텐츠·스타일·동작을 넣지 않는다.
- 원격 CDN, webfont, image, video, CSS, JS를 사용하지 않는다.
- 첫 프레임을 빈 화면으로 만드는 등장 애니메이션을 사용하지 않는다.
- 자막 두 종류를 같은 시점에 겹치지 않는다.
- 가짜 Studio token UI나 지원되지 않는 control을 만들지 않는다.

## Validation Tool

`scripts/validate_template.py`는 공용 파일, composition, token group, DOM role,
중복 ID, remote asset과 placeholder asset을 검사한다. 실행 결과가 0이 아니면
HyperFrames lint/check로 진행하지 않는다.
