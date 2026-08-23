---
name: idm
description: Use when downloading a video or file with Internet Download Manager or yt-dlp, when a YouTube download returns HTTP 403 or silently lands at 360p, when a large direct file URL should be fetched fast and resumably, or when the user asks for IDM, 아이디엠, 영상 다운로드, 고화질 수집, 720p, or 다운로드 가속. Standalone; no other skill required.
---

# IDM

Route by URL type, download, then gate on ffprobe. One script does all three.

```
python scripts/idm_download.py <url> <최종폴더> [--min-height 720] [--slug 제목축약]
```

## Save path — set it per purpose

The script never decides where the file lands. The caller passes the folder.
Do not save to the Desktop or the C drive. Work output goes on the E drive,
in the folder that matches what the download is for.

| 목적 | 최종 폴더 |
| --- | --- |
| 119 정치롱폼 원본 | `E:\정치롱폼\<YYMMDD HH시>\영상\<video_id>\` |
| 정치·일반 쇼츠 소재 | `E:\쇼츠\<YYMMDD HH시>\` |
| 그 외 작업 | E 드라이브 아래 그 작업의 폴더 |

Temp job folders are the one exception: they live under `IDM_JOBS_ROOT`
(default `E:\IDM_JOBS`) and are deleted once the file is verified and moved.

## Routing — IDM is not for YouTube

| URL | 받는 것 |
| --- | --- |
| YouTube 페이지 URL | yt-dlp |
| 일반 직접 파일 URL (mp4, zip, iso …) | IDM |

**googlevideo 서명 URL 은 Range 헤더 없는 전체 요청을 거부한다.** 측정값:

```
Range 없음                 403
Range: bytes=0-            403
Range: bytes=0-1048575     206      1MB 정상
Range: bytes=0-10485759    206     10MB 정상
Range: bytes=0-20971519    302
Range: bytes=0-<전체크기>   403
```

IDM 은 전체 요청을 보낸다. 그래서 YouTube 서명 URL 을 받지 못하고 403 오류창을
띄운 채 멈춘다. 이건 쿠키나 Referer 문제가 아니고 IDM 설정으로 우회되지 않는다.
IDM 에 chunk 크기를 강제할 CLI 수단이 없다.

`--try-idm` 으로 강제할 수 있지만 실패한다. 진단 목적으로만 쓴다.

## 360p 추락의 진짜 원인은 player_client 다

기본 `android_vr` 클라이언트의 GVS URL 은 PO Token 을 요구하는데 bgutil 은 그
클라이언트용 토큰을 발급하지 못한다. 그래서 403 이 나고, 폴백이 `format 18`
(**640x360**) 을 잡아 성공으로 보고된다.

`mweb` 또는 `web_embedded` 로 고르면 발급된 토큰과 클라이언트가 일치해서 같은
영상이 720p~1080p h264 로 받아진다. 이 스크립트의 기본값이 그것이다.

```
--extractor-args "youtube:player_client=mweb,web_embedded;fetch_pot=always"
```

`web_safari`, `tv`, `ios`, `web` 은 미디어 포맷을 하나도 내주지 않는다.
`--client ""` 를 주면 yt-dlp 기본값으로 되돌아간다.

## Options

- `--min-height` — ffprobe 뒤에 적용하는 하한. 미달이면 최종 폴더로 **옮기지 않고**
  실패로 끝낸다. 119 롱폼 원본에는 `720` 을 준다. 이게 없으면 조용한 360p 폴백이
  계속 성공으로 보고된다.
- `--height` — yt-dlp 에 요청하는 상한. 기본 1080.
- `--slug` — 최종 파일명에 들어갈 제목 축약.
- `--client` — YouTube player_client. 기본 `mweb,web_embedded`.
- `--try-idm` — 페이지 URL 에도 IDM 을 시도한다. 진단용.
- `--keep-job` — 임시 작업폴더를 남긴다.

최종 파일명은 `<video_id>_<slug>_<height>p.mp4` 다. video_id 는 출처 추적을 위해
반드시 포함한다.

## 순서

1. URL 판별. 페이지 URL 이면 yt-dlp, 직접 파일 URL 이면 IDM.
2. yt-dlp 는 `h264 + m4a` 를 먼저 고른다. av1/opus 는 CapCut 에서 문제가 될 수
   있고, m4a 는 MIME 이 `audio/mp4` 라 IDM 확장자 모달도 뜨지 않는다.
3. IDM 경로는 파일명과 확장자를 검증한 뒤 `IDMan.exe /n /d <url> /p <folder> /f <name>`.
4. `ffmpeg -c copy` 병합.
5. `ffprobe` 게이트. 영상 스트림과 0 이 아닌 길이는 항상 요구한다. 음성은 페이지
   URL 일 때만 요구한다. 임의의 직접 파일에는 음성이 없을 수 있다.
6. 통과한 뒤에야 최종 폴더로 옮긴다.

IDM 이 `START_SEC` 초 안에 한 바이트도 쓰지 못하면 실패로 보고 yt-dlp 로 넘어간다.
IDM 은 완료된 파일만 대상 폴더에 쓰므로 폴더가 비어 있는 것만으로는 실패를 알 수
없고, 403 오류창이 뜨면 무한 대기하기 때문이다.

ffprobe 게이트에는 폴백이 없다.

## 파일명 규칙

확장자는 소문자 한 토큰으로 정규화한다. `[ ] " '`, 공백, 두 번째 점이 남으면
예외를 던지고 **IDM 을 호출하지 않는다**.

audio-only WebM 은 `.webm` 이 아니라 `.weba` 로 쓴다. 서버가
`Content-Type: audio/webm` 을 보내고 그 MIME 의 정식 확장자가 `.weba` 라서,
틀리게 주면 IDM 이 `/n` 으로 막히지 않는 예/아니오 모달을 띄운다.

팝업을 자동 클릭하지 않는다. 이름을 고친다.

## 실행 환경

`yt-dlp` 는 PATH 의 실행파일을 먼저 찾고, 없으면 `python -m yt_dlp` 를 쓴다.
호출한 인터프리터에 `yt_dlp` 모듈이 있다고 가정하지 않는다. Hermes venv 에는 없다.

PO Token 공급자(`bgutil-ytdlp-pot-provider`)는
`%APPDATA%\yt-dlp\plugins\bgutil\` 에 있어야 한다. 없으면 `mweb` 도 403 이 난다.

## 보고

스크립트가 출력한 실측값만 보고한다. 코덱, 해상도, 길이, 바이트 크기, 경과,
ffprobe 판정. 종료 코드만 보고 PASS 나 완료라고 하지 않는다.
