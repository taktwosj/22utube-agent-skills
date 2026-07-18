# Tikitaka ChatGPT Two-Pass Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fail-closed, browser-assisted ChatGPT Project two-pass review workflow that produces a validated Tikitaka Stage 1 design blueprint.

**Architecture:** A deterministic Python CLI owns packet construction, canonical hashing, response validation, and gate finalization. Codex uses the existing signed-in Chrome session only for the live project interaction and preserves every sent packet and raw response as files.

**Tech Stack:** Python 3 standard library, `unittest`, Markdown/JSON contracts, Codex Chrome control, existing PowerShell sync scripts

## Global Constraints

- Use repository-relative paths and `py -3` on Windows.
- Use only ChatGPT project `g-p-6a245b804c2c8191907088f317842a55-syoceudaebonbunseog`.
- Do not use ChatGPT API, Claude CLI, generic ChatGPT chats, or another project.
- Preserve user changes outside the scoped Tikitaka files.
- Stop on any failed gate; do not create CapCut, SRT, voice, render, export, or upload assets.

---

### Task 1: Packet builder and canonical hash

**Files:**
- Create: `skills/00-tikitaka/scripts/chatgpt_review_workflow.py`
- Create: `tests/test_tikitaka_chatgpt_review_workflow.py`

**Interfaces:**
- Consumes: a Tikitaka `20_script` directory and its Stage 1 artifacts
- Produces: `canonical_packet_sha256(text: str) -> str` and Round 1/2 packet files

- [ ] **Step 1: Write failing tests**

```python
def test_canonical_hash_removes_only_current_top_level_hash_line():
    text = (
        "content_type: shorts\n"
        "sent_packet_sha256: placeholder\n"
        "embedded: |\n"
        "  sent_packet_sha256: keep-me\n"
    )
    assert workflow.canonical_packet_sha256(text) == hashlib.sha256(
        (
            "content_type: shorts\n"
            "embedded: |\n"
            "  sent_packet_sha256: keep-me\n"
        ).encode("utf-8")
    ).hexdigest()

def test_build_round1_writes_required_metadata_and_artifacts():
    result = workflow.build_round1(work_dir, review_cycle_id="cycle-1")
    assert result["review_round"] == 1
    assert Path(result["packet_path"]).is_file()
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
py -3 -m unittest discover -s tests -p "test_tikitaka_chatgpt_review_workflow.py" -v
```

Expected: FAIL because `chatgpt_review_workflow.py` does not exist.

- [ ] **Step 3: Implement the packet builder**

Implement:

```python
def normalize_lf(text: str) -> str: ...
def canonical_packet_sha256(text: str) -> str: ...
def build_round1(work_dir: Path, review_cycle_id: str) -> dict[str, object]: ...
def build_round2(work_dir: Path, review_cycle_id: str) -> dict[str, object]: ...
```

The builders must fail on missing required artifacts and write UTF-8/LF files
under `chatgpt_review/`.

- [ ] **Step 4: Verify GREEN**

Run the Task 1 command and require all tests to pass.

### Task 2: Raw response validator

**Files:**
- Modify: `skills/00-tikitaka/scripts/chatgpt_review_workflow.py`
- Modify: `tests/test_tikitaka_chatgpt_review_workflow.py`

**Interfaces:**
- Consumes: exact saved packet and raw ChatGPT response
- Produces: `validate_response(packet_path, response_path, round_number) -> dict`

- [ ] **Step 1: Write failing tests**

Test exact metadata echo, first-line route, final status, wrong project route,
tampered hash, and missing Round 2 recommendation.

- [ ] **Step 2: Verify RED**

Run the focused test module and confirm failures are caused by the missing
validator behavior.

- [ ] **Step 3: Implement minimal validation**

```python
def validate_response(
    packet_path: Path,
    response_path: Path,
    round_number: int,
) -> dict[str, object]:
    ...
```

Return parsed metadata only after all fail-closed checks pass.

- [ ] **Step 4: Verify GREEN**

Run the focused test module and require all tests to pass.

### Task 3: Codex decision ledger and final gate

**Files:**
- Modify: `skills/00-tikitaka/scripts/chatgpt_review_workflow.py`
- Modify: `tests/test_tikitaka_chatgpt_review_workflow.py`

**Interfaces:**
- Consumes: Round 1 response, `round1_codex_decisions.json`, Round 2 response
- Produces: `chatgpt_review_gate.json`

- [ ] **Step 1: Write failing tests**

Test rejection of incomplete decisions, `PENDING_EVIDENCE`,
`REVISE_REQUIRED`, `EVIDENCE_REQUIRED`, and post-Round-2 protected field
changes. Test a complete `PASS_RECOMMENDED` fixture.

- [ ] **Step 2: Verify RED**

Run the focused module and confirm the expected failures.

- [ ] **Step 3: Implement finalization**

```python
def validate_codex_decisions(path: Path) -> dict[str, object]: ...
def finalize_gate(work_dir: Path) -> dict[str, object]: ...
```

Write the gate atomically only after both response validations and all decision
checks pass.

- [ ] **Step 4: Verify GREEN**

Run the focused module and require all tests to pass.

### Task 4: Strengthen the existing harness

**Files:**
- Modify: `skills/00-tikitaka/scripts/tikitaka_harness_runner.py`
- Modify: `tests/test_script_handoff_gate_execution_contract.py`

**Interfaces:**
- Consumes: finalized review artifacts
- Produces: fail-closed `chatgpt_review_gate` status inside the script handoff gate

- [ ] **Step 1: Write failing regression tests**

Add tests proving the harness rejects a response whose echoed cycle ID,
packet ID, or sent hash differs, and rejects a gate claiming
`PASS_RECOMMENDED` when the raw response says otherwise.

- [ ] **Step 2: Verify RED**

Run:

```powershell
py -3 -m unittest discover -s tests -p "test_script_handoff_gate_execution_contract.py" -v
```

Expected: the new tamper tests fail against the current validator.

- [ ] **Step 3: Reuse the workflow validator from the harness**

Load the sibling workflow module and validate both raw responses rather than
trusting duplicated JSON fields.

- [ ] **Step 4: Verify GREEN**

Run the Task 4 command and require the new tests to pass.

### Task 5: Skill contract and live project source

**Files:**
- Modify: `skills/00-tikitaka/SKILL.md`
- Modify: `skills/00-tikitaka/shorts_script_analysis_single_source_v20260706.md`
- Modify: `skills/00-tikitaka/references/chatgpt_project_router_instruction.md`
- Modify: `tests/test_skill_router_contracts.py`
- Modify: `tests/test_tikitaka_production_type_contract.py`

**Interfaces:**
- Consumes: CLI commands and browser workflow
- Produces: discoverable operator instructions and exact project contract

- [ ] **Step 1: Add failing contract assertions**

Require the CLI filename, all four subcommands, exact project ID, and
`SOURCE_CONTRACT_MISSING` recovery instruction.

- [ ] **Step 2: Verify RED**

Run the two contract test modules and confirm the new markers are absent.

- [ ] **Step 3: Update the skill router**

Document the exact CLI/browser sequence without adding production-stage
responsibilities to `00-tikitaka`.

- [ ] **Step 4: Verify GREEN**

Run both contract modules and require all tests to pass.

- [ ] **Step 5: Attach the single-source contract in the live project**

Use the signed-in Chrome session, attach only
`shorts_script_analysis_single_source_v20260706.md`, and rerun a routing probe.
Expected response starts with `ROUTE=SHORTS` and does not contain
`SOURCE_CONTRACT_MISSING`.

### Task 6: Focused regression, runtime sync, and real URL

**Files:**
- Modify only if a test proves a scoped defect in the files above
- Create episode artifacts under the portable 11short handoff root after the user supplies a URL

**Interfaces:**
- Consumes: completed source tree and user Shorts URL
- Produces: runtime-visible skill, review artifacts, and validated `20_script/design_blueprint.md`

- [ ] **Step 1: Run focused regression**

```powershell
py -3 -m unittest discover -s tests -p "test_tikitaka*.py" -v
py -3 -m unittest discover -s tests -p "test_script_handoff_gate_execution_contract.py" -v
py -3 -m unittest discover -s tests -p "test_skill_router_contracts.py" -v
py -3 -m unittest discover -s tests -p "test_integrated_blueprint_contract.py" -v
```

- [ ] **Step 2: Sync managed runtimes**

Run the repository-provided update script for the selected skill, then verify
Git/runtime file hashes and `codex debug prompt-input` visibility.

- [ ] **Step 3: Run the real episode**

Acquire and lock the supplied source, create the Stage 1 candidate, execute both
ChatGPT review rounds in one project chat, finalize the gate, and run the
Tikitaka harness.

- [ ] **Step 4: Validate the blueprint**

Require `20_script/design_blueprint.md` to pass the integrated blueprint
validator in design phase.

- [ ] **Step 5: Commit and push scoped files**

Stage only the Tikitaka review automation, its tests, and these design/plan
documents. Exclude unrelated caption, TOP5, and user changes. Push the current
branch and verify local HEAD, upstream tracking ref, and GitHub commit SHA
match.
