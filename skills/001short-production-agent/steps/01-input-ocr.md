# 01 입력·OCR
원본 영상, 사용자 초벌 리뷰, Gemini 분석을 받는다. OCR·장면·음성 판단은 원본 전체만 권위로 삼는다.

[원본 5분류 대본 계약](../references/original-source-transcript.md)에 따라 새 에피소드 intake v2와 state에 계약 버전을 고정하고, `10_analysis/original-source-evidence.json`을 만든다. 각 변화점의 고해상도 키프레임 OCR과 source audio/caption을 SHA로 묶어 대조한다. 화면 글자와 실제 원음 발언·원본 나레이션을 분리한다. 글자가 불명확하면 확대 재확인하고 못 읽으면 `WAIT_OCR_UNRESOLVED`다. 원본에서 확인되지 않은 TTS를 만들지 않는다.
