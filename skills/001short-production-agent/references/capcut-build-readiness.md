# CapCut Build Readiness and Stall Triage

Use this before diagnosing a Stage 08 build that appears to run for many minutes without producing an editable project.

## Core diagnosis

Separate **media complexity** from **control-plane readiness**. Adding a source video, source-audio cuts, and captions increases assembly work, but a 30-minute no-project condition usually means the builder was never reached or repeated a fast failure. Read the first error and canonical state before changing media.

## Readiness gate

Before invoking the builder, verify all of the following in one probe and report the first failing layer:

1. canonical state exists at the single path declared by `workflow.json`;
2. current stage and entry status are accepted by `validate_stage.py`;
3. source identity, approved timeline, design handoff, and design-lock evidence exist and their hashes agree;
4. clean visual media, manifest, and receipt agree with the original source and approved evidence;
5. audio lock, caption lock, final SRT, duration, and cue list agree;
6. build manifest binds the same episode, source, clean visual, and root-template hash;
7. the exact immutable `shrt_white_base_v2` root ZIP exists locally and passes the SHA declared by its root and layout contracts;
8. edit-lock ownership is valid and CapCut is closed;
9. required track roles are discoverable from the template;
10. the final target path does not contain an abandoned partial build.

Do not spend time generating downstream evidence while an earlier readiness layer is missing.

## State-machine consistency

Treat these as one contract:

- `workflow.json` canonical `runtime.state_path`;
- every builder state write;
- `validate_stage.py` entry statuses;
- Stage 08 pass status and Stage 09 first status.

A builder must write to the canonical state path. The written stage/status must be accepted by the next validator. Add an integration test that executes the transition rather than testing workflow JSON in isolation.

## Transactional project creation

Never copy an unvalidated working project directly to the final CapCut target.

1. extract the pinned template into an isolated authority root;
2. clone to a unique staging project;
3. replace media, sync IDs/mirrors, and write contracts in staging;
4. run build-input, static-project, and postbuild validators;
5. on any exception, remove only the staging project;
6. after PASS, atomically promote staging to the final target;
7. register the final project exactly once.

This prevents a mid-build exception from leaving a folder that makes every retry fail with `LOCAL_CAPCUT_PROJECT_EXISTS`.

## Template and track rules

- The Git skill package may intentionally exclude CapCut ZIP/media assets. Skill installation is not template installation. Verify the external template asset before Stage 01-07 work.
- Resolve tracks by stable role/name plus structural checks. Do not depend on raw numeric indexes such as `tracks[9]`; template reordering must fail with a clear track-mapping error, not mutate the wrong lane.
- Keep this skill's `shrt_white_base_v2` authority independent. Do not borrow another production lane's template or validator to make a build pass.

## Required integration test

Maintain at least one portable fixture that proves:

```text
locked source + clean visual + audio/SRT + evidence + pinned miniature template
  -> staging build
  -> validators PASS
  -> atomic final project
  -> canonical state advances to the first Stage 09 status
```

Contract-only and parallelism-only tests do not prove that a project can be created.

## Operator-facing review

When comparing this lane with a working builder, lead with:

1. whether the media assembly itself is harder;
2. whether a one-command runner/bootstrap exists;
3. whether the required external template is present;
4. whether state transitions agree;
5. whether failed builds are transactional and retry-safe.

Avoid presenting twenty checks as twenty unrelated problems. Identify the first broken boundary and distinguish confirmed code defects from hypotheses that require the Windows traceback/state file.
