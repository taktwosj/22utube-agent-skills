---
name: idm
description: Use when downloading a YouTube or other web video with Internet Download Manager instead of yt-dlp alone, when yt-dlp returns HTTP 403 or silently falls back to 360p, when a download must be fast or resumable, or when the user asks for IDM, 아이디엠, 영상 다운로드, 고화질 수집, or 다운로드 가속. Standalone; no other skill required.
---

# IDM

Download with IDM by handing it a signed direct stream URL, then merge and verify locally.

Never point IDM at a page URL. Never fix a popup by clicking it.

## Why this exists

IDM cannot resolve a YouTube page URL. Given one it opens its GUI and waits forever.
yt-dlp can resolve it but downloads DASH streams itself, and without a PO Token
provider those return `HTTP 403: Forbidden` partway through. The usual fallback
then picks format 18, which is **640x360**, and the run reports success.

This skill splits the job: yt-dlp resolves and signs, IDM transfers, ffmpeg merges,
ffprobe verifies.

## Save path — set it per purpose

The script never decides where the file lands. The caller passes the folder.
Do not save to the Desktop or the C drive. Work output goes on the E drive,
in the folder that matches what the download is for.

| 목적 | 최종 폴더 |
| --- | --- |
| 119 정치롱폼 원본 | `E:\정치롱폼\<YYMMDD HH시>\영상\<video_id>\` |
| 정치·일반 쇼츠 소재 | `E:\쇼츠\<YYMMDD HH시>\` |
| 그 외 작업 | E 드라이브 아래 그 작업의 폴더 |

Temporary job folders are the one exception: they live under `IDM_JOBS_ROOT`
(default `E:\IDM_JOBS`) and are deleted once the final file is verified and moved.

## Run

```
python scripts/idm_download.py <url> <최종폴더> [--height 1080] [--min-height 720] [--slug 제목축약] [--keep-job]
```

- `--height` — ceiling requested from yt-dlp.
- `--min-height` — floor enforced after ffprobe. Below it the file is **not** moved
  and the run fails. Pass `720` for 119 longform source. Without it a silent 360p
  fallback still counts as success.
- `--slug` — short title fragment for the final filename.
- `--keep-job` — keep the temp job folder for inspection.

Final filename is always `<video_id>_<slug>_<height>p.mp4`. The video id is
mandatory so a file can be traced back to its source.

## Order of operations

1. `yt-dlp -J` resolves the format chain and returns signed direct URLs.
   Format preference is `h264 + m4a` first — av1/opus can break CapCut, and
   m4a is served as `audio/mp4` so IDM raises no extension prompt.
2. Filename and extension are validated before IDM is called.
3. `IDMan.exe /n /d <url> /p <folder> /f <name>` per stream, polled to a stable size.
4. `ffmpeg -c copy` merges video and audio.
5. `ffprobe` must find a video stream, an audio stream, and a nonzero duration.
6. Only then does the file move to the destination folder.

Any failure in steps 1-4 falls back to plain yt-dlp. The ffprobe gate is not
optional and has no fallback.

## Filename rule

Extensions are normalised to one lowercase token. If `[ ] " '`, a space, or a
second dot survives, the script raises and **does not call IDM**.

Audio-only WebM is written as `.weba`, not `.webm`. The server sends
`Content-Type: audio/webm`, whose registered extension is `.weba`; give IDM the
wrong one and it opens a yes/no modal that `/n` does not suppress.

Do not automate the popup. Fix the name.

## Prerequisite: PO Token provider

If downloads land at 360p, the cause is upstream. Check the yt-dlp log for:

```
Downloading android vr player API JSON
ERROR: unable to download video data: HTTP Error 403: Forbidden
```

That means no PO Token provider is registered. Install `bgutil-ytdlp-pot-provider`
and place the plugin under `%APPDATA%\yt-dlp\plugins\bgutil\`. Until that is
fixed, `--min-height 720` will correctly fail every run rather than deliver
unusable source.

## Reporting

Report the measured values the script prints — codec, resolution, duration,
byte size, elapsed, and the ffprobe verdict. Do not report PASS or 완료 from the
exit code alone.
