# top5isu TOP55 Template Contract

## Root Authority

The OneDrive template manifest and ZIP are immutable root evidence. The current
canonical profile is `top5isu_v2_top55`, rebuilt from the operator's local
`TOP55` CapCut project. Resolve the active factory root at runtime; never store
a machine-specific factory root in a handoff manifest.

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

1. Confirm CapCut is closed before root/package writes.
2. Validate the immutable archive and manifest.
3. Extract to a temporary directory.
4. Create a fresh local project name, project ID, draft ID, and timeline ID.
5. Replace every template path placeholder with the new local draft path.
6. Replace every sample image. Episode image count is dynamic.
7. Clone one of the four animation prototypes onto every episode image.
8. Mark one or two emotional peak images as high-impact slots.
9. Write only the local clone and validate current media links/readback.
10. Open/play CapCut only when the operator explicitly requests app review.

Never mutate the OneDrive ZIP or root project in place. Never use a previous
episode as the root.

## Locked Layout

```text
template_profile=top5isu_v2_top55
canvas=1080x1920
required_tracks=IMAGE_EFFECT_PRESETS,FRAME,LOGO,TTS_TEXT,SOURCE_TEXT,T2,T1
image_prototype_segments=4
episode_image_count=dynamic
image_ui_y=0
image_json_transform_y=0.0
frame_full_duration=true
logo_full_duration=true
```

Track roles:

- `IMAGE_EFFECT_PRESETS`: episode images, exactly one animation per image
- `FRAME`: `transparent_center_black_1080x1920.png`, full duration
- `LOGO`: `jungboitsu.png`, full duration
- `TTS_TEXT`: narration captions; cue count is dynamic
- `SOURCE_TEXT`: source label
- `T2`: second title line
- `T1`: first title line
- derived audio lane: `A_TTS`; optional `A_SOURCE`, `A_SFX`, `A_BGM`

## Animation Contract

Root prototype order:

1. `레트로 페이드 인` — generic
2. `스트레치 인` — generic
3. `불꽃 스와이프` — high impact
4. `불꽃 회오리` — high impact

Every image must retain exactly one animation. Ordinary images alternate the
generic prototypes. Exactly one or two episode images at explosion, anger,
reversal, or wow moments use one of:

```text
불꽃 회오리
불꽃 스와이프
불꽃 마법
```

Do not apply fire effects to every image. The point is to prevent a static
slideshow while keeping one or two real emphasis moments.

## Portability

Portable packages must have:

- zero `.bak` files
- zero foreign absolute user paths in project control files
- localized active sample media, frame, logo, fonts, and effect resources
- fresh IDs in every derived project
- no OneDrive upload of full editable CapCut project folders; only the immutable
  root ZIP and lightweight episode reports/pointers belong in OneDrive
