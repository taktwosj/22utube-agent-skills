# Gemini Source Identity Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make the user’s only Shorts chain fail closed: 00-tikitaka design -> 000short-production-agent assembly.

**Architecture:** The browser extension owns one fresh UI run and emits verifiable run evidence. The Python runner binds that run to trusted yt-dlp metadata before saving. Stage 2 independently binds the real local media by SHA256 and live ffprobe before allowing production.

**Tech Stack:** Chrome MV3 JavaScript, Node test runner, Python 3.11+, pytest, ffprobe, JSON contracts.

## Global Constraints

- Active factory root: C:\Users\arajun\OneDrive\22utube\22factory_20260628.
- Git skill source: C:\Users\arajun\agent-skills.
- Gemini intake is AI Studio web UI only; no Gemini API fallback.
- Never use stored URL, prompt, prior result, or old episode identity as the current source.
- A Run action occurs exactly once per run_nonce.
- Google Search must be VERIFIED_OFF while URL Context is VERIFIED_ON.
- Persistent Chrome storage may contain boolean preferences only; pending jobs and run results use session memory and expire.
- No PASS, FINAL, production PASS, or upload_ready without matching evidence.
- Stage 1 design authority is 00-tikitaka; Stage 2 assembly authority is 000short-production-agent.
- Actual CapCut work remains based on shrt white; this repair must not create or foreground CapCut.

---

### Task 1: Extension single-run and stale-state fail closure

**Files:**
- Modify: C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\browser_extensions\ai-studio-shorts-runner\tests\core.test.mjs
- Modify: C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\browser_extensions\ai-studio-shorts-runner\tests\submit_contract.test.mjs
- Modify: C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\browser_extensions\ai-studio-shorts-runner\src\core.mjs
- Modify: C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\browser_extensions\ai-studio-shorts-runner\src\core-browser.js
- Modify: C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\browser_extensions\ai-studio-shorts-runner\content.js
- Modify: C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\browser_extensions\ai-studio-shorts-runner\popup.js

**Interfaces:**
- Produces: bridge result with playgroundClickVerified=true, generationEvidence, runNonce, requestedUrl, and the existing prompt binding fields.
- Consumes: current popup form URL only; persistent storage keeps booleans only.

- [ ] **Step 1: Write failing extension tests**

Add tests equivalent to:

~~~javascript
test('run evidence requires an actual Playground click and generation signal', () => {
  const base = validLastRun();
  assert.throws(() => validateResultBinding(parsed, {...base, playgroundClickVerified: false}), /WAIT_PLAYGROUND_RESET_REQUIRED/);
  assert.throws(() => validateResultBinding(parsed, {...base, generationEvidence: ''}), /WAIT_GENERATION_NOT_STARTED/);
});

test('content script dispatches exactly one click for one run', () => {
  const block = functionBody(contentJs, 'clickOnce');
  assert.equal((block.match(/\.click\(\)/g) || []).length, 1);
  assert.doesNotMatch(block, /dispatchEvent\(new MouseEvent\(['"]click/);
});
~~~

Also assert:

- popup/content never write the job, URL, prompt, note, last run, or last result to chrome.storage.local;
- session jobs carry a schema version and short TTL;
- duplicate bridge request IDs and concurrent runs are rejected;
- Ctrl+Enter is dispatched once, not once to the prompt and again to document;
- core.mjs and core-browser.js expose the same contract version.

- [ ] **Step 2: Run tests and confirm RED**

Run: npm test

Expected: failures for missing playgroundClickVerified/generationEvidence and double click/state cleanup.

- [ ] **Step 3: Implement minimum browser changes**

Use one DOM click:

~~~javascript
function clickOnce(el) {
  el.click();
  return 'CLICKED_ONCE';
}
~~~

Require the Playground element to be found and clicked; URL text alone is not VERIFIED_NEW_CHAT. After Run, poll for a visible Stop/Cancel control, a disabled Run control, or a new Model/loading state. Return a concrete generationEvidence token; otherwise throw WAIT_GENERATION_NOT_STARTED. Do not set generationStarted=true unconditionally.

Move pending job/last-run/last-result to chrome.storage.session, add a service worker access-level bootstrap when content-script access is required, and keep only boolean settings in chrome.storage.local. Reject expired/schema-old pending jobs. Clear current session run/result state atomically before filling a new prompt.

Find the exact URL Context switch by its own label/control relationship. Find Google Search independently, force it OFF, and return searchGroundingStatus=VERIFIED_OFF. Add an in-flight job lock and request-ID deduplication.

- [ ] **Step 4: Run extension tests and verification**

Run: npm run verify

Expected: all extension tests PASS.

---

### Task 2: Python runner rejects false bridge attestations before save

**Files:**
- Modify: C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\ai_studio_runner\tests\test_runner_contract.py
- Modify: C:\Users\arajun\OneDrive\22utube\22factory_20260628\00_asset_tools\ai_studio_runner\src\ai_studio_runner\playwright_ai_studio.py

**Interfaces:**
- Consumes: Task 1 bridge result.
- Produces: SAVED only after trusted metadata, run nonce, source video ID, duration, observed title, and browser-run evidence agree.

- [ ] **Step 1: Write failing runner tests**

~~~python
def test_bridge_requires_playground_click_and_generation_evidence():
    result = valid_bridge_result()
    result["playgroundClickVerified"] = False
    result["generationEvidence"] = ""
    errors = validate_bridge_run_result(result, "nonce-1")
    assert "PLAYGROUND_CLICK_NOT_VERIFIED" in errors
    assert "GENERATION_EVIDENCE_REQUIRED" in errors
~~~

Add tests proving:

- the BRAlwARPPFo cat fixture never reaches save_result_files even after current run_nonce, source_video_id, video_url, observed_source_title, and 59-second duration are inserted;
- missing searchGroundingStatus=VERIFIED_OFF is rejected;
- the same run ID cannot overwrite an existing result bundle.

- [ ] **Step 2: Run runner tests and confirm RED**

Run: .venv\Scripts\python.exe -m pytest tests\test_runner_contract.py -q

Expected: new bridge-evidence assertions fail.

- [ ] **Step 3: Implement minimum runner validation**

Require bridge_result.playgroundClickVerified is true, searchGroundingStatus is VERIFIED_OFF, and generationEvidence is in the explicit allowlist.

Strengthen semantic identity: compare trusted-title subject tokens against the analysis body with identity fields removed. A title copied only into observed_source_title is not evidence. Require a meaningful subject token from a non-generic title in the content body; otherwise RESULT_SOURCE_MISMATCH. Preserve exact nonce, URL ID, source_video_id, trusted title, and duration checks.

Write JSON, Markdown, and run manifest to temporary sibling files, fail if final paths already exist, then atomically rename the complete bundle. On a source mismatch, write a mismatch evidence bundle under 99_archive/gemini_source_mismatch without promoting it to the active germini folder.

- [ ] **Step 4: Run runner suite**

Run: set PYTHONPATH=src then .venv\Scripts\python.exe -m pytest -q

Expected: all runner tests PASS.

---

### Task 3: Stage 2 live-media proof and honest tests

**Files:**
- Modify: C:\Users\arajun\agent-skills\skills\000short-production-agent\scripts\validate_stage2_tikitaka_handoff.py
- Modify: C:\Users\arajun\agent-skills\skills\000short-production-agent\scripts\validate_production_gate.py
- Modify: C:\Users\arajun\agent-skills\skills\00-tikitaka\scripts\tikitaka_harness_runner.py
- Modify: C:\Users\arajun\agent-skills\tests\test_000short_tikitaka_v2_handoff_contract.py
- Modify: C:\Users\arajun\agent-skills\tests\test_production_gate_behavioral_contract.py
- Modify: C:\Users\arajun\agent-skills\tests\test_script_handoff_gate_execution_contract.py

**Interfaces:**
- Produces: source_probe_status=PASS, actual_source_duration_sec, source_sha256, exact edit_id coverage.
- Consumes: source_identity_lock.json, source_manifest.json, source_evidence.json, crosscheck_report.json, real source.mp4.

- [ ] **Step 1: Remove test auto-magic and add RED forgery test**

Delete generic write_json behavior that silently converts {"materials": {}} into a linked draft or merges missing manifest identity fields. Fixtures must call explicit helpers.

Add:

~~~python
def test_forged_probe_json_cannot_make_text_file_pass():
    create_valid_tikitaka_v2_package(root, source_bytes=b"not a video")
    with pytest.raises(GateFail, match="WAIT_SOURCE_EVIDENCE_PROBE_REQUIRED"):
        validate_stage2_tikitaka_handoff(root)
~~~

Generate one tiny valid MP4 byte fixture at test runtime with ffmpeg and cache the bytes for all positive fixtures.

Add RED cases for:

- brainstorm requested ID, report1 source ID, contract source URL, and source lock ID disagreeing;
- voice_audio_route_decided=true without a concrete voice_audio_route value;
- reversed edit_block_sequence;
- source_ref/source_block_id mismatch;
- caption role or source_audio/TTS policy mismatch;
- final validate_gate with no draft_content.json;
- final validate_gate with an unlinked or synthetic source material.

- [ ] **Step 2: Run target tests and confirm RED**

Run: pytest for the three target contract files.

Expected: fake text source currently passes and the new test fails.

- [ ] **Step 3: Implement live ffprobe**

Add probe_source_media(path) that executes:

~~~text
ffprobe -v error -show_entries format=duration:stream=codec_type -of json <source>
~~~

Require return code 0, at least one video stream, numeric positive duration, and duration agreement with source_identity_lock.json within 0.25 seconds. Never trust evidence JSON alone.

Require 10_analysis/brainstorm_handoff.json and compare its requested_source_url/requested_video_id with source_identity_lock.json, report1_handoff.json, and contract.source_url when present. report1_handoff.json must contain exact source_url, source_video_id, and a non-empty allowed voice_audio_route.

Compare timeline and maps by ordered edit IDs and per-edit semantics: source_ref/source_block_id, source_order/original_order, timeline_order/urakkai_order, assembly_role, caption_type, and source-audio/TTS policy. Sets alone are insufficient.

Before final validate_gate returns PASS or upload_ready, require the real draft_content.json and run the media-link validator against the same live-probed source path. The pre-CapCut state must not emit production PASS or upload_ready.

- [ ] **Step 4: Run target and full skill suites**

Run the three target files first, then all repository tests with the runner venv pytest executable.

Expected: target and full suites PASS with no hidden fixture mutation.

---

### Task 4: Contract sync, packaging, and independent review

**Files:**
- Review/modify only if tests require: the three named SKILL.md files and gemini_raw_intake_prompt.md.
- Rebuild: ai-studio-shorts-runner.zip.
- Sync: Codex, Claude, and Zcode runtime copies from Git source.

- [ ] **Step 1: Add or update skill pressure tests**

Use a fresh-context scenario where an agent is offered a status-only source manifest, raw Gemini JSON, and an empty CapCut draft. It must stop before Stage 2 and name source identity, live probe, maps, and media link blockers.

- [ ] **Step 2: Validate skill folders and runtime hashes**

Run quick_validate.py for all three skills and the repository contract tests. Confirm Git source SHA256 equals Codex, Claude, and Zcode runtime SHA256.

- [ ] **Step 3: Rebuild extension zip**

Package only the extension directory contents. Verify the zip contains current content.js, popup.js, both core files, assets, manifest, docs, and tests.

- [ ] **Step 4: Reload and live-check the unpacked extension**

Use the existing Chrome extension entry. Do not touch normal browsing tabs beyond the extension management/reload action. Confirm the popup opens empty, old PV8H6fEF9fw is absent, and the installed version matches the source manifest.

- [ ] **Step 5: Run whole-change review**

Dispatch an independent reviewer over the final diff and test evidence. Fix all Critical/Important findings, rerun covering tests, then rerun the complete suites.
