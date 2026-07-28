# Operator-Supplied Ranked Image Intake and Re-delivery

Use this when the operator sends TOP5 images across one or more messages, especially when a rank has multiple images or the operator corrects the rank after upload.

## Intake contract

1. Treat the operator's latest explicit rank label as authoritative (`이것도 4`, `5 추가`, `아람코2`). Do not infer rank solely from message order.
2. Preserve every source file unchanged under an episode source/reference directory before processing.
3. Name sources with both rank and within-rank order, for example:

   ```text
   rank_5_alphabet_01.jpg
   rank_5_alphabet_02.jpg
   rank_4_microsoft_01.jpg
   rank_4_microsoft_02.jpg
   ```

4. Record original path, rank, company/person role, dimensions, byte size, and SHA-256 in an asset manifest.
5. Multiple images per rank are valid. Do not collapse a 10-image set into five images merely because the content is TOP5.
6. Process production copies separately; never overwrite the operator originals.

## Semantic QA

For each supplied image, mark rather than silently reject:

- `IDENTITY_UNVERIFIED` for a person whose identity is not confirmed.
- `SYNTHETIC_OR_COMPOSITE` for AI/composite illustrations presented as symbolic imagery.
- `HISTORICAL_OR_RETRO` for old logos/products that identify the company but may imply the wrong era.
- `VISIBLE_TEXT` for screenshots or captions whose wording may remain visible in the edit.
- `RIGHTS_SOURCE_UNKNOWN` when provenance is not established.

Use uncertain or synthetic material only as illustrative B-roll; never turn it into evidence for a factual claim.

`HISTORICAL_OR_RETRO` is a descriptive QA flag, not a rejection. When the operator says an old logo, product, interface, or archival image was chosen deliberately for `후킹`, contrast, or nostalgia:

1. Mark it `APPROVED` with `role=intentional_retro_hook`.
2. Preserve its within-rank order instead of replacing it with a modern image.
3. Pair it with a current company identifier when useful so the timeline communicates past-to-present rather than an accidental outdated claim.
4. Record the operator's intent in `40_assets/asset_decisions.json`; do not keep warning about the already-resolved creative choice.

If the operator later supplies a safer same-rank image to replace an identity-unverified person or synthetic illustration, preserve both originals, remove only the superseded production copy, update the decision record, regenerate the assembly/contact sheet, and verify the expected image count remains unchanged.

## Production copies

- Keep the original aspect ratio.
- Fit or compose into the measured TOP55 image window without stretching faces or logos.
- Blurred-background fill is acceptable when the source is too narrow, provided the foreground remains unwarped.
- Produce a contact sheet for QA, but do not substitute the contact sheet for individual asset delivery.

## Re-delivery to the operator

When the operator asks `각각 이미지 다시 올려봐`, deliver the exact requested individual files, in rank order, each with a short rank/company label and its own `MEDIA:` attachment line.

- Default to original source files, not processed crops, unless the operator asks for edited/CapCut-ready versions.
- Do not send only a contact sheet.
- Preserve within-rank order and include every accepted image.
