# Root-contract and production-plan CapCut execution

Use this reference when Stage 05 has approved content but Stage 08 cannot deterministically assemble the CapCut draft.

## Core split

Keep three authorities separate:

1. **Immutable root project** — CapCut-native styles, transforms, masks, effects, animations, fixed assets, and track skeleton.
2. **`root_contract.json`** — one-time extracted anchor map for exactly one root profile.
3. **`production_plan.json`** — per-episode executable placements compiled from the human-facing content matrix.

The builder is an executor, not a designer. It must not rewrite copy, choose tracks, infer source ranges, or invent timing.

## Trace the existing pipeline before redesigning it

Do not mistake a failed run for absence of cloning or absence of JSON input. Read the current execution order first. A builder may already extract the root ZIP, inject episode values, clone to a working project, regenerate project/draft/timeline IDs, copy to a target, and validate.

When that is already true, adding “another JSON file” or proposing “clone the root and replace values” does not identify the defect. State the narrower gap: the existing config and approved timeline are not yet a single complete execution plan, anchor mapping is implicit or index-based, heterogeneous subdrafts are misclassified, or transaction/state handling prevents a successful retry.

When the operator says the current system already clones the root and writes new values, acknowledge that correction immediately and compare the real current sequence against the proposed compiled-plan sequence. Never describe an already-implemented mechanism as the missing architecture.

## Root contract

Extract once from a verified immutable root and record:

- `root_profile`, root archive/tree SHA-256, and schema version
- logical anchor key (`VIDEO`, `T1`, `T2`, `A9`, `A10`, `STATE`, `A11`, `A12`, screen lanes)
- template `track_id`, `segment_id`, and `material_id`
- allowed replacement fields
- preserved style fields

Runtime code must resolve anchors through the contract. Never use `tracks[n]` for episode assembly. A one-time extractor may receive a reviewed role order for a pinned root, but the resulting contract must contain the actual IDs and root fingerprint.

Do not hand-author CapCut IDs in an episode plan. Generate the contract from the root, review it once, then lock it.

Each root project gets its own contract. Never borrow or fall back to anchors from another root profile.

### Current runtime authority: `shrt_white_base_v2` 15-track role map

Stage 05 and Stage 08 use `shrt_white_base_v2`; the v1 map below is historical reference only. The immutable v2 archive is bound to SHA-256 `bb4a09b7f9334594e087b56ee52efae4e9d8856a41754d9b36ef89c1dde5f33a`. Runtime identity comes from the reviewed layout contract's `track_id` and `type`, never array position.

| role | type | track_id | runtime contract |
|---|---|---|---|
| `VIDEO` | `video` | `87074004-5895-4963-A536-91A8D163149E` | episode media; volume `0` |
| `SCREEN_EFFECT` | `effect` | `D08A03AF-328A-4bc7-B0BC-27FF6DFFDA1E` | full episode duration |
| `SCREEN_WHITE` | `video` | `D434E862-E960-4c18-BE6A-E7778F98657C` | full episode duration |
| `STATE_EFFECT_3` | `text` | `B8E30AA7-4DAA-40df-9E66-855F344DB87F` | `LASER_CUT` seed |
| `STATE_EFFECT_2` | `text` | `BD486150-9596-4e58-B0FD-EFC809EA956B` | `GLITCH_SHAKE` seed |
| `STATE_EFFECT_1` | `text` | `5DF23088-4DF6-4eb2-95B3-B5A40DD6EAB8` | `FLICKER_RAVE` seed |
| `A10_TEXT_WHITE` | `text` | `4FEF3E81-010E-417f-8BA6-EBCCF4C7133C` | primary speaker only |
| `A10_TEXT_YELLOW` | `text` | `9B6875F3-CC8B-46cd-A565-5C432A0ADFC9` | every other resolved speaker |
| `A9_TEXT` | `text` | `1C649FC9-0312-4d8d-A1EA-3093B9B8EB1B` | approved TTS caption |
| `T2` | `text` | `D44CF2E1-D024-417e-B972-DFF5A15231AE` | full episode duration |
| `T1` | `text` | `FBBECFF2-12F3-4291-BD22-43D1B7A68944` | full episode duration |
| `A9` | `audio` | `DD2665AE-9FF5-46b9-B863-8B17A9B0EABB` | muted seed retained when no TTS media placement exists |
| `A10` | `audio` | `ABF4EBDC-FE4B-42b6-B7C7-C1AF9E35097F` | muted seed retained when no source-audio placement exists |
| `A11_SFX` | `audio` | `A1E0292E-7BB5-46c1-93C8-74B49C4931DC` | three seeds: transition `1`, reversal `2`, wow `3`; volume `1` |
| `A12` | `audio` | `ABFBB04B-6CCF-45a6-B134-DBEFC749C31F` | approved BGM; full duration and volume `1` |

Situation captions are sequential placements at the approved target position and use exactly one approved effect lane per cue. Uncertain speakers are `A10_TEXT_UNASSIGNED` and are omitted; the compiler must not guess. The builder preserves seed styling and changes only allowlisted text/range/media fields.

### `shrt_white_base_v1` 12-track role map

This table is the human-readable projection of `shrt_white_base_v1_layout_contract_v1.json`. Track identity is anchored by the contract's root archive SHA-256, `track_id`, and `type`; the array index and role are supporting lookup clues. `UNDETERMINED` must not be treated as optional or required without the episode audio/content policy.

| index | track_id | type | 역할 | requirement | segment 규칙 | 참조 자산 |
|---:|---|---|---|---|---|---|
| 0 | `87074004-5895-4963-A536-91A8D163149E` | `video` | `VIDEO` | `REQUIRED` | 근본 1개; target start `0`, duration `550000` | `나의 사전 설정25##CC3DC1AC-43DD-4e50-A877-08F300BE9329`; 회차별 placeholder video material |
| 1 | `D08A03AF-328A-4bc7-B0BC-27FF6DFFDA1E` | `effect` | `SCREEN_EFFECT` | `REQUIRED` | 근본 1개; target start `0`, duration `3000000` | 미러링 effect `7399472757014007046` |
| 2 | `D434E862-E960-4c18-BE6A-E7778F98657C` | `video` | `SCREEN_WHITE` | `REQUIRED` | 근본 1개; target start `0`, duration `20850000` | `transparent_center_white_1080x1920.png` (`##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##/Resources/media/transparent_center_white_1080x1920.png`) |
| 3 | `5DF23088-4DF6-4eb2-95B3-B5A40DD6EAB8` | `text` | `STATE` | `UNDETERMINED` | 근본 1개; target start `5250000`, duration `3000000` | placeholder `(상황설명)` |
| 4 | `4FEF3E81-010E-417f-8BA6-EBCCF4C7133C` | `text` | `A10_TEXT` | `UNDETERMINED` | 근본 1개; target start `2600000`, duration `3000000` | placeholder `"화자발언"` |
| 5 | `1C649FC9-0312-4d8d-A1EA-3093B9B8EB1B` | `text` | `A9_TEXT` | `UNDETERMINED` | 근본 1개; target start `0`, duration `3000000` | placeholder `TTS` |
| 6 | `D44CF2E1-D024-417e-B972-DFF5A15231AE` | `text` | `T2` | `UNDETERMINED` | 근본 1개; target start `0`, duration `3000000` | placeholder `T2` |
| 7 | `FBBECFF2-12F3-4291-BD22-43D1B7A68944` | `text` | `T1` | `UNDETERMINED` | 근본 1개; target start `0`, duration `3000000` | placeholder `T1` |
| 8 | `3CFF23A4-974F-4071-926C-25668E59B759` | `audio` | `A9` | `UNDETERMINED` | 근본 1개; duration `716666` | 오디오 소재명 미채집; timing만 계약에 기록됨 |
| 9 | `40CF81E0-3E59-4900-966C-6514EEAA7D14` | `audio` | `A10` | `UNDETERMINED` | 근본 1개; start `2600000`, duration `750000` | 오디오 소재명 미채집; timing만 계약에 기록됨 |
| 10 | `20812C0B-5B18-44e8-A3E0-4837AD25408B` | `audio` | `A11` | `UNDETERMINED` | 근본 1개; start `5250000`, duration `3500000` | 오디오 소재명 미채집; timing만 계약에 기록됨 |
| 11 | `ABFBB04B-6CCF-45a6-B134-DBEFC749C31F` | `audio` | `A12` | `UNDETERMINED` | 근본 1개; duration `48133333` | 오디오 소재명 미채집; timing만 계약에 기록됨 |

The v1 role order remains identical to historical `ROLE_BY_TRACK` in `scripts/build_episode_capcut.py`: `VIDEO`, `SCREEN_EFFECT`, `SCREEN_WHITE`, `STATE`, `A10_TEXT`, `A9_TEXT`, `T2`, `T1`, `A9`, `A10`, `A11`, `A12`. Do not use that index map for v2 assembly.

## Production plan

Stage 05 compiles the approved human matrix into a machine plan. Every placement must contain enough information to execute without inference:

- logical `anchor`
- explicit `operation`
- `target_range_us`
- text or logical asset key
- video/source-audio `source_range_us` when applicable
- volume/mute/duck mode when applicable
- root profile

Use logical asset keys plus an asset manifest or episode-relative paths instead of machine-specific absolute paths.

Required operations include at least:

- `replace_text_preserve_style`
- `replace_media_and_range`
- `clone_template_segment`
- explicit omit/clear semantics for optional lanes

`PRODUCTION_PLAN_READY` means every required placement has an anchor, operation, target range, and required source/media binding; root profile is selected; and lane-specific gaps/overlaps are validated. It does not require every heavy post-build evidence receipt to exist first.

## CapCut document classification

A CapCut root archive can contain heterogeneous `draft_content.json` documents:

- root editable draft
- active timeline mirror
- subdrafts/compound clips with unrelated layouts

Never assume every document has the root track count. In the Windows `shrt white` root bundled at commit `cd41d74`, root and active timeline have 12 tracks, while five subdraft documents each have one unrelated track. Applying `len(tracks) < 12` to every document deterministically raises `PINNED_TRACK_LAYOUT_INVALID`.

Classify documents by contracted anchor presence:

- update a document only when it contains the contracted track/segment/material anchors
- require the root and active timeline to contain required anchors
- skip unrelated subdrafts safely
- if a subdraft contains a contracted anchor, update it and validate the mirror explicitly

Do not overwrite unrelated subdrafts with the root content; compound-clip subdrafts are not automatically mirrors.

## Style preservation

For text anchors, preserve the complete copied rich-text material and modify only allowlisted fields:

- rich text `text`
- each style range
- segment target timerange

Preserve font, size, position, color, stroke, background, animation, render/layer index, transform, and any CapCut-native objects unless the contract explicitly allows an override.

## Audio and optional lanes

Do not clear a lane unless the production plan explicitly omits it. If code clears A9, A11, or A12 template segments, it must repopulate them from approved placements before validation. A declared role in `ROLE_BY_TRACK` is not proof that the builder assembles that role.

## Transactional build

Use this order:

1. verify root fingerprint and production-plan schema
2. extract/clone the root into a unique staging directory
3. apply placements by contract anchors
4. generate new project/draft/timeline and required segment/material IDs
5. synchronize root, active timeline, and only relevant mirrors
6. run material-reference, duration, path, style-preservation, and ID-mirror checks
7. atomically promote staging to the final CapCut project path
8. on any failure, remove staging and leave the final path absent

Never copy to the final target before all validations pass. A failed build must not leave a folder that causes `LOCAL_CAPCUT_PROJECT_EXISTS` on retry.

Use one canonical workflow state path (`90_workflow/state.json`) and one coherent Stage 08→09 status transition. The builder and router must not write/read different state files or incompatible entry statuses.

## Diagnostics

Record monotonic elapsed time and the first error for:

- archive extraction
- source/media copy
- plan validation
- anchor resolution and placement
- ID synchronization
- mirror synchronization
- static validation
- post-build validation
- final promotion

There is no reason for a Shorts draft copy to silently run for 30 minutes. Stop on the first deterministic failure; do not hide it with repeated retries.

## Tests

Before changing the builder, add a failing fixture test that uses the bundled root archive. Minimum coverage:

- actual root anchor extraction
- track reordering does not affect contract-based execution
- one-track unrelated subdrafts are skipped, not rejected
- T1/T2 rich-text style remains identical except text/style ranges
- all required roles in the production plan are assembled (including A9/A11/A12)
- source root remains byte/hash unchanged
- failed staging leaves no final target
- full root/timeline/ID mirror validation

When repository tests scan for forbidden text tokens, restrict the scan to intended text extensions. Do not decode ZIP or other binary assets as text, because random bytes create false positives.

## Schema–executor parity

Do not publish operations in `production_plan.schema.json` that the executor rejects as unsupported. For every declared operation, keep a three-way parity test across:

1. JSON schema acceptance
2. executor implementation
3. actual root-fixture readback

If only T1/T2 `replace_text_preserve_style` is implemented, label the result as a T1/T2 pilot. Do not claim the full production-plan integration until VIDEO, A9/A9_TEXT, A10/A10_TEXT, STATE, A11, and A12 placements have fixture tests and readback evidence. A direct defect fix (for example, skipping unrelated one-track subdrafts) is distinct from completion of the larger architecture.

## Cross-machine implementation handoff

When implementation or Windows visual verification will continue on another PC, provide one checksum-verifiable handoff ZIP containing:

- `README_START_HERE.md`
- exact GitHub URL, base commit, branch, and target skill path
- work order with in-scope and forbidden skill paths
- root contract, production plan, receipt, and readback
- actual pilot project ZIP
- complete patch including untracked new files
- file-level manifest with SHA-256
- outer ZIP SHA-256

State whether commit, push, runtime installation, and Windows CapCut visual verification were actually performed. Do not use `git diff` alone for the handoff patch because untracked new files are omitted; append `git diff --no-index /dev/null <new-file>` for each untracked file or stage them explicitly before generating the patch. Never use `git add .` in a dirty multi-skill repository.
