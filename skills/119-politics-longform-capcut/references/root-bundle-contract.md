# 119 Root Bundle Contract

> `LEGACY_V7_ROLLBACK_ONLY`: 이 계약과 `capcut_active_root_v1.json`은 기존 v7
> 번들의 검증·복구에만 사용한다. 새 119 회차의 현재 생산 근본은
> `V8_MANUAL_OVERLAY_65`이며 `clean-assembly-harness.md`와
> `build_politics_v8_project.py --root-project`가 선택한다.

## Authority discovery

기존 v7 회차를 명시적으로 복구할 때만 아래 discovery sequence를 사용한다:

```text
WORKSPACE_ROOT
-> 00_asset_tools/templates/capcut/jungchilong/capcut_active_root_v1.json
-> versioned contract selected by active pointer and verified by contract SHA-256
-> archive + manifest + layout contract + evidence, each verified by its bound SHA-256
-> resolved root object
```

The active pointer is the sole discovery entry point. A handoff path, old contract path, archive
name, or caller-supplied hash cannot select a root; handoff text is continuity context, never root authority.
Resolve every stored path relative to `WORKSPACE_ROOT`; reject absolute paths and paths that escape
it.

Archive JSON/TMP stores root-internal path fields under the portable
`C:/__CAPCUT_ROOT_BUNDLE__/` token and `draft_root_path` under
`C:/__CAPCUT_DRAFT_ROOT_BUNDLE__/`. Candidate preparation keeps the local CapCut project bound to
its real local draft path, writes only the archive copy with the tokens, and binds the manifest to
that archive copy. After verified extraction, the builder remaps the tokens and the verified legacy
archive-root name to the new local project and CapCut draft roots before validation.

## Status meanings

```text
PASS_ROOT_CONTRACT         bundle identity and declared activation basis verified
WAIT_ROOT_BUNDLE_*         required authority artifact or declared evidence missing
FAIL_ROOT_BUNDLE_*         schema, relation, inventory, or hash mismatch
WAIT_USER_VISUAL_GATE      historical v5 root visual evidence not completed
WAIT_CAPCUT_OPEN_CLOSE     historical v5 root post-open evidence not completed
VISUAL_GATE                episode-only user visual gate; never inherited from root evidence
```

The v5 legacy activation basis may keep both historical root evidence fields at `WAIT`. That
exception identifies the already selected v5 root; it does not approve an episode, a render, or an
upload. Never promote either historical root WAIT to PASS and never copy it into episode
`VISUAL_GATE`.

## Version and immutability

Verify the active pointer's contract hash before reading root detail. Then verify the archive,
manifest, layout contract, and promotion evidence against the paths, hashes, schemas, gates,
lineage, and inventory declared by the versioned contract. Any missing artifact is
`WAIT_ROOT_BUNDLE_*`; any malformed relation, inventory, or hash is `FAIL_ROOT_BUNDLE_*`.

The active v5 archive, manifest, layout contract, promotion evidence, and versioned contract are
immutable. Do not edit or overwrite them. A new root must use v6 or later and must satisfy the
evidence gates declared by its own versioned contract before activation.

## Candidate preparation and activation

Use this state flow exactly:

```text
staging copy
-> prepare candidate bundle
-> PASS_ROOT_PROMOTION_STATIC + visual WAIT + post-open WAIT
-> user visual approval and CapCut open/save/close evidence
-> activate candidate
-> atomic active pointer update
-> immutable active version
```

Run `promote_capcut_root.py prepare` with the workspace, staging source, local CapCut root,
v6-or-later version, root profile, base-layout profile, active parent contract, ffmpeg, and content
start. Preparation derives every candidate destination from both `root_version` and `root_profile`,
writes a new versioned bundle, and returns
`CANDIDATE_ROOT_BUNDLE_PREPARED`. It must not change `capcut_active_root_v1.json`.

After the evidence records exact `PASS_USER_VISUAL_GATE` and `PASS_CAPCUT_OPEN_CLOSE`, run
`promote_capcut_root.py activate` with the workspace and candidate contract relative path.
Activation revalidates the full candidate and active-parent lineage, then atomically replaces the
active pointer as its final successful filesystem operation. Any failed gate, drift, downgrade,
existing version, wrong parent, or pointer replacement leaves the original pointer bytes unchanged.
For every v6-or-later candidate, activation requires exact `PASS_ROOT_PROMOTION_STATIC` and exact
manifest `root_version`, `root_profile`, and `base_layout_profile` identity even when all changed
files and hashes are consistently rebound.

Editing or overwriting v5 is forbidden. Start every new visual root at v6 or later. Candidate static
PASS is not active identity. Root visual evidence and active root identity never grant an episode
`VISUAL_GATE`.

## 119-only layout boundary

The v5 layout has nine physical tracks. Track 5 contains both the chapter-hook seed and the lower
two-line-slot seed; this does not create a tenth track. Preserve the declared role selectors,
timing, and geometry exactly.

Shorts-only tracks, effects, and audio routing are forbidden in 119. Do not import a 15-track
layout, A9-A12 roles, WHITE/YELLOW speaker routing, STATE effects, or Shorts Stage 05/09 rules.
