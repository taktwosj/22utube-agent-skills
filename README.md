# Agent Skills

Git source of truth for 22utube/11utube production skills and selected personal workflow skills.

## Roles

- Git repo: official skill source under `skills/<skill>`.
- Codex runtime: copy installed to `$HOME/.codex/skills`.
- Claude runtime: copy installed to `$HOME/.claude/skills`.
- Hermes runtime: copy installed to `%LOCALAPPDATA%/Hermes/skills/22utube` on Windows and `$HOME/.hermes/skills/22utube` on macOS/default Unix hosts.
- OneDrive: lightweight production handoff data only, including manifests, reports, scripts, captions, CapCut draft manifests/snapshots/restore notes, and upload copy.

Runtime folders are install targets, not edit targets. Edit skills in this repo, then run install/update/verify.

## Managed Skill Set

Active production skills:

```text
001short-production-agent
top5isu-shorts
110-politics-longform-script
111-politics-longform-voice-srt
112-politics-longform-hyperframes
```

정치롱폼 라우팅. 번호 순서가 곧 실행 순서다.

```text
일반 정치롱폼 요청              -> 110  소스·자막 -> 확정 대본
확정 대본 있음, 음성·SRT 없음    -> 111  나레이션·오디오 시간축·SRT
음성·SRT·시간축 있음            -> 112  화면·모션·렌더
CapCut 을 명시적으로 요청       -> 119  동결된 레거시 lane
HyperFrames 실패                -> WAIT 또는 FAIL. 119 자동 우회 금지
```

`119-politics-longform-capcut`은 사용자가 CapCut·캡컷·119를 직접 말했을
때만 쓴다. 일반 `정치롱폼` 요청으로는 걸리지 않는다.

Bundled knowledge and planning skills:

```text
222mara
```

Naver blog workflow skills:

```text
naver-blog-posting
```

`naver-blog-posting` is installed to Codex only. It resolves the separate
`22blog` workspace from the current repository, OneDrive environment roots, or
Windows OneDrive account settings instead of hardcoding a username or machine
path.

`222mara` is the self-contained, offline Mara/쇼츠학개론 knowledge skill. Its
bundled canonical cards include the visually audited 1-4강 curriculum evidence;
it does not perform live web searches.

No other production or support skills are managed by this repository.

`manifests/skill-set.json` is the authoritative install list.
`manifests/capcut-template-set.json` records CapCut template identities and
verification requirements. Raw local CapCut draft folders stay in the active
machine's CapCut project storage; OneDrive keeps only manifests, snapshots, and
restore notes unless an explicit handoff package is requested.

Current general Shorts production authority is
`skills/001short-production-agent/SKILL.md`.

## First Install

Windows:

```powershell
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME\agent-skills"
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\install.ps1" -Target all
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\verify.ps1" -Target all
```

macOS:

```bash
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME/agent-skills"
bash "$HOME/agent-skills/scripts/install.sh" --target all
bash "$HOME/agent-skills/scripts/verify.sh" --target all
```

## Update

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target all -Prune
```

macOS:

```bash
bash "$HOME/agent-skills/scripts/update.sh" --target all --prune
```

## Strict Claude Match

Claude CLI should not keep old 22utube production skills beside the Git-managed
set. Use strict mode to make Claude's runtime match `manifests/skill-set.json`
exactly:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target claude -Prune -Strict
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\verify.ps1" -Target claude -Strict
```

```bash
bash "$HOME/agent-skills/scripts/update.sh" --target claude --prune --strict
bash "$HOME/agent-skills/scripts/verify.sh" --target claude --strict
```

Strict mode moves unmanaged skill folders with `SKILL.md` into the configured
backup folder as `DISABLED_<skill>_<timestamp>`. It does not delete them.

Use dry-run before prune:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target all -Prune -DryRun
```

```bash
bash "$HOME/agent-skills/scripts/update.sh" --target all --prune --dry-run
```

## Safety Rules

- Bulk install/update keeps copy semantics. `scripts/link-managed-skill.ps1` links one manifest-managed skill at a time; whole runtime-root links and system/plugin paths are forbidden.
- `update` refuses dirty worktrees.
- `git pull` uses `--ff-only`.
- Automatic stash is not supported.
- `--only` and `--prune` cannot be combined.
- `--only` and strict mode cannot be combined.
- Prune removes only folders with a managed marker file.
- Strict mode disables any unmanaged skill folder under the selected target.
- Existing runtime folders are backed up before overwrite.
- `verify` failure makes update fail.

## Verification Status

See `docs/verification-status.md` for the current evidence checklist and the
minimum live check required on another Windows PC or the Mac mini.

## Current Reports And Handoff

- `docs/work-report-2026-06-29-draft-fast-final-lock.md`: latest cleanup report
  for DRAFT_FAST / FINAL_LOCK, Korean text gate, and CapCut report rules.
- `docs/git-down-guide.md`: copy-paste update guide for office Windows and Mac
  mini.

## Telegram Hermes

Telegram-Hermes integration is an allowlisted command bridge. Bot tokens, chat IDs, and auth files stay outside Git. See `docs/install-telegram-hermes.md` and `manifests/telegram-hermes.commands.json`.
