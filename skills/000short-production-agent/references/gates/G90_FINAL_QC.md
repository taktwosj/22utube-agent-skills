# G90 — Final Rendered Video QC and Release Gate

> Lane: `general_shorts_production`
> Owner skill: `000short-production-agent`
> Requires: G80 PASS (rendered MP4 + media integrity)
> Schema version: `shared-gates-separated-lanes-v2`

## Purpose

Final QC on the rendered video, then the release gate. **Separate from
G80.** A content problem found at G90 rewinds to the owning gate; never
patch G90 output only.

## Release requires both

```text
FINAL_QC_PASS   (user final QC, recorded as ledger event)
UPLOAD_APPROVED (separate user approval event)
```

Either alone does NOT release. `release_allowed` flips to true only when
both are present in the ledger, with FINAL_QC_PASS preceding
UPLOAD_APPROVED (RW-P03-02).

## Actual upload

Actual upload is `WAIT_UPLOAD_APPROVAL`. Even at G90 PASS the lane does
NOT upload automatically. The user must explicitly approve.

## Rewind matrix (V2 design section 19)

```text
source identity changes         → G00 (return to 00-tikitaka)
selected source range changes   → G10/G20 with user confirmation
governing thesis changes        → G10 (return to 00-tikitaka)
creative script/order change    → G20 (return to 00-tikitaka)
generated audio duration change → G30 then G40
caption text/timing change      → G40
track placement/order issue     → G50
missing/incorrect CapCut asset  → G60
structural contamination        → discard target build, rerun G60 clean
visual issue without data change → G60 rework
render corruption               → G80
final content problem           → rewind to owning gate
upload metadata only            → G70
actual upload approval missing  → G90 WAIT_UPLOAD_APPROVAL
```

Every rewind appends `LOCK_INVALIDATED` to the ledger with reason and
affected SHA values.

## Stop conditions

```text
WAIT_UPLOAD_APPROVAL          user has not explicitly approved upload
WAIT_USER_INPUT               final QC pending
REWORK_REQUIRED               content problem found, rewind to owning gate
```

## Validator contract

On PASS (both FINAL_QC_PASS and UPLOAD_APPROVED recorded, in order):
`auto_advance_class=NONE`. No further automatic work. The episode is
released only when the user explicitly commands upload.
