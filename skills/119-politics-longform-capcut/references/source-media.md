# 출처 미디어

대본 승인 뒤 A 작업자 한 명이 수행한다. 입력은 승인 대본과 출처 URL·SRT·로컬 미디어다. 출력은 이 회차 source media와 source captions뿐이다. narration, Resources, root, target, CapCut draft, `episode_cards.json`을 수정하지 않는다.

ASSEMBLY_ONLY에서 동일 source identity·media SHA·transcript SHA·검증된 컷이 PASS이면 다시 다운로드·메타데이터 조회·exact quote 검증을 하지 않는다.

## 순서

1. SRT 시간대와 문장으로 후보 구간을 좁힌다.
2. 같은 원본은 전체를 한 번만 다운로드한다.
3. `yt-dlp --download-sections`를 쓰지 않는다.
4. 로컬 `ffmpeg`로 승인 발화·편집 리듬에 맞춰 필요한 구간만 자른다.
5. 다운로드와 컷 직후 `ffprobe`로 stream과 길이를 확인한다.
6. 원본 bytes로 SHA-256을 계산한다.
7. 실제 cut에서 source caption을 split 또는 clamp한다.
8. 표시용 SRT를 평균 15자/줄, 최대 2줄로 정리한다.
9. raw cut transcript와 display SRT의 텍스트 보존을 `validate_srt_text_fidelity.py`로 확인한다.

ASR cue 경계는 컷 지점을 정하지 않는다.

## source caption 표시 계약

```text
TARGET_CHARS_PER_LINE = 15
MAX_LINES             = 2
TARGET_CHARS_PER_CUE  = 30
HARD_MAX_LINE_CHARS   = 18
```

원본 발화 텍스트를 축약·의역·자연화하지 않는다. 30자를 넘으면 문장부호·어절·호흡 경계에서 다음 cue로 나누고 source cut 경계는 바꾸지 않는다.

허용 display transform:

```text
SPLIT
CLAMP
LINE_BREAK
DIALOGUE_MARKER_REMOVAL
```

`CLAMP`는 컷 경계의 앞뒤 연속 구간 제거만 허용한다. 내부 단어 추가·삭제·치환은 `SOURCE_TRANSCRIPT_TEXT_CHANGED`다.

## 실패와 재개

다운로드·stream·duration·hash·local cut·caption layout·text fidelity에서 실제 실패가 난 파일만 다시 처리한다. 완료 시 join owner에게 실제 경로, source in/out, duration, SHA-256, raw transcript SHA, 표시 SRT SHA를 전달한다.
