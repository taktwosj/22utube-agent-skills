# CapCut QA Rules

Use this reference before hand-editing `draft_content.json`.

## Safe Edit Pattern

1. Back up `draft_content.json`.
2. Read the existing material/segment structures.
3. Clone existing structures; do not invent fields.
4. Write UTF-8 JSON.
5. Re-read and verify the exact Korean strings.
6. Run the SRT harness if captions or text tracks changed.
7. Generate a visual snapshot contact sheet.

## Korean Text

PowerShell and heredocs can corrupt Korean when the console code page is wrong.

Safer options:

- Read Korean text from an existing UTF-8 file.
- Build critical Korean strings with Unicode code points.
- Verify with Python `repr()` after writing.

Check both:

- `production_console.json`
- actual CapCut `draft_content.json`

Console text being correct does not prove CapCut draft text is correct.

## Opening Cut Duration Lock

For `youtube_midform` and `youtube_longform`, verify the first two base visual segments before reporting a REVIEW draft as ready:

- visual segment 01 starts at `0.0s` and lasts exactly `8.0s`
- visual segment 02 starts at `8.0s` and lasts exactly `8.0s`
- later visual segments start at or after `16.0s`

These first two slots are reserved so the user can replace either still image with an 8-second video clip. Caption and title tracks may have their own timing, but the underlying visual slots must not be shortened, extended, or rippled by SRT sync or auto scene distribution.

## Snapshot

Use:

```powershell
py -3 {OneDrive}\22utube\11utube\tools\capcut_visual_snapshot.py `
  --episode-dir "{Episode}" `
  --mode longform `
  --manifest "{Episode}\video\capcut_draft_manifest.json" `
  --draft "{CapCutDraft}\draft_content.json" `
  --output-dir "{Episode}\video\capcut_snapshots_{label}" `
  --count 3
```

Inspect the contact sheet for:

- landscape 16:9
- first two visual slots are replaceable 8-second slots
- title not mojibake
- captions not mojibake
- no huge title/caption overflow
- image visible
- no broken/blank frame
