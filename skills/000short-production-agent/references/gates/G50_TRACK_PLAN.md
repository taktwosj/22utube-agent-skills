# G50 — Final Second-Level Track Assembly Plan

> Lane: `general_shorts_production`
> Owner skill: `000short-production-agent`
> Requires: G40 PASS (caption/SRT lock)
> Schema version: `shared-gates-separated-lanes-v2`

## Purpose

Build the second-level track assembly plan from the locked G40 timing.
This is the input the G60 CapCut assembly consumes.

## Artifacts produced

```text
40_assets_used/track_plan.json
40_assets_used/track_plan.md   (rendered from JSON)
```

## Plan contents

For every segment:
```text
slot_id
assembly_role
source_order
timeline_order
clip_start_us
clip_end_us
audio_role (ON / OFF / duck)
caption_role
locked_timing_reference: G40 caption_lock
```

## Validation rules

- timeline order matches design_handoff (no creative reorder)
- audio ON/OFF/duck policy consistent with production profile
- caption roles match the design blueprint (no reinterpretation)
- every clip's timing derives from G40 caption_lock

## Creative authority boundary

Same as G40: production implements the design, never reinterprets it.
A profile change requires returning to `00-tikitaka` G20.

## Validator contract

On PASS, `auto_advance_class=DETERMINISTIC_ONLY`.
