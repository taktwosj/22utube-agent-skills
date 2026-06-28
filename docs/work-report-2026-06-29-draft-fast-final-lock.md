# Work Report: DRAFT_FAST / FINAL_LOCK Gate Cleanup

Date: 2026-06-29

Repo: `https://github.com/taktwosj/22utube-agent-skills.git`

Implementation commit: `3ca5107 Split draft fast and final lock gates`

## Result

`000short-production-agent` was updated so the Shorts factory now has a clear
split between fast review drafts and final upload-ready production.

- `DRAFT_FAST` is the default mode.
- `FINAL_LOCK` runs only when the user explicitly requests final upload
  readiness.
- Git remains the official skill source.
- Runtime targets on this Windows machine were updated and verified for Codex,
  Claude, and Hermes.

## Problems Found

Parallel agent review found these main conflicts:

- `SCRIPT_LOCK` rules were blocking ordinary CapCut draft creation.
- `final_report.md` was used both before and after CapCut, creating ambiguity.
- `upload_ready` could be interpreted as technical PASS without user approval
  and rights-risk confirmation.
- `일반템플릿` remained in several rules even though the current official
  template manifest has only `black` and `insta white`.
- Korean text corruption was documented, but not hard-failed by a post-CapCut
  validator.

## Changes Made In Git

Changed files:

- `skills/000short-production-agent/SKILL.md`
- `skills/000short-production-agent/03_CAPCUT_LAYOUT_CONTRACT.md`
- `skills/000short-production-agent/04_HARNESS_REQUIREMENTS.md`
- `skills/000short-production-agent/scripts/validate_capcut_timeline_order.py`
- `skills/000short-production-agent/scripts/validate_production_gate.py`
- `tests/test_11short_reporting_and_fast_mode_contract.py`

Main rule changes:

- `DRAFT_FAST` may create a reviewable CapCut draft without claiming
  `SCRIPT_LOCK`, production `PASS`, `FINAL`, or `upload_ready`.
- `FINAL_LOCK` owns writer/persona gates, `SCRIPT_LOCK`,
  `production_gate_result.json`, `post_capcut_timeline_gate_result.json`,
  `--stage all`, upload copy, and upload readiness.
- `pre_capcut_script_package_status` replaces the old
  `final_report_before_capcut` gate.
- `technical_ready=true` is separated from `upload_ready=YES`.
- `upload_ready=YES` still requires user approval and source/remake risk check.
- Official template defaults are now only `black` and `insta white`.
- The post-CapCut validator now fails `KOREAN_TEXT_FAST_GATE` when actual
  `draft_content.json` text contains mojibake patterns such as `????` or `�`.
- The report contract now requires `캣컵복사하기` as the final CapCut copy block.

## Local Runtime Harness Patch

The active Shorts runtime harness is outside this Git repo:

`%UTUBE_ROOT%\11short\shorts_remake_harness.py`

It was updated locally to:

- run the same `KOREAN_TEXT_FAST_GATE` scan on CapCut draft text materials
- reject the legacy spaced label `캣컵 복사하기`
- require the current `캣컵복사하기` fenced block in `reports/final_report.md`

This harness file is OneDrive production tooling, not part of the
`22utube-agent-skills` Git repo.

## Verification

Commands run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile skills\000short-production-agent\scripts\validate_capcut_timeline_order.py skills\000short-production-agent\scripts\validate_production_gate.py
python -m py_compile "%UTUBE_ROOT%\11short\shorts_remake_harness.py"
powershell -ExecutionPolicy Bypass -File scripts\update.ps1 -Target all -Strict
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Target all -Strict
```

Results:

```text
Ran 13 tests ... OK
VERIFY PASS warnings=0
Codex marker commit: 3ca5107
Claude marker commit: 3ca5107
Hermes marker commit: 3ca5107
git status: clean
```

## Current Operating Rule

Use this wording when handing work to another agent:

```text
Default Shorts factory work is DRAFT_FAST.
DRAFT_FAST creates a reviewable CapCut draft and runs only fast draft checks.
It must not claim SCRIPT_LOCK, production PASS, FINAL, or upload_ready.

FINAL_LOCK must be explicitly requested.
FINAL_LOCK runs writer/persona gates, SCRIPT_LOCK, production gate, post-CapCut
gate, capcut/all harness, visual QA, copy-ready upload package, and upload_ready
approval/risk checks.
```
