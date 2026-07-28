# VMake Residual Cleanup and Promotion QA

Use this reference when VMake reports completion but baked-in text, comments, or watermarks may remain.

## Candidate discipline

- Treat each VMake run as a candidate, not as the canonical clean asset.
- Keep the source, Auto pass, Manual/Subtitle-box pass, and any fallback outputs under distinct filenames and record SHA-256 values.
- A `Processing` completion or active `Download` button is not visual-clean evidence.
- Never overwrite `clean_source.mp4` until a candidate passes the promotion gates below.

## Mandatory visual sampling

Create and inspect both:

1. A full-duration contact sheet at roughly 1 fps.
2. A dense contact sheet for the first 1.5 seconds at roughly 4 fps.

The dense early sheet is required because short-lived comments and titles often disappear before a normal 1 fps sample. Check top title, corner watermark, lower comments, black blocks, smears, repeated textures, and damage to the actual subject.

## Retry interpretation

- Auto pass 2 is not automatically better than Auto pass 1; compare the output frames.
- Manual brush or Subtitle-box processing is not accepted merely because Apply completed. Download and inspect the resulting MP4 independently.
- If a pass retains source text or leaves the same residual, mark that candidate `REJECTED`; do not describe it as VMake-clean.
- If VMake cannot remove a residual after reasonable retries, report that boundary directly instead of repeatedly spending credits or claiming success.

## Localized fallback

A local fallback may be used only when it is within the operator's requested clean-only scope and is disclosed as a hybrid result.

- Start from the best VMake candidate.
- Limit the fallback to the smallest non-semantic region and shortest time window possible.
- Prefer a visually soft treatment in dark/background regions over a large `delogo` interpolation that creates geometric blocks.
- Reject any candidate with visible rectangular borders, black polygons, repeated textures, or damage to road, faces, vehicles, products, or other meaningful content.
- Do not call a hybrid result a pure VMake output. Record the VMake base and the exact fallback scope in `clean_visual_manifest.json`.

## Original-audio preservation

When the visual stream is re-encoded or patched:

1. Remux the original source audio back into the promoted MP4 when compatible.
2. Compare decoded PCM SHA-256 between original and final audio; container-level Opus/Ogg hashes may differ because of metadata even when samples are identical.
3. Require the decoded PCM hashes to match for an `original audio preserved` claim.

## Promotion gates

Promote a candidate to `clean_source.mp4` only when all are true:

- full-duration contact sheet: PASS
- dense first-1.5-second contact sheet: PASS
- no readable baked-in title, watermark, or comment in the requested removal scope
- no severe cleanup artifact
- ffprobe duration/resolution/FPS are within the production contract
- original-audio PCM match: PASS when original audio preservation is required
- source, final, evidence, method, hashes, and any hybrid disclosure are recorded
