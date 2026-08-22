# VMake API Clean-Video Path (preferred)

## Purpose

Use this reference first whenever the episode needs a clean visual asset from VMake. It replaces
ad-hoc browser clicking with the vendor's official REST/SDK interface. Fall back to
[references/vmake-dom-clean-video-automation.md](vmake-dom-clean-video-automation.md) only when the
API errors, times out, or the account has no key provisioned yet.

VMake publishes a developer API at `https://vmake.ai/developers` (dashboard → `api key` tab). It sits
on the same plan/credit balance as the browser UI — calling it is not a separate purchase, and it
draws down the same monthly quota the operator already pays for.

## One-time setup (per machine)

1. Sign in to the operator's VMake account in a browser session the operator controls (Aside or the
   operator's own browser). Never enter the VMake password yourself.
2. Open `https://vmake.ai/developers` → `api key` tab → **Create New Key**, name it after the machine
   (e.g. `001short-<hostname>`).
3. The secret is shown once. Click **Show secret access key** to reveal it (the table masks it by
   default), then immediately store both values and never print them again:
   ```
   MT_AK="<access key>"
   MT_SK="<secret key>"
   ```
   Save to `~/.openclaw/.env` (the path the official SDK/CLI expect). `chmod 600` the file.
4. Download the SDK zip linked from the developers page's "SDK Install" card (the URL changes between
   releases — always re-read it from the page rather than reusing a cached link) and extract it as
   `sdk/` under a stable local directory, e.g. `~/.local/share/vmake_sdk/sdk`.
5. Create a Python venv next to it and install the two runtime dependencies the SDK needs but its
   zip does not vendor:
   ```bash
   cd ~/.local/share/vmake_sdk
   python3 -m venv .venv
   .venv/bin/pip install requests alibabacloud_oss_v2
   ```
6. Verify auth without spending credits:
   ```bash
   export MT_AK="..." MT_SK="..."   # source from ~/.openclaw/.env
   .venv/bin/python sdk/cli.py list-tasks
   ```
   A JSON payload listing task presets (including `videoscreenclear`) confirms the key works.

**Never** paste `MT_AK`/`MT_SK` values, the SDK zip's signed contents, or any VMake OSS download URL
into chat, logs the user will see, or committed files. Treat a VMake output URL exactly like a
password-reset link — fetch it once, then let it expire.

## Running a job

```bash
cd ~/.local/share/vmake_sdk
export MT_AK="..." MT_SK="..."
.venv/bin/python sdk/cli.py run-task --task videoscreenclear \
  --input /absolute/path/to/episode/00_input/source.mp4 \
  --params '{"parameter":{"rsp_media_type":"url"}}'
```

`run-task` with a local file path does the whole job in one call: uploads to VMake's OSS bucket,
calls `/skill/consume.json` to validate quota, submits `/v1/videoscreenclear_async`, and polls up to
128 times until `status` reports completion. For a ~25s short this took roughly two minutes end to
end (upload sub-second, algorithm processing ~100s, poll interval widening 0s → 7s → 15s → 18s...).

Exit code `0` with a JSON body containing `"code": 0` and a non-empty `output_urls` array is success.
Exit code `1`, a `ConsumeDeniedError`, or `meta.code != 0` means the job did not run — do not retry
blindly; read the error message (quota exhausted, invalid input, unsupported format) before deciding
next steps.

## Retrieving the result

`output_urls[0]` is a signed, time-limited `oss.vl.starii.com` URL. Fetch it once with `curl`/`fetch`
straight to `40_assets_used/clean_source.mp4` inside the episode root; never let it sit in a shell
history file or get echoed to a terminal the user can see. Then run the same acceptance gate as the
DOM path — see [vmake-dom-clean-video-automation.md § Canonical clean-asset intake](vmake-dom-clean-video-automation.md#canonical-clean-asset-intake):
ffprobe duration/resolution/streams, duration difference vs the locally verified source ≤ 1.0s, no
frame-level visual QA. `[[vmake-no-qa]]` applies identically here.

## Task presets

`list-tasks` enumerates what the current key can call. As of the 2026-08-20 check, the watermark/
subtitle-removal preset is `videoscreenclear` (video) — the API-side equivalent of the browser UI's
base "Smart" tier, not "Smart pro". The UI's "Smart pro" quality tier is gated to the higher paid
plan and is not exposed through this API preset; do not assume the API bypasses that plan gate.
`eraser_watermark`/`image_restoration` cover image tasks; `hdvideoallinone` covers quality
enhancement rather than removal. Confirm the exact set for the active account with `list-tasks`
before relying on a preset name, since VMake can add or rename presets.

## Payment boundary

Never create an API key that requires entering payment details, never call an endpoint that would
upgrade the plan, and never retry a `ConsumeDeniedError` by purchasing more credits. If the account's
existing plan/credits are insufficient for the requested job, stop and report
`WAIT_VMAKE_PRO_OR_FULL_CLEAN_FILE` exactly as the DOM path does — the operator decides whether to
top up.

## Failure → DOM fallback

If the API is unreachable, the SDK dependency chain is broken on a given machine, or the account has
no key yet and provisioning one is impractical mid-episode, fall back to
[vmake-dom-clean-video-automation.md](vmake-dom-clean-video-automation.md) for that run. Record which
path actually produced the clean asset in the episode's evidence rather than assuming API-first
silently succeeded.

## Cross-computer use

The API key, `.env` path, SDK install directory, and venv are machine-local, exactly like the DOM
path's browser session state. Never copy one machine's key, SDK checkout, or absolute paths to
another machine — each machine provisions its own key from the same VMake account.
