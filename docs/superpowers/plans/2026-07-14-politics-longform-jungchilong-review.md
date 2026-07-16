# Politics Longform Jungchilong Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the politics-longform skill, factory policy, review workflow, generic CapCut builder, and validators around the verified `jungchilong` root.

**Architecture:** Keep human editorial review in one chronological Markdown packet with stable segment ids, while JSON artifacts remain the machine-readable authority. A generic Python contract module validates Stage 1, external review, approved design, preassembly locks, and postassembly evidence; a separate builder consumes only approved JSON and locked clips.

**Tech Stack:** Python 3 standard library, unittest, PowerShell, CapCut JSON, ffprobe/ffmpeg.

## Global Constraints

- Use `{WORKSPACE_ROOT}` and `%LOCALAPPDATA%`; never add user-home absolute paths.
- v3 root archive SHA-256 is `WAIT_V3_TEMPLATE_PROMOTION` until the promoted
  internal-intro archive passes restore validation.
- Political-longform canvas is `1920x1080`; thumbnail assets remain `1280x720`.
- Stage 1 never creates CapCut or locked clips.
- Stage 2 never assembles before approved design and locked-clip gates pass.
- Root/archive/local `jungchilong` are immutable; edit only a new episode clone.

---

### Task 1: Contract regression tests

**Files:**
- Modify: `tests/test_politics_longform_embedded_contract.py`
- Create: `{WORKSPACE_ROOT}/22factory_20260628/00_asset_tools/tools/politics_longform/test_politics_longform_pipeline.py`

**Interfaces:**
- Consumes: current skill and factory documents.
- Produces: failing assertions for root authority, Stage 1 artifacts, review gates, preassembly locks, canvas, audio, portability, and dynamic counts.

- [x] Add skill contract assertions for `jungchilong`, archive hash, `1920x1080`, review artifacts, approved timeline, audio policy, ownership, and YP007 legacy-only wording.
- [x] Add pipeline unit fixtures with two clips and three commentary segments.
- [x] Run the focused tests and confirm expected failures from missing contract/tool behavior.

### Task 2: Skill and factory policy alignment

**Files:**
- Modify: `skills/111-politics-longform/SKILL.md`
- Modify: `{WORKSPACE_ROOT}/22factory_20260628/AGENTS.md`
- Modify: `{WORKSPACE_ROOT}/22factory_20260628/docs/YOUTUBE_PRODUCTION_WORK_ORDER.md`

**Interfaces:**
- Consumes: design spec and Task 1 assertions.
- Produces: one consistent root/stage/audio/ownership contract.

- [x] Replace YP007 authority with the verified archive and local clone process.
- [x] Define Stage 1 source evidence, draft design, one-file external packet, and truthful status rules.
- [x] Define Stage 2 returned-review validation, approval invalidation, speech locks, locked clips, assembly, and final gates.
- [x] Run focused skill tests to confirm the document contract passes.

### Task 3: Generic review and gate validator

**Files:**
- Create: `{WORKSPACE_ROOT}/22factory_20260628/00_asset_tools/tools/politics_longform/politics_longform_pipeline.py`
- Test: `{WORKSPACE_ROOT}/22factory_20260628/00_asset_tools/tools/politics_longform/test_politics_longform_pipeline.py`

**Interfaces:**
- Produces: `render_review_packet(draft, output)`, `parse_review_packet(path)`, `validate_stage1(episode_dir)`, `validate_external_review(episode_dir)`, `validate_preassembly(episode_dir)`, and CLI subcommands.

- [x] Implement deterministic one-file packet rendering with stable segment markers.
- [x] Implement parsing and immutable transcript/timing/source comparison.
- [x] Implement source manifest/hash/probe, continuous timeline, decision, invalidation, lock, ownership, and audio evidence checks.
- [x] Run unit tests until all new validator tests pass.

### Task 4: Generic approved-design CapCut builder

**Files:**
- Create: `{WORKSPACE_ROOT}/22factory_20260628/00_asset_tools/tools/politics_longform/build_politics_longform_from_approved.py`
- Extend: `{WORKSPACE_ROOT}/22factory_20260628/00_asset_tools/tools/politics_longform/test_politics_longform_pipeline.py`
- Modify: `{WORKSPACE_ROOT}/22factory_20260628/00_asset_tools/tools/politics_longform/rebuild_20260714_jungchilong.py`
- Modify: `{WORKSPACE_ROOT}/22factory_20260628/00_asset_tools/tools/politics_longform/test_rebuild_20260714_jungchilong.py`

**Interfaces:**
- Consumes: approved design, locked EDL, locked labels, locked clip manifest, verified local base.
- Produces: local episode clone and `50_capcut_project` manifest/snapshots/restore notes/assembly blueprint.

- [x] Implement portable root resolution and template/archive checks.
- [x] Implement dynamic clip/text row assembly at 1920x1080 with embedded-audio requirements.
- [x] Make the July 14 builder explicitly legacy, portable, and 1920x1080; remove machine-dependent test media assumptions.
- [x] Run generic and legacy builder tests until green.

### Task 5: Runtime sync and full verification

**Files:**
- Sync managed runtimes through `scripts/install.ps1 -Target codex -Only 111-politics-longform` after source tests pass.

**Interfaces:**
- Consumes: verified Git skill source and factory tools.
- Produces: Codex runtime parity plus final evidence report.

- [x] Run `py -3 -m unittest discover -s tests -p "test_*.py" -v` in `%USERPROFILE%\agent-skills`.
- [x] Run all three politics tool test modules in the factory.
- [x] Run `scripts/verify.ps1 -Target repo`.
- [x] Install only `111-politics-longform` into Codex and verify source/runtime SHA parity.
- [x] Run a synthetic Stage 1 packet -> returned packet -> approved design -> preassembly validation scenario.
- [x] Report exact PASS/WAIT states, including `LOCAL_GUI_RESTORE=WAIT_USER_RESTORE` until a real GUI check occurs.

### Task 6: Independent adversarial hardening

**Files:**
- Modify: factory politics-longform pipeline, builder, tests, policy, and work order.
- Modify: `skills/111-politics-longform/SKILL.md` and its embedded contract test.

- [x] Anchor external review to the immutable Stage 1 sent-packet manifest.
- [x] Reject fake media by rerunning real ffprobe for sources and locked clips.
- [x] Reject status-only Stage 1 candidates and enforce cross-file continuity.
- [ ] Pin the promoted v3 archive root, generated file count, ZIP SHA, and intro
  SHA outside mutable manifest control; do not reuse the v2 37-file value.
- [x] Validate final semantic text and timing, not only counts and gaps.
- [x] Remove the public preassembly bypass and require strong machine-bound GUI evidence.
- [x] Reject media roots inside the factory even when environment hints are absent.
- [x] Make assembly transactional with project, registry, and report rollback.
- [ ] Re-run the current factory and repository suites after v3 promotion; old
  counts are historical evidence only.
