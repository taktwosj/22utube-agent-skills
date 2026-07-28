# CapCut Stale Subdraft And Cloud Replacement

Use this runbook when the operator reports template/sample media in CapCut even though the episode asset files and root validator passed.

## Priority Rule

The operator's actual visual observation overrides a structural validator PASS. Do not answer from file existence or root material hashes alone.

## Diagnose Active Content

1. Close CapCut before editing.
2. Build a contact sheet from the media files physically inside the project and compare their SHA-256 values with approved builder inputs.
3. Map every active image-track segment `material_id` to its material name and source path; require unique expected assets and existing files.
4. Compare the root `draft_content.json`, active timeline content, and every existing `subdraft/*/draft_content.json` semantically.
5. A stale subdraft can make CapCut display template placeholders even when root media and segment mappings are correct.

## Staging Promotion And Path Integrity

A staging build can pass while CapCut still opens a `미디어 연결` dialog. The usual durable cause is that `draft_content.json` was promoted correctly but `draft_info.json` or a Timeline mirror still points to the staging folder.

Before first app launch:

1. Close CapCut.
2. Promote the staging directory to the final local draft directory.
3. Replace the staging prefix with the final path in **every JSON file**, not only root `draft_content.json`.
4. Treat these as full-content mirrors and require identical semantic content and, when no app rewrite has occurred, identical hashes:
   - root `draft_content.json`
   - root `draft_info.json` — critical because `root_meta_info.json` normally points here
   - `Timelines/*/draft_content.json`
   - `Timelines/*/draft_info.json`
   - `subdraft/*/draft_content.json`
5. For `template.json` and `attachment/patch/mini_draft.json`, replace stale absolute prefixes but do not overwrite their distinct schema with full draft content.
6. Verify every active video/audio material path exists and that zero JSON files contain the old staging prefix.
7. Verify `root_meta_info.json` has one canonical row whose `draft_fold_path`, `draft_json_file`, cover, name, duration, and IDs belong to the promoted project.

If CapCut shows `0/N개 미디어 연결됨` even though the files exist, do **not** manually reconnect them one by one. Cancel the dialog, quit CapCut without editing, repair the offline mirrors and stale prefixes, then reopen. Successful repair is evidenced by no reconnect dialog, valid media-bin thumbnails, playable source video, normal timeline waveforms, and zero `Unsupported Media` or `파일에 액세스할 수 없음` labels.

CapCut may rewrite one mirror after opening or closing. After visual review, close the app, re-read the newest root draft, synchronize the full-content mirrors once more, rerun the draft validator, and only then produce the final assembly report.

When the first visual is a real source MP4 but the builder accepts images only, build with a placeholder image, then replace that first material with a silent video material offline, preserve the source audio separately on `A_SOURCE`, copy the MP4 into project-local media, and mirror the resulting content before launch. Do not leave the placeholder material active on the timeline.

## Clean Repair

- Patch the builder so every existing subdraft content mirror receives the new episode content.
- Patch the actual-draft validator to fail stale subdraft content with `FAIL_TOP5ISU_CONTENT_MIRROR`.
- Add a regression fixture containing a stale sample sentinel; prove RED before the builder/validator change and PASS afterward.
- Rebuild from the immutable root into a fresh staging folder. Do not patch the promoted project in place.
- Before app launch, require build-time root, timeline, template mirrors, and subdraft mirrors to match.
- After CapCut opens, it may rewrite `template-2.tmp`; post-open authority is the current root/timeline/subdraft semantic state plus active material references and actual visual review.

## Visual Verification

Open only the repaired project. Confirm the media bin, preview, and timeline thumbnails contain the approved assets and zero placeholders. Record duration and visible asset count. A contact sheet alone is not final visual evidence after a user-reported mismatch.

## Cloud Replacement

1. Upload explicitly to `TAKKTWO/macmini`; never use another account space or folder.
2. If CapCut silently renames the new cloud project with `(1)`, inspect cloud name, size, duration, and count before deleting anything.
3. Delete only the smaller/older verified erroneous cloud copy.
4. Rename the verified new copy back to the canonical project name.
5. Recheck that exactly one canonical cloud project remains.
6. CapCut may also rename the local folder/meta to `(1)`. Close CapCut, restore the canonical local folder and `draft_meta_info.json`, update `root_meta_info.json` to exactly one entry, and rerun the actual-draft validator.

## Report

Record root cause, old erroneous cloud size, new verified cloud size, canonical name, location, visual asset count, validator results, and whether MP4/YouTube actions remained unperformed.
