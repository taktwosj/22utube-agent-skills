# G00 — Intake / Source / Content Profile / Production Mode / Target / Budget Lock

> Lane: `general_shorts_design`
> Owner skill: `00-tikitaka`
> Schema version: `shared-gates-separated-lanes-v2`

## Purpose

Lock the inputs that the entire Shorts design will be derived from. After
G00 PASS, source identity, content profile, production mode, requested
target and the episode cost guard are frozen. Material changes after G00
require `WAIT_USER_EDITORIAL_CONFIRMATION`.

## Required inputs

The user may supply any of three intake modes (V2 design section 30.1):

```text
A. Shorts/source URL only
B. URL + one-line user description
C. URL + external (Gemini) analysis result
```

Mode C is **optional**. The local source is primary evidence. External
analysis is supplementary; if it disagrees with local primary evidence,
raise `EXTERNAL_ANALYSIS_MISMATCH` and do NOT silently adopt the external
result.

Local pipeline regardless of intake mode:

```text
URL → local download → ffprobe → caption/speaker analysis → OCR
    → scene/motion/audio-event analysis → first analysis blueprint
```

## Artifacts produced

```text
10_analysis/source_fingerprint.json
10_analysis/cache/analysis_cache_manifest.json
10_analysis/cache/{transcript,ocr,scene,motion,speaker,audio_event}_segments.json
20_script/intake_lock.json
90_workflow/manual_gate_state.json   (projection)
90_workflow/gate_ledger.jsonl        (append)
```

## Locked fields (G00)

```text
source_sha256
content_profile = general_shorts
production_mode
requested_target ∈ {design_only, editorial_locked, capcut_ready,
                    upload_package, rendered}
episode_budget (cost_guard)
source_fingerprint
```

## Cost guard (V2 design section 7.4)

G00 must create the episode cost policy. No configured budget means no
paid automatic action. Paid TTS is `NOT_AUTHORIZED` until the user
authorizes a `COST_AUTHORIZED` ledger event.

## Stop conditions

```text
WAIT_USER_INPUT                 source/URL missing or ambiguous
EXTERNAL_ANALYSIS_MISMATCH      external analysis disagrees with local
WAIT_USER_EDITORIAL_CONFIRMATION material scope change requested
STOP_SOURCE_OF_TRUTH_CONFLICT   source identity ambiguous
```

## Validator contract

`scripts/validate_stage_gate.py` validates only. On PASS it emits a
gate_result with `auto_advance_class=DETERMINISTIC_ONLY`. It never calls
an external model, opens CapCut, or performs paid TTS.

## External authority

External analysis may use only:
```text
PASS_RECOMMENDED
REVISE_REQUIRED
EVIDENCE_REQUIRED
```

External analysis must NOT claim `PASS`, `DESIGN_LOCK`, `USER_APPROVED`,
`PRODUCTION_PASS`, or any final-authority token.
