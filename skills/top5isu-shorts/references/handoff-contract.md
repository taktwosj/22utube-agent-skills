# top5isu Internal Stage Contract

`top5isu_build_contract_v1` is the internal production authority for the standalone factory.

## Internal Lifecycle

```text
INTAKE -> SCRIPT_DESIGN -> AUDIO_ASSETS -> CAPCUT_PROJECT -> FINAL_REPORT
```

No external skill handoff is permitted. Every stage writes into the same episode root and preserves the selected `style_profile` and `template_profile=top5isu_v1`.

## Script Inputs

- `20_script/design_blueprint.md`
- `20_script/script.json`
- `20_script/tts_copy_text.txt`
- `20_script/top5isu_build_contract.json`

The blueprint and build contract must pass their validators before audio, assets, or CapCut assembly starts.

## Production Outputs

- normalized narration and approved source speech under `30_audio`
- episode-only visual assets under `40_assets`
- real editable local CapCut clone plus snapshots under `50_capcut_project`
- validator and final reports under `90_reports`

## Status Ownership

The same `top5isu-shorts` skill owns all internal statuses. `FINAL_LOCK` is allowed only after every applicable static gate plus actual CapCut visual/playback review passes. Upload remains a separate explicit operator approval.
