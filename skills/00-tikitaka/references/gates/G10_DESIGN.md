# G10 — First Design Blueprint and Evidence Map

> Lane: `general_shorts_design`
> Owner skill: `00-tikitaka`
> Schema version: `shared-gates-separated-lanes-v2`

## Purpose

Produce the **first design blueprint**. This is a source analysis document,
NOT a finished creative script. It maps the original onto timeline roles
that downstream gates (G20 manual review, then 000short G30-G90 production)
consume without reinterpretation.

## Required inputs (locked at G00)

```text
10_analysis/source_fingerprint.json
10_analysis/cache/analysis_cache_manifest.json
10_analysis/cache/transcript_segments.json
10_analysis/cache/ocr_segments.json
10_analysis/cache/scene_segments.json
10_analysis/cache/motion_segments.json
10_analysis/cache/speaker_segments.json
10_analysis/cache/audio_event_segments.json
```

## Artifacts produced

```text
20_script/design_blueprint.json   (canonical machine file)
20_script/design_blueprint.md     (rendered from JSON, never hand-edited)
20_script/timeline_design.json
20_script/timeline_design.md      (rendered)
20_script/caption_beat_map.json
```

Canonical authority rule (V2 design section 37): the machine JSON is
canonical. The MD is rendered deterministically by
`shared/workflow-harness/core/canonical_render.py`. The two are never
edited independently. A hand-edited MD requires an explicit reconcile
step; otherwise `HUMAN_MD_CANONICAL_JSON_MISMATCH`.

## Required roles in the first blueprint

The first blueprint is a source analysis, not a creative completion.
Mandatory roles:

```text
speaker speech
narration candidate
situation description candidate
screen action
audio event
existing on-screen text
original time
source_order
confidence
```

## Situation description rule (V2 design section 32)

Situation descriptions are an independent role. They are **visible text by
default**. The final design may opt a specific situation description into
TTS, but the first blueprint must NOT auto-convert them to TTS.

```text
raw transcript marker  ≠  approved situation-description caption
```

Examples of situation descriptions (parenthesized visible lines):

```text
(공을 힘껏 걷어찬다)
(말이 그대로 주저앉는다)
(강아지가 언덕 아래로 미끄러진다)
(철컹 소리에 모두 고개를 돌린다)
(겁에 질려 몸을 벌벌 떤다)
(웃음을 참지 못하고 키득거린다)
```

## External packet rule

When the first blueprint is presented to the user, the urakkai prompt
packet (see `prompt_templates/shorts_urakkai_prompt.md`) must accompany
it so the user can manually transport it to an external reviewer.

The packet is **generated locally** via
`scripts/build_external_prompt.py`. It is never auto-sent.

## Allowed vs forbidden

Allowed (within urakkai scope):

```text
reorder original segments
rewrite narration
edit situation-description wording
differentiate expression/emotion/speed
propose a different Shorts profile
```

Forbidden:

```text
distort original speaker speech
invent actions not in the video
change the outcome of an original event
```

## Stop conditions

```text
WAIT_EXTERNAL_RETURN          urakkai packet waiting for user transport
CONTEXT_EXPANSION_REQUIRED    more source range needed for evidence
HUMAN_MD_CANONICAL_JSON_MISMATCH
STOP_SOURCE_OF_TRUTH_CONFLICT
```

## Validator contract

`scripts/validate_stage_gate.py` checks:
- every required role present
- design_blueprint SHA matches between `.json` and rendered `.md`
- timeline_design assembly_role present on every segment
- no CapCut audio track ids leaked into timeline_design (semantic tracks only)

On PASS, `auto_advance_class=DETERMINISTIC_ONLY`.
