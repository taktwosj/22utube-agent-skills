---
name: 001short-production-agent
description: Use when an original Shorts video, user review, and Gemini analysis must become an OCR-verified original blueprint, first recommendation, VMake-clean CapCut assembly, and evidence-backed production validation.
---

# 001short Production Router

## Executable Protocol (Mandatory)

- Run the executable validator for the machine contract. It must reject `URAKKAI_STRUCTURE_UNCHANGED`, `UPLOAD_METADATA_MISSING`, and `PUBLIC_UPLOAD_NOT_APPROVED`; do not replace those failures with prose judgment.

## Hard Gates

- Own only `owner_skill=001short-production-agent`, `lane=general_shorts_production`. Stop `WAIT_LANE_CONFLICT` for another lane; do not mix `000short-production-agent`, `top5isu-shorts`, `00-tikitaka`, or `111-politics-longform`.
- Read `workflow.json`, then `{episode_root}/90_workflow/state.json`; require `episode_id`, `current_stage`, and `status`. Resolve the sole stage from `workflow.json.production_stages`; never accept a caller override.
- Read only the resolved `steps/<stage>.md`. Do not advance state without the real evidence and successful validator required by `workflow.json`; preserve its declared `WAIT` or `FAIL` result.
- Treat the executable contract as authoritative through its validator. If validator behavior, `workflow.json`, or this router conflicts, stop `STOP_PROTOCOL_CONFLICT`.
- Keep one GUI owner, source read-only, the pinned root immutable, and public upload at `WAIT_UPLOAD_APPROVAL` until explicit approval evidence passes its validator.

## Exact Progressive Load

1. Always read `workflow.json`, the current episode state, and exactly `steps/<current_stage>.md`.
2. Run `python -B scripts/validate_executable_protocol.py --self-check` before every routing run. Do not load `protocol.json` prose for routing.
3. Select and read exactly one stage reference below. A matching conditional replacement supersedes that row's default; never load both or bulk-read `references/`.

| Stage | Default reference | Conditional replacement |
|---|---|---|
| 01 | `references/youtube-source-acquisition.md` | `references/parallel-execution.md` for an approved evidence-only fanout |
| 02 | `references/structure-blueprint-reporting.md` | `references/blueprint_matrix.md` when matrix construction is the active task |
| 03 | `references/blueprint_matrix.md` | `references/parallel-execution.md` for an approved evidence-only fanout |
| 04 | `references/stage04-external-review-contract.md` | none |
| 05 | `references/checks/design-lock.md` | `references/root-contract-production-plan.md` when compiling the production plan |
| 06 | `references/vmake-dom-clean-video-automation.md` | `references/vmake-residual-cleanup-qa.md` for residual-cleanup QA |
| 07 | `references/checks/audio-caption.md` | `references/bgm-a12-capcut-cloud.md` for explicitly requested BGM-only work |
| 08 | `references/capcut-build-readiness.md` | `references/interim-capcut-project-sync.md` for explicit interim/cloud sync; `references/capcut-macos-ui-verification-fallback.md` for macOS UI fallback |
| 09 | `references/checks/render.md` | `references/capcut-tts-visual-qa-post-open.md` for post-open text/TTS QA; `references/capcut-export-telegram-handoff.md` for explicit export or Telegram handoff |

Do not load `references/detailed-contract-from-original-skill.md` at runtime; it preserves moved source wording for candidate audit only.

## Validators

- Stages 05–09: run `python -B scripts/validate_stage.py --state <episode_root>/90_workflow/state.json --stage <stage> --check <workflow check>` with every required argument from the selected step and workflow.
- Stage 05: additionally run `python -B scripts/validate_executable_protocol.py --plan <episode_root>/20_script/production_plan.json` before build or advance.
- Stage 08: run the workflow checks in order: `prebuild`, `build_inputs`, `capcut_project`, `postbuild`; run `python -B scripts/validate_capcut_cloud_media.py` before CapCut cloud upload.
- Stage 09: run `render`; before `all_harness_pass`, `WAIT_UPLOAD_APPROVAL`, `upload_ready`, or `uploaded`, run `python -B scripts/validate_executable_protocol.py --completion-report <episode_root>/90_reports/completion_report.json`.

Run `python -B scripts/check_thin_router.py` after router edits. Report the current state only; this isolated candidate is not production-ready.
