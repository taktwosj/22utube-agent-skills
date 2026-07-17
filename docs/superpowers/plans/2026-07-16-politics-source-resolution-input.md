# Politics Source Resolution Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to execute this plan task-by-task.

**Goal:** Permit `1280x720` and `1920x1080` source videos while keeping the final CapCut canvas at `1920x1080`.

**Architecture:** This is a contract hardening change. The production pipeline already preserves real source dimensions and does not enforce a 1920x1080-only source gate, so the Git skill, Codex runtime skill, and regression test are the required implementation surfaces.

**Tech Stack:** Markdown skill contract, Python `unittest`.

## Global Constraints

- Preserve existing unrelated dirty-worktree changes.
- Do not alter the `jungchilong` final canvas.
- Do not change thumbnail resolution rules.
- Do not commit or push without a separate user request.

---

### Task 1: Lock the source-resolution contract

**Files:**
- Modify: `tests/test_politics_longform_embedded_contract.py`
- Modify: `skills/111-politics-longform/SKILL.md`
- Modify: Codex runtime `111-politics-longform/SKILL.md`

**Interfaces:**
- Consumes: source ffprobe `width` and `height`.
- Produces: explicit `preferred_source_resolution`, `accepted_source_resolutions`, and `final_canvas_resolution` contract tokens.

- [ ] **Step 1: Write the failing test**

```python
def test_source_intake_accepts_720p_and_1080p_while_canvas_stays_1080p(self):
    for token in (
        "preferred_source_resolution=1920x1080",
        "required_accepted_source_resolutions=1920x1080|1280x720",
        "final_canvas_resolution=1920x1080",
        "source_dimensions_preserved_from_ffprobe=true",
        "thumbnail_resolution_contract=1280x720",
        "SOURCE_RESOLUTION_ACCEPTED",
    ):
        self.assertIn(token, self.skill_text)
```

- [ ] **Step 2: Run the targeted test and confirm it fails because the contract tokens are absent**

```powershell
py -3 -m unittest tests.test_politics_longform_embedded_contract.PoliticsLongformEmbeddedContractTests.test_source_intake_accepts_720p_and_1080p_while_canvas_stays_1080p
```

- [ ] **Step 3: Add the minimal source-resolution wording to both SKILL.md copies**

The wording must distinguish source input, final canvas, and thumbnail resolution.

- [ ] **Step 4: Run the targeted and full contract tests**

```powershell
py -3 -m unittest tests.test_politics_longform_embedded_contract
```

- [ ] **Step 5: Review the final diff and confirm no unrelated file was overwritten**

```powershell
git diff -- skills/111-politics-longform/SKILL.md tests/test_politics_longform_embedded_contract.py
```
