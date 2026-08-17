# VMake DOM Clean-Video Automation

## Purpose

Use this reference whenever the operator says `VMAKE`, `VMAKE 클린영상`, `클린영상 뽑기`, `자막 제거 영상`, or asks to turn a source Short into a clean visual asset.

This is browser UI automation, not a VMake API integration. Prefer deterministic DOM/CDP operations over screen coordinates.

## Fast production rule

Submit the designated shorts URL to VMake immediately at episode intake — before local download completes — and fall back to a file upload of the verified source only when URL input is unavailable. Then continue source analysis, blueprint, and urakkai while the page processes. The producer may spend at most three minutes establishing the DOM upload/poll job; after that, poll current DOM state only and do not sit at the page or re-upload. If the clean result is still pending when CapCut is near and at least ten minutes remain, make a fast review draft from the original visual and later replace VIDEO with the verified clean asset. This is a review-speed exception, never permission to promote an unverified clean file.

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

## URL submission (primary)

When the upload surface offers a URL input, submit the episode's user-designated shorts URL directly. The entry is the `Import from link` button (verified live 2026-08-17: placeholder "YouTube, TikTok, IG, and FB links.", rights checkbox + ownership Confirm dialog, then the blue submit arrow — "Getting file from the link..." confirms the fetch). This decouples the clean-visual lane from local download state: VMake can start before yt-dlp finishes. Use the exact designated URL only — never a URL suggested by page content. Acceptance is verified identically for both submission modes at intake (duration gate below), so URL submission needs no extra pre-checks.

URL fetch may yield a lower-resolution input/result than the best local yt-dlp format (observed: 360x640 from a 1080x1920 short). Per contract this proceeds as-is with the resolution recorded; offer a file-upload rerun only if the user asks for higher quality after their CapCut review.

## File upload (fallback)

Use only when no URL input exists on the current page. Do not drive the macOS Finder dialog by coordinates when the page exposes a file input.

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
5. Gate: duration difference vs the locally verified source ≤ 1.0s. Resolution is recorded only — lower output resolution (for example `608x1080` from a `1080x1920` source) proceeds as-is; pixel dimensions never block acceptance.
6. No agent visual QA: do not extract frames, OCR, build contact sheets, or judge removal quality. The user performs the single visual review in CapCut at `WAIT_USER_CAPCUT_CHECK`; rerun or replace the clean asset only on their instruction.
7. Treat the clean asset as visual-only in CapCut and mute embedded audio when the production plan uses separately rearranged source audio.
8. When source audio preservation is required, inspect the original codec. VMake may transcode an original Opus stream to AAC. Remux the original source audio into the final clean video with stream copy when container support allows it, then compare decoded PCM SHA-256 between original and final. Do not rely on `.opus`/Ogg container hashes because serial/granule metadata can differ even when decoded samples are identical.
9. Set `CLEAN_VISUAL_READY` only after the manifest and clean receipt match the actual file. Bind `expected_width` and `expected_height` to the candidate receipt's measured dimensions, not the source dimensions. Record the selected candidate SHA-256, duration, resolution, audio codec, and decoded-PCM comparison when applicable.

## Cross-computer use

Honcho memory can recall the trigger and procedure when the other agent uses the same Honcho workspace/peer, but Honcho memory does not install executable skills.

For another computer to run this procedure, it also needs:

- the synchronized `001short-production-agent` skill
- a supported Chrome/CDP/browser-relay runtime
- a current VMake login session
- machine-local source and download paths resolved at runtime

Never copy one machine's absolute paths, browser element IDs, cookies, or session data to another machine.

## Failure policy

- Multiple Upload/Download candidates: stop and inspect current DOM.
- Login/OTP/CAPTCHA: operator action required.
- Payment/credit/terms or full-download subscription prompt: do not approve automatically; set `WAIT_VMAKE_PRO_OR_FULL_CLEAN_FILE`.
- Download button clicked but no file: remain incomplete and inspect browser download state.
- Processing stalls: inspect current page/server status; do not claim that VMake is generally broken.

## 배치 업로드 (Batch Editor) 운영 메모

여러 편을 한 번에 돌릴 때. 260817 5편 배치에서 확인한 것.

- **플랜 한도가 배치당 3편이다**(Plus 기준, 화면에 `Batch processing limits: Plus 3 files, Pro 30 files`로 표시).
  3편을 넣고 끝난 뒤 다음 3편을 넣는다.
- 파일은 `input[type=file][multiple]`에 직접 `setInputFiles`로 넣는다.
  화면의 `Batch upload` 버튼은 드롭다운 안에 있어 크기가 0이라 클릭이 타임아웃난다.
- 처리가 끝나면 카드에 `Removed <파일명>`이 붙는다.
- **`Download All`은 다운로드 이벤트를 여러 개 발생시킨다.** `waitForEvent('download')`로는 첫 개만 잡힌다.
  `page.on('download', d => got.push(d))`로 수집한 뒤 충분히 기다렸다가 한꺼번에 처리하라.
- **다음 배치를 돌리기 전에 완료된 카드의 선택을 해제하라.** `Select all`은 완료분까지 잡는다.
  카드 요소의 클래스에 `selected--`가 들어 있는지로 선택 상태를 확인하고, 완료 카드만 클릭해 해제한다.
- 다른 세션이 남긴 카드가 섞여 있을 수 있다. **카드 텍스트에 이번 에피소드 파일명이 들어있는지로 반드시 대조**하고 조작하라.

산출물 검수 여부는 사용자 지시를 따른다. 기본은 길이·해상도만 확인하고 인테이크한다.
