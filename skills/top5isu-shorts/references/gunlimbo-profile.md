# Gunlimbo Profile

Use this profile for `style_profile=gunlimbo`.

## Story Policy

- Separate source footage, verified speaker speech, and explanation TTS.
- Keep the story causal: setup -> complication -> emotional turn -> close.
- Use friendly editorial images rather than unnecessary photorealism.
- Insert emotion assets only at a real beat, normally for about two seconds.

## Speaker Audio

When meaningful source speech exists, full-source vocal isolation is mandatory
before any quote clip is cut:

```text
source_vocal_isolation.policy=REQUIRED_WHEN_MIXED_AUDIO
source_vocal_isolation.status=PASS
source_vocal_isolation.processed_before_speaker_clip_cut=true
source_vocal_isolation.q_clips_source=vocals_stem
source_vocal_isolation.original_video_audio_muted=true
source_vocal_isolation.residual_music_review=PASS
source_vocal_isolation.voice_artifact_review=PASS
speaker_segments[*].source_stem=vocals_stem
```

Run Demucs/approved equivalent on the complete original A/B source audio, then
cut `Q1`, `Q2`, and later quotes from `vocals.wav`. Never run isolation only on
short Q fragments. If full-source isolation cannot run, stop at
`WAIT_VOCAL_ISOLATION`; mixed music-and-voice quote clips are not an allowed
fallback.

The contract must contain explicit `speaker_segments` with source ranges when
meaningful source speech exists. If analysis proves there is no meaningful
source speech, the only caption-only exception requires:

```text
source_speaker_mode=no_meaningful_source_speech
source_dialogue_analysis_status=NO_DIALOGUE
speaker_segments=[]
source_cta_reuse=false
```

```text
speaker_segments_preserved=true
speaker_mute_forbidden=true
speaker_mute_forbidden failure=FAIL_SPEAKER_SEGMENT_MUTED
```

TTS explains context around the approved speaker ranges. It must not replace
the speaker's key line or overlap it unintelligibly.

## Emotion Assets

Allowed roles include surprise, sadness, anger, joy, confusion, and dismissive
reaction. Each insertion records timing, asset identity, duration, and reason.
Do not use a reaction asset as filler or let it obscure verified source speech.
