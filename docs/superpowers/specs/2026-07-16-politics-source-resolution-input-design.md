# Politics Source Resolution Input Design

## Goal

Allow political-longform source intake at either `1280x720` or `1920x1080` while preserving the final `jungchilong` CapCut canvas at `1920x1080`.

## Contract

- `preferred_source_resolution=1920x1080`
- `required_accepted_source_resolutions=1920x1080|1280x720`
- A valid `1280x720` source must not fail only because it is below 1920x1080.
- The two listed resolutions are guaranteed inputs, not an exhaustive allowlist; other valid resolutions such as 1440p or 4K remain allowed after normal media validation.
- Source `width` and `height` remain the real ffprobe values in the source and locked-clip manifests.
- The final CapCut canvas remains `1920x1080`.
- A `1280x720` 16:9 source is fit to the final canvas with aspect ratio preserved and without distortion.
- Thumbnail resolution remains a separate `1280x720` delivery contract.

## Files

- `skills/111-politics-longform/SKILL.md`: document source-intake and final-canvas separation.
- `tests/test_politics_longform_embedded_contract.py`: prevent regression to 1920x1080-only source intake.
- Codex runtime `111-politics-longform/SKILL.md`: mirror the same contract without overwriting its newer unrelated content.

## Validation

Run the targeted embedded-contract test, then the full politics-longform contract test module. Confirm the Git worktree and Codex runtime both contain the exact resolution tokens.
