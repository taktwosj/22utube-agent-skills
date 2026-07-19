# Stage 2 core CapCut assembly

Use this reference when a locked political-longform episode is approved, the user
wants the native CapCut project now, and optional thumbnail/upload metadata is not
part of the current scope.

## Core completion contract

A core assembly is complete only when all are true:

1. a new native CapCut project folder exists;
2. `root_meta_info.json` contains the new project;
3. the built-content gate reports no timeline gaps/overlaps;
4. canvas, clip count, caption count, and duration match the runtime lock;
5. separate audio tracks/materials are zero unless explicitly requested;
6. every root and `Timelines/*` content mirror is byte-identical;
7. all referenced video media exists;
8. no build-staging directory remains.

Render complete and upload complete remain separate states. Never infer them
from JSON registration.

## Exact microsecond timeline normalization

Legacy EDLs often store decimal seconds that produce one-microsecond gaps or
ends. Normalize only in the disposable Stage 2 runtime copy:

- convert `content_start_sec` to integer microseconds;
- walk clips in approved order with one cumulative integer cursor;
- set each `timeline_start_sec` from the cursor;
- advance by `round(duration_sec * 1_000_000)`;
- set `timeline_end_sec` from the new cursor;
- derive source labels from those exact EDL starts/ends;
- force commentary and flow ranges to be continuous and make the final range end
  exactly at the project end;
- update runtime-only hashes/decisions that legitimately cover normalized files.

Do not copy normalized timing back over the Stage 1 lock.

For source captions, build runtime SRTs per source from approved caption text and
provenance. Clamp each cue to its locked clip source bounds. Quantize cue starts
upward and cue ends downward to milliseconds so an SRT cue cannot straddle an
exact clip boundary. Rebuild caption rows through the current provenance
contract rather than hand-adjusting visible timeline text.

## Windows path-length rule

Do not include a long project name in the temporary copy directory. A staging
name such as:

```text
._b-{UUID}
```

keeps deep `Timelines/.../common_attachment/...` paths under Windows limits.
The `finally` cleanup guard must match the same short prefix and verify that the
resolved staging parent is the expected CapCut root before deleting it.

A copy error that names deep attachment files can be a destination path-length
failure, not missing template files. Verify the template archive/base, then
compare full destination lengths before attempting content repair.

## Optional output harness separation

If render/upload is explicitly out of scope, missing thumbnail canvas, people,
hooks, description, hashtags, or YouTube API profile must not roll back a valid
native CapCut assembly. Record:

```json
{
  "status": "PASS_ASSEMBLY",
  "final_output_harness": "DEFERRED_CORE_ASSEMBLY_ONLY",
  "final_gate": "BLOCKED",
  "upload_ready": false
}
```

This is not permission to skip core media/timeline checks. Run the full output
harness later when the user requests upload preparation.

## Visible-term validation

Ban internal tokens such as `M1-`, `roughcut`, `edl`, mojibake, and U+FFFD.
Do not blacklist an ordinary Korean word globally. For example, `진입` is valid
inside approved viewer-facing copy such as `마지막 쟁점 진입`; reject it only when
it exposes an internal workflow label.

## Focused verification

When there is no canonical suite, create an OS-safe temporary script with
`tempfile` under `%TEMP%` and prefix `hermes-verify-`. Verify both the changed
builder behavior and produced artifacts, run it with the project Python, and
remove it even on failure. Report this explicitly as `PASS_AD_HOC`, never as
suite green.

Minimum assertions per project:

- project folder and registry entry;
- current built-content gate PASS;
- core-mode manifest fields;
- exact canvas/count/duration;
- zero separate audio;
- expected mirror count and one common SHA-256;
- assembly package PASS and upload package blocked;
- approved Shorts IDs unchanged;
- no staging leftovers.
