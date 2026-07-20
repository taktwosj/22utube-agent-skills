# G40 — Measured-Audio-Based Caption Cue and SRT Lock

> Lane: `general_shorts_production`
> Owner skill: `000short-production-agent`
> Requires: G30 PASS (measured audio lock)
> Schema version: `shared-gates-separated-lanes-v2`

## Purpose

Derive final cue timing from the measured audio locked at G30, then
generate or reconcile the final SRT. The SRT lock uses G30's measured
duration as its authority — never the other way around.

```text
G40:
  derive final cue timing from measured audio
  → generate or reconcile SRT
  → validate cue order, gaps, overlaps
  → lock final caption SHA
```

## SRT lock requires measured audio

`srt_lock_requires_measured_audio: true`. If G30 has not produced a
measured-duration lock, G40 cannot PASS.

## Artifacts produced

```text
30_audio_srt/caption_lock.json
30_audio_srt/final.srt
```

The caption_lock records:
- final cue count
- locked cue text
- locked timing
- locked line breaks
- locked punctuation
- final SRT SHA

## Creative authority boundary

Production may adjust timing to fit measured audio. Production may NOT:
- rewrite hook
- reorder urakkai
- convert a speaker quote to TTS
- convert a situation description to a quote
- introduce a new caption role
- introduce a new clip or BGM not in the design

If timing-only repair is insufficient, the lane returns to
`00-tikitaka` G20 with `WAIT_TIKITAKA_DESIGN_REPAIR`.

## Validator contract

Checks:
- G30 measured-duration lock present
- every cue's end time ≤ measured audio duration
- no cue overlap
- final SRT SHA matches caption_lock
- no forbidden creative changes vs design_handoff

On PASS, `auto_advance_class=DETERMINISTIC_ONLY`.
