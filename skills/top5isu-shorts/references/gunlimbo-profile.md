# Gunlimbo Profile

Use this profile for `style_profile=gunlimbo`.

## Story Policy

- Separate source footage, verified speaker speech, and explanation TTS.
- Keep the story causal: setup -> complication -> emotional turn -> close.
- Use friendly editorial images rather than unnecessary photorealism.
- Insert emotion assets only at a real beat, normally for about two seconds.

## Speaker Audio

The contract must contain explicit `speaker_segments` with source ranges.

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
