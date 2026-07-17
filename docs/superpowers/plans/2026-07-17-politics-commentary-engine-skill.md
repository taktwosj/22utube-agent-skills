# Politics Commentary Engine Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `111-politics-longform` produce an independently reasoned master political-commentary script before TTS, captions, lower two-line text, images, or CapCut assembly.

**Architecture:** Add one master-commentary contract to the Git-owned skill and protect it with repository contract tests. Keep the existing production pipeline, but change lower T1 from a primary writing surface into a derivative of a user-approved master script.

**Tech Stack:** Markdown skill contract, Python `unittest`, PowerShell runtime installer and verifier.

## Global Constraints

- Edit the current `22utube-agent-skills` repository as the Git source of truth; do not edit runtime copies directly.
- Preserve unrelated dirty files in `000short-production-agent`.
- Do not create images, TTS, subtitles, CapCut drafts, exports, or upload packages.
- Do not treat a numeric quality score as user approval.
- Keep facts, source claims, interpretation, counterargument, and judgment distinguishable.
- Derive TTS and lower commentary only from `commentary_master_script_approved.md`.

---

### Task 1: Add a failing commentary contract test

**Files:**
- Modify: `tests/test_politics_longform_embedded_contract.py`

**Interfaces:**
- Consumes: `skills/111-politics-longform/SKILL.md`
- Produces: contract assertions for master-script artifacts, reasoning order, approval gate, and lower-text derivation

- [ ] **Step 1: Write the failing test**

Add a test that requires:

```python
def test_commentary_master_script_precedes_tts_lower_text_and_capcut(self):
    for token in (
        "## 정치평론가 마스터 원고 계약",
        "commentary_master_script_draft.md",
        "commentary_fact_map.json",
        "commentary_quality_review.json",
        "commentary_master_script_approved.md",
        "DRAFT_USER_REVIEW",
        "WAIT_COMMENTARY_USER_REVIEW",
        "하단 두 줄에서 평론을 역산하지 않는다",
        "주장 -> 근거 -> 해석 -> 반론 -> 판단",
    ):
        self.assertIn(token, self.skill_text)
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest tests.test_politics_longform_embedded_contract.PoliticsLongformEmbeddedContractTests.test_commentary_master_script_precedes_tts_lower_text_and_capcut -v
```

Expected: `FAIL` because `## 정치평론가 마스터 원고 계약` is absent.

### Task 2: Add the master political-commentary contract

**Files:**
- Modify: `skills/111-politics-longform/SKILL.md`
- Modify: `skills/111-politics-longform/agents/openai.yaml`

**Interfaces:**
- Consumes: verified transcript/source claims and current-event fact checks
- Produces: `commentary_fact_map.json`, `commentary_master_script_draft.md`, `commentary_quality_review.json`, and user-approved `commentary_master_script_approved.md`

- [ ] **Step 1: Update skill discovery metadata**

Extend the description trigger to include political-commentary master scripts, commentator narration, and lower-commentary writing. Update `agents/openai.yaml` so the visible description names master commentary rather than only CapCut lower chapters.

- [ ] **Step 2: Add the positive writing recipe**

Add `## 정치평론가 마스터 원고 계약` before `## Workflow`. Require this exact reasoning order:

```text
주장 -> 근거 -> 해석 -> 반론 -> 판단
```

Define:

```text
source_claim: source speaker's attributable claim
verified_fact: independently checked current fact
interpretation: causal or institutional reading
counterargument: strongest plausible objection
judgment: conclusion that survives the objection
```

Require one governing thesis and 3-5 commentary blocks. Each block must provide a new distinction, causal explanation, or decision criterion rather than repeat the source.

- [ ] **Step 3: Add artifacts and approval gate**

Require:

```text
20_script/commentary_fact_map.json
20_script/commentary_master_script_draft.md
20_script/commentary_quality_review.json
20_script/commentary_master_script_approved.md
```

The draft status is `DRAFT_USER_REVIEW`. Before explicit user approval, stop with `WAIT_COMMENTARY_USER_REVIEW`. A quality score may make the draft reviewable but never approved.

- [ ] **Step 4: Convert lower T1 into a derivative**

Replace the current primary-writing instruction with:

```text
하단 두 줄에서 평론을 역산하지 않는다.
```

Require TTS, subtitle cues, image prompts, lower A/B commentary, and CapCut text to be segmented from the approved master script without changing its argument.

### Task 3: Verify, install, and re-verify

**Files:**
- Test: `tests/test_politics_longform_embedded_contract.py`
- Verify: `scripts/verify.ps1`
- Install: `scripts/install.ps1`

**Interfaces:**
- Consumes: updated Git source skill
- Produces: matching Codex, Claude, and Hermes runtime copies with managed markers

- [ ] **Step 1: Run targeted GREEN test**

Run:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest tests.test_politics_longform_embedded_contract -v
```

Expected: all tests in that module pass.

- [ ] **Step 2: Run repository verification**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Target repo
```

Expected: `VERIFY PASS`.

- [ ] **Step 3: Commit only commentary-engine files**

Commit only:

```text
skills/111-politics-longform/SKILL.md
skills/111-politics-longform/agents/openai.yaml
tests/test_politics_longform_embedded_contract.py
docs/superpowers/plans/2026-07-17-politics-commentary-engine-skill.md
```

Do not stage the existing dirty Shorts validator or its test.

- [ ] **Step 4: Install the one skill into all managed runtimes**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Target all -Only 111-politics-longform
```

Expected: `111-politics-longform` is synced to Codex, Claude, and Hermes with refreshed managed markers.

- [ ] **Step 5: Verify all runtime copies**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Target all
```

Expected: source and target hashes match for Codex, Claude, and Hermes and the verifier ends with `VERIFY PASS`.

## Self-Review

- Spec coverage: master reasoning, fact separation, counterargument, approval gate, and derivative caption rule are mapped to Tasks 1-2.
- Placeholder scan: no deferred implementation placeholders are present.
- Interface consistency: every runtime consumes the same Git-owned `111-politics-longform` folder.
