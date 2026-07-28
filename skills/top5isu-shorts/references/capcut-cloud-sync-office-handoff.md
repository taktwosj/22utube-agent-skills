# CapCut Cloud Sync for Office Handoff

Use this after a verified local TOP5ISU CapCut project exists. The operator has standing approval to sync every completed project to the fixed destination below; do not ask again for routine cloud handoff.

## Fixed destination for this operator

```text
TAKKTWO / macmini
```

- In a CapCut-project conversation, the operator's words `동기화`, `프로젝트 동기화`, or `캣컵 동기화` mean **CapCut cloud project upload/sync**, not OneDrive file copying. Do not substitute an OneDrive handoff and call it synchronized.
- `TAKKTWO` is the fixed account space for this workflow. Do not inspect, select, compare, recommend, or upload to another account space.
- Do not reinterpret `TAKKTWO` as an unshared or wrong account. It is the operator's intended CapCut account space.
- Keep CapCut cloud upload distinct from YouTube upload, render, export, or Trend Hunter server delivery.

## Operator manual upload and stop override

- If the operator says `내가 올렸어`, treat cloud upload as operator-performed. Immediately stop every upload dialog, retry, duplicate replacement, cloud-ID repair, and GUI click. Do not overwrite or re-upload the operator's copy.
- If the operator says `그만해`, stop all CapCut GUI actions and project-file mutations immediately. Preserve the current local project and reports as-is.
- After either phrase, cloud row readback or metadata reconciliation is allowed only when the operator explicitly asks for verification. Until then record `capcut_cloud_upload_performed_by=operator` and `cloud_readback=NOT_REQUESTED`; never infer a verified cloud name, size, duration, or time.

## Cloud-upload preflight

Run this before opening the upload destination picker, especially for projects cloned or generated outside CapCut.

1. Close CapCut before changing project files or `root_meta_info.json`.
2. Verify the project has all three canonical content mirrors at both root and active timeline where applicable:
   - `draft_content.json`
   - `draft_info.json`
   - `template-2.tmp`
3. `draft_info.json` must contain the current project content, not merely metadata. For a generated project, make it a byte or semantic mirror of the verified `draft_content.json` at root and active timeline.
4. In `root_meta_info.json`, the exact project row must:
   - preserve the complete local-project row shape; never replace it with a minimal custom dictionary
   - use the same `draft_id` as `draft_meta_info.json`
   - point `draft_json_file` to the project's existing root `draft_info.json`
   - point `draft_cover` to the existing project cover
   - point `draft_fold_path` to the real Mac project folder
   - retain authoritative Home-display fields such as `draft_timeline_materials_size` and standard local-project flags
   - avoid inheriting a superseded project's cloud entry/space/user IDs
   - generated clones must clear inherited cloud identity before first app launch: `cloud_draft_cover=""`, `cloud_draft_sync=false`, completed/entry/modified/space/user IDs set to neutral local sentinels, and parent entry set to `-1`
   - calculate `draft_timeline_materials_size` from the current project-local active media; never preserve the template prototype's old size
   If inherited cloud IDs or a prototype size remain, stop at `FAIL_INHERITED_CLOUD_IDENTITY` before opening an upload helper. A blank/stale upload helper after a generated clone is evidence to re-check these fields, not permission to retry blindly.
   If the row is structurally incomplete, Home can show `0.0B` even when the project files are intact; repair the row and verify the displayed size before upload.
5. Never guess or recalculate the top-level `draft_ids` field. Preserve its existing semantics/value unless an authoritative CapCut workflow explicitly changes it.
6. Verify every local VIDEO/audio material needed on the office machine is copied under the project folder and referenced by that project-local path.
7. For lanes that intentionally defer A9/A11/A12 or other tracks, clear both the track segments and their stale combination-prototype references:
   - remove unused IDs from segment `extra_material_refs`
   - remove the corresponding unused entries in `materials.drafts`
   - remove stale unused `subdraft/` prototypes
   - keep root/timeline `draft_content.json`, `draft_info.json`, `template-2.tmp`, and `template.json` caches consistent
8. Remove transient `.bak` files from the finished generated project before upload and confirm the project parses cleanly.
9. Run the cloud-media validator across every live material and parseable cache. For online transitions/effects, preserve portable resource/effect IDs but clear only machine-local cache paths. Remove inherited `subdraft/` residue only after proving its ID is absent from live segment refs and `materials.drafts`; keep a backup outside the live project.
10. After any app open/playback, close CapCut and reselect draft authority by validity, not mtime. Prefer root `draft_content.json`; reject a newer mirror if it contains `##_draftpath_placeholder_*_##`, missing episode media, stale stock identity, or wrong image/material counts. Resynchronize only full-content mirrors and rerun both draft and cloud-media validators.

## UI sequence

1. Open CapCut only after the local project and preflight validators PASS; routine cloud handoff to `TAKKTWO / macmini` has standing approval.
2. Preferred fixed-destination flow: open `공간`, explicitly select `TAKKTWO`, then open `macmini` before choosing the local-project upload action.
3. If the current CapCut build exposes upload only from the exact Home project row, right-click that row and choose `업로드` **only when an explicit destination dialog appears**. If it uploads immediately through an inherited cloud association, stop and use the preferred space-first flow instead.
4. In the destination dialog choose `TAKKTWO`.
5. Choose `macmini`.
6. Before the final click, verify the breadcrumb exactly reads:

   ```text
   CapCut / TAKKTWO / macmini
   ```

7. Click the enabled `업로드` button.
8. If CapCut warns that an existing project/item is already present and asks whether to upload again, replace, or continue, choose the affirmative `예/계속/다시 업로드` action for the latest verified project. This operator has explicitly approved that duplicate-safe continuation.

## Upload-blocking warnings and recovery

### `프로젝트를 사용할 수 없음` / abnormal project path

Do not keep retrying the upload button. Close CapCut and inspect the generated project contract first. The common durable causes are a missing root/timeline `draft_info.json`, a `root_meta_info.json` row whose `draft_json_file` points nowhere, or a root-row `draft_id` that does not match `draft_meta_info.json`. Repair those fields atomically while CapCut is closed, reopen Home, and retry.

### `미디어 경로 손실`

Do not immediately choose the warning's affirmative upload button. Choose `미디어 확인` first and read the exact missing filenames.

- If the item is required by a live segment, reconnect it to a project-local copy and mirror the new path across canonical root/timeline documents.
- If it is a deliberately deferred or unused Windows prototype, remove it rather than reconnecting it. Check nested `materials.drafts`, matching `subdraft/<id>`, and segment `extra_material_refs`; clearing only the visible track is insufficient because CapCut scans unused nested prototype materials during cloud upload.
- Search all project JSON/cache mirrors for the missing filename until the count is zero, reopen CapCut, and rerun upload.
- Treat a warning-free upload start as a gate. Do not knowingly upload a project with missing required media for office handoff.

## Verification

Do not report success merely because the destination dialog closed.

1. Wait until the upload-task badge beside the account space disappears and no error is shown.
2. If the final upload helper turns into a blank/stale CEF window and remains there after a reasonable upload wait, do not classify the upload from that window alone. Dismiss only the stale helper, then verify the cloud destination directly. A visible project row in the fixed destination is authoritative; a blank helper is not.
3. Open `TAKKTWO` explicitly and verify the account-space label before entering the folder.
4. Verify the `macmini` folder's modified time changed to the upload time.
5. Open `macmini` and read back the project row:
   - project name
   - size
   - duration
   - type=`프로젝트`
   - latest edit/upload time
6. Only then report cloud sync complete and office-visible.
7. Re-read the local generated project after CapCut has opened/saved it:
   - canonical root/timeline mirrors still parse and are semantically aligned
   - required VIDEO/audio materials exist
   - expected title/caption text and timing still exist
   - stale missing-media filenames are absent
   - the exact project has one root-meta row
8. Resolve track roles from the root contract, segment material IDs, or actual text/material content. Never diagnose a missing T1/T2/A-track by assuming a remembered numeric track index; root variants may place the same role at a different index.
9. Update `assembly_report.md` and `production_summary.json` with:
   - `capcut_cloud_upload_performed=true`
   - `capcut_cloud_location=TAKKTWO/macmini`
   - verified time and visible project facts
10. If a lightweight OneDrive episode exists, resync only the updated reports; never copy the raw CapCut draft there.

## macOS UI fallback and coordinate safety

Use the normal `computer_use` capture → element click → recapture workflow first. If a desktop-control session has ended or returns no CapCut elements, retry/restart that session rather than treating the tool as permanently unavailable. When CapCut is still visible to macOS Accessibility, the following bounded fallback is allowed:

1. Use `System Events` or JXA to read the exact CapCut window bounds and locate the project title by its full accessibility description, such as `HomePageDraftTitle:<exact-project-name>`.
2. Capture only the current CapCut window region with `screencapture`; do not capture or share the whole desktop. Re-capture after every state change because CapCut menus and dialogs move.
3. Use coordinate clicks only from that fresh AX/screenshot read. If `cliclick` is needed, pass `-r` so the user's real cursor returns to its original position immediately.
4. A right-click context menu can extend beyond the nominal CapCut window bounds. Verify the visible `업로드` label before clicking it; never reuse an old coordinate.
5. After opening `공간`, verify the active account space is exactly `TAKKTWO`, open `macmini`, and verify the cloud row.
6. If neither the primary desktop tool nor macOS AX can read CapCut, stop UI actions and ask for `hermes computer-use doctor`; do not perform blind clicks.

This is a recovery pattern, not evidence that the primary desktop tool is generally broken.

## Pitfalls

- The Home-screen `프로젝트 동기화` popover and its global `기본 공간` setting are not the manual folder chooser. They may display the previously used `TAKKTWO/자동 업로드`; changing the default space only selects an account's `자동 업로드` folder, not `macmini`.
- For this fixed handoff, do not rely on the Home `프로젝트 동기화` popover. Prefer entering `TAKKTWO` → `macmini` first. A Home-row right-click is acceptable only when it opens an explicit destination picker and the final breadcrumb is verified before upload.
- A normal left-click on a Home project row opens the editor instead of selecting it for upload. Use right-click. If the editor opens accidentally, wait for autosave/load to settle and close the editor window to return Home before retrying.
- The cloud `공간` page can reopen on another account root or folder. Explicitly click `TAKKTWO`, then open `macmini`, before verifying the cloud row.
- Account storage increasing is supporting evidence, not proof of success. The project row inside `macmini`—exact name, size, duration, and type=`프로젝트`—is the completion authority.
- A folder name such as `macmini`, `HOME`, or `OFC` does not prove which account space is active; always read the breadcrumb.
- Returning from a modal may reopen the previously visited folder (for example `OFC`). Go back to the account root before checking `macmini`.
- A disappearing dialog is not proof of completion; verify the cloud row inside `macmini`.
- Do not infer sharing semantics from labels such as team/workspace. Follow the operator-fixed destination above.
- Coordinate-based automation is acceptable only after a fresh screenshot/AX read; UI coordinates can shift between Home, account root, and upload dialogs.
