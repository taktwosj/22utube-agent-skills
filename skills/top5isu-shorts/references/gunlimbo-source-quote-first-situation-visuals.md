# Gunlimbo Source-Quote-First + Situation Visuals

Use this workflow when the operator supplies a short public-figure/news clip and asks to place the real statement first, then explain it with 군림보 narration while avoiding portrait-heavy generated visuals.

## Authority and fact separation

1. Preserve the supplied clip unchanged under `00_source/` and record duration, dimensions, codec, size, and SHA-256.
2. Extract and ASR the audio, but treat the operator's exact transcript and an authoritative published transcript as higher authority than Whisper for homophones or spacing. Example: Whisper may render `무제한` as `무지한`; do not copy the ASR error into captions.
3. Verify each claim against current reporting or an official transcript. Keep adjacent policy contexts separate: a statement about political cost in a holding-tax discussion must not be presented as if it specifically referred to jeonse loans.
4. Write a claim ledger with `verified_attributed`, `verified_context_only`, or `unverified` status.

## Opening and audio lanes

1. Put the supplied source video at `00:00` with its original speaker audio; do not recreate that quote with Supertone when the actual clip is available and approved.
2. Isolate meaningful source speech with the approved vocal-isolation workflow and keep it on `A_SOURCE`.
3. Start the 군림보 explanation after the source clip plus a short natural gap, normally about 300–400 ms, on `A_TTS`.
4. Remove narration that merely repeats the opening quote. The first generated sentence should explain the quote's meaning or consequences.
5. Create exact visible captions for the source quote and separate display/spoken authorities for generated narration.
6. Normalize source speech and Supertone separately so their integrated loudness differs by no more than roughly 1 dB when practical without clipping.

## Selective Supertone QA

- Generate one WAV per grammatical sentence with the locked 군림보 voice.
- ASR every sentence and preserve passing hashes.
- Regenerate only failed indices.
- If a provider stutters on a phrase, change only `tts_spoken_copy.txt` to a semantically equivalent, pronunciation-safe form; keep `tts_copy_text.txt` unchanged.
- Rebuild timings, SRT, manifests, and timeline WAVs after every repair.

## Situation-first Image2 policy

After the real opening clip, generated visuals should explain the issue rather than repeatedly depicting the public figure.

- Housing example: renters, loan flows, apartment-price pressure, deposit risk, fraud traps, policy adjustment, and targeted support.
- Do not generate a recognizable politician/public-figure portrait unless the operator explicitly asks.
- Use ordinary people and symbolic environmental storytelling.
- Reject generated currency with faces, digits, lettering, or pseudo-banknote text. Use blank abstract tokens, light streams, keys, contracts, or pressure gauges instead.
- Reject logos, readable text, placards, watermarks, split panels, and effects that obscure captions or faces.
- Run one actual Image2 sample through the final TOP55 frame before batching.

## Visual/timing contract

- Visual 1 may be source video; subsequent visual boundaries follow the sentence starts of generated narration.
- For a horizontal source clip in the TOP55 window, preserve the speaker and avoid destructive crop; fit or crop only after a frame preview confirms the face and podium are intact.
- Long stills follow the emotion-effect frequency rule in `SKILL.md`.

## Deferred-next-source queue

If the operator supplies another URL for later, record it as `QUEUED_AFTER_CURRENT` with the URL and next action. Do not interrupt or mix it into the active episode until the current project, cloud upload, and reporting are complete.
