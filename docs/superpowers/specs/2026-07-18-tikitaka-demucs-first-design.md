# Tikitaka Demucs-First Source Voice Design

## Goal

Make full-source vocal separation a default `00-tikitaka` Stage 1 preprocessing
step so every retained speaker quote is designed from a stable `vocals.wav`,
never from audio cut before separation.

## Approved Scope

The default order for Shorts with source media is:

```text
source.mp4 identity lock
-> extract the complete source audio
-> run Demucs on the complete source audio
-> create and validate vocals.wav
-> detect and lock speaker ranges against vocals.wav
-> create the Stage 1 timeline and handoff
-> let 000short-production-agent cut Q clips from vocals.wav
-> keep embedded source-video audio muted in CapCut
```

The only skip state is `NOT_REQUIRED_NO_SOURCE_SPEECH`. It is valid when the
source has no audio stream or when the absence of human speech is explicitly
confirmed by the user or source evidence. Pure BGM must not be classified as
no-source-speech without that confirmation.

`no_vocals.wav` is never a production input. Separate BGM remains optional.

## Considered Approaches

### Selected: Tikitaka performs analysis preprocessing

`00-tikitaka` invokes a deterministic preprocessing script immediately after
the source identity lock. The Tikitaka harness validates the resulting
artifacts but does not launch Demucs or the next skill. Stage 2 consumes the
validated manifest and `vocals.wav`.

This places separation before speaker-range design, preserves the
Codex-owned-stage-transition rule, and avoids running Demucs twice.

### Rejected: production performs the first separation

This is too late because Stage 1 would still choose source ranges from mixed
audio and could hand off ranges that sound different after separation.

### Rejected: both stages run Demucs

This duplicates expensive work and can create different outputs when the model
or dependency version changes. One artifact and one hash chain are safer.

## Ownership

### `00-tikitaka`

- Owns full-source audio extraction and Demucs execution as source-analysis
  preprocessing.
- Creates `10_analysis/audio/full_source_audio.wav`.
- Creates `10_analysis/audio/vocals.wav`.
- Creates `10_analysis/source_voice_separation.json`.
- Uses `vocals.wav` for speaker-range verification and Stage 1 design.
- Records the `vocals.wav` reference on every `speaker_quote`.
- Does not create final Q clips, CapCut drafts, exports, or upload packages.

### Tikitaka harness

- Validates the separation manifest, artifact paths, hashes, duration parity,
  sample rate, source binding, and skip reason.
- Writes gate state only.
- Never launches Demucs or `000short-production-agent`.

### `000short-production-agent`

- Requires the validated separation artifact at Stage 2 entry.
- Cuts Q clips only from the declared `vocals.wav`.
- Applies 0.1 to 0.2 second handles when source bounds allow and short fades at
  both ends.
- Keeps embedded source-video audio muted for every caption type, including
  `speaker_quote`.
- Places Q and N audio on separate lanes without overlap unless the locked
  design explicitly permits overlap.
- Performs listening review and final loudness normalization.

## Artifact Contract

The canonical gate file is:

```text
10_analysis/source_voice_separation.json
```

A successful separation records:

```json
{
  "gate_name": "SOURCE_VOICE_SEPARATION_GATE",
  "status": "PASS",
  "owner_skill": "00-tikitaka",
  "source_fingerprint_sha256": "<64 lowercase hex>",
  "separation_engine": "demucs",
  "separation_model": "htdemucs",
  "separation_scope": "FULL_SOURCE_AUDIO",
  "source_audio_path": "10_analysis/audio/full_source_audio.wav",
  "source_audio_sha256": "<64 lowercase hex>",
  "demucs_input_sha256": "<same as source_audio_sha256>",
  "vocals_path": "10_analysis/audio/vocals.wav",
  "vocals_sha256": "<64 lowercase hex>",
  "source_duration_sec": 42.0,
  "source_audio_duration_sec": 42.0,
  "vocals_duration_sec": 42.0,
  "duration_tolerance_sec": 0.25,
  "sample_rate_hz": 48000,
  "source_voice_music_removed": true,
  "q_segment_source": "10_analysis/audio/vocals.wav",
  "no_vocals_used": false,
  "created_by": "prepare_source_voice.py"
}
```

A valid skip records:

```json
{
  "gate_name": "SOURCE_VOICE_SEPARATION_GATE",
  "status": "NOT_REQUIRED_NO_SOURCE_SPEECH",
  "owner_skill": "00-tikitaka",
  "source_fingerprint_sha256": "<64 lowercase hex>",
  "no_source_speech_confirmed": true,
  "confirmation_source": "user|source_evidence|no_audio_stream",
  "source_voice_music_removed": false,
  "no_vocals_used": false
}
```

All artifact paths are episode-root-relative. Machine-specific absolute paths
are forbidden in the manifest.

Every `speaker_quote` timeline segment additionally records:

```json
{
  "source_audio_ref": "10_analysis/audio/vocals.wav",
  "source_audio_provenance": "demucs_full_source_vocals",
  "source_audio_range": {
    "start_sec": 3.2,
    "end_sec": 6.7
  }
}
```

`source_audio=on` means the separated Q audio is audible. It no longer means
that the embedded audio stream of the source video may remain enabled.

## Execution Contract

The preprocessing command accepts an episode root and a source path. It:

1. Probes the source with `ffprobe`.
2. If there is no audio stream, writes the valid skip manifest.
3. Otherwise verifies `ffmpeg` and the Python `demucs` module.
4. Extracts the entire audio at 48 kHz.
5. Runs Demucs with the `htdemucs` model and `--two-stems vocals`.
6. Converts the resulting vocal stem to the stable 48 kHz artifact path.
7. Probes both WAV files.
8. Rejects duration drift over 0.25 seconds.
9. Writes hashes and the PASS manifest only after all checks succeed.

Temporary Demucs output, including `no_vocals.wav`, is discarded after the
stable vocal artifact has been created.

Missing dependencies do not trigger a fallback separator:

```text
WAIT_FFMPEG_AVAILABLE
WAIT_FFPROBE_AVAILABLE
WAIT_DEMUCS_AVAILABLE
```

Artifact or binding failures use:

```text
WAIT_SOURCE_VOICE_SEPARATION
WAIT_SOURCE_VOICE_DURATION_PARITY
WAIT_SOURCE_VOICE_HASH_BINDING
WAIT_SOURCE_VOICE_Q_PROVENANCE
```

## Failure and Recovery

- A source with an audio stream and no valid PASS/skip manifest blocks
  `SCRIPT_HANDOFF_GATE`.
- A `speaker_quote` is forbidden when the manifest is
  `NOT_REQUIRED_NO_SOURCE_SPEECH`.
- A `speaker_quote` referring to the original video or pre-cut mixed audio
  fails `WAIT_SOURCE_VOICE_Q_PROVENANCE`.
- A missing Demucs dependency stops before Stage 1 design; it is never silently
  replaced with raw source audio.
- Severe residual music or robotic voice detected by listening review blocks
  final production and returns to weak enhancement/noise-reduction repair.
- Q and N overlap, missing fades, embedded source-video audio, or failed final
  normalization blocks the relevant production gate.

## Validation Strategy

Unit and contract tests cover:

- whole-source extraction is passed to Demucs before any Q range is cut;
- a valid PASS manifest binds the source, full audio, and vocals hashes;
- invalid duration, sample rate, hash, scope, or absolute paths fail;
- no-audio sources produce `NOT_REQUIRED_NO_SOURCE_SPEECH`;
- a manual skip without confirmation fails;
- Stage 1 handoff fails without the source-voice gate;
- Stage 2 rejects speaker quotes not sourced from `vocals.wav`;
- source-video embedded audio is rejected even for `speaker_quote`;
- existing no-speaker and narration paths remain valid with the explicit skip;
- the Tikitaka harness remains validator-only and n8n remains `NOT_REQUIRED`
  unless explicitly selected.

No test requires an installed Demucs model. Execution tests mock the external
process boundary while validator tests use small generated WAV fixtures.

## Rollback

The change is isolated on a dedicated branch and committed separately from the
existing mixed worktree. Reverting the feature commit restores the previous
source-audio behavior without touching unrelated user changes.
