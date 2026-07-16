# top5isu Handoff Contract

`top5isu_build_contract_v1` extends, but never replaces, the Stage 1 Tikitaka
handoff.

## Stage 1 Inputs

- `report1_handoff.json`
- `script_handoff_gate.json`
- `timeline_design.json`
- `block_map.json`
- `tts_copy_text.txt`

The script handoff must be PASS, user approval must be explicit, and the voice
route must be decided before production.

## Style Extension

`top5isu_build_contract.json` adds:

- `style_profile=top5|gunlimbo`
- `template_profile=top5isu_v1`
- immutable archive evidence
- required tracks and visual locks
- profile-specific audio policy
- `ffmpeg loudnorm` measurement policy

The production owner may replace assets and add audio lanes but may not rewrite
the approved script or choose another template.

## Status Ownership

- Stage 1 PASS: `00-tikitaka`
- Contract PASS: `top5isu-shorts` validator
- CapCut and final PASS: `000short-production-agent`

No upstream skill may infer downstream PASS.
