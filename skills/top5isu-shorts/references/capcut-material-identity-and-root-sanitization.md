# CapCut Material Identity Collision And Root Sanitization

Use this when physical episode images are correct but CapCut repeats a template/stock image in the media bin, timeline thumbnails, preview, or cloud project.

## Failure class

This is a **material identity/cache collision**, not automatically an Image2, crop, path, or decoder failure.

Typical evidence:

- episode PNG hashes and dimensions are correct;
- active segment paths point to those PNGs;
- several `materials.videos[]` entries inherit the same remote `material_id`;
- `source`, `source_platform`, category, copyright, or `key_value.json` still identify a stock asset;
- CapCut resolves the inherited stock identity/cache ahead of the replacement path and displays one stock image repeatedly.

The durable mistake is cloning a prototype and changing only `path`, `media_path`, or filename while leaving its remote identity metadata intact.

## Diagnosis

Close CapCut before reading or editing.

1. Hash every approved builder input and every project-local image.
2. Map each `IMAGE_EFFECT_PRESETS` segment's internal `material_id` to its `materials.videos[]` object.
3. Require the expected image count, existing local path, expected hash, and a unique external `material_id` for every active image.
4. Inspect `material_name`, `source`, `source_platform`, category fields, `is_copyright`, `origin_material_id`, `material_url`, and `key_value.json`.
5. Search every control surface and the canonical ZIP for the stock filename, display name, and remote material ID:
   - root `draft_content.json`, `draft_info.json`, `template-2.tmp`
   - active Timeline and subdraft mirrors
   - `template.json` and `attachment/patch/mini_draft.json`
   - `draft_meta_info.json`, including escaped JSON in `draft_materials[*].value[*].extra_info`
   - `key_value.json`
   - archive member names and text control files
6. Treat the operator's actual CapCut screenshot as a failed visual gate even when paths and a structural validator pass.

## Episode repair

For every replacement image material:

- assign a fresh internal material object ID when cloning;
- assign a distinct local external `material_id`;
- use a hash-derived episode filename to break filename/cache aliases;
- set `source=0`, `source_platform=0`, category fields empty, `is_copyright=false`, `check_flag=0`;
- clear remote URL, origin ID, and stock provenance;
- generate fresh local/unique/request IDs;
- set `key_value.json={}`;
- remove `.bak` and stale patch caches only after preserving required `template-2.tmp` mirrors;
- synchronize all full-content mirrors while preserving distinct-schema `template.json` and `mini_draft.json`.

After CapCut opens, it may add an unnamed empty video track. After closing the app, remove it **only if it has no name and zero segments**, then resynchronize mirrors and rerun validation. Never delete an unnamed track containing content.

## Canonical root cleanup

Do not keep a remote stock photo as a root animation prototype.

1. Back up the canonical candidate and ZIP/manifest hashes outside skill-discovery directories.
2. Work in a separate clean candidate.
3. Replace the stock prototype with four text-free neutral local placeholders while preserving the four approved animation prototypes.
4. Give each root placeholder a unique external local `material_id` and local-only metadata.
5. Remove stock provenance from root, Timeline, subdraft, template, mini-draft, meta, key-value, physical media, and ZIP surfaces.
6. Lock root visual constants:
   - information logo: UI `50% / X 0 / Y 1500`; JSON scale `0.5`, x `0`, y `0.78125`;
   - `T1/T2=#f1ff00`;
   - `TTS_TEXT/SOURCE_TEXT=#ffffff`.
7. Rebuild the ZIP; remeasure archive SHA-256 and file count; update root and template manifests; promote the manifest last.
8. Run the package validator against the promoted canonical directory.

The builder must delete neutral root placeholders after copying episode images so they do not remain active or inert in a derived project.

## Required regression test

A root cleanup is incomplete until a direct-copy derived project is built with real approved assets.

Require:

- fresh project and timeline IDs;
- episode image hashes match inputs;
- unique external material IDs equal the episode image count;
- zero stock tokens and zero neutral placeholder files;
- `key_value.json={}`;
- exact logo and text color readback;
- all image transitions and semantic motion/high-impact slots preserved;
- draft validator PASS;
- actual CapCut media-bin, timeline-thumbnail, first-frame, CTA-frame, and logo UI readback PASS when the operator reported a visual mismatch.

## Validator guards

The package validator should fail on:

- legacy stock filename, display name, or remote material ID;
- non-empty root `key_value.json`;
- non-local prototype source/platform metadata;
- stock category/copyright residue;
- missing or duplicate root prototype external material IDs;
- wrong root text colors.

Use a pre-clean backup as a negative fixture: the new validator must reject it while the clean canonical package and a direct-copy derived draft pass.

## Cloud replacement

Upload the verified version explicitly through `TAKKTWO / macmini` → `업로드` → `프로젝트 업로드`. Do not rely on auto-upload routing. Read back name, size, duration, type, and edit time. Preserve older erroneous copies unless deletion is explicitly authorized; mark the clean-root rebuild as latest in project pointer and version history.