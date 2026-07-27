# Interim Editable CapCut Project and Sync

Use this reference when the operator says the VIDEO, TTS, captions, SFX, or BGM can be replaced later but wants an editable CapCut project now.

## Deliverable boundary

This is an **interim editable project**, not a finished episode.

- Use status `WAIT_USER_CAPCUT_CHECK` after static validation.
- List every deferred anchor explicitly.
- Do not report render, cloud upload, or final visual approval unless each was actually performed.
- Do not use unfinished assets as a reason to skip structural validation.

## Safe assembly pattern

1. Keep the root ZIP and extracted root authority unchanged.
2. Create a root contract and episode production plan.
3. Place only assets that are ready.
4. For intentionally deferred anchors, clear template segments so placeholder audio/text does not survive silently.
5. Assemble under a unique staging directory located on the same filesystem as the final CapCut root.
6. Regenerate project, draft, and timeline IDs and validate every mirror reference.
7. Update project metadata only after ID synchronization.
8. Promote staging with an atomic rename only after validation PASS.
9. Register exactly one row in `root_meta_info.json`, keeping a backup before modification.
10. Create the project ZIP from the promoted project and verify it with ZIP readback.

## Deferred-video pilot

If the downloaded source already has baked-in title/captions and the operator says the video can be changed later:

- `VIDEO`: current source media, full duration
- `A10`: original source audio, full duration
- `T1`, `T2`: approved title text, Teacher style preserved
- `STATE`, `A10_TEXT`, `A9_TEXT`, `A9`, `A11`, `A12`: clear until the clean-video/TTS pass
- Set the VIDEO segment volume to 0 when a separate A10 track carries the source audio, preventing double playback.
- Copy VIDEO and A10 files into the project `Resources/media` tree; do not leave references pointing only to episode-local absolute paths.

When clean media arrives, replace the existing VIDEO/A9/STATE/A11/A12 anchors. Do not rebuild the root structure or reuse another lane.

## Cloud identity isolation

A cloned root must not inherit the root project's cloud linkage.

- Generate a new local draft ID.
- Set the new project name and local fold/root paths.
- Clear or reset inherited cloud entry, parent, space, and user identifiers according to the local CapCut metadata contract.
- Never infer that local creation means CapCut cloud upload succeeded.
- CapCut cloud upload is a separate action and requires explicit scope.

## CapCut cloud project sync

In a CapCut-project context, `동기화`, `프로젝트 동기화`, and `캣컵 동기화` mean CapCut cloud project upload/sync. OneDrive is a separate file-handoff action and must not be substituted.

Fixed destination:

```text
User3160027826975의 공간 / MAC
```

Use Home → exact project row right-click → `업로드` → `User3160027826975의 공간` → `MAC`. Verify the breadcrumb before the final click. Ignore `TAKKTWO`.

### Generated-project cloud preflight

Run while CapCut is closed:

1. Require root and active-timeline `draft_content.json` plus `draft_info.json`; generated projects should mirror the verified current content into `draft_info.json` and `template-2.tmp`.
2. In the exact `root_meta_info.json` row, require:
   - `draft_id` equals `draft_meta_info.json:draft_id`
   - `draft_json_file` points to the existing root `draft_info.json`
   - `draft_fold_path` and `draft_cover` point to existing Mac paths
3. Preserve the top-level `draft_ids` value; do not replace it with row count or guess its counter semantics.
4. Copy required VIDEO/audio into project-local `Resources/media` and verify every live segment points there.
5. When a lane deliberately clears template VIDEO/A9/A10/A11/A12 anchors, also remove their stale combination prototype references from segment `extra_material_refs`, nested `materials.drafts`, and matching unused `subdraft` entries. Clearing visible track segments alone does not make a project cloud-safe.
6. Keep root/timeline `draft_content.json`, `draft_info.json`, `template-2.tmp`, and relevant `template.json` caches consistent; remove transient `.bak` residue.

### Post-open save normalization

CapCut editor open/close is a state-changing operation even when the operator only inspects the project.

1. Close CapCut before touching project files, then compare root/active-timeline `draft_content.json`, `draft_info.json`, and `template-2.tmp` by mtime, duration, track/material structure, and parseability. Do not assume `draft_content.json` stayed authoritative.
2. CapCut may write the actual app-saved, frame-quantized timeline to `draft_info.json`/`template-2.tmp` while leaving the pre-open 12-track build in `draft_content.json`. If the newer payload is the one that opened and played successfully, treat that app-saved payload as authority and atomically mirror it across the six root/timeline files while preserving project/draft/timeline IDs.
3. Remove CapCut-generated `.bak` files and an empty `subdraft/` only while the app is closed. Never delete a non-empty subdraft without proving it is an unused prototype.
4. Opening the project can repopulate a nonexistent Mac cache path for a live online effect. Preserve stable `resource_id`/`effect_id`, clear only the machine-local `path`, and apply the same targeted patch to root/timeline `draft_content`, `draft_info`, `template-2`, relevant `template.json`, and `attachment/patch/mini_draft.json`.
5. Rerun `validate_capcut_cloud_media.py` after every open/close repair. Once PASS, do not reopen the local project before Home-row upload.
6. After cloud-row reopen/playback verification, close CapCut, repeat this normalization for the local copy, regenerate the project ZIP from that final promoted directory, and rerun ZIP/mirror/cloud-media checks. The pre-open ZIP is no longer the final handoff.
7. CapCut may rotate `draft_meta_info.json:draft_id` after the local editor save **and rotate it again after a cloud-row reopen/save**. After every final close, read the current `draft_id`; do not reuse the pre-open builder ID from memory.
8. If `validate_id_mirrors` reports `ID_MIRROR_MISMATCH` after a successful reopen, diagnose exact keyed mismatches before broad rewriting. The common stale fields are root/timeline `attachment_editing.json → editing_draft.cover_extra_info.draft_id` and timeline `attachment/patch/mini_draft.json → mini_draft_data.header.draft_id`. Replace only the previous exact draft ID with the current `draft_meta_info.json:draft_id`, then rerun the validator.
9. Once the post-cloud ID repair, online-effect path repair, cloud-media validator, and ZIP readback all PASS, do not reopen the local project again. Regenerate the ZIP after the last repair and record that final SHA-256; any earlier ZIP hash is superseded.

## Source-order unchanged title-only project

Use this branch when the operator asks to keep the clean source exactly in order, add only T1/T2, create CapCut, and sync it.

- Canonical mode: `SOURCE_ORDER_UNCHANGED_CLEAN_ONLY`.
- Do not require an urakkai structural delta or invent a multi-scene production plan.
- Use one full-duration VIDEO segment with source and target starting at `0`, and set `volume=0`.
- Decode or copy the original source audio into one project-local A10 asset and use one full-duration A10 segment with `volume=1`; this prevents duplicate playback while preserving the operator's original sound.
- Keep only full-duration T1 and T2 text anchors. Clear `STATE`, `A10_TEXT`, `A9_TEXT`, `A9`, `A11`, and `A12` segments and scrub their stale prototype references.
- Copy VIDEO and A10 under `Resources/media`; require one VIDEO readback, one A10 readback, zero bottom-caption segments, exact T1/T2 text, and source start `0` for both media segments.
- CapCut can quantize an exact media duration to its frame grid on save. If the project visibly opens and plays and the app-saved payload preserves the full source, use the app-saved frame-quantized duration as the CapCut timeline authority; keep the clean-source receipt's measured media duration separately.
- A Home/cloud row duration such as `00:09` is rounded UI metadata, not proof of the measured source duration. Preserve measured media duration, app-saved timeline duration, and displayed cloud duration as separate evidence.
- Cloud completion still requires the exact `User3160027826975의 공간/MAC` row readback and cloud reopen/playback; `TAKKTWO` remains out of scope.

### Upload warnings and deterministic diagnosis

Before opening CapCut, run:

```bash
python3 scripts/validate_capcut_cloud_media.py "/absolute/path/to/project"
```

The probe must inspect every live segment `material_id` and `extra_material_refs`, not only VIDEO/A9/A10. Root fixtures can leave live white-card photos, screen effects, animations, or template cache paths outside the obvious media tracks.

- `프로젝트를 사용할 수 없음` or abnormal path: stop retrying, close CapCut, and repair missing `draft_info.json` or mismatched/nonexistent `root_meta_info.json` path and ID fields.
- `미디어 경로 손실`: never press `업로드` to force past the warning. Choose `미디어 확인`. CapCut may open the editor without showing a filename list; that does **not** prove the warning is harmless. Close CapCut and enumerate all live and unreferenced material paths across parseable root/timeline/cache JSON files.
- A live photo/background must be copied into project-local `Resources/media` and its path rewritten to the draft placeholder. Do not leave a Windows `onlineMaterial` cache path just because the preview currently renders.
- For a live online effect that has a stable `resource_id`/`effect_id`, preserve those IDs and clear only the nonexistent machine-local cache `path`. Reopen the cloud project later to verify the effect. If the effect has no portable identity, remove or replace it explicitly rather than inventing a local cache file.
- Remove unreferenced Windows animation/effect materials and the deferred-anchor materials they belonged to. Clearing visible segments alone is insufficient.
- Apply the repair to root and active-timeline `draft_content.json`, `draft_info.json`, `template-2.tmp`, and parseable CapCut caches that carry the same material IDs. Preserve CapCut-specific `template.json` structure; patch matching material fields in place rather than replacing the whole file with `draft_content`.
- Remove transient `.bak` files and empty/non-authoritative `subdraft` residue while CapCut is closed, then rerun the validator until Windows path count, missing live media count, and unreferenced missing path count are all zero.
- Do not open the repaired local project before retrying the upload: CapCut may regenerate stale caches. Upload directly from Home → exact project row.
- If the final upload helper becomes a blank/stale CEF window after the click, wait a reasonable upload interval but do not infer success or failure from the helper itself. Dismiss only the stale helper, explicitly select `User3160027826975의 공간`, open `MAC`, and use the visible project row as the authority.
- Do not report sync complete because the picker closed, a folder timestamp changed, or storage usage increased. Open `User3160027826975의 공간/MAC` and read back the exact cloud project row (name, size, duration, type, latest time), then reopen that cloud row and verify the first structural transitions, titles, TTS, and absence of offline media.

## Required readback

Before reporting completion, independently read the promoted project and check:

- T1/T2 text and timeranges, resolving roles from the root contract, segment material IDs, or actual text content rather than a remembered numeric track index
- VIDEO and A10 timeranges
- project-internal media files exist
- intentionally deferred tracks contain zero segments
- root/timeline `draft_content.json`, `draft_info.json`, and `template-2.tmp` still parse and remain semantically aligned after CapCut opens/saves the project
- stale missing-media filenames are absent across project JSON/cache mirrors
- draft name and duration
- new local cloud entry state
- ID mirror validator PASS
- exactly one `root_meta_info.json` registration
- project ZIP `testzip()` PASS
- full skill test suite PASS
- cloud row inside `User3160027826975의 공간/MAC` shows the exact name, size, duration, type=`프로젝트`, and latest time

## OneDrive handoff sync

Sync a compact handoff, not an unexplained project directory.

Recommended layout:

```text
capcut/
  project.zip
  deterministic_build_script.py
decisions/
  HUMAN_DESIGN_BLUEPRINT.md
  production_plan.json
contracts/
  root_contract.json
  asset_manifest.json
reports/
  build_receipt.json
  FINAL_REPORT.md
  source-analysis.md
workflow/
  state.json
sync_manifest.json
```

The sync manifest records path, byte count, source hash, destination hash, and match status. Perform a fresh destination readback after copy. A successful copy command alone is not proof of synchronization.

## Root 01 field note

The known `shrt white` root has a 12-track root and active timeline plus several one-track subdrafts. Apply root-layout operations only to documents that contain contracted anchor IDs. Do not reject or rewrite a one-track subdraft merely because it has fewer than 12 tracks.

However, cloud-upload media validation is a separate gate: if `미디어 확인` identifies a stale Windows sample inside nested `materials.drafts` or its matching one-track `subdraft`, and that prototype belongs to an intentionally cleared/deferred anchor, remove the unused prototype, matching `extra_material_refs`, and its unused subdraft. Preserve unrelated live prototypes. Recheck every root/timeline/cache mirror for the exact missing filename before retrying upload.
