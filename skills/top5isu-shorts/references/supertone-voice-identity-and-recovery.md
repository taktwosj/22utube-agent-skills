# Supertone Voice Identity And Recovery

## Trigger

Use this reference whenever a TOP5/군림보 episode requires generated narration, a provider returns 401/403, or a newly generated voice sounds different from prior accepted episodes.

## Fixed operator voice identity

```text
provider=Supertone
voice_id=otFXhy6zBa2LQ8AYSWUeDB
model=sona_speech_2t
language=ko
pitch_shift=0
pitch_variance=1
speed=1
```

This profile is an identity lock, not merely a default. Do not silently substitute Edge, macOS `say`, Yuna, another Supertone voice, or an auto-selected provider. A technically valid audio file with the wrong voice is a failed asset.

## Preflight

1. Read a recent accepted `30_audio/tts_manifest.json` and confirm the fixed voice ID and model.
2. Load the active API key only from the approved secret file/environment; never print or serialize it.
3. Confirm the request body explicitly sets `language=ko`, `model=sona_speech_2t`, and the fixed voice settings.
4. If credentials or provider routing changed, generate one short Korean preview line first. Do not synthesize the full script until the preview voice identity is accepted or matches the prior profile.

## Failure behavior

- On 401/403 or missing credential, stop at `WAIT_SUPERTONE_AUTH`.
- Report the provider/authentication blocker without exposing the credential.
- Do not use another TTS provider as an automatic fallback.
- Retrying with a stale `.env` is not a fix. Use the current approved secret path or ask the operator to refresh the credential.

## Spoken-copy and segmentation contract

Keep two text authorities with different jobs:

```text
20_script/tts_copy_text.txt      # visible/caption wording and factual display authority
20_script/tts_spoken_copy.txt    # pronunciation-only Korean reading form
```

The spoken copy may expand tokens for reliable pronunciation but must preserve the same fact and amount:

```text
2026 -> 이천이십육년
TOP5 -> 탑 파이브
AI -> 에이아이
241조 원 -> 이백사십일조 원
```

Never copy pronunciation spellings into visible captions unless the operator asks. Never change a number merely to make synthesis easier.

Use grammatical sentences as the synthesis unit:

1. Split on sentence-ending punctuation, not input lines. One source line may contain two or more synthesis sentences.
2. Generate exactly one provider response per sentence and store sentence index, expected spoken text, duration, path, and hash.
3. Run Korean ASR on each sentence clip before concatenation. Verify the expected company, rank, amount, and closing verb in addition to repeated-token checks.
4. Preserve passing sentence files. Regenerate only failed sentences, then rebuild concat order, target timings, manifest entries, and final hash.
5. Join clips with a short consistent natural gap, normally 80–150 ms, without overlap.

Sentence-level generation is required because it makes audible faults repairable without changing already-approved narration. The earlier minimum-block approach is not valid for this operator's TOP5 lane: a long block can hide or spread a provider stutter, while regenerating the entire track can introduce new defects in sentences that already passed.

Typical provider artifacts include repeated words (`글로벌 글로벌`), repeated syllables (`실실적`, `삼성전전자`), number-tail repetition (`칠칠`), inserted filler words, rank changes, clipped greetings, or a dropped closing phrase. A valid duration/hash does not make such audio acceptable.

Record sentence order, text, duration, gap, and hash in the manifest. Never accept a bad clip merely because full-track ASR looks plausible. See `supertone-sentence-assembly-qa.md` for targeted repair patterns.

## Artifact QA

Before CapCut assembly:

1. Run Korean ASR with language fixed to `ko` on the final joined audio.
2. Check for adjacent duplicate tokens and compare all rank numbers/amounts with the visible script.
3. Inspect the opening, every block boundary, and the final sentence; these are common clipping/stutter locations.
4. Listen to a delivered preview or perform direct playback QA. Whisper can normalize or miss repeated syllables, so ASR is supporting evidence, not a substitute for hearing the audio.
5. If the operator reports an audible artifact, treat that report as a failed audio gate even when ASR says PASS. Identify the exact sentence clip, regenerate only that sentence, rerun its ASR and direct playback check, then rebuild and recheck the joined audio.
6. Only after speech QA passes should loudness normalization, subtitles, image boundaries, and CapCut timing be finalized.

## Verification

1. Write provider, voice ID, model, language, speed/pitch settings, duration, loudness, and SHA-256 to the manifest.
2. Assert the fixed voice ID and model before CapCut assembly.
3. Run Korean ASR verification with language fixed to `ko`; require Korean text detection.
4. ASR language PASS does not prove speaker identity, so manifest identity and operator voice expectation remain separate gates.
5. Wrong-language or wrong-speaker audio must be excluded from builder inputs rather than left beside the final audio with an ambiguous filename.

## Durable lesson

When the operator says “원래 음성 보이스아이디” or notes that the result is an English/female voice, treat it as a voice-identity regression. Restore the fixed Supertone male profile; do not defend or normalize the fallback output.
