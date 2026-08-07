# YouTube Shorts source acquisition

Use this reference in Stage 01 to normalize an accepted intake origin into the canonical OneDrive episode root. Accepted origins are a Google Drive folder/file, a YouTube Shorts URL, or a user-designated Desktop local folder. The final working, assembly, and validation root is always `C:\Users\arajun\OneDrive\22utube\22factory_20260628\0000shrt\<YYMMDD_short-title_source-id>`.

## Accepted origins and canonical receipt

Normalize the selected source as `00_input/source.mp4` under the canonical OneDrive root, then create immutable `90_workflow/onedrive_intake_receipt.json`. Record `origin_type`, `origin_locator`, canonical source URL and ID when applicable, `input_relative_path`, SHA-256, measured duration, and storage policy. Do not mutate the normalized source after receipt creation; replace it only through a new receipt and Stage 01 revalidation.

- Google Drive folder/file: record the read-only locator, visible file identity, and copied-file SHA-256. Drive is optional intake only; never write, share, or upload there.
- YouTube Shorts URL: record the canonical Shorts/watch URL, video ID, extractor metadata readback, and copied/downloaded-file SHA-256.
- User-designated Desktop local folder: record the exact user-designated locator, selected file name, and copied-file SHA-256. Do not infer another Desktop file.

## Durable acquisition sequence

Keep metadata, media, subtitle, and audio extraction independent so one optional request cannot block the whole episode.

1. Resolve the accepted origin with the origin-specific identity evidence above. For a YouTube URL, inspect compact metadata first and persist only fields needed by the episode: video ID, title, channel, duration, dimensions, FPS, language, upload date, and selected format.
2. Copy or download the selected source to the canonical OneDrive root without subtitle flags and preserve it as immutable analysis authority.
3. Request the original-language automatic subtitle separately. Prefer the exact original track such as `en-orig` instead of broad selectors such as `en.*` when the extractor exposes multiple translated/generated variants.
4. Extract an analysis WAV with ffmpeg.
5. Write ffprobe data and SHA-256 for source video, subtitle, WAV, and metadata.
6. Generate sampled frames/contact sheets for scene and baked-in-text inspection.

## Metadata persistence without stdout truncation

Do not depend on a full `yt-dlp --dump-single-json` payload surviving an agent/tool stdout limit. Prefer `--write-info-json --skip-download -o <episode>/00_input/source`, read `source.info.json` locally, then write a compact `source_metadata.json` containing only the fields required by the episode. Keep the full info file as evidence but do not paste it into chat or tool output.

## Transcript and visible-caption reconciliation

Automatic subtitles may cover only the opening narration while later meaning is carried by baked-in screen captions. Never treat a short VTT as proof that the rest of the video has no text or no message.

1. Extract the full analysis WAV and run local ASR with timestamps.
2. Generate a 1fps contact sheet for overall scene inventory.
3. If caption boundaries or fast cuts remain ambiguous, generate a 2fps sheet and inspect scene/text changes at 0.5-second precision; use 4fps only around short unresolved boundaries.
4. Classify audible words as `TRANSCRIPT`, visible creator captions as `SCREEN_LABEL` or `SCREEN_CLAIM`, and unconfirmed music/SFX/ambient details as `UNVERIFIED`.
5. If ASR detects speech only in the opening but later frames carry captions, state exactly that; do not promote visible captions into verified spoken audio.
6. Derive structural boundaries from actual scene, action, speaker, text, or narrative-function changes rather than from the sampling interval itself.

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

## Optional comment insight pass

When the local Mac mini comment app reports `hasApiKey=true`, do not read, print, or persist the API key. Prove availability only with its live response: `ok=true`, a video title, and no `comment_error`. Request 50 public comment threads, sample relevance and latest ordering, then rank locally with like count, reply count, and recency. Select five or six genuinely different reaction clusters rather than six near-duplicate popular comments.

Store only the compact insight result in `10_analysis/comment_insights.json`: reaction cluster, representative public comment excerpt, like/reply counts, and the creative use or rejection reason. Comments are audience interpretation for Stage 03/04 hooks; they never verify a source fact or identity. If comments are disabled, quota-limited, or the local request fails, record `COMMENTS_UNAVAILABLE` and continue source analysis.

## Visual-density gate

Before planning T1/T2 or STATE, inspect whether the downloaded source already contains baked-in text. If it does, the human blueprint must explicitly choose one:

- obtain/produce a clean visual before new overlays
- keep the baked-in subtitles and omit overlapping STATE/A10_TEXT
- crop/cover only when it does not obscure faces or essential action

Never silently stack new captions over baked-in captions.
