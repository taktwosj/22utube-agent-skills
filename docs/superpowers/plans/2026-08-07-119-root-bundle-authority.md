# 119 Root Bundle Authority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make one verified 119 root bundle the only machine-readable authority for root discovery, episode building, and future immutable root promotion, while preserving the existing v5 ZIP and manifest byte-for-byte.

**Architecture:** Place one deep module at the root-discovery seam: an active pointer selects a versioned contract, and that contract binds the archive, manifest, layout contract, evidence, lineage, and activation policy by workspace-relative path and SHA-256. Resolver, builder, and promoter all cross that same interface; the builder cannot accept a caller-supplied archive/hash pair, and promotion prepares an immutable candidate before a separate atomic activation step.

**Tech Stack:** Python 3 standard library (`argparse`, `dataclasses`, `hashlib`, `json`, `pathlib`, `tempfile`, `zipfile`), JSON contracts, `unittest`, PowerShell verification commands.

## Global Constraints

- Work only in `C:\Users\arajun\AppData\Local\Temp\agent-skills-119-optimize-20260807` and the explicitly named workspace bundle directory `C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\templates\capcut\jungchilong`.
- Preserve all existing uncommitted 119 changes; do not revert or overwrite `SKILL.md`, `build_politics_card_project.py`, `capture_politics_relink_readback.py`, or its new tests.
- The existing v5 ZIP `jungchilong_v5_chapter_image_lower2_CAPCUT_20260803.zip` and manifest `template_manifest_v5_chapter_image_lower2.json` are immutable and must retain their current bytes.
- The v5 archive SHA-256 remains `5D6241ED9816DD6F4123446DF35D54DF51318E61FEFF53CA13A96EE5E84A7F60`, manifest SHA-256 remains `59AFDAF7BE780205CA17FAB4AB5D6E33B0D3A794F81B575392F3E356287658B8`, archive root remains `P0_ROOT_jungchilong_v5_chapter_image_lower2/`, ZIP file-entry count remains `43` with `0` directory entries, manifest file count remains `43`, and track count remains `9`.
- `root_profile=jungchilong_v5_chapter_image_lower2` and `base_layout_profile=jungchilong_base_v4_hook10_lower2` are different named concepts; never coerce them to one value.
- Record v5 `visual_gate=WAIT_USER_VISUAL_GATE` and `post_open_validation=WAIT_CAPCUT_OPEN_CLOSE` truthfully. These historical root-promotion evidence fields do not change the current active v5 identity and never satisfy or replace an episode's separate `VISUAL_GATE`.
- Do not import Shorts-only rules: no 15-track contract, WHITE/YELLOW speaker routing, STATE effects, A9/A10/A11/A12 roles, Stage 05, or Stage 09.
- Actual episode assembly, Terra fresh-agent loop, CapCut GUI, render, upload, runtime installation, commit, and push are out of scope.
- Every path stored in pointer, contract, layout, or evidence is relative to `WORKSPACE_ROOT`; local CapCut paths may appear only as historical observations inside legacy promotion evidence.
- Missing, malformed, or hash-mismatched authority evidence is fail-closed. Never turn missing evidence into `PASS_ROOT_CONTRACT`.
- Each deliverable has its own RED -> GREEN cycle and review gate. Stop on its named stop rule instead of widening scope.
- Commit step for every task: `NOT RUN by authority`. Push and runtime install: `NOT RUN by authority`.

## File Map

### Skill source worktree

- Create `skills/119-politics-longform-capcut/references/root-bundle-contract.md`: normative pointer, contract, layout, evidence, activation, and status semantics for a fresh worker.
- Create `skills/119-politics-longform-capcut/scripts/root_bundle.py`: deep root-bundle module; the one interface used by resolver, builder, and promoter.
- Modify `skills/119-politics-longform-capcut/scripts/resolve_politics_capcut_root.py`: thin CLI adapter over `root_bundle.resolve_active_root()`.
- Modify `skills/119-politics-longform-capcut/scripts/build_politics_card_project.py`: consume a resolved root and remove the archive/hash bypass.
- Modify `skills/119-politics-longform-capcut/scripts/promote_capcut_root.py`: split candidate preparation from activation and remove hard-coded v4 profile output.
- Modify `skills/119-politics-longform-capcut/SKILL.md`: route active pointer -> resolver -> builder and document immutable versioning and truthful gates.
- Create `skills/119-politics-longform-capcut/scripts/tests/test_root_bundle.py`: interface-level bundle resolution tests.
- Create `skills/119-politics-longform-capcut/scripts/tests/test_build_politics_card_project.py`: builder seam tests.
- Create `skills/119-politics-longform-capcut/scripts/tests/test_promote_capcut_root.py`: immutable candidate and atomic activation tests.
- Create `tests/test_politics_root_bundle_contract.py`: repository contract test for documentation, CLI surface, and workspace bundle artifacts.

### Workspace root bundle

- Create `00_asset_tools/templates/capcut/jungchilong/capcut_active_root_v1.json`: sole active pointer.
- Create `00_asset_tools/templates/capcut/jungchilong/contracts/capcut_root_contract_v5.json`: immutable v5 identity and lineage.
- Create `00_asset_tools/templates/capcut/jungchilong/layout_contracts/jungchilong_v5_layout_contract_v1.json`: explicit 9-track 119 layout.
- Create `00_asset_tools/templates/capcut/jungchilong/evidence/jungchilong_v5_promotion_evidence_v1.json`: static evidence plus truthful historical WAIT fields.
- Modify `00_asset_tools/templates/capcut/jungchilong/RESTORE_NOTES.md`: mark the v2 instructions as legacy and make the active pointer the current entry point.

---

### Task 1: Versioned v5 Root Bundle Authority

**Deliverable:** A fresh worker can start from one active pointer, distinguish v5 root identity from its v4-based layout profile, inspect the exact 9-track layout, and see the historical visual/post-open WAIT without mistaking it for episode visual approval.

**Files:**

- Create: `skills/119-politics-longform-capcut/references/root-bundle-contract.md`
- Create: `tests/test_politics_root_bundle_contract.py`
- Create: `C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\capcut_active_root_v1.json`
- Create: `C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\contracts\capcut_root_contract_v5.json`
- Create: `C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\layout_contracts\jungchilong_v5_layout_contract_v1.json`
- Create: `C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\evidence\jungchilong_v5_promotion_evidence_v1.json`
- Modify: `C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\RESTORE_NOTES.md`
- Read only: existing v5 ZIP, existing v5 manifest, and `promotion_reports/promotion_relinkprobev3_to_v5.json`

**Interfaces:**

- Consumes: immutable v5 ZIP/manifest and historical promotion report.
- Produces: pointer schema `politics-longform-capcut-active-root.v1`, contract schema `politics-longform-capcut-root-bundle.v1`, layout schema `politics-longform-capcut-layout.v1`, and evidence schema `politics-longform-capcut-root-evidence.v1`.
- Invariant: the pointer contains only `active_root_version`, `contract.relative_path`, `contract.sha256`, and `activation_basis`; all root detail lives behind the versioned contract.
- Invariant: `activation_basis.mode=LEGACY_V5_STATIC_LOCK` is allowed only for `active_root_version=v5`; future versions require evidence gates declared by their versioned contract.

- [ ] **Step 1: Capture immutable baseline hashes and write failing authority tests**

Record the current v5 ZIP and manifest hashes before adding any bundle file:

```powershell
$bundleRoot = 'C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\templates\capcut\jungchilong'
Get-FileHash -Algorithm SHA256 "$bundleRoot\jungchilong_v5_chapter_image_lower2_CAPCUT_20260803.zip"
Get-FileHash -Algorithm SHA256 "$bundleRoot\template_manifest_v5_chapter_image_lower2.json"
```

In `tests/test_politics_root_bundle_contract.py`, add these named tests. Each test loads real JSON and asserts the behavior encoded in its name; the layout test also compares every declared row with the immutable ZIP document:

```text
test_active_pointer_binds_versioned_contract_by_hash
test_v5_contract_binds_archive_manifest_layout_and_evidence_by_hash
test_v5_identity_distinguishes_root_and_base_layout_profiles
test_v5_layout_declares_exact_nine_track_roles_and_geometry
test_v5_evidence_preserves_static_pass_and_visual_post_open_wait
test_root_evidence_visual_wait_is_not_episode_visual_gate
test_restore_notes_routes_current_work_to_active_pointer_and_marks_v2_legacy
test_v5_archive_and_manifest_baseline_hashes_are_unchanged
```

The tests must load paths relative to `WORKSPACE_ROOT`, recompute every bound SHA-256, open the ZIP read-only, verify the single archive root and 43-file inventory against the immutable manifest's 43 files, assert `0` ZIP directory entries and exact inventory equality, and inspect the root `draft_content.json` to verify the track IDs, types, indexes, selectors, timing, and geometry declared by the layout contract.

- [ ] **Step 2: Run the Task 1 tests and verify RED**

Run:

```powershell
python -m unittest tests.test_politics_root_bundle_contract -v
```

Expected: FAIL because `capcut_active_root_v1.json`, the versioned v5 contract, layout contract, evidence, and current restore routing do not yet exist. If the failure is an archive or manifest baseline hash mismatch, stop `WAIT_V5_IMMUTABILITY_BREACH`; do not recreate or modify either immutable file.

- [ ] **Step 3: Write the normative bundle reference**

In `references/root-bundle-contract.md`, define the only valid discovery sequence:

```text
WORKSPACE_ROOT
-> 00_asset_tools/templates/capcut/jungchilong/capcut_active_root_v1.json
-> versioned contract selected by active pointer and verified by contract SHA-256
-> archive + manifest + layout contract + evidence, each verified by its bound SHA-256
-> resolved root object
```

Define these status meanings exactly:

```text
PASS_ROOT_CONTRACT         bundle identity and declared activation basis verified
WAIT_ROOT_BUNDLE_*         required authority artifact or declared evidence missing
FAIL_ROOT_BUNDLE_*         schema, relation, inventory, or hash mismatch
WAIT_USER_VISUAL_GATE      historical v5 root visual evidence not completed
WAIT_CAPCUT_OPEN_CLOSE     historical v5 root post-open evidence not completed
VISUAL_GATE                episode-only user visual gate; never inherited from root evidence
```

Document that handoff text is continuity context, never root authority; v5 artifacts are immutable; a new root must use v6 or later; and Shorts-only tracks/effects/audio routing are forbidden in 119.

- [ ] **Step 4: Create the exact v5 layout contract from the immutable archive**

The layout contract must declare canvas `1920x1080`, duration `180000000`, content start `10000000`, track count `9`, and these immutable tracks:

```text
0 CFA8AA4D-4183-4B2B-90DF-EAD865D78FA7 video   ROOT_INTRO_BACKGROUND
1 B85D9009-6BE0-428A-8979-230A57D08967 video   PRIMARY_VIDEO_SLOT
2 C917C24A-730B-4BEA-801C-385B44D194F2 sticker LOWER_RAIL
3 5A7C7C19-F89A-41F1-B77C-95CAAA6F7ECD sticker UPPER_RAIL
4 3A2EF03A-79F8-4429-9C76-47790D7BA74D text    CTA
5 A55954D1-1E93-4309-8367-383E59C528B6 text    CHAPTER_HOOK_SEED_AND_LOWER_SLOT
6 BAD824D4-EBBB-4FDD-A572-F58458B2AF2F text    INTRO_HOOK
7 77215B57-6407-4628-9D9A-8019C9502585 text    CHAPTER_TITLE
8 64BBB006-B1B7-4C11-9826-E08A7E26F3E3 text    SOURCE_AND_DATE
```

For every role, store `track_index`, `track_id`, `track_type`, material selector, exact seed target range, and exact `clip.scale`, `clip.rotation`, `clip.transform`, and `clip.alpha` read from the archive. Store `__INTRO_HOOK_LINE_1__\n__INTRO_HOOK_LINE_2__`, `__LOWER_LINE_1__\n__LOWER_LINE_2__`, `__CHAPTER__`, `출처 __SOURCE__\n__DATE__`, and the CTA prefix `구독은 ` as selectors. Represent track 5's chapter-hook seed and lower-slot seed as two declared roles on one physical track; do not invent a tenth track.

- [ ] **Step 5: Create v5 evidence, versioned contract, and active pointer in hash order**

Create evidence first. It must bind the existing archive and manifest, cite `promotion_reports/promotion_relinkprobev3_to_v5.json`, set `static_gate=PASS_ROOT_PROMOTION_STATIC`, `visual_gate=WAIT_USER_VISUAL_GATE`, `post_open_validation=WAIT_CAPCUT_OPEN_CLOSE`, and set `episode_visual_gate_inherited=false`. It must describe `source_candidate=PL_20260802_relink_probe_3m_v3` without converting its local source path into portable authority.

After layout and evidence are final, compute their SHA-256 values and the existing manifest SHA-256. Create `contracts/capcut_root_contract_v5.json` with:

```text
schema=politics-longform-capcut-root-bundle.v1
root_version=v5
root_profile=jungchilong_v5_chapter_image_lower2
base_layout_profile=jungchilong_base_v4_hook10_lower2
immutable=true
parent_root_version=v4
source_candidate=PL_20260802_relink_probe_3m_v3
archive.relative_path + sha256 + archive_root + file_count
manifest.relative_path + sha256 + required_status
layout_contract.relative_path + sha256 + required_schema
promotion_evidence.relative_path + sha256 + required_static_gate
activation_policy.mode=LEGACY_V5_STATIC_LOCK
activation_policy.allows_historical_visual_wait=true
activation_policy.allows_historical_post_open_wait=true
activation_policy.episode_visual_gate_inherited=false
```

Then compute the contract SHA-256 and create `capcut_active_root_v1.json` last with `active_root_version=v5`, the versioned contract path/hash, and `activation_basis.mode=LEGACY_V5_STATIC_LOCK`. Do not point the active pointer at legacy `capcut_root_contract_v1.json`.

- [ ] **Step 6: Correct `RESTORE_NOTES.md` without deleting legacy history**

Make its first status line `LEGACY V2 RESTORE REFERENCE — NOT ACTIVE ROOT`. Add a `Current work` section that starts at `capcut_active_root_v1.json`, requires resolver verification, identifies v5 as current, and states that the historical v2 ZIP is never selected for new work. Keep the v2 recovery facts in a clearly labeled legacy section.

- [ ] **Step 7: Run Task 1 GREEN checks and immutability check**

Run:

```powershell
python -m unittest tests.test_politics_root_bundle_contract -v
python -m json.tool 'C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\capcut_active_root_v1.json' > $null
Get-FileHash -Algorithm SHA256 'C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\jungchilong_v5_chapter_image_lower2_CAPCUT_20260803.zip'
Get-FileHash -Algorithm SHA256 'C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\template_manifest_v5_chapter_image_lower2.json'
```

Expected: all tests PASS; ZIP hash equals `5D6241ED9816DD6F4123446DF35D54DF51318E61FEFF53CA13A96EE5E84A7F60`; manifest hash equals the Step 1 baseline. The evidence still reports both historical WAIT values. Stop rule: any immutable hash drift or layout/archive mismatch is `WAIT_V5_IMMUTABILITY_BREACH`.

- [ ] **Step 8: Commit**

`NOT RUN by authority`.

---

### Task 2: Resolver-to-Builder Deep Seam

**Deliverable:** Resolver and builder share one small interface that returns a verified root; callers cannot bypass the active pointer with a hand-entered ZIP path or SHA.

**Files:**

- Create: `skills/119-politics-longform-capcut/scripts/root_bundle.py`
- Create: `skills/119-politics-longform-capcut/scripts/tests/test_root_bundle.py`
- Create: `skills/119-politics-longform-capcut/scripts/tests/test_build_politics_card_project.py`
- Modify: `skills/119-politics-longform-capcut/scripts/resolve_politics_capcut_root.py`
- Modify: `skills/119-politics-longform-capcut/scripts/build_politics_card_project.py`
- Modify: `skills/119-politics-longform-capcut/SKILL.md`

**Interfaces:**

- Produces `ResolvedRoot` with fields `root_version`, `root_profile`, `base_layout_profile`, `contract_path`, `contract_sha256`, `archive_path`, `archive_sha256`, `archive_root`, `manifest_path`, `manifest_sha256`, `layout_path`, `layout_sha256`, `evidence_path`, `evidence_sha256`, `activation_mode`, `root_visual_gate`, `root_post_open_validation`, and `episode_visual_gate_inherited`.
- Produces `resolve_active_root(workspace_root: Path, active_pointer_relative: Path = DEFAULT_ACTIVE_POINTER) -> ResolvedRoot`.
- The CLI resolver serializes `ResolvedRoot.to_report()` and prints `status=PASS_ROOT_CONTRACT` only after all relations, hashes, inventory, layout, lineage, and activation rules pass.
- The builder interface accepts `--workspace-root`; it must reject the removed `--root-archive` and `--root-sha256` options as unknown arguments.

- [ ] **Step 1: Write failing resolver interface tests**

In `scripts/tests/test_root_bundle.py`, construct complete temporary workspaces and implement these named tests through `resolve_active_root()`. Each rejection test asserts the exact error code listed after the block:

```text
test_resolves_active_v5_bundle_and_reports_historical_wait_without_episode_promotion
test_rejects_pointer_contract_hash_mismatch
test_rejects_missing_layout_or_evidence
test_rejects_manifest_layout_or_evidence_hash_mismatch
test_rejects_root_profile_base_layout_profile_relation_mismatch
test_rejects_archive_root_file_count_or_inventory_mismatch
test_rejects_non_relative_or_escaping_paths
test_allows_legacy_v5_static_lock_only_for_v5
test_future_activation_requires_declared_visual_and_post_open_pass
```

Use a real temporary ZIP and real SHA-256 values. Assert exception codes exactly, including `FAIL_ROOT_BUNDLE_CONTRACT_HASH`, `WAIT_ROOT_BUNDLE_LAYOUT_NOT_FOUND`, `FAIL_ROOT_BUNDLE_EVIDENCE_HASH`, `FAIL_ROOT_BUNDLE_PROFILE_RELATION`, `FAIL_ROOT_BUNDLE_INVENTORY`, and `FAIL_ROOT_BUNDLE_ACTIVATION_POLICY`.

- [ ] **Step 2: Write failing builder seam tests**

In `scripts/tests/test_build_politics_card_project.py`, patch only the local filesystem/CapCut-process adapters and implement these named assertions:

```text
test_builder_resolves_archive_only_from_workspace_active_pointer
test_builder_report_binds_contract_version_and_hash
test_builder_stops_before_extract_when_root_bundle_resolution_fails
test_builder_cli_rejects_root_archive_and_root_sha256_bypass
```

The build report must include a `root_bundle` object containing the resolved `root_version`, contract path/hash, archive path/hash, layout path/hash, evidence path/hash, and historical root WAIT fields. It must retain episode `VISUAL_GATE=WAIT_USER_VISUAL_GATE` as an independent top-level gate.

- [ ] **Step 3: Run the Task 2 tests and verify RED**

Run:

```powershell
python -m unittest discover -s skills/119-politics-longform-capcut/scripts/tests -p 'test_root_bundle.py' -v
python -m unittest discover -s skills/119-politics-longform-capcut/scripts/tests -p 'test_build_politics_card_project.py' -v
```

Expected: resolver tests fail because `root_bundle.py` does not exist; builder tests fail because the old bypass arguments are still required.

- [ ] **Step 4: Implement the deep root-bundle module**

Implement `ResolvedRoot`, `sha256_file()`, `load_json_object()`, `workspace_relative_path()`, `validate_archive_inventory()`, `validate_layout_against_archive()`, `validate_activation_policy()`, and `resolve_active_root()` in `root_bundle.py`. Keep JSON parsing, path containment, hash verification, relationship validation, inventory validation, and activation policy inside this module; callers learn only `resolve_active_root()` and `ResolvedRoot`.

For v5, require `LEGACY_V5_STATIC_LOCK`, static evidence PASS, explicit historical WAIT values, and `episode_visual_gate_inherited=false`. For v6+, require the versioned contract's activation policy and do not silently grant the v5 exception. Return the WAIT fields in the report; never rewrite them to PASS.

- [ ] **Step 5: Make resolver a thin CLI adapter**

Replace direct contract/archive/manifest logic in `resolve_politics_capcut_root.py` with one call to `resolve_active_root(args.workspace_root)`. Remove `--contract-relative-path`; retain only `--workspace-root`. Emit the full resolved report as UTF-8 JSON and preserve nonzero exit `2` on any `RuntimeError`.

- [ ] **Step 6: Route builder through the same seam**

In `build_politics_card_project.py`, replace:

```text
--root-archive <path>
--root-sha256 <value>
```

with:

```text
--workspace-root <path>
```

Call `resolve_active_root()` immediately after `require_capcut_closed()` and before cards parsing, media copying, extraction, or target mutation. Use only `resolved.archive_path` and `resolved.archive_sha256`. Add the complete `resolved.to_report()` payload under `root_bundle` in the build report.

- [ ] **Step 7: Update the skill contract and exact commands**

In `SKILL.md`, remove the duplicate hard-coded archive path/SHA from the execution command. State:

```text
active pointer -> PASS_ROOT_CONTRACT resolver -> builder --workspace-root
```

State that handoff data, an old contract path, and direct archive/hash arguments cannot select a root. Preserve existing Stage 2, media, static/readback, visual, render, and upload gates unchanged. Explicitly separate `root_bundle.root_visual_gate` from the episode `VISUAL_GATE`.

- [ ] **Step 8: Run Task 2 GREEN and routing checks**

Run:

```powershell
python -m unittest discover -s skills/119-politics-longform-capcut/scripts/tests -p 'test_root_bundle.py' -v
python -m unittest discover -s skills/119-politics-longform-capcut/scripts/tests -p 'test_build_politics_card_project.py' -v
python skills/119-politics-longform-capcut/scripts/resolve_politics_capcut_root.py --workspace-root 'C:\Users\arajun\OneDrive\22utube\22factory_20260628'
python -m unittest tests.test_politics_root_bundle_contract tests.test_politics_lane_routing tests.test_skill_router_contracts -v
python -m py_compile skills/119-politics-longform-capcut/scripts/root_bundle.py skills/119-politics-longform-capcut/scripts/resolve_politics_capcut_root.py skills/119-politics-longform-capcut/scripts/build_politics_card_project.py
```

Expected: all targeted tests PASS; live resolver prints `PASS_ROOT_CONTRACT`, `root_version=v5`, both distinct profile names, and historical visual/post-open WAIT. Stop rule: if resolver cannot prove the complete active bundle, stop `WAIT_ROOT_BUNDLE_NOT_VERIFIED`; do not restore direct builder arguments.

- [ ] **Step 9: Commit**

`NOT RUN by authority`.

---

### Task 3: Immutable Versioned Promotion and Contract Enforcement

**Deliverable:** Future roots are prepared as new immutable version bundles, reviewed through explicit gates, and activated only by an atomic final pointer update; v5 cannot be overwritten.

**Files:**

- Create: `skills/119-politics-longform-capcut/scripts/tests/test_promote_capcut_root.py`
- Modify: `skills/119-politics-longform-capcut/scripts/promote_capcut_root.py`
- Modify: `skills/119-politics-longform-capcut/scripts/root_bundle.py`
- Modify: `skills/119-politics-longform-capcut/references/root-bundle-contract.md`
- Modify: `skills/119-politics-longform-capcut/SKILL.md`
- Modify: `tests/test_politics_root_bundle_contract.py`

**Interfaces:**

- `prepare_candidate(workspace_root: Path, source_root: Path, capcut_root: Path, root_version: str, root_profile: str, base_layout_profile: str, parent_contract_relative_path: Path, ffmpeg: str, content_start_sec: float) -> CandidateBundle`: creates a new archive, manifest, layout, evidence, and versioned contract without changing `capcut_active_root_v1.json`.
- `activate_candidate(workspace_root: Path, contract_relative_path: Path) -> ResolvedRoot`: verifies the complete candidate, requires its declared activation gates, rejects an existing version or downgrade, and atomically replaces the pointer last.
- CLI commands are `promote_capcut_root.py prepare --workspace-root <workspace> --source-root <draft> --capcut-root <capcut-root> --root-version v6 --root-profile <profile> --base-layout-profile <profile> --parent-contract-relative-path <path> --ffmpeg <ffmpeg>` and `promote_capcut_root.py activate --workspace-root <workspace> --contract-relative-path <path>`.
- Existing v5 bundle files are read-only inputs. New visual designs begin at `root_version=v6`.

- [ ] **Step 1: Write failing promotion immutability tests**

In `scripts/tests/test_promote_capcut_root.py`, add real temporary workspace/draft fixtures and implement these named tests. Each test asserts the pointer bytes before and after the operation as applicable:

```text
test_prepare_requires_version_profile_base_layout_and_parent_contract
test_prepare_rejects_v5_and_any_existing_bundle_target
test_prepare_writes_candidate_bundle_without_changing_active_pointer
test_prepare_manifest_uses_requested_root_and_base_layout_profiles
test_prepare_records_static_pass_but_visual_and_post_open_wait
test_activate_rejects_visual_or_post_open_wait_for_v6
test_activate_rejects_contract_or_artifact_hash_drift
test_activate_rejects_non_monotonic_version_or_wrong_parent
test_activate_updates_active_pointer_last_and_atomically
test_activation_failure_leaves_original_pointer_bytes_unchanged
```

Patch the expensive ffmpeg and CapCut registration adapters, but use real temp files, ZIPs, JSON, and hashes for bundle behavior. Assert that a prepared v6 candidate remains inactive with `visual_gate=WAIT_USER_VISUAL_GATE` and `post_open_validation=WAIT_CAPCUT_OPEN_CLOSE`.

- [ ] **Step 2: Run the Task 3 tests and verify RED**

Run:

```powershell
python -m unittest discover -s skills/119-politics-longform-capcut/scripts/tests -p 'test_promote_capcut_root.py' -v
```

Expected: FAIL because promotion currently has one phase, accepts caller-chosen output paths, hard-codes `jungchilong_base_v4_hook10_lower2`, publishes archive/manifest during static promotion, and has no atomic active pointer update.

- [ ] **Step 3: Split candidate preparation from activation**

Refactor `promote_capcut_root.py` so `prepare` requires:

```text
--workspace-root
--source-root
--capcut-root
--root-version v6-or-later
--root-profile
--base-layout-profile
--parent-contract-relative-path
--ffmpeg
--content-start-sec
```

Derive all output names under the workspace bundle directory from `root_version` and `root_profile`; do not accept arbitrary archive/manifest/evidence/contract output paths. Write each artifact via a temporary sibling and `os.replace`. Refuse `v5`, any version not greater than the active version, any existing destination, and any parent not equal to the active versioned contract. Remove the hard-coded v4 profile and write both requested profile concepts explicitly.

Preparation may emit `PASS_ROOT_PROMOTION_STATIC`, but must leave root visual and post-open gates at WAIT and must not touch the active pointer. Its success message is `CANDIDATE_ROOT_BUNDLE_PREPARED`, never `PASS_ROOT_CONTRACT`, `ACTIVE`, or `FINAL`.

- [ ] **Step 4: Implement activation as a separate final operation**

The `activate` command must resolve and verify the candidate contract directly through a `resolve_candidate_root()` internal seam, require `static_gate=PASS_ROOT_PROMOTION_STATIC`, `visual_gate=PASS_USER_VISUAL_GATE`, and `post_open_validation=PASS_CAPCUT_OPEN_CLOSE` for v6+, confirm parent version equals the current active version, then write a complete new pointer to a temporary sibling and call `os.replace` as the final filesystem operation.

If any check or replacement fails, keep the original pointer bytes unchanged and return nonzero. Do not mutate or delete the candidate; it remains available for evidence repair. Never apply the v5 `LEGACY_V5_STATIC_LOCK` exception to v6+.

- [ ] **Step 5: Extend docs and SKILL promotion contract**

Document this exact state flow in both `root-bundle-contract.md` and `SKILL.md`:

```text
staging copy
-> prepare candidate bundle
-> PASS_ROOT_PROMOTION_STATIC + visual WAIT + post-open WAIT
-> user visual approval and CapCut open/save/close evidence
-> activate candidate
-> atomic active pointer update
-> immutable active version
```

State that editing v5 is forbidden, a new root starts at v6, candidate static PASS does not make it active, and neither root visual evidence nor active identity grants an episode `VISUAL_GATE`.

- [ ] **Step 6: Run Task 3 GREEN and full scoped regression**

Run:

```powershell
python -m unittest discover -s skills/119-politics-longform-capcut/scripts/tests -p 'test_promote_capcut_root.py' -v
python -m unittest discover -s skills/119-politics-longform-capcut/scripts/tests -p 'test_*.py' -v
python -m unittest tests.test_politics_root_bundle_contract tests.test_politics_clean_assembly_harness_contract tests.test_politics_lane_routing tests.test_skill_router_contracts -v
python -m py_compile skills/119-politics-longform-capcut/scripts/root_bundle.py skills/119-politics-longform-capcut/scripts/resolve_politics_capcut_root.py skills/119-politics-longform-capcut/scripts/build_politics_card_project.py skills/119-politics-longform-capcut/scripts/promote_capcut_root.py
python 'C:\Users\arajun\.codex\skills\.system\skill-creator\scripts\quick_validate.py' skills/119-politics-longform-capcut
git diff --check
```

Expected: targeted 119 and routing tests PASS; existing baseline failures outside this plan remain explicitly reported rather than hidden. Recheck the v5 ZIP and manifest against Task 1 baselines. Stop rule: if activation can occur while either v6 visual or post-open evidence is WAIT, if pointer bytes change on a failed activation, or if v5 bytes drift, stop `FAIL_ROOT_PROMOTION_IMMUTABILITY`.

- [ ] **Step 7: Final scope report**

Report exactly:

```text
ROOT_BUNDLE_AUTHORITY: PASS|FAIL|WAIT
RESOLVER_BUILD_SEAM: PASS|FAIL|WAIT
PROMOTION_IMMUTABILITY: PASS|FAIL|WAIT
V5_ZIP_IMMUTABLE: PASS|FAIL
V5_MANIFEST_IMMUTABLE: PASS|FAIL
ROOT_VISUAL_EVIDENCE: WAIT_USER_VISUAL_GATE
ROOT_POST_OPEN_EVIDENCE: WAIT_CAPCUT_OPEN_CLOSE
EPISODE_VISUAL_GATE: NOT_RUN
ACTUAL_EPISODE: NOT_RUN
TERRA_FRESH_AGENT_LOOP: NOT_RUN
COMMIT: NOT RUN
PUSH: NOT RUN
RUNTIME_INSTALL: NOT RUN
```

- [ ] **Step 8: Commit**

`NOT RUN by authority`.

## Plan Self-Review

- Spec coverage: all audit findings map to one of the three deliverables; Shorts-only rules and later episode/Terra work are explicitly excluded.
- Inventory evidence: read-only evidence shows ZIP SHA-256 `5D6241ED9816DD6F4123446DF35D54DF51318E61FEFF53CA13A96EE5E84A7F60`, manifest SHA-256 `59AFDAF7BE780205CA17FAB4AB5D6E33B0D3A794F81B575392F3E356287658B8`, `43` ZIP file entries, `0` ZIP directory entries, `43` manifest files, and exact ZIP/manifest inventory equality.
- Seam check: resolver, builder, and promoter share `resolve_active_root()`/`ResolvedRoot`; no parallel archive/hash interface remains.
- Truthful-state check: current v5 identity may resolve through its explicit legacy activation basis while historical root visual/post-open fields remain WAIT; episode `VISUAL_GATE` remains independent and NOT RUN in this plan.
- Immutability check: v5 ZIP/manifest are read-only, new root work is v6+, and pointer mutation is the last atomic activation operation.
- Authority check: commit, push, runtime install, actual episode, CapCut GUI, render, upload, and Terra loop are all `NOT RUN by authority`.

## Execution Handoff

Use subagent-driven execution with one fresh implementation worker and one independent review worker per deliverable. Do not start Deliverable 2 until Deliverable 1 GREEN evidence is reviewed; do not start Deliverable 3 until Deliverable 2 GREEN evidence is reviewed. Stop after Deliverable 3's scoped verification and final status report.
