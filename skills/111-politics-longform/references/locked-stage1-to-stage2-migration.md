# Locked Stage 1 → Stage 2 migration

Use this reference when an approved political-longform episode passes its Stage 1
gate but fails the current Stage 2 preassembly contract.

## Safety invariant

The approved Stage 1 bytes remain the authority. Do not repair a legacy contract
mismatch by silently changing `design_blueprint_approved.json`, signed review
packets, locked EDLs, or locked clip manifests in place.

## Diagnostic sequence

1. Snapshot SHA-256 for every path in `design_lock_manifest.json.required_files`.
2. Run each validator separately and retain full JSON output:
   - Stage 1 lock gate
   - external-review signature/receipt gate
   - preassembly gate
3. Recompute the locked hashes after every allegedly read-only validator.
4. Classify failures rather than collapsing them into one label:
   - immutable review metadata mismatch
   - missing explicit approval decision fields
   - portable media-path incompatibility
   - missing media or clip hash/probe mismatch
   - template/local-base mismatch
   - validator side effect on a locked report

A Stage 1 PASS never implies preassembly PASS.

## Non-destructive compatibility pattern

Create a local, disposable runtime copy outside the synchronized production tree.
The adapter may normalize only what the current runtime contract needs:

- restore immutable metadata from the still-valid signed review packet;
- retain user-approved final visible lines;
- add explicit `decision`/`decision_reason` fields only in the runtime copy;
- convert placeholder clip paths to media-root-relative paths;
- verify every physical clip against its locked SHA-256 and ffprobe evidence;
- run current preassembly against the runtime copy.

Keep a machine-readable compatibility report containing:

- source episode and original design-lock hash;
- pre/post hashes for all locked source files;
- exact normalized fields;
- external signature validation result;
- runtime preassembly result;
- `source_stage1_mutated: false`.

Do not copy normalized runtime inputs back over the Stage 1 lock.

## Validator side-effect pitfall

Some validation CLIs serialize their computed gate back into a report JSON. Before
running one against a lock:

- inspect whether the command writes;
- prefer a temporary copy;
- snapshot the target report bytes first;
- distinguish byte drift from semantic signature validity, but never call byte
  drift a clean lock match.

If a locked report is unexpectedly rewritten, stop production, preserve the
original lock manifest, search backups/temp audit copies/version history, and
record expected hash, actual hash, signed receipt result, and cause. Do not forge
or casually replace the old hash.

## Recovery technique

On Windows, Volume Shadow Copy can be used as a last-resort historical source when
an important pre-write backup is unavailable. Create the link through Python's
`os.symlink()` with an exact target of
`\\?\GLOBALROOT\Device\HarddiskVolumeShadowCopyN\`; shell quoting and MSYS path
conversion can corrupt this special path. Treat a shadow copy as read-only and
remove the temporary link after investigation.

## CapCut output separation

- Restore/verify the locked template archive before assembly.
- Use a new deterministic project name; do not reuse or delete an unknown draft.
- Back up `root_meta_info.json` before registration.
- Keep locked historical `50_capcut_project` snapshots untouched.
- Store new snapshots, manifests, and harness reports in an additive Stage 2
  output area.
- Report separately: folder created, registry entry written, harness passed,
  render completed, upload completed.

## Completion gate

Do not claim Stage 2 completion until all are real and verified:

1. compatibility/runtime test GREEN;
2. current preassembly PASS;
3. native CapCut project created and registered;
4. root and timeline mirrors byte-consistent;
5. audio/gap/frame/cleanup harnesses PASS;
6. additive final design, assembly, and upload-package artifacts exist;
7. render/upload status stated separately and honestly.
