# top5isu Standalone Report Contract

## 조립도 보고서

After CapCut assembly, write exactly one final assembly report at:

```text
90_reports/assembly_report.md
```

Required shape:

```text
# 조립도 보고서

## 프로젝트 실체
CapCut 프로젝트명: <exact-project-name>
CapCut 프로젝트 폴더명: <exact-project-name>
CapCut 프로젝트 경로: <actual-local-path>/<exact-project-name>
CapCut 프로젝트 파일 이름: <exact-project-name>

## 설계 반영 및 검증
profile: top5|gunlimbo
stage: CAPCUT_PROJECT|FINAL_REPORT
blueprint: PASS|FAIL|WAIT
contract: PASS|FAIL|WAIT
template_package: PASS|FAIL|WAIT
track_mapping: PASS|FAIL|WAIT
capcut_draft: PASS|PASS_MANUAL_EDIT_EXPECTED|FAIL|WAIT
visual_playback_review: PASS|FAIL|WAIT
export_loudness: PASS|NOT_APPLICABLE|WAIT
upload_ready: no unless explicitly approved

## 사용자 수동 편집
manual_edit_policy=MANUAL_EDIT_EXPECTED
manual_edit_difference_is_failure=false
current_draft_reread_required=true

## 캣컵복사하기
<exact-project-name>
```

The last non-empty line must be the exact CapCut project file/folder name. The
reported local project path must exist and contain `draft_content.json`. Run
`scripts/validate_top5isu_assembly_report.py` with that expected name.

## Manual Edit Re-entry

The operator opening CapCut and editing duration, tracks, text, cuts, timing, or
media is normal and must not be reported as a problem merely because it differs
from the generated snapshot. Re-read current `draft_content.json` and current
project metadata. Use manual-edit validation and describe current state. Do not
restore old values unless the operator explicitly asks.

## Final Lock

`FINAL_LOCK` requires every applicable gate to pass. A local project file does
not authorize upload, publishing, scheduling, or deletion. Upload remains an
explicit operator decision.
