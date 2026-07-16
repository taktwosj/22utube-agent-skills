# Politics Source Caption Track Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an editable, small source-speech caption track to the politics-longform design and assembly contract.

**Architecture:** Store one shared `source_caption_track` policy object in the episode draft blueprint and draft timeline. Teach the canonical `111-politics-longform` skill to carry that role into Stage 2 after speech lock, while preserving the external-review immutable payload.

**Tech Stack:** Markdown, JSON, Python unittest, politics-longform Stage 1 validator.

## Global Constraints

- Canvas is `1920x1080`.
- Caption role is `source_caption` with editable CapCut text.
- Caption size is absolute CapCut size `8.0`, matching the approved lower lane.
- Caption timing follows speech cues after speech boundary lock, not commentary intervals.
- Maximum two lines; white fill and black stroke.
- Burned-in duplicates are cropped or masked; otherwise status is `NEEDS_VISUAL_REVIEW`.
- Stage 1 does not create CapCut, speech locks, locked clips, renders, or upload-ready claims.

---

### Task 1: Add a failing embedded-contract test

**Files:**
- Modify: `{AGENT_SKILLS_ROOT}/tests/test_politics_longform_embedded_contract.py`

**Interfaces:**
- Consumes: canonical skill text loaded by the existing test fixture.
- Produces: `test_skill_requires_editable_small_source_caption_track`.

- [ ] Add assertions for `source_caption`, `editability=editable`, absolute size
  `8.0`, one-line 20-character cues, `speech boundary lock`, and
  `NEEDS_VISUAL_REVIEW`.
- [ ] Run `py -3 -m unittest tests.test_politics_longform_embedded_contract.PoliticsLongformEmbeddedContractTests.test_skill_requires_editable_small_source_caption_track -v`.
- [ ] Confirm it fails because the current skill lacks the source-caption contract.

### Task 2: Update the canonical skill and runtime copy

**Files:**
- Modify: `{AGENT_SKILLS_ROOT}/skills/111-politics-longform/SKILL.md`
- Synchronize: `{CODEX_HOME}/skills/111-politics-longform/SKILL.md`

**Interfaces:**
- Consumes: the approved source-caption specification.
- Produces: Stage 1 screen-role, Stage 2 assembly, and CapCut validation rules.

- [ ] Add a concise `소형 원본자막 텍스트 트랙` contract to the canonical skill.
- [ ] Add `source_caption` to Stage 2 semantic roles and exact-text/timing validation.
- [ ] Copy the canonical skill to the runtime installation without changing unrelated skill files.
- [ ] Re-run the targeted embedded-contract test and confirm PASS.

### Task 3: Update the current episode design

**Files:**
- Modify: `{EPISODE_ROOT}/10_analysis/design_blueprint_draft.json`
- Modify: `{EPISODE_ROOT}/10_analysis/timeline_design_draft.json`
- Modify: `{EPISODE_ROOT}/10_analysis/design_blueprint_draft.md`

**Interfaces:**
- Consumes: the approved `source_caption_track` JSON object.
- Produces: two identical JSON policy objects plus a human-readable screen-role section.

- [ ] Insert the exact policy object after `transcript_policy` in both JSON files.
- [ ] Document placement, size, timing, style, and burned-in handling in the Markdown blueprint.
- [ ] Verify the two JSON objects are deeply equal and all JSON parses.
- [ ] Confirm the external sent and returned packet hashes remain unchanged.

### Task 4: Run fresh gates

**Files:**
- Update by validator: `{EPISODE_ROOT}/90_reports/stage1_gate.json`
- Update by validator: `{EPISODE_ROOT}/90_reports/external_review_gate.json`

**Interfaces:**
- Consumes: the modified episode design and unchanged review packets.
- Produces: fresh Stage 1 and external-review evidence.

- [ ] Run the full embedded-contract unittest module.
- [ ] Run `politics_longform_pipeline.py validate-stage1` with the local media root.
- [ ] Run `politics_longform_pipeline.py validate-external`.
- [ ] Confirm no CapCut, speech-lock, locked-clip, render, or upload-ready artifact was created.
