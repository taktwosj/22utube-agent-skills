# top5isu Template Contract

## Root Authority

The OneDrive template manifest and ZIP are immutable root evidence. Resolve
their location from the active factory root. Never store a machine-specific
factory root in a handoff manifest.

Required integrity fields:

- `archive_file`
- `archive_sha256`
- `manifest_sha256`
- `packaged_file_count`
- `content_bundle_sha256`
- `archive_root=top5isu/`

Every build remeasures the archive hash and file count. A status string alone
is not proof.

## Clone Transaction

1. Confirm CapCut is closed.
2. Validate the immutable archive and manifest.
3. Extract to a temporary directory.
4. Create a fresh local project name, project ID, draft ID, and timeline ID.
5. Replace every template path placeholder with the new local draft path.
6. Replace all seven sample images while preserving effect segments.
7. Write only the local clone.
8. Validate media links and actual playback.

Never mutate the OneDrive ZIP or root project. Never use a previous episode as
the root.

## Locked Layout

```text
canvas=1080x1920
required_tracks=IMAGE_EFFECT_PRESETS,TTS,T2,T1,LOGO
image_effect_count_required=7
image_ui_y=-600
image_json_transform_y=-0.15625
logo_full_duration=true
```

Portable packages must have zero `.bak` files and zero foreign absolute user
paths.
