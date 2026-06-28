# SRT Sync Rules

Use this reference when audio and captions do not match.

## Source Of Truth

- Text source: final TTS source text, preferably `script/long_script_voice.txt`.
- Timing source: actual rendered voice audio, preferably `video/audio/full_voice.wav`.
- Timing extraction: Whisper/faster-whisper segments or word timings.
- Display text: original TTS script, not Whisper's recognized text.

Whisper Korean text often contains recognition errors. Use it for timestamps, not captions.

## Required Outputs

Write the same cue set to:

```text
audio/main_capcut.srt
video/audio/full.srt
audio/voice_segments_synced.json
audio/whisper_resync/main_capcut_whisper_mapped.json
```

Then rebuild the CapCut `auto_captions` track from that cue set.

## Do Not Do This

- Do not stretch 8 or 42 scene descriptions over Whisper timings.
- Do not trust proportional scene timing after TTS is generated.
- Do not use Whisper's misrecognized Korean as final captions.
- Do not claim sync is fixed until CapCut draft captions match the SRT exactly.

## Verification

Run:

```powershell
py -3 {OneDrive}\22utube\11utube\video\capcut_draft_srt_harness.py `
  --draft "{CapCutDraft}\draft_content.json" `
  --srt "{Episode}\audio\main_capcut.srt" `
  --audio "{Episode}\video\audio\full_voice.wav" `
  --mode longform
```

If the harness fails after a title-only edit, resnap the caption segment `target_timerange` values from `audio/voice_segments_synced.json`.
