# G70 — Upload and Thumbnail Package Preparation

> Lane: `general_shorts_production`
> Owner skill: `000short-production-agent`
> Requires: G60.USER PASS (user visual gate)
> Schema version: `shared-gates-separated-lanes-v2`

## Purpose

Prepare the upload metadata package and thumbnail. The package is
prepared, NOT uploaded. `release_allowed=false` at all times in G70.

## Artifacts produced

```text
70_upload/upload_package.json
70_upload/thumbnail.<ext>
70_upload/upload_metadata.json
```

## Hard rule

```text
release_allowed = false
actual upload = WAIT_UPLOAD_APPROVAL
```

G70 PASS only means the package is ready. Actual upload requires a
separate user approval at G90.

## Validator contract

Checks:
- upload_package present
- thumbnail exists and is non-empty
- release_allowed=false recorded in the state projection
- no actual upload artifact (no .uploaded marker)

On PASS, `auto_advance_class=DETERMINISTIC_ONLY`.
