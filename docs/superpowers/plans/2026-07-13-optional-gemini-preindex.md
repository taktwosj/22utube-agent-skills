# Optional Gemini Pre-index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Gemini an optional, unverified pre-index for `00-tikitaka`; use supplied Gemini notes when available, but proceed directly from `source.mp4` when they are absent or fail.

**Architecture:** Keep source evidence as the only final authority. Encode the routing decision in `SKILL.md`, reduce the Gemini prompt to candidate extraction for `T1`, `T2`, `TTS`, verified-quote candidates, and situation-caption candidates, and protect both behaviors with repository contract tests.

**Tech Stack:** Markdown skill contract, UTF-8 JSON prompt contract, Python `unittest`, PowerShell repository verifier.

## Global Constraints

- Gemini output is never verified timing, dialogue, OCR, or final script truth.
- Missing Gemini output alone must never block Tikitaka when source media can be acquired.
- Exact dialogue, timing, OCR, source identity, and final production decisions remain based on `source.mp4`, ffprobe, STT, OCR, and frames.
- The AI Studio web-UI-only and source-binding safety contract remains unchanged when Gemini is explicitly requested.
- Do not modify unrelated files or runtime assets outside the managed install flow.

---

### Task 1: Add the optional-intake regression contract

**Files:**
- Create: `tests/test_tikitaka_optional_gemini_contract.py`
- Modify: `tests/test_tikitaka_production_type_contract.py`

**Interfaces:**
- Consumes: `skills/00-tikitaka/SKILL.md` and `skills/00-tikitaka/references/gemini_raw_intake_prompt.md`.
- Produces: executable assertions for optional routing, direct-source fallback, unverified-note handling, and compact candidate slots.

- [ ] **Step 1: Write the failing test**

```python
def test_missing_gemini_does_not_block_direct_source_analysis():
    assert "## Optional Gemini Pre-index" in TIKITAKA
    assert "Do not block Tikitaka only because Gemini raw intake is absent" in TIKITAKA
    assert "source.mp4" in TIKITAKA

def test_prompt_is_a_compact_candidate_index():
    for token in ('"t1_candidates"', '"t2_candidates"', '"tts_candidates"',
                  '"speaker_quote_candidates"', '"situation_caption_candidates"'):
        assert token in GEMINI_PROMPT
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_tikitaka_optional_gemini_contract -v`

Expected: FAIL because the optional routing section and compact candidate fields do not exist yet.

- [ ] **Step 3: Update the old heading-dependent assertion**

Change the section boundary in `test_tikitaka_production_type_contract.py` from `## Gemini Raw Intake First` to `## Optional Gemini Pre-index` so the existing order test tracks the renamed section.

### Task 2: Implement optional routing and compact Gemini notes

**Files:**
- Modify: `skills/00-tikitaka/SKILL.md`
- Modify: `skills/00-tikitaka/references/gemini_raw_intake_prompt.md`

**Interfaces:**
- Consumes: a Shorts URL, an optional pasted Gemini JSON, and/or `source.mp4`.
- Produces: unverified candidate hints for `T1`, `T2`, `TTS`, `""`, and `()` plus direct-source fallback behavior.

- [ ] **Step 1: Implement the minimal skill routing**

Define this order: supplied Gemini notes -> use as unverified index without rerun; explicit Gemini request -> run AI Studio; otherwise -> acquire/confirm `source.mp4` and analyze directly; Gemini failure -> continue direct when source is available.

- [ ] **Step 2: Replace the oversized prompt with the compact JSON contract**

Keep `status`, `video_url`, `video_duration_sec`, `shorts_type_assessment.story_type`, `shorts_type_assessment.production_type`, candidate arrays, `uncertainty_ko`, and `final_warning_ko`. Cap candidates at 12 and require every candidate to remain unverified.

- [ ] **Step 3: Run the focused test and verify GREEN**

Run: `python -m unittest tests.test_tikitaka_optional_gemini_contract tests.test_tikitaka_production_type_contract tests.test_ai_studio_source_identity_contract -v`

Expected: PASS.

### Task 3: Verify, publish, and sync managed runtimes

**Files:**
- Verify only: repository and managed runtime copies.

**Interfaces:**
- Consumes: committed Git source.
- Produces: pushed branch, draft PR, and matching managed runtime hashes.

- [ ] **Step 1: Run repository checks**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1 -Target repo`

Expected: `VERIFY PASS`.

- [ ] **Step 2: Check the patch and commit only intended files**

Run: `git diff --check`, inspect `git diff --stat` and `git diff`, then commit the two skill files, two tests, and this plan.

- [ ] **Step 3: Push and create a draft PR**

Push the current non-default branch and create or update a draft PR through `gh`.

- [ ] **Step 4: Install and verify the committed `00-tikitaka` skill**

Run: `powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -Target all -Only 00-tikitaka`, then `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1 -Target all`.

Expected: all managed target hashes match the committed source and `VERIFY PASS`.
