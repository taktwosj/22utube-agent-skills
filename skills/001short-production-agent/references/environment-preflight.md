# Environment preflight (one-time tool setup)

Episodes never search for, install, or debug tools mid-run. All tool
resolution happens once, before Stage 01, through the receipt.

## Rules

1. At episode intake run `python3 scripts/preflight_env.py --require-fresh`.
   If it reports STALE or FAIL, run `python3 scripts/preflight_env.py` once to
   refresh. Episodes read tool paths from the receipt
   (`~/.cache/22utube/001short_env_receipt.json`), not from ad-hoc `which`
   hunting.
2. Required: `yt-dlp`, `ffmpeg`, `ffprobe`. Optional (recorded, non-fatal):
   `tesseract`, `whisper`, `demucs` — Demucs is only needed for the type 3/4/5
   stem paths, never for `SOURCE_CLIP` trim paths.
3. **Installs happen only in the user's own terminal.** Never `brew install`
   from an agent shell: macOS tags agent-downloaded files with quarantine
   (`com.apple.quarantine: ...;<agent>;`) and every exec then freezes forever
   at `_dyld_start` waiting for a Gatekeeper verdict that never arrives.
   Verified 2026-08-16/17: an agent-shell ffmpeg install froze the entire
   machine's ffmpeg/ffprobe (even `-version`), wedged merges, and left
   unkillable processes.
4. Recovery from a quarantine freeze (user terminal, in order):
   `sudo xattr -dr com.apple.quarantine /opt/homebrew/Cellar` → **reboot**
   (attribute removal alone does not clear the kernel's stuck exec queue) →
   rerun preflight. Agent-side `xattr` cannot remove the tags (provenance
   protection denies it even unsandboxed).
5. A command that produces no output within ~10s is treated as FROZEN, not
   slow: stop, diagnose (`xattr -l <binary>`, `sample <pid> 2` showing
   `_dyld_start`), and report — do not retry in a loop and do not fall back to
   hand-downloaded binaries.
