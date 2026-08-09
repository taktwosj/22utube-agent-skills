# PRE-119 handoff validation

Read this before `direct-script.md` whenever a strong PRE-119 marker or at least two
auxiliary markers are present. A strong marker locks this route even while approval is
still waiting.

Strong markers are `20_script/pre119_handoff.json`, schema
`togun-pre119-handoff-v3`, route `TOGUN_PRE119_TO_119_DIRECT`,
`EDITORIAL_OWNER=TOGUN_PRE119`, and `PRE119_SOURCE_CANDIDATE`. Auxiliary markers are
`20_script/119_final_script.md`, `10_analysis/pre119_editorial_packet.md`,
`00_source/source_packet.md`, `90_reports/source_gap_and_status.md`, and
`00_README.md`. One auxiliary marker alone does not select PRE-119.

Route locking and validation PASS are separate. After PRE-119 is selected, PASS
requires schema `togun-pre119-handoff-v3`, route
`TOGUN_PRE119_TO_119_DIRECT`, editorial owner `TOGUN_PRE119`, and source state
`PRE119_SOURCE_CANDIDATE`. A malformed identity stays on the locked PRE-119
route with `FAIL_PRE119_HANDOFF_IDENTITY`; it cannot fall through to direct-script.

Run:

```powershell
python scripts/validate_pre119_handoff.py `
  --package-root <pre119-package> `
  --approved-script-sha256 <sha256-calculated-at-user-approval> `
  --approval-evidence <user_message:id-or-runtime-approval:id>
```

The validator compares the raw-byte SHA-256 of `119_final_script.md`, the packet's
`script_lock.current_final_script_sha256`, and the externally supplied approved SHA.
Packet-internal PASS or approval fields cannot approve the packet. Absolute paths and
parent traversal are rejected. Results go only to
`90_reports/pre119_handoff_validation.json`; validation never creates
`episode_cards.json`.

After PASS, run A/D and requested B/C. Only then may the join owner compile cards from
real path, SHA-256, duration, and transcript provenance evidence.
