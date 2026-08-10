# 출처 미디어

대본 승인 뒤 A 작업자 한 명이 수행한다. 입력은 승인 대본과 출처 URL·SRT·로컬 미디어다.
출력은 이 회차의 source media와 source captions뿐이다. narration, Resources, root, target,
CapCut draft, `episode_cards.json`을 수정하지 않는다.

ASSEMBLY_ONLY에서 동일 source identity·media SHA·transcript SHA·검증된 컷이 이미 PASS이면
다시 다운로드·메타데이터 조회·exact quote 검증을 하지 않는다.

## 순서

1. SRT 시간대와 문장으로 필요한 후보 구간을 좁힌다.
2. 같은 원본은 전체를 한 번만 다운로드한다.
3. `yt-dlp --download-sections`를 쓰지 않는다.
4. 로컬 `ffmpeg`로 승인된 발화·편집 리듬에 맞춰 필요한 구간만 자른다.
5. 다운로드와 컷 직후 `ffprobe`로 video/audio stream과 길이를 확인한다.
6. 원본 bytes로 SHA-256을 계산한다.
7. 실제 cut에서 source caption을 split 또는 clamp한다.
8. 화면 표시용 source SRT를 `평균 15자/줄, 최대 2줄`로 정리한다.

ASR cue 경계는 컷 지점을 정하지 않는다. cue에 맞추기 위해 source in/out을 이동하지 않는다.

## source caption 표시 계약

```text
TARGET_CHARS_PER_LINE = 15
MAX_LINES             = 2
TARGET_CHARS_PER_CUE  = 30
HARD_MAX_LINE_CHARS   = 18
```

- 원본 발화 텍스트를 축약·의역·자연화하지 않는다.
- 각 cue는 한 줄 또는 두 줄만 허용한다.
- 평균 한 줄 15자를 목표로 하며, 두 줄 전체는 30자 이내로 한다.
- 한 줄이 18자를 넘으면 FAIL이다.
- 30자를 넘는 문장은 문장부호·어절·호흡 경계에서 다음 cue로 나눈다.
- cue 분할은 같은 source cut 안에서 시간상 연속되게 하고 source cut 경계를 바꾸지 않는다.
- 글자를 줄이기 위해 font size를 축소하지 않는다.
- 작업 메모나 CLEAN_SUMMARY를 source SRT에 넣지 않는다.

검증:

```powershell
python scripts/validate_politics_caption_layout.py `
  --srt <source_caption.srt> `
  --report <caption_report.json>
```

## 실패와 재개

다운로드·stream·duration·hash·local cut·caption layout에서 실제 실패가 난 파일만 다시 처리한다.
정상 원본과 완료 컷은 다시 분석하지 않는다. 완료 시 join owner에게 실제 경로, source in/out,
duration, SHA-256, transcript SHA, 표시용 SRT만 전달한다.
