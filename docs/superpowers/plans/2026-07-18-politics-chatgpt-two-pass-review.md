# Politics ChatGPT Two-Pass Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed, same-conversation, two-pass ChatGPT master-commentary review gate to `111-politics-longform` while preserving the current `jungchilong_base_v3_intro15` production contract.

**Architecture:** Keep detailed review semantics in the existing reference contract, keep only routing and gate order in `SKILL.md`, and add a deterministic Python validator for artifact hashes, conversation identity, suggestion decisions, timeline order, and flow-audit status. Preserve the existing lower two-line `commentary_review_packet_*` pipeline as a separate gate.

**Tech Stack:** Markdown skill contracts, Python 3 standard library, `unittest`, PowerShell install and verification scripts, Git/GitHub.

## Global Constraints

- Git source of truth: `C:\Users\arajun\agent-skills`.
- Preserve all unrelated dirty files.
- Root profile: `jungchilong_base_v3_intro15`.
- Canvas: `1920x1080`.
- YP007: legacy visual reference only.
- Root ZIP: `{WORKSPACE_ROOT}\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\jungchilong_v3_intro15_CAPCUT_20260715.zip`.
- Master review and lower-commentary review remain separate.
- Round 2 uses the exact round-1 ChatGPT conversation ID.
- External output remains `PENDING_CODEX_REVIEW`.
- Explicit user approval remains required after the external-review gate.
- No production media, CapCut draft, TTS, image, export, or upload action is in scope.

---

### Task 1: Establish the v3 skill baseline

**Files:**
- Merge source: commit `491cb6b398ec5bd9d7e0e33675764afb744f6dde`
- Modify: `skills/111-politics-longform/SKILL.md`
- Modify: `skills/111-politics-longform/agents/openai.yaml`
- Test: `tests/test_politics_longform_embedded_contract.py`

**Interfaces:**
- Consumes: workspace `AGENTS.md` v3 template authority
- Produces: one Git-owned skill containing the master-commentary contract and v3 root markers

- [ ] **Step 1: Integrate the current v3 source contract**

Run:

```powershell
git merge --no-ff origin/codex/sync-local-skills-20260630
```

Confirm that the merged history contains commit
`491cb6b398ec5bd9d7e0e33675764afb744f6dde`. Resolve `SKILL.md` by using that
commit's v3 production contract as the baseline and then adding the
master-commentary review contract.

- [ ] **Step 2: Write failing v3 marker assertions**

Require these exact tokens:

```python
for token in (
    "target_profile: jungchilong_base_v3_intro15",
    "canvas: 1920x1080",
    "YP007, YP005, YM007 are legacy visual references only.",
    "jungchilong_v3_intro15_CAPCUT_20260715.zip",
    "content_start_sec=15.083333",
):
    self.assertIn(token, self.skill_text)
```

- [ ] **Step 3: Run the marker test and verify RED**

Run:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest tests.test_politics_longform_embedded_contract -v
```

Expected: PASS after the v3 source commit is merged. Stop if any marker is
missing; do not reconstruct the source contract from the older 1280x720 branch.

- [ ] **Step 4: Apply the minimal v3 contract**

Replace pre-v3 canvas and root descriptions with the exact v3 markers and make
YP007 reference-only. Keep `jungchilong` immutable and clone-only.

- [ ] **Step 5: Re-run the marker tests**

Expected: all v3 root tests pass.

### Task 2: Add failing two-pass contract tests

**Files:**
- Modify: `tests/test_politics_longform_chatgpt_project_contract.py`
- Modify: `tests/test_politics_longform_embedded_contract.py`

**Interfaces:**
- Consumes: design spec artifact names and status values
- Produces: RED tests for round separation, same-conversation continuity, and approval boundaries

- [ ] **Step 1: Add contract assertions**

Require:

```python
required = (
    "MASTER_COMMENTARY_REVIEW_GATE",
    "master_commentary_review",
    "round1_packet_sent.md",
    "round1_codex_decisions.json",
    "round2_packet_sent.md",
    "round2_receipt.json",
    "conversation_id",
    "round1_return_sha256",
    "flow_continuity_status",
    "PASS_RECOMMENDED",
    "REVISE_REQUIRED",
    "EVIDENCE_REQUIRED",
    "WAIT_CHATGPT_REVIEW_REPAIR",
)
```

Assert that `EVIDENCE_AUDIT` is assigned to round 2, and that existing
`commentary_review_packet_*` names remain identified as lower-commentary
artifacts.

- [ ] **Step 2: Run the tests and verify RED**

Run:

```powershell
python -m unittest tests.test_politics_longform_chatgpt_project_contract -v
```

Expected: failure for missing two-pass artifacts and continuity contract.

### Task 3: Implement the reference contract and skill routing

**Files:**
- Modify: `skills/111-politics-longform/SKILL.md`
- Modify: `skills/111-politics-longform/references/chatgpt_politics_longform_review_contract.md`
- Modify: `skills/111-politics-longform/references/chatgpt_project_router_instruction.md`

**Interfaces:**
- Consumes: round-1 draft packet, external return, Codex decisions, revised script/fact map/timeline
- Produces: unambiguous round-1 and round-2 ChatGPT instructions

- [ ] **Step 1: Split the external roles**

Set round 1 to `INDEPENDENT_REVIEW + REVISION_PROPOSAL`. Set round 2 to
`EVIDENCE_AUDIT + FLOW_CONTINUITY_AUDIT`.

- [ ] **Step 2: Define the canonical artifacts and hash chain**

Add the exact directory and file names from the design. Require full round-2
self-containment and same-conversation identity.

- [ ] **Step 3: Add the fail-closed workflow order to `SKILL.md`**

Keep only the routing, artifact names, stop codes, validator command, and user
approval boundary in `SKILL.md`; leave detailed response schemas in the
reference contract.

- [ ] **Step 4: Run contract tests and verify GREEN**

Expected: all ChatGPT project contract tests pass.

### Task 4: Add the deterministic two-pass validator

**Files:**
- Create: `skills/111-politics-longform/scripts/validate_chatgpt_two_pass_review.py`
- Create: `tests/test_politics_longform_chatgpt_two_pass_validator.py`

**Interfaces:**
- Consumes: `--review-dir PATH`
- Produces: JSON to stdout with `status`, `errors`, `conversation_id`, artifact hashes, suggestion counts, `round2_verdict`, and `flow_continuity_status`

- [ ] **Step 1: Write failing behavioral tests**

Create fixtures in temporary directories and assert failure for:

```text
missing round 2
conversation mismatch
parent return hash mismatch
decision coverage mismatch
PENDING_EVIDENCE
revised artifact hash mismatch
segment-order drift
REVISE_REQUIRED
EVIDENCE_REQUIRED
flow continuity failure
remaining blockers
forbidden external approval claim
```

Add one complete same-conversation fixture that expects `status == "PASS"`.

- [ ] **Step 2: Run the validator tests and verify RED**

Run:

```powershell
python -m unittest tests.test_politics_longform_chatgpt_two_pass_validator -v
```

Expected: import failure because the validator does not exist.

- [ ] **Step 3: Implement the validator**

Use only the Python standard library. Compute SHA-256 from the real files, parse
the two manifests, receipts, and decision JSON, normalize `/c/{id}` from each
conversation URL, compare ordered suggestion IDs and segment IDs, and return a
nonzero exit code on any error.

- [ ] **Step 4: Run validator tests and verify GREEN**

Expected: all behavioral tests pass.

### Task 5: Validate the skill and managed runtimes

**Files:**
- Validate: `skills/111-politics-longform/`
- Verify: `scripts/verify.ps1`
- Install: `scripts/install.ps1`

**Interfaces:**
- Consumes: completed Git skill source
- Produces: a matching Codex managed copy for the current request

- [ ] **Step 1: Run targeted tests**

```powershell
python -m unittest `
  tests.test_politics_longform_embedded_contract `
  tests.test_politics_longform_chatgpt_project_contract `
  tests.test_politics_longform_chatgpt_two_pass_validator -v
```

- [ ] **Step 2: Run skill validation**

```powershell
python C:\Users\arajun\.codex\skills\.system\skill-creator\scripts\quick_validate.py `
  skills\111-politics-longform
```

- [ ] **Step 3: Run repository verification**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Target repo
```

- [ ] **Step 4: Install only this skill**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Target codex -Only 111-politics-longform
```

- [ ] **Step 5: Verify the Codex runtime copy**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Target codex
```

### Task 6: Commit and publish only the approved scope

**Files:**
- Stage only the v3/two-pass skill, tests, validator, spec, and plan

**Interfaces:**
- Consumes: verified working tree
- Produces: pushed feature branch and draft pull request

- [ ] **Step 1: Inspect the final scoped diff**

```powershell
git status --short
git diff --check
git diff --stat
```

- [ ] **Step 2: Stage explicit paths only**

Never use `git add -A`. Exclude dirty `222mara` and Shorts production-gate
files.

- [ ] **Step 3: Commit**

```powershell
git commit -m "feat: add politics ChatGPT two-pass review gate"
```

- [ ] **Step 4: Integrate current remote changes without dropping user work**

Fetch, inspect, and merge the remote branch changes. Re-run targeted tests after
the merge.

- [ ] **Step 5: Push and open a draft PR**

```powershell
git push -u origin agent/politics-chatgpt-two-pass-v3
gh pr create --draft --fill
```

## Self-Review

- Spec coverage: v3 preflight, same-conversation round chain, flow continuity,
  master/lower review separation, deterministic gate, approval boundary, and
  publication are mapped to Tasks 1-6.
- Placeholder scan: no `TBD`, `TODO`, or deferred implementation steps.
- Interface consistency: artifact names and status values match the design.
