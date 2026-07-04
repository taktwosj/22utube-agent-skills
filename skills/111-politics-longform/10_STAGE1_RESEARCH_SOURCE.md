# Stage 1 - Research And Source

Stage 1 is the Claude-friendly pre-CapCut phase. Its job is to produce a source
handoff package for Codex Stage 2.

Do:

- research the political issue and source context
- collect original URLs
- verify source channel and upload date
- download FHD/1080-first source video when available
- attempt subtitle/caption extraction during the YouTube download, preferring
  Korean manual captions, then Korean auto captions
- write candidate `roughcut_edl.json`
- write candidate `source_labels.json`
- write `topic_flow.json`
- optionally write rough `lower_t1_draft.json`
- write handoff and status files for Stage 2

YouTube download command shape:

```powershell
yt-dlp --no-playlist --write-info-json --write-subs --write-auto-subs --sub-langs "ko.*,ko,en.*" --convert-subs srt ...
```

Caption rule:

- If a Korean caption is available, save it beside the source as
  `00_source\{video_id}\source_full.ko.srt`.
- If only a non-Korean caption is available, save it with its language suffix
  and record that Korean captions were unavailable.
- If no caption is available from YouTube, write the exact `yt-dlp` evidence to
  `stage1_status.json` and the Stage 1 report. Do not pretend a transcript
  exists.
- Caption extraction failure is not the same as video download failure, but it
  must be reported plainly because Stage 2 needs transcript evidence to lock
  speech boundaries.

Do not:

- create, edit, inspect, or claim any CapCut draft
- mention `jungchilong` details except to say CapCut belongs to Stage 2
- create `speech_boundary_lock.json`
- create locked clips
- claim final, export complete, upload-ready, or production PASS

Stage 1 may write rough T1, but it is not final. Stage 2 owns final T1 lock
after speech, source, and visual checks.

Required CapCut boundary sentence for Claude handoff:

```text
CapCut build is Stage 2 only. Stage 1 did not create, edit, inspect, or claim any CapCut draft.
jungchilong base availability is checked by Stage 2; if missing, Stage 2 reports WAIT_JUNGCHILONG_BASE_MISSING.
```
