# Agent Skills

Git source of truth for 22utube/11utube production skills and selected personal workflow skills.

## Roles

- Git repo: editable source under `skills/<skill>`.
- OneDrive release store: immutable commit-pinned releases under sibling `agent-skills-runtime`.
- Each machine: a local verified cache under `%LOCALAPPDATA%/22utube/agent-skills-runtime` on Windows or `${XDG_CACHE_HOME:-$HOME/.cache}/22utube/agent-skills-runtime` on macOS/Unix.
- Codex, Claude, and Hermes: per-skill links into the local verified cache, never into Git or OneDrive.

Runtime folders and release folders are not edit targets. Edit skills in Git, publish a clean commit, then activate and verify it on each machine.

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

## Publish A Release

Publishing refuses a dirty repository. `release_id` is the full Git commit, and `active.json` is updated only after the immutable release, manifest, hashes, and `READY` marker validate.

```text
python -B scripts/skill_release.py publish --dry-run
python -B scripts/skill_release.py publish
```

## Activate On Home, Office, Or Mac Mini

Run from the same OneDrive factory repo after the published `active.json` and release have synced. Activation validates before and after copying to the machine-local cache, backs up replaced runtime destinations, then creates per-skill runtime links.

```text
python -B scripts/skill_release.py activate --target all --dry-run
python -B scripts/skill_release.py activate --target all
python -B scripts/skill_release.py verify --target all
```

Add `--self-check` to `verify` when per-skill self-check execution is wanted.

## Safety Rules

- Only enabled skills in `manifests/skill-set.json` are published.
- Runtime links must resolve inside the local verified cache release. Whole runtime-root links, mutable Git/OneDrive targets, and system/plugin names or paths are forbidden.
- Existing immutable releases and local cache releases are never mutated; mismatched content is refused.
- Existing runtime folders are backed up before overwrite.
- Test-only root overrides require `AGENT_SKILLS_TEST_ROOT_OVERRIDE=1`.
- `scripts/link-managed-skill.ps1` is development-only and requires `-DevOnly` outside its isolated test harness. It is not a production activation path.

## Verification Status

See `docs/verification-status.md` for the current evidence checklist and the
minimum live check required on another Windows PC or the Mac mini.

## Current Reports And Handoff

- `docs/work-report-2026-06-29-draft-fast-final-lock.md`: latest cleanup report
  for DRAFT_FAST / FINAL_LOCK, Korean text gate, and CapCut report rules.
- `docs/git-down-guide.md`: verified publish/activate guide for Home Windows,
  Office Windows, and Mac mini.

## Telegram Hermes

Telegram-Hermes integration is an allowlisted command bridge. Bot tokens, chat IDs, and auth files stay outside Git. See `docs/install-telegram-hermes.md` and `manifests/telegram-hermes.commands.json`.
