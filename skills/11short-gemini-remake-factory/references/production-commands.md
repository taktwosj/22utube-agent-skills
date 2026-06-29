# Production Commands

Replace `{work}`, `{url}`, and `{draft_name}` before running.

## Create Work Folder

```powershell
$env:WORKSPACE_ROOT = "$env:USERPROFILE\OneDrive\22utube"
$env:UTUBE_ROOT = "$env:WORKSPACE_ROOT\11utube"
$env:SHORT_ROOT = "$env:UTUBE_ROOT\11short"
$work = "$env:SHORT_ROOT\000short-production-agent\episodes\{yyMMdd-videoid}"
New-Item -ItemType Directory -Force -Path $work | Out-Null
```

## Download Source

```powershell
py -3 -m yt_dlp `
  --no-playlist `
  --write-info-json `
  --write-comments `
  --write-auto-subs `
  --sub-lang "ja,ko,en" `
  --sub-format "json3/vtt/best" `
  -f "bestvideo[width<=1920][height<=1920][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/bestvideo[width<=1920][height<=1920][ext=mp4]+bestaudio/best[width<=1920][height<=1920]/bv*+ba/b" `
  --merge-output-format mp4 `
  --remux-video mp4 `
  -o "$work\source.%(ext)s" `
  "{url}"
```

If subtitles trigger blocking, rerun without subs:

```powershell
py -3 -m yt_dlp --no-playlist --no-write-subs --no-write-auto-subs --write-info-json --write-comments -f "bestvideo[width<=1920][height<=1920][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/bestvideo[width<=1920][height<=1920][ext=mp4]+bestaudio/best[width<=1920][height<=1920]/bv*+ba/b" --merge-output-format mp4 --remux-video mp4 -o "$work\source.%(ext)s" "{url}"
```

## Probe And Contact Sheets

```powershell
ffprobe -v error -show_entries format=duration -show_entries stream=width,height,r_frame_rate,codec_type -of json "$work\source.mp4"
ffmpeg -y -hide_banner -loglevel error -i "$work\source.mp4" -vf "fps=1/2,scale=216:384,tile=5x6" -frames:v 1 "$work\contact_sheet.jpg"
ffmpeg -y -hide_banner -loglevel error -i "$work\source.mp4" -vf "fps=1,scale=162:288,tile=9x7" -frames:v 1 "$work\contact_sheet_1s.jpg"
```

## Build Gemini Request

Use the canonical CapCut remake system prompt, then paste the generated `gemini_request.md` into Gemini/Google AI Studio with URL context enabled.

```powershell
py -3 "$HOME\agent-skills\skills\11short-gemini-remake-factory\scripts\build_gemini_request.py" --url "{url}" --out "$work\gemini_request.md"
```

## Extract Original Audio

```powershell
ffmpeg -y -hide_banner -loglevel error -i "$work\source.mp4" -map 0:a:0 -vn -c:a libmp3lame -q:a 2 "$work\source_original_audio.mp3"
```

## Optional Hook-Forward Source

Use this when the strongest beat is not already in the first 1-2 seconds. Replace the times before running. After this, use `source_hooked.mp4` for CapCut and extract original audio from `source_hooked.mp4`.

```powershell
ffmpeg -y -hide_banner -loglevel error -ss "00:12.300" -to "00:13.500" -i "$work\source.mp4" -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 160k "$work\hook_preview.mp4"
ffmpeg -y -hide_banner -loglevel error -i "$work\source.mp4" -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 160k "$work\source_main_reencoded.mp4"
$concat = @(
  "file '$($work.Replace('\','/'))/hook_preview.mp4'",
  "file '$($work.Replace('\','/'))/source_main_reencoded.mp4'"
)
$concat | Set-Content -Encoding ascii "$work\concat_hook.txt"
ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i "$work\concat_hook.txt" -c copy "$work\source_hooked.mp4"
ffmpeg -y -hide_banner -loglevel error -i "$work\source_hooked.mp4" -map 0:a:0 -vn -c:a libmp3lame -q:a 2 "$work\source_original_audio.mp3"
```

If no hook-forward source is needed, keep using `source.mp4` and extract audio from `source.mp4`.

## Supertone TTS

```powershell
py -3 "$env:SHORT_ROOT\supertone_11short_tts.py" --model sona --text-file "$work\voice_opening.txt" --out "$work\voice_opening.mp3" --voice-id 6e43a7b9ffa9834c154ab7
py -3 "$env:SHORT_ROOT\supertone_11short_tts.py" --model sona --text-file "$work\voice_body.txt" --out "$work\voiceover_body.mp3" --voice-id 049d87c31d8e431b15f468
```

## Harness

```powershell
py -3 "$env:SHORT_ROOT\shorts_remake_harness.py" "$work" --stage analysis
Copy-Item "$work\shorts_remake_harness_report.json" "$work\shorts_remake_harness_report_analysis.json" -Force

py -3 "$env:SHORT_ROOT\shorts_remake_harness.py" "$work" --stage assets
Copy-Item "$work\shorts_remake_harness_report.json" "$work\shorts_remake_harness_report_assets.json" -Force
```

## CapCut Draft

```powershell
py -3 "$env:UTUBE_ROOT\tools\youtube_ko_subtitles\capcut_factory_profile.py" `
  --draft-name "{draft_name}" `
  --video "$work\source.mp4" `
  --srt "$work\guide_ko.srt" `
  --top-title "{top_title_text}" `
  --source-audio "$work\source_original_audio.mp3" `
  --intro-audio "$work\voice_opening.mp3" `
  --voiceover-audio "$work\voiceover_body.mp3" `
  --voiceover-srt "$work\voice_body_split.srt" `
  --ocr-srt "$work\onscreen_ko.srt" `
  --ocr-layout-json "$work\onscreen_layout.json" `
  --analysis-json "$work\analysis.json"
```

If hook-forward preprocessing was applied, replace the video argument with:

```powershell
--video "$work\source_hooked.mp4"
```

If the reference draft exists and exact style is required, add:

```powershell
--factory "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\0613 FIRE"
```

Then run:

```powershell
py -3 "$env:SHORT_ROOT\shorts_remake_harness.py" "$work" --stage capcut --draft-name "{draft_name}"
Copy-Item "$work\shorts_remake_harness_report.json" "$work\shorts_remake_harness_report_capcut.json" -Force

py -3 "$env:SHORT_ROOT\shorts_remake_harness.py" "$work" --stage all --draft-name "{draft_name}"
Copy-Item "$work\shorts_remake_harness_report.json" "$work\shorts_remake_harness_report_all.json" -Force
```

## Known OCR Font Patch

If capcut harness says `onscreen overlay font size must be 12, got 15`, patch only the OCR overlay text track in `draft_content.json` so all nested `size` and `font_size` values for OCR text materials are `12`, then rerun capcut harness.
