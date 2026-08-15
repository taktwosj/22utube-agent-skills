# 01 입력·OCR

`NORMAL_FAST` task-owner가 원본 영상, 사용자 초벌 리뷰, Gemini 분석을 연속 확인한다. 별도 OCR·장면·음성 worker를 호출하지 않는다. OCR·장면·음성 판단은 원본 전체만 권위로 삼는다. 글자가 불명확하면 확대 재확인하고 못 읽으면 `WAIT_OCR_UNRESOLVED`다.

Stage 02가 각 `Bxx`에 `situation_action`, `lead_speaker`, `delivery_mode`, `narrative_function`, `split_basis`를 분리해 쓸 수 있도록 변화점과 evidence를 `10_analysis/source-analysis.md`에 남긴다. 현재 revision을 검증한 뒤 관련 source-analysis가 바뀐 경우에만 validator를 다시 실행한다.
