# Tikitaka Demucs-First Source Voice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `00-tikitaka` create and validate a full-source Demucs vocal stem before speaker ranges are designed, then require Stage 2 speaker audio to come from that stem while embedded source-video audio stays muted.

**Architecture:** A new Tikitaka preprocessing command owns external `ffprobe`, `ffmpeg`, and Demucs execution and writes one hash-bound manifest. A separate validator owns artifact verification and is consumed by the Tikitaka harness and the Stage 2 handoff gate. Existing timeline and CapCut validators add provenance and mute rules without taking over stage transitions.

**Tech Stack:** Python 3, standard library, ffmpeg/ffprobe CLI, Demucs Python module, JSON, unittest, JSON Schema.

## Global Constraints

- Run Demucs on the complete source audio before any speaker/Q range is cut.
- The default model is `htdemucs` with `--two-stems vocals`.
- Stable WAV artifacts use 48 kHz audio.
- Manifest paths are episode-root-relative and never machine-specific.
- `no_vocals.wav` is never copied into the episode package or used in production.
- The only skip is `NOT_REQUIRED_NO_SOURCE_SPEECH` with explicit confirmation or no audio stream.
- Harnesses validate and report; they do not launch Demucs or the next skill.
- n8n remains `NOT_REQUIRED` unless explicitly selected.
- Embedded source-video audio is muted for every caption type.
- Missing ffmpeg, ffprobe, or Demucs fails closed without a separator fallback.

---

### Task 1: Full-source vocal preprocessing command

**Files:**
- Create: `skills/00-tikitaka/scripts/prepare_source_voice.py`
- Create: `tests/test_tikitaka_source_voice_pipeline.py`

**Interfaces:**
- Consumes: episode root, relative source path, optional confirmed no-speech reason.
- Produces: `10_analysis/audio/full_source_audio.wav`, `10_analysis/audio/vocals.wav`, and `10_analysis/source_voice_separation.json`.
- Exposes: `prepare_source_voice(root: Path, source: Path, *, model: str = "htdemucs", no_source_speech_confirmed: bool = False, confirmation_source: str = "") -> dict[str, Any]`.

- [ ] **Step 1: Write failing execution-order and skip tests**

Add tests that patch `subprocess.run` and verify the command order is
`ffprobe(source)`, `ffmpeg(full extraction)`, `python -m demucs.separate`, then
`ffmpeg(stable vocals)`. Assert the Demucs input is
`10_analysis/audio/full_source_audio.wav`, not a speaker-range clip. Add a
no-audio probe test that writes `status=NOT_REQUIRED_NO_SOURCE_SPEECH`, and a
manual skip test that fails unless confirmation is present.

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```powershell
$env:PYTHONPATH='tests'
py -3 -m unittest test_tikitaka_source_voice_pipeline
```

Expected: import or file-not-found failure for `prepare_source_voice.py`.

- [ ] **Step 3: Implement deterministic preparation**

Implement:

```python
class GateFail(Exception):
    pass

def prepare_source_voice(
    root: Path,
    source: Path,
    *,
    model: str = "htdemucs",
    no_source_speech_confirmed: bool = False,
    confirmation_source: str = "",
) -> dict[str, Any]:
    """Create full-source audio, Demucs vocals, and the bound gate manifest."""
```

Use `ffprobe` JSON to detect audio streams and source duration. Use
`shutil.which` for `ffmpeg`/`ffprobe` and `importlib.util.find_spec("demucs")`
for Demucs. Run Demucs with `sys.executable -m demucs.separate -n <model>
--two-stems vocals -o <temporary-directory> <full_source_audio.wav>`. Copy the
stable stem through ffmpeg to 48 kHz, probe it, enforce 0.25-second duration
parity, hash all declared files, and write the manifest only after success.

- [ ] **Step 4: Run the new tests and verify GREEN**

Run the Task 1 command again. Expected: all Task 1 tests pass.

- [ ] **Step 5: Commit Task 1**

```powershell
git add -- skills/00-tikitaka/scripts/prepare_source_voice.py tests/test_tikitaka_source_voice_pipeline.py
git commit -m "feat: prepare full-source Demucs vocals in Tikitaka"
```

### Task 2: Hash-bound source voice validator

**Files:**
- Create: `skills/00-tikitaka/scripts/validate_source_voice_separation.py`
- Modify: `tests/test_tikitaka_source_voice_pipeline.py`

**Interfaces:**
- Consumes: episode root and `10_analysis/source_voice_separation.json`.
- Produces: a PASS result or a fail-closed token.
- Exposes: `validate_source_voice_separation(root: Path, manifest_path: Path | None = None) -> dict[str, Any]`.

- [ ] **Step 1: Add failing validator tests**

Cover PASS, valid no-speech skip, unconfirmed skip, absolute artifact path,
wrong source fingerprint, mismatched file hash, non-full-source scope, wrong
Demucs input hash, sample rate other than 48000, duration drift over 0.25
seconds, `source_voice_music_removed != true`, and
`no_vocals_used != false`.

- [ ] **Step 2: Run the validator tests and verify RED**

Run the Task 1 test command. Expected: validator import or assertion failures.

- [ ] **Step 3: Implement validator**

Implement strict helpers for JSON loading, root-relative path resolution,
SHA-256, and ffprobe. PASS must prove:

```python
required_equalities = {
    "separation_engine": "demucs",
    "separation_scope": "FULL_SOURCE_AUDIO",
    "sample_rate_hz": 48000,
    "source_voice_music_removed": True,
    "q_segment_source": "10_analysis/audio/vocals.wav",
    "no_vocals_used": False,
    "created_by": "prepare_source_voice.py",
}
```

Require `demucs_input_sha256 == source_audio_sha256`, actual file hashes equal
the manifest, source/vocals durations stay within the declared tolerance, and
the source fingerprint matches `10_analysis/source_identity_lock.json`.

- [ ] **Step 4: Run tests and verify GREEN**

Run the Task 1 test command. Expected: all source-voice tests pass.

- [ ] **Step 5: Commit Task 2**

```powershell
git add -- skills/00-tikitaka/scripts/validate_source_voice_separation.py tests/test_tikitaka_source_voice_pipeline.py
git commit -m "feat: validate Tikitaka source voice separation evidence"
```

### Task 3: Tikitaka Stage 1 gate and contract

**Files:**
- Modify: `skills/00-tikitaka/scripts/tikitaka_harness_runner.py`
- Modify: `skills/00-tikitaka/SKILL.md`
- Modify: `skills/00-tikitaka/shorts_script_analysis_single_source_v20260706.md`
- Modify: `tests/test_script_handoff_gate_execution_contract.py`
- Modify: `tests/test_tikitaka_production_type_contract.py`

**Interfaces:**
- Consumes: source voice gate status and timeline speaker segments.
- Produces: `SCRIPT_HANDOFF_GATE` PASS only when source-voice evidence is PASS or a valid no-speech skip and the timeline is coherent.

- [ ] **Step 1: Add failing Stage 1 contract tests**

Add fixtures for a valid manifest. Assert `SCRIPT_HANDOFF_GATE` fails with
`WAIT_SOURCE_VOICE_SEPARATION` when missing. Assert a `speaker_quote` fails with
`WAIT_SOURCE_VOICE_Q_PROVENANCE` when its `source_audio_ref` or
`source_audio_provenance` is missing or points to raw video. Assert no-speech
skip plus a speaker quote fails.

- [ ] **Step 2: Run focused Stage 1 tests and verify RED**

```powershell
$env:PYTHONPATH='tests'
py -3 -m unittest test_script_handoff_gate_execution_contract test_tikitaka_production_type_contract
```

Expected: new assertions fail because source-voice evidence is not yet part of
the gate.

- [ ] **Step 3: Integrate validator-only harness behavior**

Add `source_voice_separation_status(work_dir)` that imports the validator from
the script directory and returns a normal harness status block. Include it in
`build_script_handoff_gate` requirements and visible reports. Extend
`timeline_design_status` so `speaker_quote` requires:

```python
{
    "source_audio_ref": "10_analysis/audio/vocals.wav",
    "source_audio_provenance": "demucs_full_source_vocals",
}
```

Do not call the preparation command from the harness.

- [ ] **Step 4: Update the two Tikitaka authorities**

Document the order immediately after source identity lock, the narrow
source-analysis audio exception, the valid skip, the meaning of
`source_audio=on`, and the Stage 2 handoff. Remove contradictory wording that
says Tikitaka can never create any audio file; preserve the prohibition on TTS,
Q clips, CapCut, render, export, and upload artifacts.

- [ ] **Step 5: Run focused Stage 1 tests and verify GREEN**

Run the Task 3 command. Expected: all tests pass.

- [ ] **Step 6: Commit Task 3**

```powershell
git add -- skills/00-tikitaka/SKILL.md skills/00-tikitaka/shorts_script_analysis_single_source_v20260706.md skills/00-tikitaka/scripts/tikitaka_harness_runner.py tests/test_script_handoff_gate_execution_contract.py tests/test_tikitaka_production_type_contract.py
git commit -m "feat: gate Tikitaka handoff on Demucs vocals"
```

### Task 4: Stage 2 provenance and embedded-audio mute

**Files:**
- Modify: `skills/000short-production-agent/scripts/validate_stage2_tikitaka_handoff.py`
- Modify: `skills/000short-production-agent/scripts/validate_capcut_media_links.py`
- Modify: `skills/000short-production-agent/schemas/timeline_design.schema.json`
- Modify: `skills/000short-production-agent/SKILL.md`
- Modify: `skills/000short-production-agent/02_PIPELINE_RULES.md`
- Modify: `skills/000short-production-agent/03_CAPCUT_LAYOUT_CONTRACT.md`
- Modify: `tests/test_000short_tikitaka_v2_handoff_contract.py`
- Modify: `tests/test_000short_media_link_gate.py`

**Interfaces:**
- Consumes: validated source voice manifest and timeline segment provenance.
- Produces: Stage 2 entry PASS only when Q source is the full-source Demucs vocal stem; media-link PASS only when source-video embedded audio is muted.

- [ ] **Step 1: Add failing Stage 2 tests**

Update valid fixtures with a generated 48 kHz WAV and source voice manifest.
Add failures for missing manifest, raw-video `source_audio_ref`, unbound vocals
hash, no-speech skip with speaker quotes, and source-video
`audio_enabled=true` even when `caption_type=speaker_quote`.

- [ ] **Step 2: Run focused Stage 2 tests and verify RED**

```powershell
$env:PYTHONPATH='tests'
py -3 -m unittest test_000short_tikitaka_v2_handoff_contract test_000short_media_link_gate
```

Expected: new assertions fail under the old speaker-quote exception.

- [ ] **Step 3: Enforce Stage 2 source voice evidence**

Load and validate `10_analysis/source_voice_separation.json`. For each
speaker-quote segment require the stable vocals path and provenance token.
Return `source_voice_separation_status` and `source_voice_vocals_path` in the
Stage 2 validation result.

- [ ] **Step 4: Enforce source-video mute**

Remove the speaker-quote exception from `validate_capcut_media_links.py`.
Any active source-video material with `audio_enabled=true` or
`source_video_audio_enabled=true` fails
`FAIL_SOURCE_VIDEO_AUDIO_NOT_MUTED`. Speaker voice must be a separate audio
material sourced from the Q/vocals route.

- [ ] **Step 5: Update schema and production instructions**

Require `source_audio_ref` and `source_audio_provenance` for speaker-quote
segments. Document full-source Demucs provenance, Q handles of 0.1 to 0.2
seconds, short fades, Q/N non-overlap, listening checks, weak optional
enhancement only after artifacts are detected, and final loudness
normalization.

- [ ] **Step 6: Run focused Stage 2 tests and verify GREEN**

Run the Task 4 command. Expected: all tests pass.

- [ ] **Step 7: Commit Task 4**

```powershell
git add -- skills/000short-production-agent/SKILL.md skills/000short-production-agent/02_PIPELINE_RULES.md skills/000short-production-agent/03_CAPCUT_LAYOUT_CONTRACT.md skills/000short-production-agent/schemas/timeline_design.schema.json skills/000short-production-agent/scripts/validate_stage2_tikitaka_handoff.py skills/000short-production-agent/scripts/validate_capcut_media_links.py tests/test_000short_tikitaka_v2_handoff_contract.py tests/test_000short_media_link_gate.py
git commit -m "feat: require Demucs vocal provenance in Stage 2"
```

### Task 5: Final regression and skill validation

**Files:**
- Modify only if a focused verification exposes a feature-caused defect.

**Interfaces:**
- Consumes: all feature commits.
- Produces: fresh verification evidence and a clean scoped diff.

- [ ] **Step 1: Run source-voice and handoff suites**

```powershell
$env:PYTHONPATH='tests'
py -3 -m unittest test_tikitaka_source_voice_pipeline test_script_handoff_gate_execution_contract test_tikitaka_production_type_contract test_000short_tikitaka_v2_handoff_contract test_000short_media_link_gate test_11short_reporting_and_fast_mode_contract
```

Expected: all selected tests pass.

- [ ] **Step 2: Run Python syntax checks**

```powershell
py -3 -m py_compile skills/00-tikitaka/scripts/prepare_source_voice.py skills/00-tikitaka/scripts/validate_source_voice_separation.py skills/00-tikitaka/scripts/tikitaka_harness_runner.py skills/000short-production-agent/scripts/validate_stage2_tikitaka_handoff.py skills/000short-production-agent/scripts/validate_capcut_media_links.py
```

Expected: exit code 0.

- [ ] **Step 3: Run skill format validators**

```powershell
py -3 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" skills/00-tikitaka
py -3 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" skills/000short-production-agent
```

Expected: both skills validate successfully.

- [ ] **Step 4: Check scoped Git state**

```powershell
git diff --check
git status --short
git log --oneline -6
```

Expected: no whitespace errors and only approved files differ from the branch
base.

- [ ] **Step 5: Create a final verification commit only if needed**

If verification required an implementation correction, stage only that
correction and its regression test, then commit:

```powershell
git commit -m "test: verify Tikitaka Demucs-first workflow"
```
