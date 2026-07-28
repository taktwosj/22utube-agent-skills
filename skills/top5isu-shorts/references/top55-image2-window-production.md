# TOP55 Image2 Window-Fit Production

Use this for TOP55/top5isu episode images when the operator asks for generated visuals or complains that images do not fit the visible card window.

## Source of truth

Never infer the image ratio from the 1080×1920 canvas, a previous template, or the source image dimensions. Measure the alpha-zero opening of the active `FRAME` PNG first.

Current TOP55 root frame:

```text
canvas=1080x1920
transparent_window_bbox=x54..1019,y514..1307
transparent_window_size=966x794
transparent_window_ratio=1.21662469
```

The episode image deliverable is therefore exactly `966×794`. Keep important faces, hands, symbols, and objects inside the central 80% of the generation so a tiny center crop cannot cut them.

## Generation route

- Official final route: ChatGPT web Image generation through `browser_prompt_runner`/CDP.
- Stock photos, screenshots, PIL graphics, SVG, HTML, local infographic cards, and procedural placeholders are not substitutes for requested generated images.
- Local processing is limited to deterministic crop/resize, manifest construction, contact sheets, and frame-fit diagnostics. It must not invent the image content.
- Start in a fresh ChatGPT conversation. Run one real sample first and visually approve style/composition before batching.
- Prompt for a landscape image at about `1.2166:1`, with central-safe composition, no embedded text, no letters/numbers, no watermark, and no split panels. CapCut title, TTS caption, and source labels stay on their own tracks.

## Any-ratio runner pitfall

The shared runner may detect only roughly 16:9 outputs. ChatGPT can correctly generate TOP55 images around `1383×1137` (about 1.2164:1) while a 16:9 detector waits forever.

Do not assume generation failed and do not immediately regenerate. Inspect generated-image candidates by dimensions only. If the image exists, recover it through the browser context with credentials and save the real PNG. For the remaining batch, copy the runner into the episode folder and broaden only the copied detector:

```text
naturalWidth >= 512
naturalHeight >= 512
ratio=0.50..2.10
rendered_ratio=0.45..2.30
```

Never overwrite the shared runner merely to handle one episode ratio. If a batch stalls after several successful saves, keep completed PNGs, create a missing-only prompt file, open a fresh ChatGPT conversation, and resume only missing IDs.

## Finalization and QA

1. Count actual CDP-downloaded PNG files.
2. Center-crop/resize each real generated image to exactly `966×794`.
3. Verify every final file is `966×794`, non-empty, and has a unique SHA-256 hash.
4. Build `image2_manifest.json` with explicit prompt and image-directory paths; require `manifest_found`, no missing IDs, and no failed files.
5. Visually inspect every scene for narrative match, central-safe composition, readable accidental text, logos/watermarks, distorted hands/faces, and style consistency.
6. Composite at least one image behind the actual frame as a diagnostic fit preview.
7. Select one or two emotional peaks for the fire-effect slots only after image QA.
8. When importing into a derived CapCut project, media metadata must use the actual image dimensions; never coerce these files back to a stale `1000×800` assumption.

## Operator-supplied reference still intake

When the operator sends still images while a source URL is being analyzed, treat
them as ordered production references, not casual chat attachments.

1. Save each original attachment unchanged under the local external-drive intake
   root keyed by the source video ID, for example:
   `.../top5isu-intake/<video_id>/references/`.
2. Use ordered, role-bearing names such as
   `01_rooney_rowing_reference.jpg` or
   `04_haaland_saying_row_reference.jpg`; never rely on cache filenames.
3. Record dimensions, byte size, SHA-256, operator-stated role/dialogue intent,
   visible text/numbers, logos/watermarks, and crop notes in a reference manifest.
4. Preserve the operator's intended story relation exactly: e.g. a face still may
   be the reaction/dialogue cue and a separate action still the payoff. Do not
   collapse them into one generic subject label.
5. A user-stated dialogue role is production intent, not independent proof that
   the pictured person actually said the line. Keep factual verification
   separate before final narration.
6. Flag visible publisher logos, social-platform marks, composite circles, or
   pre-existing captions for rights and crop review. Do not erase or alter the
   original reference file.
7. Reference stills may guide story order, crop, or Image2 prompts, but they are
   not automatically approved final assets. Keep them out of the CapCut media set
   until the script/image plan and usage route are approved.
8. If URL extraction is temporarily blocked, continue receiving and indexing
   operator-provided references; do not invent the unavailable source content or
   claim the stills alone prove the full video narrative.

## Operator review gate

Before changing an existing CapCut project, deliver in Telegram:

- one contact sheet,
- one actual TOP55 frame-fit preview,
- every individual final PNG.

Report the measured window, final dimensions, actual Image2 count, manifest result, and proposed high-impact indices. Do not replace project media until the operator approves the reviewed set.

## Approved replacement and versioned rebuild

After approval, do not overwrite the previous editable project. Preserve it and
create a fresh `<episode>_vN_Hermes` clone with new project/timeline IDs.

- The builder CLI must accept official `scene_*.png` Image2 outputs as well as
  legacy `asset_*.png` inputs.
- Read actual PNG dimensions into both video materials and
  `draft_meta_info.json`; never retain a stale 1000×800 constant.
- Reuse the approved narration, exact subtitle cues, and current image boundaries
  unless the operator requested timing changes.
- Require one animation on every image and only one or two high-impact fire slots.
- Read back track order, T1/T2, source text, subtitle count, image dimensions,
  per-image SHA-256 equality, effect names/indices, sample residue, `.bak`,
  placeholders, missing paths, and fresh IDs from the installed project folder.
- Run package, contract, track-mapping, draft, and assembly-report validators.
- Update `assembly_report.md`, `local_paths.md`, `production_summary.json`, and
  pending Trend Hunter metadata with current project plus prior version history.
- If a stalled runner is intentionally terminated after completed PNGs were
  preserved, treat the resulting SIGTERM as cleanup evidence, not an image
  generation failure.
- Open/play CapCut only when explicitly requested.
