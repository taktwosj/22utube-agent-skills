---
name: 000short-production-agent
description: Use only when the user explicitly asks to create, validate, or repair production assets, subtitles, layout JSON, CapCut drafts, render packages, export packages, upload packages, or production packages.
---

# 11short Production Agent

## Ownership Matrix

- `00-tikitaka`: script draft only.
- `00script-writer`: polish existing script only.
- `000short-production-agent`: production assets only.
- `22utube-production-agent`: shared factory policy only.

## Escalation Rule

Do not start this skill from script-adjacent intent alone. Use it only when the
user explicitly asks for subtitles, layout JSON, render plans, CapCut drafts,
exports, upload packages, production packages, production validation, or repair.

Route Tikitaka, 우라까이, hook, 상단, timed 중단, or Gemini source-note scripting
to `00-tikitaka`; wording-only improvement to `00script-writer`; shared policy
questions to `22utube-production-agent`.

## Default Boundary

Default state is `PRODUCTION_GATE`.

No production pass is allowed from intent alone. Do not claim `PASS`,
`SCRIPT_LOCK`, upload-ready, export-ready, or complete unless the required
evidence files exist and the relevant validator has been run in this turn.

Working drafts, compatibility drafts, and draft-fast packages are intermediate
states. They are not production approval.

## Active Root

For new 22utube Shorts production, read:

```text
${env:WORKSPACE_ROOT}\22factory_20260628\AGENTS.md
```

Create new Shorts episode outputs under:

```text
22factory_20260628\01_shorts_factory\episodes\SH_YYYYMMDD_slug
```

Store CapCut metadata, manifests, snapshots, reports, and upload/final packages
in OneDrive. The editable CapCut draft itself stays in the local CapCut project
directory on the machine that builds it.

Legacy `11utube/11short/000short-production-agent/episodes` folders are
reference or explicit repair targets unless the user asks for legacy work.

## Production Inputs

Before generating or repairing production assets, identify the current authority:

- `source.mp4` or equivalent source file
- source provenance and usable-file check
- source-evidence/watch/direct-frame findings when the video content matters
- script authority, usually `final_script_ko.txt` or the current Tikitaka draft
- humanized final Korean text when visible text is final
- target template/layout
- requested voice/audio policy, if any

Missing `source.mp4` is a hard stop for source-derived production. Do not proceed
to source evidence, verified analysis, SRT/layout, CapCut, export, upload, or
final validation without source acquisition and provenance.

## Owned Outputs

This skill may create, validate, or repair:

- SRT/subtitle files
- caption/layout JSON
- render plans
- explicitly requested voice/audio files for production use
- CapCut draft folders and draft JSON
- production manifests
- export packages
- upload packages
- reports and validation logs

This skill does not originate Tikitaka creative structure when no script authority
exists. Ask for or route to the script owner first.

## Standard Sequence

1. Confirm active root and episode folder.
2. Confirm source file and provenance.
3. Confirm script authority and visible-text cleanup status.
4. Build or repair SRT/layout/render-plan assets.
5. Build or repair the local CapCut draft.
6. Snapshot CapCut draft JSON into the episode metadata folder.
7. Run the required harness or validator for the current stage.
8. Report `PASS/FAIL/WAIT` with evidence paths and one concrete next blocker.

## CapCut Rules

For any CapCut draft/project/profile creation, modification, repair, patch, or
validation response, the final answer must end with a `캣컵복사하기` Markdown
block containing only the CapCut project name. Put paths and reports in the main
body, never inside that block.

## Validation Rules

Use validators and harness scripts that already exist in this skill before
claiming a stage is complete.

If a validator fails, stop at that stage, report the failing item, fix it if the
request allows, and re-run validation. Do not continue downstream on a failed
stage.

Do not confuse:

- working draft created
- harness pass
- production gate pass
- upload ready

Each state needs its own evidence.

## Reference Routing

- For CapCut text effect presets, read
  `references/capcut_text_effect_presets.md`.
- For Shorts craft constraints, read `references/shorts-academy.md`.
- For the old Tikitaka production-script contract, read
  `references/tikitaka-script-v17.md`.
- For work-order, pipeline, layout, harness, and cut-assembly details, read the
  numbered root docs in this skill folder.
- For old full-contract details or legacy repair only, read
  `references/archived-full-skill-20260629.md`.

Keep this `SKILL.md` as the active production router. Do not re-add broad
Tikitaka, 우라까이, channel-family, hook, or analysis triggers to the description.
