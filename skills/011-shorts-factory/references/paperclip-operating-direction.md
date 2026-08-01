# 011 Shorts Factory: Paperclip Operating Direction

This governs `쇼츠팩토리 P0`. It is the mandatory Paperclip entry for every new `001short-production-agent` episode; no one starts a local standalone 001 job.

## Fixed team and models

| Agent | Primary | Cheap profile | Responsibility | Cannot do |
|---|---|---|---|---|
| `P0-총괄` | `gpt-5.6-terra` / Medium | Terra / Low | Create issue, normalize user direction, own state/locks, dispatch and report | CapCut edit, script rewrite, self-promotion |
| `P0-제작` | `gpt-5.6-terra` / High | Terra / Medium | Execute 001 Stage 01–08 on Mac mini and prepare evidence | User-approval bypass or self-verification |
| `P0-검증` | `gpt-5.6-terra` / Medium | Terra / Low | Read-only SHA, deterministic and static profile validation | Edits, enablement, state promotion, creative copy judgment |

Never leave any live P0 agent on `gpt-5.3-codex-spark` or `Auto`. Luna, Max, Ultra, and LazyCodex are OFF by default. LazyCodex is an isolated maintenance-only exception for a confirmed compound code failure; it is not normal production.

## Required task entry

1. `P0-총괄` creates one issue and records user direction before source analysis.
2. It writes `{episode_root}/90_workflow/paperclip_entry.json` containing exactly: `episode_id`, `paperclip_issue_id`, `company=쇼츠팩토리 P0`, `active_writer_machine=macmini`, `coordinator=P0-총괄`, `producer=P0-제작`, `verifier=P0-검증`, and attached `source_skill_md_sha256`.
3. `P0-제작` runs `validate_paperclip_entry.py` before Stage 01. Missing is `WAIT_PAPERCLIP_ENTRY`; a mismatch is `FAIL_PAPERCLIP_ENTRY`.
4. Only Mac mini owns browser/VMake/CapCut edits. A reviewer can read artifacts but never edits the draft.

## Production checkpoints

| Gate | P0-제작 delivers | P0-검증 decides |
|---|---|---|
| Source | source identity and one VMake DOM job started | issue receipt, source identity, no duplicate VMake upload |
| Comment insight (optional) | compact 5–6 diverse public-reaction clusters or `COMMENTS_UNAVAILABLE` | live-response proof only; no API key in task, artifact, or log; comments never become source fact |
| Stage 03–04 | urakkai blueprint and dynamic speaker plan | evidence only; no subjective rewrite |
| Urakkai review | Claude Opus 5/Low result; Codex Sol/Low only when Claude CLI call fails | correct provider/fallback evidence and `WAIT_USER_URAKKAI_APPROVAL` |
| CapCut polish | closed-draft profile receipt | every source-audio segment is vocal-retain `choice=2`; source audio is muted under A9 and restored outside; all audio is -14 LUFS; every video join has W Flash; every video has AI HD=3, smart 42/47, sharpen/clear 50 |
| Text/motion | track readback and project evidence | STATE is a present scene/emotion hook at most 8 meaningful characters; 2 speakers use 2 lines and 3 speakers use 3 lines; no frozen/offline media |

If any row fails, the verifier returns one first failure to `P0-제작`. Do not advance state and do not open a second repair track. The producer cannot mark its own output PASS.

## Paperclip is an active gate, not a diary

Every issue has one current gate record: `stage`, `status`, `owner`, `input_sha256`, `output_path`, `validator_command`, `validator_exit`, `first_failure_code`, and `next_action`. `P0-검증` reads the actual receipt/JSON/SHA and writes `PASS`, `WAIT`, or `FAIL`; it never turns a producer sentence into PASS.

- `PASS`: the named deterministic validator exited successfully and its evidence hash matches.
- `WAIT`: an external/user prerequisite is genuinely missing; the exact one next action is named.
- `FAIL`: the verifier posts the first failed code and routes only that repair to `P0-제작`.

Therefore Paperclip shows what is currently good or broken as work happens. Its history is also retained for later root-cause review, but it is not merely retrospective. It cannot judge VMake image beauty or user creative preference; those remain user decisions.

## VMake speed path

Immediately after source identity, `P0-제작` starts VMake via DOM/file input, then continues analysis and urakkai while VMake processes. No coordinate-driven Finder, blind sleep, repeated upload, or visual-quality judgment. If the clean file is pending near CapCut and at least ten minutes remain, create an original-visual review draft and swap only the later verified clean asset. A VMake pending/download failure is `WAIT_VMAKE_*`, not a reason to stall the rest of the episode.

## User authority

The user supplies episode-specific emotional direction and makes the final visual judgment. The coordinator transmits it, including permission for a playful fictional hook, imagined thought, exaggeration, or reversal. The producer records source observation separately from `CREATIVE_URAKKAI`; it may not frame invented identity, relationship, crime, medical/legal, or defamatory claims as fact. Stage 04 runs Claude Opus 5/Low once; only an actual Claude CLI failure permits one Codex Sol/Low fallback. Report the revised draft and wait for user approval before Stage 05, unless the user explicitly says automatic mode for that episode.

## Deployment truth

For every 001/011 source change: run source tests, record the package SHA, import one exact Paperclip version, attach it to all three agents, and read back attachment state. Git PASS or an import card alone is not Paperclip deployment PASS.
