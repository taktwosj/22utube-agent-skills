# Stage 2 - CapCut Build

Stage 2 is the Codex-owned finalization phase.

Input gate:

- `00_source\source_manifest.json` exists
- all used `source_full.mp4` files exist
- `stage1_status.json` is `PASS_SOURCE_DOWNLOADED`
- ffprobe evidence exists for each used source
- candidate `roughcut_edl.json`, `source_labels.json`, and `topic_flow.json` exist

If any source download is missing or Stage 1 says `WAIT_DOWNLOAD`, stop and
report `WAIT_DOWNLOAD`. Do not make a CapCut draft.

Build sequence:

1. verify source identity against manifest and metadata
2. verify transcript/SRT or create enough speech evidence to lock boundaries
3. create `10_analysis\speech_boundary_lock.json`
4. create `10_analysis\roughcut_edl_locked.json`
5. create `10_analysis\source_labels_locked.json`
6. cut locked clips from source media
7. verify every locked clip with ffprobe
8. run `scripts/validate_clean_base.py` against `jungchilong`
9. copy the clean `jungchilong` visual skeleton to a new episode draft
10. run post-copy episode cleanup on the copied draft
11. patch root and `Timelines/*` CapCut JSON mirrors
12. run `scripts/validate_politics_longform_draft.py` against the copied draft
13. scan cache folders, root `{GUID}` folders, and `subdraft` references
14. validate encoding, forbidden terms, safe area, T1, flow, and preview frames
15. write `90_reports\final_harness_report.json`

Only after final harness PASS may Stage 2 prepare upload text, thumbnail hooks,
or completion reporting.
