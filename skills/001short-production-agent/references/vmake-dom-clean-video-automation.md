# VMake DOM Clean-Video Automation

## Purpose

Use this reference whenever the operator says `VMAKE`, `VMAKE 클린영상`, `클린영상 뽑기`, `자막 제거 영상`, or asks to turn a source Short into a clean visual asset.

This is browser UI automation, not a VMake API integration. Prefer deterministic DOM/CDP operations over screen coordinates.

## Fast production rule

Start one upload immediately after source identity, then continue source analysis, blueprint, and urakkai while the page processes. The producer may spend at most three minutes establishing the DOM upload/poll job; after that, poll current DOM state only and do not sit at the page or re-upload. If the clean result is still pending when CapCut is near and at least ten minutes remain, make a fast review draft from the original visual and later replace VIDEO with the verified clean asset. This is a review-speed exception, never permission to promote an unverified clean file.

## Scope routing

`0쇼츠` is a content lane/category; `001short-production-agent` is a production workflow, so they are not mutually exclusive choices.

When the operator explicitly says `클린 작업하고 그대로`, `순서 그대로 클린만`, or equivalent, record `production_mode=SOURCE_ORDER_UNCHANGED_CLEAN_ONLY`:

- preserve source order and full duration;
- do not force an urakkai reorder merely to satisfy the structural-reorder gate;
- do not fabricate `FINAL_DESIGN_LOCKED` when no design was requested;
- complete source acquisition and full-length VMake clean validation first;
- create CapCut assets only when the requested scope includes them.

This exception is only for explicit clean-only/passthrough work. A request presented as `우라까이` still requires meaningful structural reordering.

## Entry points

```text
https://vmake.ai/workspace
https://vmake.ai/video-watermark-remover/upload
```

Authentication, password, OTP, CAPTCHA, payment, credit use, and terms acceptance remain operator-controlled. Never store or print credentials, cookies, tokens, or session identifiers.

## DOM-first contract

An observed Upload button had this shape:

```html
<button type="button" class="btn--KTGbF intl-primary--jKiKf">
  ...
  <span>Upload</span>
</button>
```

The CSS-module class suffixes may change. Do not treat them as durable selectors. Select by semantics and require exactly one visible, enabled match:

```javascript
const matches = [...document.querySelectorAll('button[type="button"]')]
  .filter(button =>
    button.textContent.trim() === 'Upload' &&
    !button.disabled &&
    button.offsetParent !== null
  );

if (matches.length !== 1) {
  throw new Error(`VMAKE_UPLOAD_BUTTON_COUNT=${matches.length}`);
}

matches[0].click();
```

Execute through CDP `Runtime.evaluate` or a current browser DOM reference. Never reuse stale element references after navigation or React rerender.

## File upload

Do not drive the macOS Finder dialog by coordinates when the page exposes a file input.

1. Inspect `input[type=file]` candidates.
2. Prefer an input whose `accept` includes video and is associated with the active Upload surface.
3. Require exactly one valid candidate. If ambiguous, resnapshot/reinspect instead of guessing.
4. With direct CDP, use `DOM.setFileInputFiles` with the episode's absolute `source.mp4` path.
5. With OpenClaw managed Chrome, first copy the exact source under `/tmp/openclaw/uploads/`, verify the staged SHA-256 equals the episode source, run `openclaw browser upload <staged-path>` to arm the next chooser, and then click the current Upload DOM ref.
6. Verify the page displays the selected filename or enters an upload/processing state.

The OpenClaw upload sandbox is a portability/security boundary, not a reason to ask the operator to navigate Finder manually. Never treat a failed file-arm followed by a successful Upload click as an uploaded file; re-arm before clicking again.

Coordinate clicking is a last fallback only after DOM access is unavailable and a fresh screenshot proves the target.

## Processing-state polling

Poll page state rather than sleeping blindly:

- visible text containing `Processing`
- percentage text
- `progress` element values
- `aria-valuenow`
- completion controls becoming visible and enabled

During processing:

- do not refresh
- do not upload the same file again
- do not treat `Leaving won't stop the process` as failure
- do not treat a fixed percentage as completion

A prior run was cancelled at `Processing... 94%`; that run is not download-completion evidence.

## Download

After processing, re-snapshot the current DOM. Accessible names may be longer than the visible label, for example:

```text
Download 5s preview video Free!
Download full video Subscribe to Vmake Pro for continued use.
```

Match by semantic prefix and meaning, not only exact `Download`, and explicitly distinguish preview from full output. Require one visible, enabled candidate for the intended result.

A download command needs an explicit destination path whose parent exists. A closed dialog, changed page, click receipt, or shorter preview is not success; confirm a new playable MP4 exists on disk.

### Paid-plan rerender and multi-card results

Login can rerender the editor and invalidate every existing DOM ref. After the operator completes login, resnapshot before acting. A paid account may replace the full-download button with `Processing... <percent>% Auto-download When Ready`; wait for the same card to return to `Download` rather than clicking another card's already-ready result.

VMake can keep several result cards in one editor. Do not click the first `Download` globally unless the first card is proven to be the current upload. Bind Upload filename, card order/identity, mode, processing state, and Download control together. If the page exposes several `Download` buttons, query within the intended card or verify the resulting request/file against source duration and expected processing timestamp.

### Authorized download-request fallback

A browser-managed `download.saveAs` can lose its temporary artifact after the authorized click even though VMake generated a valid download request. The durable retry pattern is:

1. click the intended current-card Download control once;
2. inspect recent browser network requests;
3. select the newest authorized `GET` whose path ends in `.mp4` and whose query contains `attname`/`filename`;
4. fetch that URL internally to the requested destination without printing the signed URL or any query signature;
5. verify ffprobe duration, resolution, streams, size, and SHA-256.

Do not assume the newest historical OSS URL is the current result: preview, full Auto, Manual, and Subtitle-box outputs may use different hosts or paths. Filter by request time and the click that just occurred, and reject a file whose duration equals a preview rather than the source.

### Access boundary

- A free preview shorter than the source is evidence only, never canonical `clean_source.mp4`.
- If the full output requires Pro/subscription, do not purchase, subscribe, split the source to evade the limit, or promote a partial preview.
- Record `WAIT_VMAKE_PRO_OR_FULL_CLEAN_FILE` and request an approved Pro login session or the operator-provided full clean MP4.
- Password, OTP, CAPTCHA, payment, credit use, and terms acceptance remain operator actions.

## Canonical clean-asset intake

1. Identify the newly downloaded MP4 by creation/modification time and browser download state.
2. Copy it into the episode as `clean_source.mp4`; never make Downloads the permanent CapCut authority.
3. Record source identity and SHA-256.
4. Verify with ffprobe:
   - playable video stream
   - duration
   - resolution
   - FPS
   - expected audio presence
5. Compare against the source for duration/resolution compatibility.
6. Perform OCR and visual review on sampled first, early, middle, and last frames. Always add a dense early contact sheet (for short clips, first 1.5 seconds at about 4 fps) because transient comments or subtitle overlays may survive only during the first second and disappear from a 1 fps overview. Confirm every intended baked-in title, watermark, subtitle, and comment overlay is removed; inspect inpainted regions for smearing, duplicated objects, black boxes, hard rectangular seams, temporal flicker, frozen frames, or missing content. `Auto/Smart` completion is not visual QA: it may remove an upper title and watermark while leaving a lower comment overlay in the first section.
7. Reject each candidate independently. Auto pass 2, Manual brush, or Subtitle box processing is not evidence that the residual was fixed; download the exact new candidate and rerun the same dense QA. Never promote an output whose hash/file identity points to an older preview or Auto result.
8. If VMake repeatedly leaves a small transient overlay and the operator's approved scope is clean-only, a narrowly timed, localized post-process fallback may be used only when all of the following are true: the affected bbox/time range is recorded; road/face/vehicle/story content is outside the treatment; before/after dense contacts show no readable text, hard box, or severe distortion; and the final report explicitly labels the hybrid method. Reject conspicuous delogo geometry; prefer the least destructive visually acceptable treatment. Do not silently call a hybrid result pure VMake output.
9. Treat the clean asset as visual-only in CapCut and mute embedded audio when the production plan uses separately rearranged source audio.
10. When source audio preservation is required, inspect the original codec. VMake may transcode an original Opus stream to AAC. Remux the original source audio into the final clean video with stream copy when container support allows it, then compare decoded PCM SHA-256 between original and final. Do not rely on `.opus`/Ogg container hashes because serial/granule metadata can differ even when decoded samples are identical.
11. Set `CLEAN_VISUAL_READY` only after the manifest and clean receipt match the actual file. Record the selected candidate SHA-256, duration, visual evidence, audio codec, and decoded-PCM comparison.

## Cross-computer use

Honcho memory can recall the trigger and procedure when the other agent uses the same Honcho workspace/peer, but Honcho memory does not install executable skills.

For another computer to run this procedure, it also needs:

- the synchronized `001short-production-agent` skill
- a supported Chrome/CDP/browser-relay runtime
- a current VMake login session
- machine-local source and download paths resolved at runtime

Never copy one machine's absolute paths, browser element IDs, cookies, or session data to another machine.

### OneDrive Paperclip handoff

When the operator says `페이퍼클립 쓰자` during a Shorts task, use the OneDrive progress-board pattern rather than assuming the official Paperclip API/MCP:

1. Resolve the currently selected OneDrive root by realpath before writing. Do not use a historical `.ODContainer-*` path merely because it already contains old templates or scripts.
2. Create or update `22utube/11utube/11short_handoff/{project_id}` under the active root.
3. Include `handoff_manifest.json`, `job_state.json`, `validation_report.json`, `evidence_pack.json`, `HANDOFF_CODEX.md`, and `work/`.
4. Copy the verified `source.mp4`, compact metadata, relevant preview evidence, and blocker report into `work/` using relative paths in manifests.
5. If no worker currently owns the task, use `status=blocked`, `locked_by=null`, and state one exact next action. A partial VMAKE preview stays evidence only.
6. The next Mac/home-Windows/office-Windows worker must claim the project before acting. One project may have only one active worker. While work is actually running, use that machine's editing status such as `editing_on_macmini`, `editing_on_home_windows`, or `editing_on_office_windows`; do not claim directly as `assets_ready` before the asset and QA exist.
7. `HANDOFF_CODEX.md` must carry the DOM-first upload rule, expected full duration, clean QA criteria, access boundary, and any explicit `SOURCE_ORDER_UNCHANGED_CLEAN_ONLY` lock.
8. After full clean QA passes, save `work/clean_source.mp4`, update evidence/validation, set `status=assets_ready`, clear blocker, and release the lock.
9. Verify both the board validator and readback from the active OneDrive path. Local creation inside a stale backing store is not cross-machine visibility evidence.

Honcho stores the durable rule; OneDrive Paperclip stores current status, lock, blocker, next action, files, and evidence.

## Failure policy

- Multiple Upload/Download candidates: stop and inspect current DOM.
- Login/OTP/CAPTCHA: operator action required.
- Payment/credit/terms or full-download subscription prompt: do not approve automatically; set `WAIT_VMAKE_PRO_OR_FULL_CLEAN_FILE`.
- Download button clicked but no file: remain incomplete and inspect browser download state.
- Processing stalls: inspect current page/server status; do not claim that VMake is generally broken.
