# Stage 1 Output Contract

Required files:

```text
episode_manifest.json
00_source\source_manifest.json
00_source\{video_id}\source_full.mp4
00_source\{video_id}\source_full.ko.srt  when Korean captions are available
00_source\{video_id}\source_full.info.json
00_source\{video_id}\source_full.ffprobe.json
10_analysis\roughcut_edl.json
10_analysis\source_labels.json
10_analysis\topic_flow.json
20_script\lower_t1_draft.json  optional rough draft only
90_reports\stage1_handoff_to_codex.md
90_reports\stage1_status.json
```

Download rule:

- `PASS_SOURCE_DOWNLOADED` is allowed only when the actual `source_full.mp4` exists and ffprobe evidence proves it is playable.
- If the file is missing, blocked, partial, private, DRM-limited, or only a proxy is available, report `WAIT_DOWNLOAD`.
- If download failed, say plainly in Korean that the download did not complete.
- Do not hide download failure behind rough notes, screenshots, candidate URLs, or analysis.

Caption extraction rule:

- Stage 1 must attempt captions during source download with `--write-subs`,
  `--write-auto-subs`, Korean-first `--sub-langs`, and SRT conversion.
- Save Korean captions as `source_full.ko.srt` whenever YouTube provides manual
  or auto captions.
- If Korean captions are unavailable, record `caption_status:
  WAIT_CAPTION_UNAVAILABLE` or `caption_status: PASS_CAPTION_NON_KO_ONLY` with
  exact evidence. Do not invent or summarize transcript text as if it were SRT.
- If captions are unavailable but the video downloaded and ffprobe passed,
  `PASS_SOURCE_DOWNLOADED` may still be true, but Stage 2 must create or verify
  speech evidence before speech-boundary lock.

`stage1_status.json` must include:

```json
{
  "status": "PASS_SOURCE_DOWNLOADED or WAIT_DOWNLOAD",
  "download_completed": true,
  "download_failed_reason": "",
  "source_full_path": "",
  "caption_status": "PASS_CAPTION_EXTRACTED or WAIT_CAPTION_UNAVAILABLE or PASS_CAPTION_NON_KO_ONLY",
  "caption_path": "",
  "caption_evidence": "",
  "ffprobe_evidence": {
    "duration_sec": 0,
    "width": 0,
    "height": 0,
    "video_codec": "",
    "audio_codec": ""
  },
  "stage2_may_start": false
}
```

When status is `WAIT_DOWNLOAD`, set `download_completed` to `false`,
`stage2_may_start` to `false`, and include:

- original URL
- attempted format ids or desired format
- exact failure text
- next action needed

Stage 2 must not begin from a Stage 1 package whose status is `WAIT_DOWNLOAD`.
