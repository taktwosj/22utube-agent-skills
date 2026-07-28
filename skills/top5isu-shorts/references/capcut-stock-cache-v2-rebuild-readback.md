# CapCut Stock-Cache v2 Rebuild and Readback

Use this when a TOP5ISU/군림보 project shows one repeated stock image (often flowers) even though the physical episode PNGs are correct and distinct.

## Diagnosis

Before regenerating images, compare the draft material records with the physical assets.

A cache/identity collision is confirmed when one or more of these are true:

- episode PNG hashes are distinct, but image materials reuse one external `material_id`
- `source` / `source_platform`, stock category, copyright, vendor, or stock name remains
- `key_value.json` retains the stock entry
- material paths point to an older project folder, especially when CapCut registered a suffixed folder such as `(2)`
- the referenced files do not exist even though `Resources/media/asset_*.png` does

Do not fix this by replacing PNG bytes in place. CapCut may continue resolving the inherited stock identity.

## Durable repair

1. Close CapCut.
2. Preserve the bad project as rollback evidence.
3. Validate and extract the immutable TOP55 root package.
4. Build a fresh versioned project, for example `*_v2_Hermes`, in a short staging directory on the **same filesystem** as the final CapCut root.
5. Pass `final_draft_path` on the first build. Do not build with a temporary path and string-replace later.
6. For every episode image require:
   - a unique internal material ID
   - a unique external `material_id`
   - `source=0`, `source_platform=0`
   - empty stock category/name fields
   - no copyright/stock provenance
   - an existing path under the final project's `Resources/media`
7. Empty `key_value.json` and remove the inherited stock name/ID from all parseable project controls.
8. Require root/timeline full-content mirrors to be semantically identical before promotion.
9. Promote with same-filesystem `os.replace`, then register exactly one new root-meta row. Keep the superseded row/project for rollback.

## Root-meta registration rule

Never replace a CapCut root-meta row with a minimal custom dictionary. Preserve the complete local-row shape and update only identity/path/time/size fields that are authoritative for the new project.

At minimum retain or set the fields CapCut uses for Home display, including `draft_timeline_materials_size` and the standard local-project flags. If it is omitted, Home may show `0.0B` even though the project files are intact. Do not copy a superseded project's cloud entry/space/user IDs into the fresh local project.

## Post-open authority rule

CapCut may regenerate a newer `draft_info.json` or timeline mirror containing root placeholders such as `##_draftpath_placeholder_*_##`. Therefore, **newest mtime alone is not authority**.

After closing CapCut:

1. Prefer the verified root `draft_content.json`.
2. Accept another full-content mirror only if all expected image paths exist, placeholder count is zero, stock identity is absent, and the expected image/material counts match.
3. Synchronize only full-content mirrors (`draft_content.json`, `draft_info.json`, `template-2.tmp`) from that valid authority.
4. Do not overwrite schema-specific `template.json` wholesale.
5. Re-run material/path, mirror-hash, root-meta-row, and draft validators.

## Cloud-safe preflight

Before upload, run the cloud-media validator. A visually valid local draft may still contain machine-local transition cache placeholders, `.bak` files, or an unreferenced inherited subdraft.

- For online transition/effect materials, preserve online resource/effect IDs and clear only machine-local cache `path` values.
- Back up `.bak` and unreferenced subdraft residue outside the live project, then remove them from the upload copy.
- Confirm the subdraft ID is absent from live segment refs and `materials.drafts` before removal.
- Reassert full-content mirror equality after cleanup.
- Require zero missing live paths, Windows paths, unreferenced missing paths, `.bak`, and subdraft residue.

## Visual proof

Static validation is necessary but not sufficient for a reported visual mismatch.

- Open the fresh version, not the superseded card.
- Verify the media bin and timeline contain distinct thumbnails.
- Actually play through at least an early and a later image transition.
- Capture the nonzero playback time and normal topic image at both checkpoints.
- Close CapCut and perform the post-open readback again before cloud upload.
