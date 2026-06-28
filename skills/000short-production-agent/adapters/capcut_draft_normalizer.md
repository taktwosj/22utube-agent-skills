# capcut_draft_normalizer

Normalize CapCut draft internals into a stable audit format before harness checks.

Minimum normalized structure:

```json
{
  "project_duration": 0,
  "video_tracks": [],
  "text_tracks": [],
  "audio_tracks": [],
  "top_text_count": 0,
  "middle_text_count": 0,
  "bottom_text_count": 0,
  "implemented_remix_order": "",
  "draft_content_path": "",
  "draft_meta_info_path": "",
  "draft_virtual_store_path": ""
}
```

The normalizer must not change the CapCut draft. It only creates
`capcut/normalized_draft.json` for validation.
