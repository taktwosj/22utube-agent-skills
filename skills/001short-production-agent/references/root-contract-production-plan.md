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
- logical anchor key (`VIDEO`, `T1`, `T2`, `A9`, `A10`, `STATE`, `A11`, `A12_RESERVED_EMPTY`, screen lanes)
- template `track_id`, `segment_id`, and `material_id`
- allowed replacement fields
- preserved style fields

Runtime code must resolve anchors through the contract. Never use `tracks[n]` for episode assembly. A one-time extractor may receive a reviewed role order for a pinned root, but the resulting contract must contain the actual IDs and root fingerprint.

Do not hand-author CapCut IDs in an episode plan. Generate the contract from the root, review it once, then lock it.

Each root project gets its own contract. Never borrow or fall back to anchors from another root profile.

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

**Legacy v1 12-track note:** in the Windows `shrt white` root bundled at commit `cd41d74`, root and active timeline had 12 tracks, while five subdraft documents each had one unrelated track. That layout is historical evidence only, not the current production contract. The current `shrt_white_base_v3_15` root has 15 physical tracks; `shrt_white_base_v2_15` remains valid only for episodes without `SOURCE_CREDIT`. Unrelated subdrafts still must be classified by contracted anchor presence instead of a global track-count rule.

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

Do not clear A9 or A11 unless the production plan explicitly omits that lane. If code clears an approved A9 or A11 template segment, it must repopulate that lane from approved placements before validation. `A12_RESERVED_EMPTY` is different: it is a reserved physical lane, never a BGM or placement target, and validation must reject every A12 segment, material, or production-plan placement. A declared role in `ROLE_BY_TRACK` is not proof that the builder assembles that role.

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
- all required roles in the production plan are assembled, including approved A9 and A11 placements
- `A12_RESERVED_EMPTY` has zero placements, segments, and materials
- source root remains byte/hash unchanged
- failed staging leaves no final target
- full root/timeline/ID mirror validation

When repository tests scan for forbidden text tokens, restrict the scan to intended text extensions. Do not decode ZIP or other binary assets as text, because random bytes create false positives.

## Schema–executor parity

Do not publish operations in `production_plan.schema.json` that the executor rejects as unsupported. For every declared operation, keep a three-way parity test across:

1. JSON schema acceptance
2. executor implementation
3. actual root-fixture readback

If only T1/T2 `replace_text_preserve_style` is implemented, label the result as a T1/T2 pilot. Do not claim the full production-plan integration until VIDEO, A9/A9_TEXT, A10/A10_TEXT, STATE, and A11 placements plus the empty `A12_RESERVED_EMPTY` readback have fixture tests and evidence. A direct defect fix (for example, skipping unrelated one-track subdrafts) is distinct from completion of the larger architecture.

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
