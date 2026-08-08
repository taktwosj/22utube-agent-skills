# 001short Token Loading Map

This implementation artifact is not a runtime reference. Resolve `current_stage` from `workflow.json` and the episode state, then read only that stage instruction.

| Stage | Always-read | Conditional-read: choose one replacement only | Forbidden bulk-read |
|---|---|---|---|
| 01 | `workflow.json`; episode state; `steps/01-input-ocr.md`; `references/youtube-source-acquisition.md` | `references/parallel-execution.md` for approved evidence-only fanout | Every other `steps/`; `protocol.json` prose; `references/**` glob |
| 02 | `workflow.json`; episode state; `steps/02-original-blueprint.md`; `references/structure-blueprint-reporting.md` | `references/blueprint_matrix.md` for active matrix construction | Every other `steps/`; `protocol.json` prose; `references/**` glob |
| 03 | `workflow.json`; episode state; `steps/03-first-recommendation.md`; `references/blueprint_matrix.md` | `references/parallel-execution.md` for approved evidence-only fanout | Every other `steps/`; `protocol.json` prose; `references/**` glob |
| 04 | `workflow.json`; episode state; `steps/04-external-review.md`; `references/stage04-external-review-contract.md` | none | Every other `steps/`; `protocol.json` prose; `references/**` glob |
| 05 | `workflow.json`; episode state; `steps/05-final-blueprint.md`; `references/checks/design-lock.md` | `references/root-contract-production-plan.md` when compiling the plan | Every other `steps/`; `protocol.json` prose; `references/**` glob |
| 06 | `workflow.json`; episode state; `steps/06-vmake-clean.md`; `references/vmake-dom-clean-video-automation.md` | `references/vmake-residual-cleanup-qa.md` for residual QA | Every other `steps/`; `protocol.json` prose; `references/**` glob |
| 07 | `workflow.json`; episode state; `steps/07-audio.md`; `references/checks/audio-caption.md` | none | Every other `steps/`; `protocol.json` prose; `references/**` glob |
| 08 | `workflow.json`; episode state; `steps/08-capcut-assembly.md`; `references/capcut-build-readiness.md` | `references/interim-capcut-project-sync.md` for sync; `references/capcut-macos-ui-verification-fallback.md` for macOS fallback | Every other `steps/`; `protocol.json` prose; `references/**` glob |
| 09 | `workflow.json`; episode state; `steps/09-user-review-render.md`; `references/checks/render.md` | `references/capcut-tts-visual-qa-post-open.md` for QA; `references/capcut-export-telegram-handoff.md` for export | Every other `steps/`; `protocol.json` prose; `references/**` glob |

`protocol.json` is exercised through `scripts/validate_executable_protocol.py --self-check`, `--plan`, and `--completion-report`; schemas are read only when a validator error identifies that schema as the direct diagnosis target. `references/detailed-contract-from-original-skill.md` is candidate-audit preservation, never a runtime load.
