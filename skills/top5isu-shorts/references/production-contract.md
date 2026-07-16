# top5isu Standalone Production Contract

Production is internal to `top5isu-shorts` and targets a real editable CapCut project.

## Audio and Assets

- Preserve full narration; never trim audio to force a visual duration.
- Normalize imported narration with ffmpeg loudnorm at -14 LUFS.
- Re-measure the final export when one exists.
- Replace all sample media and keep seven image-effect segments.
- TOP5 source audio is muted unless a verified quote is selected.
- Gunlimbo approved speaker segments remain audible and unmasked by TTS.

## CapCut Clone

- Lock `template_profile=top5isu_v1` and `fallback_allowed=false`.
- Validate the immutable `top5isu` root archive and manifest.
- Clone to a fresh local project with fresh project/timeline IDs.
- Never mutate the root archive or use a previous episode as a base.
- Required track order: `IMAGE_EFFECT_PRESETS,TTS,T2,T1,LOGO`.
- Required audio lanes: `A_TTS,A_SOURCE,A_SFX,A_BGM`.
- Required coordinate pair: UI `-600`, JSON `-0.15625`.
- Reject `shrt white`, `.bak`, stale sample media, and foreign user-profile paths.

## Evidence

A project claim requires the local project path, current draft JSON, validator reports, and actual CapCut visual/playback review. Static JSON alone is not project completion.
