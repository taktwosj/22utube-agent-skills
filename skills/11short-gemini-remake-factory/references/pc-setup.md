# Other PC Setup

Use this when installing the 11short Gemini remake workflow on another Windows PC.

## OneDrive

Keep this folder local with "Always keep on this device":

```text
%USERPROFILE%\OneDrive\22utube
```

Set session environment variables before production:

```powershell
$env:WORKSPACE_ROOT = "$env:USERPROFILE\OneDrive\22utube"
$env:UTUBE_ROOT = "$env:WORKSPACE_ROOT\11utube"
$env:SHORT_ROOT = "$env:UTUBE_ROOT\11short"
```

## Install Skill From OneDrive

Copy this skill into Codex skills:

```powershell
$skillSrc = "$env:SHORT_ROOT\skills_sync\11short-gemini-remake-factory"
$skillDst = "$env:USERPROFILE\.codex\skills\11short-gemini-remake-factory"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force -LiteralPath $skillSrc -Destination $skillDst
```

Restart Codex after copying.

## Required Local Tools

Check these before production:

```powershell
py -3 --version
py -3 -m yt_dlp --version
ffmpeg -version
ffprobe -version
```

CapCut Desktop must be installed. Google AI Studio must be accessible in the browser account used on that PC.

## Supertone Key

The key must be available as `SUPERTONE_API_KEY` in one of the repo `.env` locations used by `supertone_11short_tts.py`. Do not print the key.

Recommended check:

```powershell
Select-String -LiteralPath "$env:UTUBE_ROOT\.env" -Pattern "^\s*SUPERTONE_API_KEY\s*=" -Quiet
```

If the key is stored in `mindset\.env`, the existing TTS script can also load it.

## CapCut Reference Draft

The current exact visual reference is local, not automatically provided by a skill:

```text
%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\0613 FIRE
```

On a new PC, first check whether it exists:

```powershell
Test-Path "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\0613 FIRE"
```

If missing, either copy that CapCut draft folder from the production PC or ask the user whether to run the factory without the reference draft. When the user asked for the exact current process, prefer copying the reference draft.

## User Prompt On Other PC

After installing the skill, a typical request is:

```text
[$000brainstorm] [$11short-gemini-remake-factory] https://www.youtube.com/shorts/VIDEOID
Gemini 분석부터 CapCut 초안 생성, analysis/assets/capcut/all 하네스 PASS, 업로드 문구까지 진행해줘.
```

If skill chips are not available, use plain text:

```text
Use 11short-gemini-remake-factory from OneDrive. Run Brainstorm first, use Gemini/AI Studio URL context, then make the full 11short CapCut draft and stop on any harness FAIL.
```
