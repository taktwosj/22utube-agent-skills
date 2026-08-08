# 출처 미디어

대본 승인 뒤 A 작업자 한 명이 수행한다. 입력은 승인 대본과 출처 URL·SRT·로컬 미디어다.
출력은 이 회차의 source media와 source captions뿐이다. narration, Resources, root, target,
CapCut draft, `episode_cards.json`을 수정하지 않는다.

## 순서

1. SRT의 시간대와 문장으로 필요한 구간을 먼저 좁힌다.
2. 같은 원본은 `yt-dlp`로 전체를 한 번만 다운로드한다.
3. `yt-dlp --download-sections`를 쓰지 않는다.
4. 로컬 `ffmpeg`로 승인된 발화·편집 리듬에 맞춰 필요한 구간만 자른다.
5. 각 다운로드와 컷 직후 `ffprobe`로 video/audio stream 존재와 길이를 확인한다.
6. 해시 대상 파일은 text mode로 다시 쓰지 않고 원본 bytes로 SHA-256을 계산한다.

ASR cue 경계는 컷 지점을 정하지 않는다. 실제 cut이 cue를 가르면 표시 자막을 그 cut에서
split 또는 clamp한다. cue 경계에 맞추기 위해 source in/out을 이동하거나 정상 미디어를
실패 처리하지 않는다.

## 실패와 재개

활성 source 파일의 다운로드·stream·duration·hash·local cut 검사에서 구체적 실패가 난
파일 하나만 다시 처리한다. 정상인 전체 원본과 완료된 컷은 다시 다운로드하거나 분석하지
않는다. 실제 source media와 captions가 재개점이며 별도 receipt나 checkpoint를 만들지 않는다.

완료 시 join owner에게 실제 경로, source in/out, duration, SHA-256, 자막 구간만 전달한다.
