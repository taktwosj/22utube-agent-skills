# Agent Skills

Git source of truth for 22utube/11utube production skills and selected personal workflow skills.

## Roles

- Git repo: official skill source under `skills/<skill>`.
- Codex runtime: read-only entrypoints under `$HOME/.codex/skills`.
- Claude runtime: read-only entrypoints under `$HOME/.claude/skills`.
- Hermes runtime: read-only entrypoints under `%LOCALAPPDATA%/Hermes/skills/22utube` on Windows and `$HOME/.hermes/skills/22utube` on macOS/default Unix hosts.
- OneDrive: lightweight production handoff data only, including manifests, reports, scripts, captions, CapCut draft manifests/snapshots/restore notes, and upload copy.

Runtime entrypoints and active release contents are immutable, not edit targets. Edit only an isolated worktree derived from this repo, then follow the release flow below after tests, independent review, and approval of the GitHub `main` revision.

## Managed Skill Set

Active production skills:

```text
001short-production-agent
top5isu-shorts
119-politics-longform-capcut
```

현재 제작 라우팅:

```text
일반 쇼츠                      -> 001  원본표 -> 우라까이표 -> CapCut 조립
TOP5·군림보 쇼츠                -> top5isu-shorts
정치롱폼 기획·논지·대본         -> 투군 PRE-119
승인된 정치롱폼 CapCut 조립     -> 119  승인 대본·카드 잠금에 따른 조립
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

Managed support skills include `1caveman` and `idm`.

`manifests/skill-set.json` is the authoritative install list.
`manifests/capcut-template-set.json` records CapCut template identities and
verification requirements. Its `production_roots` field is the current set;
entries under the older `templates` field are compatibility references only.
Raw local CapCut draft folders stay in the active
machine's CapCut project storage; OneDrive keeps only manifests, snapshots, and
restore notes unless an explicit handoff package is requested.

Current general Shorts production authority is
`skills/001short-production-agent/SKILL.md`.

## First Install

Windows:

```powershell
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME\agent-skills"
Set-Location "$HOME\agent-skills"
```

macOS:

```bash
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME/agent-skills"
cd "$HOME/agent-skills"
```

After the reviewed revision is on GitHub `main`, use the same release flow as an update.

## Release Flow

From a clean checkout of the approved GitHub `main` revision, run exactly:

```text
python -B scripts/skill_release.py publish
python -B scripts/skill_release.py activate --target all
python -B scripts/skill_release.py verify --target all --self-check
```

## Safety Rules

- `publish` refuses a dirty source repository.
- Activate only a published immutable release and always target `all` in this managed flow.
- On the Mac mini, `--target all` also copies the verified immutable release to `/Volumes/2pow/_LOCAL_WORK/22utube/22factory_20260628/00_mcp/skill-runtime`; `--target 2pow` can sync or verify that mirror alone.
- Never copy into or edit runtime entrypoints or active release contents.
- A release is incomplete until `verify --target all --self-check` passes.

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
