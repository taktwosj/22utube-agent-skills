# 08 CapCut assembly

## Load order

1. Use [`scripts/build_episode_capcut.py`](../scripts/build_episode_capcut.py) as the production entrypoint. Do not substitute a helper, old builder, or previous episode draft.
2. Read the Stage 07 canonical locks from `30_audio_srt/audio_lock.json`, `30_audio_srt/caption_lock.json`, and `30_audio_srt/final.srt`.
3. Build only against the `shrt_white_base_v2_15` root and its v2 15-track contract.
4. Read [`references/urakkai-artifact-contract.md`](../references/urakkai-artifact-contract.md) for the manual media-relink handoff and final report fields.

## Build contract

- Accepted visual input modes are `CLEAN_VISUAL_READY` and `SOURCE_VIDEO_PROVISIONAL`. The provisional mode uses the episode source video and must remain reported as provisional. Neither mode is upload-ready evidence: static assembly ends at `CAPCUT_STATIC_VALIDATED` / `WAIT_USER_CAPCUT_CHECK`.
- `A12_RESERVED_EMPTY` must remain empty. Do not place BGM, segments, materials, or production-plan rows on A12.
- A10 authority is the validated external vocals stem required by Stage 07. CapCut built-in vocal separation is forbidden and must not be used as a bypass.
- Preserve exact approved T1, T2, caption-role, speaker-color, effect, audio, and timing placements. The builder executes the locked plan and does not redesign it.
- Static validation must read back the root and primary `Timelines/*` draft, material references, ID mirrors, geometry, timing, mute/volume policy, and the 15-track role contract before reporting `CAPCUT_STATIC_VALIDATED`.
- For an existing `SOURCE_VIDEO_PROVISIONAL` project, call `scripts/build_episode_capcut.py --config <config.json> --swap-provisional-video-only` only with a `STAGE08_VIDEO_ONLY_SWAP` edit lock and after CapCut is closed. It changes VIDEO media only, reruns static validation, and ends at `WAIT_USER_CAPCUT_CHECK`.

## Handoff

The builder may package or record media paths, but it must not promise that relinking is unnecessary. The operator performs the CapCut media relink when required. Under `AGENT_PRIMARY_CLEAN_SOURCE`, the agent validates a completed VMake clean asset and performs the VIDEO-only swap/reassembly; `USER_FALLBACK_CLEAN_SOURCE` uses a validated user-supplied asset only after the defined VMake fallback condition. CapCut visual review/refinement and approval, render, and upload are user-manual-only. The static report provides `project_path` and `media_source_path` as copyable paths, following [`references/urakkai-artifact-contract.md`](../references/urakkai-artifact-contract.md).

Load [`references/interim-capcut-project-sync.md`](../references/interim-capcut-project-sync.md) only for an explicit sync request. It is a sync reference, not the default Stage 08 assembly route.
