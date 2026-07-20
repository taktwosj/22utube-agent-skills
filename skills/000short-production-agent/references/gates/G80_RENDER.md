# G80 — Render/Export and Media Integrity Verify

> Lane: `general_shorts_production`
> Owner skill: `000short-production-agent`
> Requires: G70 PASS (upload package prepared, release_allowed=false)
> Schema version: `shared-gates-separated-lanes-v2`

## Purpose

Render the final MP4 from the locked CapCut project and verify media
integrity. G80 is **separate from G90**: G80 produces the rendered file;
G90 is the final QC + release gate.

## Artifacts produced

```text
60_exports/<episode_id>.mp4
60_exports/render_evidence.json
```

## Media integrity verification

```text
rendered MP4 exists and file size > 0
ffprobe PASS
required video stream present
required audio stream present
duration matches G40 caption_lock within tolerance
no stream errors
```

## Render authorization

Render requires either:
- explicit user command, or
- requested_target=rendered pre-authorized at G00

Otherwise WAIT_USER_INPUT.

## Stop conditions

```text
FAIL_RENDER_CORRUPTION        ffprobe fails or streams missing
FAIL_RENDER_DURATION_MISMATCH duration deviates from G40 lock beyond tolerance
WAIT_USER_INPUT               render not authorized
```

## Validator contract

On PASS, `auto_advance_class=DETERMINISTIC_ONLY`. Render does NOT imply
release — release still requires G90 FINAL_QC_PASS + UPLOAD_APPROVED.
