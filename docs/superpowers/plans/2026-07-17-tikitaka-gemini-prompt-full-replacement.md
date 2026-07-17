# Tikitaka Gemini Prompt Full Replacement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the compact `00-tikitaka` Gemini candidate prompt with the complete AI Studio Shorts Runner second-by-second observation prompt and synchronize only `00-tikitaka` to the managed runtimes.

**Architecture:** Keep `00-tikitaka` as the single skill owner. Bundle the full prompt inside its existing Markdown reference, lock the normalized prompt body to the extension prompt SHA-256, update only the Gemini routing paragraph, and install only this skill to Codex, Claude, and Hermes.

**Tech Stack:** Markdown skill instructions, Python `unittest`, PowerShell managed-skill installer, SHA-256 parity checks.

## Global Constraints

- Modify only `00-tikitaka`, its Gemini contract tests, and the approved design/plan documents.
- Do not modify, stage, revert, commit, or publish unrelated dirty files.
- The old compact candidate-index prompt must be absent.
- The normalized prompt-body SHA-256 must equal `4c40cdac22eaf42de68cf5b73883abbe35ffae4550815621171b1e8550a8cf60`.
- Gemini remains optional and AI Studio web-UI-only.
- Source-media verification remains authoritative.
- Do not use `scripts/update.ps1` while the repository is dirty.
- Do not commit or push in this task.

---

### Task 1: Replace the prompt contract test

**Files:**
- Modify: `tests/test_tikitaka_optional_gemini_contract.py`

**Interfaces:**
- Consumes: fenced `text` block from `skills/00-tikitaka/references/gemini_raw_intake_prompt.md`
- Produces: `prompt_body()` normalization and full-contract assertions

- [x] **Step 1: Write the failing tests**

Add `hashlib` and `re`, define the exact completion warning and expected normalized SHA-256, then replace the compact-candidate test with assertions for the full observation fields:

```python
CANONICAL_FINAL_WARNING = (
    "이 JSON은 Gemini 초벌 초단위 관찰값이다. 최종 대본, 화자발언 확정, "
    "컷타이밍, TTS/상황설명 배치, CapCut 제작은 Codex가 source.mp4와 "
    "STT/OCR/프레임 검증으로 확정해야 한다."
)
EXPECTED_PROMPT_SHA256 = "4c40cdac22eaf42de68cf5b73883abbe35ffae4550815621171b1e8550a8cf60"


def prompt_body() -> str:
    match = re.search(r"```text\r?\n(.*?)\r?\n```", GEMINI_PROMPT, re.DOTALL)
    if not match:
        raise AssertionError("Gemini prompt text block is missing")
    return match.group(1).replace("\r\n", "\n").rstrip("\n")
```

Require:

```python
for token in (
    '"source_audio_mode"',
    '"shorts_type_assessment"',
    '"start_sec"',
    '"end_sec"',
    '"speaker_quote_candidate_ko"',
    '"situation_caption_candidate_ko"',
    '"tts_interpretation_candidate_ko"',
    '"best_hook_moments"',
    '"best_speaker_quote_candidates"',
    '"best_situation_caption_angles"',
    '"best_tts_angles"',
    '"remake_structure_candidates"',
    '"production_type_candidates"',
    '"recommended_package_fields"',
):
    self.assertIn(token, GEMINI_PROMPT)

self.assertIn(CANONICAL_FINAL_WARNING, GEMINI_PROMPT)
self.assertEqual(
    hashlib.sha256(prompt_body().encode("utf-8")).hexdigest(),
    EXPECTED_PROMPT_SHA256,
)
```

Reject:

```python
for token in (
    '"t1_candidates"',
    '"t2_candidates"',
    '"tts_candidates"',
    '"speaker_quote_candidates"',
    '"situation_caption_candidates"',
    "후보는 전체 합계 최대 12개",
):
    self.assertNotIn(token, GEMINI_PROMPT)
```

Update the skill-routing expectations to require `## Optional Gemini Raw Observation`, `Gemini is optional raw observation, not an intake gate.`, and `unverified raw observation notes`.

- [x] **Step 2: Run the focused test and verify RED**

Run:

```powershell
py -3 -m unittest discover -s tests -p "test_tikitaka_optional_gemini_contract.py" -v
```

Expected: FAIL because the installed source still contains the compact prompt, old section heading, and old normalized SHA-256.

### Task 2: Replace the prompt and routing text

**Files:**
- Modify: `skills/00-tikitaka/references/gemini_raw_intake_prompt.md`
- Modify: `skills/00-tikitaka/SKILL.md`

**Interfaces:**
- Consumes: `22factory_20260628/00_asset_tools/browser_extensions/ai-studio-shorts-runner/assets/gemini_raw_intake_prompt.txt`
- Produces: complete bundled prompt with the exact canonical completion warning

- [x] **Step 1: Replace the Markdown prompt body**

Keep a short Markdown wrapper with the heading `# Gemini Raw Observation Prompt`
and the two-sentence usage note from the approved design. Open one `text` code
fence immediately after the note. Copy the complete normalized 8,390-character
body from
`22factory_20260628/00_asset_tools/browser_extensions/ai-studio-shorts-runner/assets/gemini_raw_intake_prompt.txt`
into that fence. The body starts with `너의 임무는 영상을 초단위로 사실 관찰하는 것이다.`
and ends with the JSON closing brace after the exact canonical
`final_warning_ko`. Close the `text` fence after that brace.

Do not retain any compact candidate-index instructions or fields.

- [x] **Step 2: Update the Tikitaka Gemini routing paragraph**

Replace only the Gemini section wording:

```text
## Optional Gemini Raw Observation

Gemini is optional raw observation, not an intake gate.
```

Existing Gemini results are reused as `unverified raw observation notes`. When explicitly requested, the skill reads the `complete second-by-second raw-observation prompt`, requires the exact canonical `final_warning_ko`, and continues to treat the result as proposed evidence until source-media verification.

- [x] **Step 3: Run the focused test and verify GREEN**

Run:

```powershell
py -3 -m unittest discover -s tests -p "test_tikitaka_optional_gemini_contract.py" -v
```

Expected: all tests in the focused file pass with zero failures.

- [x] **Step 4: Compare the prompt copies directly**

Extract the Tikitaka fenced prompt body, normalize CRLF and the final newline, and compare it to the normalized extension prompt.

Expected:

```text
PROMPT_PARITY: PASS
SHA256: 4c40cdac22eaf42de68cf5b73883abbe35ffae4550815621171b1e8550a8cf60
```

### Task 3: Verify the focused and repository contracts

**Files:**
- Verify: `tests/test_tikitaka_optional_gemini_contract.py`
- Verify: `tests/test_ai_studio_source_identity_contract.py`
- Verify: `skills/00-tikitaka/SKILL.md`
- Verify: `skills/00-tikitaka/references/gemini_raw_intake_prompt.md`

**Interfaces:**
- Consumes: changed Tikitaka source and tests
- Produces: focused pass evidence plus separately reported broader verification state

- [x] **Step 1: Run both focused contract files**

Run:

```powershell
py -3 -m unittest discover -s tests -p "test_tikitaka_optional_gemini_contract.py" -v
py -3 -m unittest discover -s tests -p "test_ai_studio_source_identity_contract.py" -v
```

Expected: both commands pass with zero failures.

- [x] **Step 2: Run repository verification**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -Target repo
```

Expected: report the actual `VERIFY PASS` or `VERIFY FAIL`. If it fails only because of unrelated pre-existing dirty work, keep that failure separate from the focused Tikitaka evidence.

- [x] **Step 3: Review the exact modified scope**

Run:

```powershell
git status --short -- skills/00-tikitaka tests/test_tikitaka_optional_gemini_contract.py docs/superpowers/specs/2026-07-17-tikitaka-gemini-prompt-replacement-design.md docs/superpowers/plans/2026-07-17-tikitaka-gemini-prompt-full-replacement.md
git diff -- skills/00-tikitaka tests/test_tikitaka_optional_gemini_contract.py
```

Confirm no command modified unrelated files.

### Task 4: Synchronize only `00-tikitaka`

**Files:**
- Source: `skills/00-tikitaka/**`
- Install targets: managed Codex, Claude, and Hermes `00-tikitaka` directories only

**Interfaces:**
- Consumes: verified source skill
- Produces: matching runtime copies and managed markers

- [x] **Step 1: Install only the selected skill**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Target all -Only 00-tikitaka
```

Expected: `SYNCED` and `MARKER` lines only for `00-tikitaka`, followed by `DONE install target=all dry_run=False`.

- [x] **Step 2: Verify selected-skill directory hashes**

Compute the source directory hash and each target directory hash while excluding the target marker file.

Expected:

```text
codex MATCH
claude MATCH
hermes MATCH
```

- [x] **Step 3: Verify Codex runtime visibility**

Run:

```powershell
codex debug prompt-input "티키타카 하자"
```

Expected: exactly one visible `00-tikitaka` skill entry.

- [x] **Step 4: Leave Git state uncommitted**

Do not stage, commit, push, revert, or clean any file. Report the exact Tikitaka-related modified paths and separately note that unrelated dirty files were preserved.
