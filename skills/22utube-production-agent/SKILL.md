---
name: 22utube-production-agent
description: Use only when a 22utube production workflow needs shared workspace policy, folder routing, archive rules, root path conventions, or cross-lane operating standards.
---

# 22utube Production Agent

## Ownership Matrix

- `00-tikitaka`: script draft only.
- `00script-writer`: polish existing script only.
- `000short-production-agent`: production assets only.
- `22utube-production-agent`: shared factory policy only.

## Escalation Rule

This skill is a policy reference. It is not the active Shorts writer, rewrite
owner, SRT/layout builder, CapCut builder, exporter, or upload packager.

If the user asks for Tikitaka remake scripting, route to `00-tikitaka`.

If the user asks to polish an existing script, route to `00script-writer`.

If the user asks to create, validate, or repair production assets, route to
`000short-production-agent` or the lane-specific production skill.

## 11short Two-Report Routing

22utube-production-agent is the first policy/root gate for new 11short/Shorts
work. Then route Shorts script/remake work to `00-tikitaka` for 보고서1.
After 보고서1 approval and voice/audio route decision, route to `000short-production-agent` for 보고서2.

This skill must not write 보고서1 or 보고서2.

## 11short Default CapCut Base Policy

For current 11short CapCut work, the default root/mother CapCut draft is:

```text
shrt white
```

Unless the user explicitly names another root CapCut template, route stage 2 to
`000short-production-agent` with `shrt white` as the only default base.
`260707-Fk5D_FboO6M-game-character-comments-CAPCUT_v1`, `260708 short`,
`*_base_v2`, `*_base_v3`, and previous episode projects are not default bases;
they are prior derived/style samples at most. If the base cannot be resolved,
the correct policy status is `WAIT_SHRT_WHITE_BASE_REQUIRED` or
`FAIL_TEMPLATE_ROOT_NOT_RESOLVED`, not a fallback to old builders.

## Default Boundary

Default state is `REFERENCE_ONLY`.

Do not claim production completion, stage `PASS`, export-ready, upload-ready, or
CapCut readiness from this skill. This skill can say which rule applies and which
owner should execute next.

## Active 22factory Root

For new 22utube work, the active OneDrive production root is:

```text
${env:WORKSPACE_ROOT}\22factory_20260628
```

Read this file before applying older path rules:

```text
${env:WORKSPACE_ROOT}\22factory_20260628\AGENTS.md
```

New work should use the lane folders under the factory root:

```text
00_asset_tools
01_shorts_factory
02_politics_longform
03_other
99_archive
```

## Shared Asset Folder Rule

`00_asset_tools` is a reusable material library, not an episode workspace.

Allowed examples:

- reusable BGM/SFX/audio under `00_asset_tools\bgm` or a clearly named audio
  asset folder
- reusable images, overlays, banners, fonts, templates, and stable helper tools
- manifest or sync reports that describe those reusable assets

Do not put episode-specific source downloads, locked clips, exports, raw CapCut
draft folders, one-off politics-longform builders, or per-episode working media
directly in `00_asset_tools`. Put episode work under the matching lane's
`episodes` folder, local CapCut draft root, or `99_archive` if it is old cleanup.

BGM is not a default requirement. Treat BGM as a selectable reusable asset:
use it only when the user chooses a BGM/SFX file, asks for a music mood, or the
locked production plan names the asset.

Do not put Git skill source or installed runtime skills in the factory root.
GitHub or the configured skill source owns skill source. OneDrive factory folders
hold production data, manifests, reports, and final/upload packages.

## Episode Folder Rule

Every new video gets one episode folder under the matching lane's `episodes`
folder. For new Shorts:

```text
01_shorts_factory\episodes\SH_YYYYMMDD_slug
```

Expected episode shape:

```text
00_source
10_analysis
20_script
30_audio_srt
40_assets_used
50_capcut_project
60_exports
70_upload
90_reports
```

CapCut editable draft folders stay in the local CapCut project directory. The
episode folder stores only project name, local path, manifests, snapshots, and
restore notes.

## Cross-Lane Rules

- Treat factory and episode paths as shared production workspace.
- Avoid destructive edits unless explicitly requested.
- Do not print secrets, tokens, cookies, API keys, session IDs, or private
  customer identifiers.
- Preserve evidence-based completion: manifests, validation logs, review MP4
  paths, final export paths, and honest status.
- Do not expose internal process labels in public video outputs.
- If source/channel/fact restrictions apply, preserve the active lane's stricter
  rule.

## Story Lane Rule

For work inside:

```text
11utube\story
```

run the story harness at the end of each stage:

```bash
python "$UTUBE_ROOT/story/scripts/harness_validate.py" {episode_dir} --stage {stage}
```

`stage = script | audio | prompts | capcut | all`

If any stage fails, stop and report the failure before continuing.

## Reference Routing

Use this skill only to answer or enforce shared policy. For lane-specific
details, read the active lane skill after this policy reference:

- Shorts script draft: `00-tikitaka`
- Script polish: `00script-writer`
- Shorts production assets: `000short-production-agent`
- Political longform: `111-politics-longform`
- Story episodes: story lane rules and harness checklist

For old full-contract details or legacy repair only, read
`references/archived-full-skill-20260629.md`.

Keep this `SKILL.md` as the shared-policy router. Do not re-add broad production,
CapCut, SRT, script-writing, or handoff triggers to the description.
