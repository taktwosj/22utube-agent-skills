# TTS Optional

Political longform normally preserves source speech. Do not add generated
narration unless the user explicitly asks for TTS, narration, generated voice,
or a separate audio track.

When explicitly requested, use the shared Supertone route:

```powershell
py -3.14 "${env:WORKSPACE_ROOT}\22factory_20260628\00_asset_tools\tools\make_supertone_tts.py" "<대본 텍스트>" "<출력파일.wav>"
```

Rules:

- read Supertone settings from environment only
- never print, paste, store, or serialize the API key
- on `home_windows`, the shared script can read Windows User environment as fallback
- if env or SDK is missing, stop with `WAIT_SUPERTONE_ENV_OR_SDK_MISSING`
- do not switch providers without explicit user approval
- keep generated voice as a separately named audio asset
