# CapCut Clean Base Contract

`jungchilong` is a visual skeleton only.

Allowed in the base:

- layout, banners, subscribe graphics, transitions, effects
- placeholder text: `__SOURCE__`, `__DATE__`, `__FLOW_*__`, `__LOWER_T1_*__`
- fixed subscribe line
- one placeholder video/material if CapCut requires it

Forbidden in the base:

- real episode source names, dates, person names, or channel names
- `source_full`, roughcut, locked clip, old onlineMaterial, or previous episode paths
- `.bak`, `before_*`, `*_backup_*`, `bottom_topic_comments_*`, `t1_topic_texts.json`
- Korean mojibake or replacement characters

Use:

```powershell
python skills/111-politics-longform/scripts/validate_clean_base.py --base "$env:LOCALAPPDATA/CapCut/User Data/Projects/com.lveditor.draft/jungchilong"
```

For an episode draft copied from `jungchilong`, use:

```powershell
python skills/111-politics-longform/scripts/validate_politics_longform_draft.py --draft "<local CapCut draft path>" --manifest "<episode>/00_source/source_manifest.json" --require-locked-clips
```
