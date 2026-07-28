# top5isu Internal Stage Contract

`top5isu_build_contract_v2` is the current internal production authority for the
standalone factory.

## Internal Lifecycle

```text
INTAKE
-> EVIDENCE_PACKET
-> CHATGPT_WRITER
-> SCRIPT_QA
-> AUDIO_ASSETS
-> CAPCUT_PROJECT
-> FINAL_REPORT
```

No external skill handoff is permitted. The logged-in ChatGPT page is an
internal model backend controlled by `top5isu-shorts`. Every stage writes into
the same episode root and preserves `style_profile`,
`template_profile=top5isu_v2_top55`, and `writer_backend=chatgpt_browser`.

## Script Inputs

- `10_analysis/evidence_packet.json`
- `10_analysis/writer_packet.json`
- `20_script/design_blueprint.md`
- `20_script/writer_prompt.md`
- `20_script/writer_response.json`
- `20_script/script_qa.json`
- `20_script/final_script.json`
- `20_script/tts_copy_text.txt`
- `20_script/top5isu_build_contract.json`

The writer response, blueprint, and build contract must pass validators before
audio, assets, or CapCut assembly starts.

## Production Outputs

- normalized narration and approved source speech under `30_audio`
- episode-only visual assets under `40_assets`
- real editable local CapCut clone plus snapshots under `50_capcut_project`
- validator and final reports under `90_reports`

## Status Ownership

The same `top5isu-shorts` skill owns all internal statuses. `FINAL_LOCK` is
allowed after every applicable static gate, current project-file readback/hash,
and assembly-report validation pass. CapCut app visual/playback review is an
explicit optional operator request. Upload remains separate approval.
