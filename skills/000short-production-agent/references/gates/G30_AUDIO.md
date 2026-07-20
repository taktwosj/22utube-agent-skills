# G30 — Audio Asset Selection or Generation and Measured Duration Lock

> Lane: `general_shorts_production`
> Owner skill: `000short-production-agent`
> Schema version: `shared-gates-separated-lanes-v2`

## Entry contract

Reject entry without all of:
```text
owner_transfer_receipt exists and valid
canonical design_handoff SHA matches receipt.canonical_handoff_sha256
source_fingerprint matches
design_blueprint SHA matches
timeline SHA matches
external review receipt valid
```

The creative source of truth is `20_script/design_handoff.json`. Production
implements it; it must NOT reinterpret it.

## Purpose (NORM-002)

Generate or select audio, then **measure actual duration** before any
final SRT lock. Order is mandatory:

```text
G30:
  generate or select audio
  → measure actual WAV / source-clip duration
  → lock measured duration evidence

G40 (later):
  derive final cue timing from measured duration
```

Never lock final SRT before generated TTS duration is measured.

## Artifacts produced

```text
30_audio_srt/audio_lock.json
30_audio_srt/<audio>.wav (if generated TTS authorized)
30_audio_srt/measured_duration_evidence.json
```

## No-generated-TTS handling (NORM-003)

When the production profile requires no generated TTS:
```text
status = NOT_REQUIRED
reason_code = NO_GENERATED_TTS
source_audio_duration_verified = true
```

The forbidden value `NOT_REQUIRED_NO_GENERATED_TTS` must NOT appear
anywhere. G40 still validates final captions against the measured source
audio and clips.

## Paid TTS authorization

Paid Supertone TTS requires a `COST_AUTHORIZED` ledger event before
generation, within the G00-authorized episode limit. No authorization =>
no paid TTS => STOP.

## Stop conditions

```text
WAIT_PAID_ACTION_APPROVAL   paid TTS not authorized
STOP_UNAPPROVED_PAID_ACTION budget missing or exceeded
WAIT_TIKITAKA_DESIGN_REPAIR audio mismatch requires creative change
```

## Validator contract

`scripts/validate_stage_gate.py` checks:
- entry owner-transfer receipt valid
- audio_lock carries measured duration
- if TTS generated: WAV exists and ffprobe duration matches audio_lock
- if no TTS: status=NOT_REQUIRED + reason_code=NO_GENERATED_TTS

On PASS, `auto_advance_class=DETERMINISTIC_ONLY`.
