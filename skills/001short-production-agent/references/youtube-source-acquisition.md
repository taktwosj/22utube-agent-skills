# YouTube Shorts source acquisition

Use this reference in Stage 01 when a Shorts URL is the analysis authority.

## Durable acquisition sequence

Keep metadata, media, subtitle, and audio extraction independent so one optional request cannot block the whole episode.

1. Inspect compact metadata first. Persist only fields needed by the episode: video ID, title, channel, duration, dimensions, FPS, language, upload date, and selected format.
2. Download the source video without subtitle flags and preserve it as immutable analysis authority.
3. Request the original-language automatic subtitle separately. Prefer the exact original track such as `en-orig` instead of broad selectors such as `en.*` when the extractor exposes multiple translated/generated variants.
4. Extract an analysis WAV with ffmpeg.
5. Write ffprobe data and SHA-256 for source video, subtitle, WAV, and metadata.
6. Generate sampled frames/contact sheets for scene and baked-in-text inspection.

## Retry pattern

A broad automatic-subtitle request may successfully write one subtitle and then receive HTTP 429 on another variant. Some yt-dlp invocations stop before downloading the video when that optional subtitle request fails.

Do not repeatedly rerun the same combined command. Preserve the subtitle that already exists, then retry the source video with subtitle writing disabled. Fetch any additional subtitle later as an independent best-effort step.

The lesson is separation of authorities, not a permanent claim that subtitle download is unavailable.

## Minimum source evidence

- canonical URL and video ID
- exact local source path
- source SHA-256
- ffprobe duration, width, height, FPS, video/audio codecs, sample rate, channels
- original-language transcript/subtitle when available
- contact sheet or sampled frames
- explicit note on baked-in title/subtitles/watermarks

## Visual-density gate

Before planning T1/T2 or STATE, inspect whether the downloaded source already contains baked-in text. If it does, the human blueprint must explicitly choose one:

- obtain/produce a clean visual before new overlays
- keep the baked-in subtitles and omit overlapping STATE/A10_TEXT
- crop/cover only when it does not obscure faces or essential action

Never silently stack new captions over baked-in captions.
