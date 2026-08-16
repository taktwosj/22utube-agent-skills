# 01 입력·OCR

`NORMAL_FAST` task-owner가 원본 영상과 제공된 사용자 초벌 리뷰·Gemini 분석을 연속 확인한다. 별도 OCR·장면·음성 worker를 호출하지 않는다. OCR·장면·음성 판단은 원본 전체만 권위로 삼는다.

분석 도구는 env receipt의 경로만 쓴다(`references/environment-preflight.md`). 에피소드 중 도구 탐색·설치 금지.

| 분석 | 도구 | 산출 |
|---|---|---|
| 원본 확인 | yt-dlp, ffprobe, SHA-256 | 영상 ID·길이·해상도·스트림 |
| 화면 분석 | ffmpeg 장면변화 탐지 + 고해상도 프레임 + 직접 확인 | 행동·인물·B구간 경계 |
| OCR | tesseract(또는 가용 엔진) + 직접 확대 확인 | baked 글자 원문·표시 시간 |
| 사운드 | ffmpeg WAV 추출 + STT(가용 시) + 직접 청취 | 실제 발화·원본 나레이션·음악/효과음 |

화자발언·나레이션·상황설명 분류는 [원본 5분류 대본 계약](../references/original-source-transcript.md)의 판정 규칙(음성 우선, 어미 신호, 화자 수 추정)을 따른다.

[원본 5분류 대본 계약](../references/original-source-transcript.md)에 따라 새 에피소드 intake v2와 state에 계약 버전을 고정하고, `10_analysis/original-source-evidence.json`을 만든다. 각 변화점의 고해상도 키프레임 OCR과 source audio/caption을 SHA로 묶어 대조한다. 화면 글자와 실제 원음 발언·원본 나레이션을 분리한다. 글자가 불명확하면 확대 재확인하고 못 읽으면 `WAIT_OCR_UNRESOLVED`다. 원본에서 확인되지 않은 TTS를 만들지 않는다.

Stage 02가 각 `Bxx`에 `situation_action`, `lead_speaker`, `delivery_mode`, `narrative_function`, `split_basis`를 분리해 쓸 수 있도록 변화점과 evidence를 `10_analysis/source-analysis.md`에도 남긴다. 현재 revision을 검증한 뒤 관련 source-analysis 또는 original-source-evidence가 바뀐 경우에만 validator를 다시 실행한다.
