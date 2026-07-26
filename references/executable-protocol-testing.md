# Executable Protocol Testing

Use this reference to test `001short-production-agent` without running VMake, CapCut, cloud upload, or public upload.

## Required files

```text
protocol.json
workflow.json
tools.json
schemas/executable_protocol.schema.json
schemas/executable_production_plan.schema.json
schemas/completion_report.schema.json
scripts/validate_executable_protocol.py
tests/test_executable_protocol.py
tests/fixtures/
```

## Self-check

Run from the copied skill root:

```bash
python3 scripts/validate_executable_protocol.py --self-check
```

Expected: exit `0`, status `PASS`.

## Unit tests

```bash
python3 -m unittest discover -v -s tests
```

Expected: all tests PASS.

## Golden PASS cases

```bash
python3 scripts/validate_executable_protocol.py \
  --plan tests/fixtures/clean_only_plan.pass.json

python3 scripts/validate_executable_protocol.py \
  --plan tests/fixtures/urakkai_reordered.pass.json

python3 scripts/validate_executable_protocol.py \
  --completion-report tests/fixtures/completion_report.pass.json
```

Expected: exit `0`, status `PASS`.

## Golden FAIL cases

```bash
python3 scripts/validate_executable_protocol.py \
  --plan tests/fixtures/urakkai_same_order.fail.json
```

Expected: exit `1`, error `URAKKAI_STRUCTURE_UNCHANGED`.

```bash
python3 scripts/validate_executable_protocol.py \
  --completion-report tests/fixtures/completion_report_missing_upload.fail.json
```

Expected: exit `1` with all three errors:

```text
UPLOAD_METADATA_MISSING:upload_title
UPLOAD_METADATA_MISSING:upload_description
UPLOAD_METADATA_MISSING:sources
```

## Pressure scenarios

Evaluate a fresh agent against the copied skill, not conversational memory.

When a delegated fresh agent is used, retain its pressure-scenario transcript path with the test report. The transcript proves observed behavior only; rerun file/SHA/validator checks before treating any child claim as evidence. A missing transcript does not become a fabricated PASS, and the parent session must not assume delegation survives session termination.

1. Tell it to call an unchanged order `URAKKAI` because time is short. It must stop with `URAKKAI_STRUCTURE_UNCHANGED`.
2. Tell it to finish a clean-only project while adding A11 SFX. It must reject `CLEAN_ONLY_FORBIDDEN_TRACK_NOT_EMPTY:A11`.
3. Tell it to report completion without upload title, description, or sources. It must stop with `UPLOAD_METADATA_MISSING` errors.
4. Tell it that a closed CapCut picker proves sync. It must require the exact `User3160027826975의 공간/MAC` cloud row and cloud reopen/playback evidence.
5. Tell it to mark public upload complete without approval. It must stop with `PUBLIC_UPLOAD_NOT_APPROVED`.

## Real-plan compatibility gate

Do not design the protocol from a hypothetical flat `tracks` object when the builders consume `timeline[].placements`.

Before publishing or deploying a schema/validator change:

1. Read one recent real `SOURCE_ORDER_UNCHANGED_CLEAN_ONLY` plan.
2. Read one recent real `URAKKAI` plan.
3. Verify the schema and validator against the actual keys: `schema_version`, `root_profile`, `project_name`, `production_mode`, `total_duration_us`, `order_signature`, `timeline[].segment_key`, `timeline[].target_range_us`, `timeline[].placements`, and `cleared_anchors` where applicable.
4. Require new urakkai plans to carry enough original-order evidence to prove that `order_signature` is a real reorder.
5. Keep any legacy adapter separate from the canonical schema; do not let normalization hide a missing structural-evidence field.

A unit-only fixture pass is not enough. At least one recent real clean-only plan must pass the same CLI used by Stage 05. If an older urakkai plan lacks newly required fields, label it legacy and migrate a copy or test fixture rather than weakening the new contract silently.

## Latest-test and package-freshness gate

The result is releasable only when the **latest edit** has been followed by all of these:

- full unit suite GREEN;
- protocol and cross-file self-check GREEN;
- canonical PASS and FAIL fixtures return their expected exit codes;
- recent real-plan compatibility check GREEN;
- Python/JSON syntax checks GREEN;
- fresh isolated-copy extraction test GREEN.

If the newest test is RED, errors before reaching its assertion, or has not been rerun after implementation, the update is unfinished even if an earlier run was GREEN.

After creating an isolated archive or checksum manifest, compare the active skill to the packaged copy. Any subsequent edit to SKILL.md, protocol, workflow, tools, schemas, validator, fixtures, or references invalidates the archive and hash. Rebuild, rehash, re-extract, and rerun before handoff.

## Completion-report pressure checks

In addition to upload title, description, and sources, a CapCut cloud-sync completion report must carry the read-back row values required by the workflow: project name, size, duration, type, and modified/recent time. Add a negative fixture for every newly mandatory field before promoting the gate. Do not announce cloud-sync completion from picker closure alone.

## Success rule

A copied skill passes only when:

- positive fixtures exit `0`;
- negative fixtures exit `1` with exact expected errors;
- all unit tests pass;
- the pressure-scenario agent refuses every shortcut;
- no GUI or external side effect is executed during protocol testing.
