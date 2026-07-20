# Vmake Clean Source Workflow

Use this workflow only for a Shorts package that will continue to production.
The original source remains the evidence and audio-analysis authority. Vmake
creates a separate clean visual for later CapCut assembly.

## Fixed Roles

```text
00_source/source.mp4
-> OCR, STT, frame checks, source identity, full-source Demucs input

00_source/clean_source.mp4
-> production visual only
-> embedded audio muted_always

10_analysis/audio/vocals.wav
-> speaker/Q range source
```

Never run OCR, STT, source identity, or Demucs against `clean_source.mp4`.
Never use the embedded audio from either video in CapCut. Audible speaker/Q
segments come only from the full-source Demucs `vocals.wav`.

## Chrome Automation

Open:

```text
https://vmake.ai/video-watermark-remover/upload
```

Use the existing signed-in Chrome session and DOM/browser control. Do not use
OS-level mouse/keyboard control.

1. Click `Import from link` under `Or import from link`.
2. Fill the textbox whose placeholder is:

   ```text
   We support YouTube, TikTok, IG, and FB links.
   ```

3. Check:

   ```text
   I confirm I have the rights to use the imported links.
   ```

   Check it only when the user explicitly confirmed rights for the current
   source URL. Otherwise stop with `WAIT_VMAKE_RIGHTS_CONFIRMATION`.

4. Click the enabled arrow button in the same import tooltip.
5. Wait for `Getting file from the link...` to disappear.
6. Confirm the new card shows `To be processed` and `Click Apply to begin`.
7. Keep `Auto` selected and click `Apply`.
8. Monitor the same card while it shows `Processing...`. Leaving the page does
   not stop the Vmake job.
9. When the newest card exposes `Download`, bind it to the displayed
   `File from link - ...<job suffix>` before clicking.
10. Confirm the resulting filename is:

    ```text
    File_from_link_-_<vmake-job-id>.mp4
    ```

## Download Recovery

Chrome or IDM may navigate to the signed MP4 URL and show
`ERR_BLOCKED_BY_CLIENT` instead of saving the file. This is a supported recovery
case only when all of the following are true:

- the URL came directly from the newest Vmake job's `Download` button;
- the host ends in `.stariidata.com`;
- the path ends in `.mp4`;
- both `attname` and `filename` contain the same Vmake job ID;
- the target filename starts with `File_from_link_`.

Return to the Vmake editor, download that exact signed URL directly into the
current user's Downloads folder, and record
`download_method=direct_signed_url_fallback`. Do not guess or rewrite the signed
URL.

## Registration And Gate

After the file is complete and `ffprobe` can read it, run:

```powershell
py -3 skills/00-tikitaka/scripts/register_vmake_clean_source.py `
  --root <episode-root> `
  --download "$env:USERPROFILE\Downloads\File_from_link_-_<vmake-job-id>.mp4" `
  --source-url "<current-shorts-url>" `
  --job-id "<vmake-job-id>" `
  --rights-confirmed `
  --confirmation-source user `
  --download-method direct_signed_url_fallback
```

This copies the result to:

```text
00_source/clean_source.mp4
```

and writes:

```text
10_analysis/vmake_clean_source.json
```

The `VMAKE_CLEAN_SOURCE_GATE` validates:

- exact source video ID and locked original SHA-256 binding;
- explicit user rights confirmation;
- Vmake job ID and downloaded filename binding;
- clean file SHA-256;
- original/clean duration parity within 0.5 seconds;
- original/clean aspect-ratio parity;
- `embedded_audio_policy=muted_always`;
- `source_voice_policy=separate_demucs_q_only`.

For `stage_1_script`, record `NOT_REQUIRED_STAGE1_ONLY`. For
`stage_2_full`, missing or invalid evidence is `WAIT_VMAKE_CLEAN_SOURCE`.
