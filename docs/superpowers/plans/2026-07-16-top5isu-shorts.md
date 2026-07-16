# top5isu Shorts Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a single `top5isu-shorts` entry skill with `top5` and `gunlimbo` profiles, plus a fail-closed `top5isu_v1` adapter in `000short-production-agent`.

**Architecture:** `top5isu-shorts` owns routing, style policy, and the build contract. `00-tikitaka` remains the Stage 1 script owner. `000short-production-agent` owns CapCut assembly and production gates through an explicit `top5isu_v1` adapter; its existing `shrt white` default remains unchanged for unrelated requests.

**Tech Stack:** Markdown skills, YAML UI metadata, JSON Schema, Python 3 validators, `unittest`.

## Global Constraints

- Do not modify `00-tikitaka` or `111-politics-longform`.
- Do not modify the OneDrive `top5isu` archive or manifest.
- Never fall back from `top5isu_v1` to `shrt white`.
- Treat CapCut UI `Y=-600` as JSON `clip.transform.y=-0.15625` for this 1080x1920 template.
- Normalize audio with `ffmpeg loudnorm` before import and require final-export remeasurement; do not assume CapCut `target_loudness` uses LUFS units.
- Keep package manifests relative and reject `.bak` or foreign user paths.

---

### Task 1: Routing and Static Skill Contract

**Files:**
- Create: `tests/test_top5isu_shorts_contract.py`
- Create: `skills/top5isu-shorts/SKILL.md`
- Create: `skills/top5isu-shorts/agents/openai.yaml`
- Modify: `manifests/skill-set.json`

**Interfaces:**
- Consumes: user intent tokens and Stage 1 handoff artifacts.
- Produces: `top5isu_build_contract_v1` and routing decisions.

- [ ] Write tests asserting trigger coverage, ownership boundaries, profile names, no-fallback rules, coordinate mapping, audio policy, and skill manifest registration.
- [ ] Run the focused test and confirm it fails because the skill does not exist.
- [ ] Add the minimal skill and registration files.
- [ ] Run the focused test and confirm it passes.

### Task 2: Profile References and Build Schema

**Files:**
- Create: `skills/top5isu-shorts/references/top5-profile.md`
- Create: `skills/top5isu-shorts/references/gunlimbo-profile.md`
- Create: `skills/top5isu-shorts/references/top5isu-template-contract.md`
- Create: `skills/top5isu-shorts/references/handoff-contract.md`
- Create: `skills/top5isu-shorts/schemas/top5isu-build-contract.schema.json`

**Interfaces:**
- Consumes: `style_profile=top5|gunlimbo`.
- Produces: schema-valid contract with immutable archive, template, track, coordinate, and audio policies.

- [ ] Extend the focused contract test with schema and reference assertions.
- [ ] Verify the new assertions fail.
- [ ] Add the four references and JSON Schema.
- [ ] Verify the focused test passes.

### Task 3: Contract and Package Validators

**Files:**
- Create: `skills/top5isu-shorts/scripts/validate_top5isu_contract.py`
- Create: `skills/top5isu-shorts/scripts/validate_top5isu_package.py`
- Create: `skills/top5isu-shorts/scripts/validate_top5isu_capcut_draft.py`
- Create: `tests/test_top5isu_validators.py`

**Interfaces:**
- Consumes: contract JSON, template manifest/archive, extracted or local draft.
- Produces: PASS JSON or fail-closed `GateFail` messages.

- [ ] Write unit tests for valid contracts, forbidden fallback, archive tampering, `.bak`, foreign paths, required tracks, image transforms, full-duration logo, sample-image residue, and profile audio policy.
- [ ] Verify tests fail because validators do not exist.
- [ ] Implement minimal validators.
- [ ] Verify validator tests pass.

### Task 4: Production Adapter

**Files:**
- Create: `skills/000short-production-agent/adapters/top5isu_v1.md`
- Create: `skills/000short-production-agent/scripts/validate_top5isu_track_mapping.py`
- Create: `tests/test_000short_top5isu_track_mapping.py`
- Modify: `skills/000short-production-agent/03_CAPCUT_LAYOUT_CONTRACT.md`
- Modify: `skills/000short-production-agent/SKILL.md`

**Interfaces:**
- Consumes: schema-valid `top5isu_build_contract_v1`.
- Produces: explicit `top5isu_v1` track mapping gate without changing the default `shrt white` path.

- [ ] Write tests for the five required tracks, explicit template evidence, no fallback, UI/JSON coordinate pair, and profile-specific audio lanes.
- [ ] Verify tests fail because the adapter is missing.
- [ ] Add the adapter, validator, and narrowly scoped routing references.
- [ ] Verify focused adapter tests and existing shrt-white tests pass together.

### Task 5: Verification and Selected Runtime Sync

**Files:**
- Sync only: `skills/top5isu-shorts`
- Sync only: changed files under `skills/000short-production-agent`

**Interfaces:**
- Consumes: validated Git-source files.
- Produces: matching Codex runtime copies.

- [ ] Run skill `quick_validate.py`.
- [ ] Run focused tests.
- [ ] Run the full unittest suite and compare against the recorded one-failure baseline.
- [ ] Copy only the two approved skill trees into `%USERPROFILE%\.codex\skills` without touching other runtime skills.
- [ ] Compare source/runtime relative file lists and SHA256 hashes.
- [ ] Report the existing unrelated baseline failure separately from new feature status.
