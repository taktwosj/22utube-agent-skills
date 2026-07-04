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

Caption accuracy rule:

- `source_full.ko.srt` from Stage 1 is extraction evidence, not subtitle accuracy
  proof. `PASS_CAPTION_EXTRACTED` means "a caption file exists and was saved";
  it does **not** mean the text is display-ready, politically accurate, or safe
  for final SRT.
- Korean **manual** captions may be usable after spot-checking. Korean **auto**
  captions are timing/keyword evidence only by default: they can contain rolling
  duplicate lines, 0.01-second transition cues, speaker arrows, boundary bleed,
  and recognition errors in names/terms such as politicians, parties, offices,
  `레임덕`, `권력증`, `정청래`, `김민석`, `윤석열`, etc.
- Stage 1 may use auto-SRT for keyword search, candidate roughcut discovery, and
  rough quote anchors, but must label it as `auto_not_display_ready` or
  equivalent when reporting. Do not hand an auto-SRT cutout to the user as the
  final subtitle file.
- If the user asks for SRT based on Stage 1 cuts, create a separate `AUTO_TIMED_ONLY`
  file or a clearly named `MANUAL_CLEAN` file. Final/public SRT requires Stage 2
  verification: de-roll/normalize cues, remove 0.01s transition cues, check cut
  boundaries against the source video/audio, and manually correct political names
  and key terms. Whisper/faster-whisper can be used as a cross-check, but its
  transcript is also not automatically final.

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
