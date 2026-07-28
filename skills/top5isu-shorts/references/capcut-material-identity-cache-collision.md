# CapCut Material Identity And Stock Cache Collision

Use this when a generated CapCut project contains the correct replacement PNG files and valid paths, but the editor preview or timeline thumbnails repeatedly show the template's old stock image.

## Failure class

This is a **material identity collision**, not necessarily an image-generation, crop, or missing-media failure.

CapCut can resolve thumbnails and decoded media through inherited material metadata as well as the physical file path. A cloned template may retain:

- one remote stock `material_id` across several prototype images
- `key_value.json` entries for the stock asset
- stock `category`, `source`, `source_platform`, URL, copyright, or purchase metadata
- remote provenance in `draft_meta_info.json`
- stale copies in root/Timeline/subdraft/template/mini-draft control surfaces

Changing only `path`, `media_path`, or the physical file can therefore leave every segment displaying the same cached stock asset.

## Diagnosis

1. Treat the operator's visual report as a failed gate even if validators pass.
2. Close CapCut before inspection or repair.
3. Hash the physical episode images and compare them with approved inputs.
4. Map each active image segment's internal material reference to its video material.
5. Inspect the external `material_id`, material name, category, source/platform, copyright, URL, and `key_value.json`.
6. Search root content, Timeline mirrors, subdrafts, `template.json`, `mini_draft.json`, `draft_meta_info.json`, and the packaged ZIP for the stock filename, stock name, and stock material ID.
7. Distinguish this from stale full-content mirrors: a mirror mismatch is repaired by synchronization; identical stock identities require material re-identification and cache cleanup.

## Episode repair

For every replacement image:

- use a hash- or episode-specific filename
- assign a fresh internal material UUID and a distinct local external `material_id`
- set `source=0`, `source_platform=0`
- clear category, material URL, origin material ID, and remote request metadata
- set copyright/purchase flags false
- clear `key_value.json`
- remove stock `.bak`, temporary patch, and stale cache surfaces only after preserving required full-content mirrors
- synchronize root `draft_content.json`, root `draft_info.json`, active Timeline mirrors, and every full-content subdraft

Reopen CapCut and verify the media bin, all timeline thumbnails, and actual preview frames. File hashes alone are not visual completion evidence.

## Canonical root repair

Do not leave a remote stock photo in the reusable root merely because builders normally replace it.

1. Back up the current canonical directory, ZIP, manifest, restore notes, and hashes outside skill-discovery roots.
2. Build a separate candidate root.
3. Preserve the four animation prototype segments, but replace the stock media with four text-free neutral local placeholders.
4. Give every prototype a distinct local `material_id`; clear stock metadata and make root `key_value.json` exactly `{}`.
5. Remove remote stock provenance from all control surfaces and the ZIP.
6. Recompute content-bundle data, packaged file count, archive SHA-256, and manifest fields.
7. Validate the candidate, then create a direct-copy regression project with real episode images.
8. Require unique material IDs for every episode image, zero placeholder files in the derived project, zero stock tokens, correct logo transform, fresh project/timeline IDs, and draft validator PASS.
9. Promote archive/notes first and the manifest last; revalidate the canonical directory.
10. Preserve the pre-clean backup and save a concise cleanup report.

## Validator requirements

A reusable TOP55 root must fail validation when any of these are present:

- legacy stock filename, stock display name, or known stock material ID
- non-empty root `key_value.json`
- prototype `source` or `source_platform` indicating remote media
- stock category or copyright metadata
- missing or duplicate prototype material IDs

Run a negative test against the preserved old root and require the stock-sample gate to fail. This proves the new guard detects the original defect rather than merely accepting the repaired package.

## Operator logo lock

For this operator's information logo, verify both representations:

- CapCut UI: `Scale 50% / X 0 / Y 1500`
- draft JSON: `scale.x=0.5`, `scale.y=0.5`, `transform.x=0`, `transform.y=0.78125`

A UI screenshot plus post-save JSON readback is required because CapCut may hold edits in a newer `draft_info.json` or temporary Timeline authority before root `draft_content.json` is refreshed.
