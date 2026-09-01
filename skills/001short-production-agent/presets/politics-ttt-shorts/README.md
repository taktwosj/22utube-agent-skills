# Politics TTT Shorts preset

This is a selector-only preset of `001short-production-agent`, not a second
production owner. It keeps the normal 001 flow: original grid, urakkai grid,
locks, shared CapCut builder and validators, then `WAIT_USER_CAPCUT_CHECK`.

Use it only after the political-longform owner has finished selecting and
locking the source range. Longform research, argument, script and card order
remain outside this preset. `SOURCE_CREDIT` text is episode data and must be the
actual channel name; it is intentionally not stored in `profile.json`.

The preset contains no Python engine. Its six selectors resolve through the
shared template, assembly-type and audio-policy matrices.

Stage 08 selects these existing shared inputs without copying builder code:

- `--profile presets/politics-ttt-shorts/profile.json`
- `--root-profile home_windows_black_top_v1`
- `--root-contract-path 00_asset_tools/templates/capcut/shrt_black_top_v1/shorts_capcut_root_contract_v1.json`

The root resolver verifies the black-top archive SHA, manifest, layout contract
and all 15 archive track identities before assembly. Static validation does not
replace the real CapCut visual gate.
