# Tikitaka Gemini Prompt Full Replacement Design

## Goal

Replace the compact Gemini candidate pre-index prompt in `00-tikitaka` with the complete second-by-second raw observation prompt already used by AI Studio Shorts Runner.

This is a replacement inside the existing `00-tikitaka` skill. It does not create a second skill, preserve a legacy mode, or add a user-facing mode selector.

## Current Problem

`skills/00-tikitaka/references/gemini_raw_intake_prompt.md` currently asks Gemini for a compact candidate index with fields such as:

- `t1_candidates`
- `t2_candidates`
- `tts_candidates`
- `speaker_quote_candidates`
- `situation_caption_candidates`

AI Studio Shorts Runner currently uses a larger second-by-second observation contract with:

- visible facts
- audible speech candidates
- on-screen text
- situation-caption candidates
- TTS interpretation candidates
- story and production type assessment
- hook, quote, situation, TTS, remake-structure, and production-type candidates
- one exact completion warning

The two prompts also use different `final_warning_ko` strings. This allows Tikitaka and the Chrome extension to disagree about whether a Gemini result is complete.

## Decision

Use the AI Studio Shorts Runner prompt as the complete Gemini raw-observation contract for `00-tikitaka`.

The replacement prompt body must match:

```text
22factory_20260628/00_asset_tools/browser_extensions/ai-studio-shorts-runner/assets/gemini_raw_intake_prompt.txt
```

The repository copy remains bundled in:

```text
skills/00-tikitaka/references/gemini_raw_intake_prompt.md
```

The Markdown file may keep a short heading and usage note outside its fenced prompt block. The entire fenced prompt body must be replaced with the extension prompt body without summarizing or retaining legacy candidate-index instructions.

## Skill Routing Changes

Update `skills/00-tikitaka/SKILL.md` as follows:

- Rename the Gemini section from compact candidate pre-index wording to optional Gemini raw observation wording.
- Keep Gemini optional. Tikitaka must still continue from `source.mp4` when Gemini was not requested or fails.
- Keep AI Studio web UI as the only Gemini route. Do not add a Gemini API fallback.
- Require the exact canonical completion warning:

```text
이 JSON은 Gemini 초벌 초단위 관찰값이다. 최종 대본, 화자발언 확정, 컷타이밍, TTS/상황설명 배치, CapCut 제작은 Codex가 source.mp4와 STT/OCR/프레임 검증으로 확정해야 한다.
```

- Treat Gemini output as unverified source notes. Final timing, dialogue, OCR, source identity, and design decisions still require source-media verification.
- Keep the existing URL-first, three-second wait, verified YouTube attachment, URL-free prompt, new-chat reset, run binding, and source-identity requirements.

## Data Flow

```text
Shorts URL
-> AI Studio Shorts Runner
-> URL input
-> wait at least 3 seconds
-> verify YouTube Video attachment
-> full second-by-second raw observation prompt
-> Gemini JSON
-> exact final_warning_ko completion detection
-> source identity and run-binding checks
-> 00-tikitaka unverified raw notes
-> source.mp4/STT/OCR/frame verification
-> Tikitaka design
```

## Test Changes

Update `tests/test_tikitaka_optional_gemini_contract.py` to require the new contract:

- `source_audio_mode`
- `shorts_type_assessment`
- timeline `start_sec` and `end_sec`
- `speaker_quote_candidate_ko`
- `situation_caption_candidate_ko`
- `tts_interpretation_candidate_ko`
- `best_hook_moments`
- `best_speaker_quote_candidates`
- `best_situation_caption_angles`
- `best_tts_angles`
- `remake_structure_candidates`
- `production_type_candidates`
- `recommended_package_fields`
- the exact canonical `final_warning_ko`

The test must reject retained legacy compact fields:

- `t1_candidates`
- `t2_candidates`
- `tts_candidates`
- `speaker_quote_candidates`
- `situation_caption_candidates`
- `후보는 전체 합계 최대 12개`

Keep the source-identity contract test that prohibits runtime binding fields inside the Gemini prompt:

- `run_nonce`
- `source_video_id`
- `observed_source_title`

Add an execution-time parity check that extracts the fenced prompt body from the Tikitaka Markdown file and compares it byte-for-byte with the extension prompt text after normalizing only the final newline.

## Runtime Synchronization

The Git repository is the source of truth. Runtime skill folders are install targets.

After tests pass:

1. Install only `00-tikitaka` to Codex, Claude, and Hermes with the repository installer.
2. Compare SHA-256 hashes for the complete `00-tikitaka` directory across the source and the three runtimes.
3. Confirm the Codex prompt-visible skill entry still resolves `00-tikitaka`.

Do not use `scripts/update.ps1` in the current dirty worktree because it intentionally refuses dirty repositories.

## Scope Protection

The repository already contains unrelated uncommitted changes. This work may modify only:

- `skills/00-tikitaka/SKILL.md`
- `skills/00-tikitaka/references/gemini_raw_intake_prompt.md`
- relevant Tikitaka Gemini contract tests
- this design document and its implementation plan

Do not stage, revert, rewrite, or include unrelated `000short-production-agent`, `top5isu-shorts`, Naver, manifest, or test changes.

Git commit and push are outside this approved scope while the worktree contains unrelated changes.

## Failure Handling

- Prompt parity mismatch: stop before runtime synchronization.
- Focused contract test failure: stop and repair the prompt or routing text.
- Broader repository verification failure unrelated to this prompt: report it separately and do not misreport the focused Tikitaka replacement as failed if its focused tests and parity checks pass.
- Runtime hash mismatch: reinstall only `00-tikitaka`, then compare again.
- Codex runtime visibility failure: report the install as incomplete.

## Rollback

Restore the two Tikitaka source files and affected tests to their pre-change Git versions, then reinstall only `00-tikitaka` to the three runtimes. Do not touch unrelated dirty files during rollback.

## Acceptance Criteria

- The old compact candidate-index prompt is absent.
- The Tikitaka fenced prompt body matches the extension prompt body.
- Tikitaka requires the same exact completion warning as the extension.
- Gemini remains optional and web-UI-only.
- Source-media verification remains authoritative.
- Focused prompt and source-identity tests pass.
- The source and installed `00-tikitaka` copies have matching hashes.
- No unrelated worktree changes are modified.
