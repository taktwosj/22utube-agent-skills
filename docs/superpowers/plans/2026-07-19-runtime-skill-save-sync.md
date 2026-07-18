# Runtime Skill Save Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Git 작업트리의 `skills/<skill-name>` 저장을 감지해 변경된 스킬만 Codex, Claude, Hermes에 즉시 동기화하고 SHA-256 일치를 검증한다.

**Architecture:** Windows `FileSystemWatcher`가 저장 이벤트를 디바운스해 변경 경로를 한 번에 모은다. 결정론적인 one-shot 동기화 스크립트가 활성 스킬명만 추출해 기존 `install.ps1 -Target all -Only`를 호출하고, 원본 및 세 런타임 디렉터리 해시를 비교한다. 로그온 예약 작업은 PowerShell을 숨김 창으로 실행한다.

**Tech Stack:** Windows PowerShell 5.1, Task Scheduler, Python `unittest`

## Global Constraints

- Git 작업트리의 `skills/<skill-name>`만 원본으로 사용한다.
- 변경된 스킬만 Codex, Claude, Hermes에 동기화한다.
- dirty 작업트리도 동기화하며 Git 커밋·푸시는 실행하지 않는다.
- 런타임 파일 변경을 Git으로 역동기화하지 않는다.
- 기존 post-commit/post-merge/post-rewrite 동기화 훅은 유지한다.
- 백그라운드 PowerShell 창은 숨김으로 실행한다.

---

### Task 1: 변경 스킬 선택 및 세 런타임 동기화

**Files:**
- Create: `scripts/sync_changed_runtime_skills.ps1`
- Test: `tests/test_runtime_skill_save_sync.py`

**Interfaces:**
- Consumes: `-ChangedPath <path[]>`, `-DryRun`
- Produces: `SYNC_RESULT_JSON=<json>` 및 성공 시 세 런타임의 동일한 디렉터리 SHA-256

- [x] 변경 경로 한 개가 정확히 한 스킬로 해석되는 실패 테스트를 작성한다.
- [x] dirty 작업트리에서도 `SKIPPED_DIRTY` 없이 실행되는 실패 테스트를 작성한다.
- [x] `install.ps1 -Target all -Only <skill>` 호출과 집중 해시 검증을 구현한다.
- [x] 테스트를 다시 실행해 통과시킨다.

### Task 2: 저장 이벤트 감시 및 숨김 예약 작업

**Files:**
- Create: `scripts/watch_runtime_skills.ps1`
- Create: `scripts/install_runtime_skill_watcher.ps1`
- Test: `tests/test_runtime_skill_save_sync.py`

**Interfaces:**
- Watcher consumes recursive `skills\` filesystem events and calls `sync_changed_runtime_skills.ps1`.
- Installer registers task `22utube Skill Runtime Save Sync` with `-WindowStyle Hidden`.

- [x] 재귀 감시, 디바운스, one-shot 호출 계약의 실패 테스트를 작성한다.
- [x] 숨김 로그온 예약 작업 계약의 실패 테스트를 작성한다.
- [x] 감시기와 등록 스크립트를 최소 구현한다.
- [x] 테스트와 PowerShell 파서 검사를 실행한다.

### Task 3: 설치 및 실환경 검증

**Files:**
- Runtime: `C:\Users\arajun\.codex\skills\00-tikitaka`
- Runtime: `C:\Users\arajun\.claude\skills\00-tikitaka`
- Runtime: `%LOCALAPPDATA%\Hermes\skills\22utube\00-tikitaka`

**Interfaces:**
- Consumes: 현재 브랜치 HEAD의 `skills/00-tikitaka`
- Produces: 세 런타임 마커의 동일한 `source_commit` 및 `source_sha256`

- [x] 분리된 clean worktree에서 `install.ps1 -Target all -Only 00-tikitaka`를 실행한다.
- [x] 예약 작업을 등록하고 즉시 시작한다.
- [x] 테스트용 스킬 파일 변경 없이 one-shot dry run으로 변경 선택을 확인한다.
- [x] 원본과 세 런타임 해시 및 GPT 웹 검수 파일 존재를 검증한다.
