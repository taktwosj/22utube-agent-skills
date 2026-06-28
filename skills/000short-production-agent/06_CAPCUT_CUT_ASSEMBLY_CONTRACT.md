# CapCut Cut Assembly Contract

For the full shared contract, read:

```text
$env:UTUBE_ROOT\11short\CAPCUT_CUT_ASSEMBLY_CONTRACT.md
```

Mandatory summary:

- Do not create exact split-only video clips for 11short CapCut drafts.
- Separate `source_order` from `timeline_order`.
- Generate `cut_manifest.json` before CapCut assembly.
- Export handle clips with `media_start_ms/media_end_ms` and initially trim them
  to `visible_start_ms/visible_end_ms` in CapCut.
- Default handles are 2000 ms before and 2000 ms after, clamped to source bounds.
- Required proof: `clips/S*_handle_*.mp4`, `proof/contact_sheet.jpg`,
  `proof/clip_durations.csv`, `proof/timeline_order.txt`, and
  `proof/capcut_assembly_report.json`.
- `handle_extendable=true` and independent clip verification are required before
  reporting CapCut project creation PASS.
- Missing proof or exact split-only clips means FAIL, not “completed”.
