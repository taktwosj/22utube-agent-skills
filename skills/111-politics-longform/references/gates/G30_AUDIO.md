# G30 — Politics Audio Lock

Measure the real source and/or narration audio before G40. `source_led` uses
source speech and records generated TTS as `status=NOT_REQUIRED` with
`reason_code=NO_GENERATED_TTS`. `narrated` requires real generated or recorded
narration audio, SHA-256, duration evidence, and ffprobe verification.
Paid generation requires a matching `COST_AUTHORIZED` ledger event and is never
started by the validator.

