# Gemini Candidate Pre-index Prompt

Use this only when the user explicitly requests Gemini/AI Studio raw intake.
The result is a compact unverified index for Codex source analysis, not a final
script or source-of-truth record.

```text
쇼츠 후보 인덱스 초벌분석

영상을 관찰하고 Codex가 source.mp4를 다시 검증할 때 탐색 시간을 줄여 줄 후보만 기록한다.
반드시 UTF-8 한글 JSON 하나만 출력한다.
마크다운, 설명문, 코드블록, 인사말은 쓰지 않는다.
첫 글자는 {, 마지막 글자는 }로 끝낸다.
모든 문자열은 큰따옴표를 사용하고 JSON에 주석을 넣지 않는다.
값이 없으면 빈 문자열 "" 또는 빈 배열 []을 쓴다.

# 임무

- 최종 대본을 쓰지 않는다.
- 확정 화자발언, 확정 컷타이밍, 확정 OCR, 확정 관계/감정/원인을 만들지 않는다.
- 보이는 사실, 들리는 말 후보, 화면에 실제 보이는 글자, 해석 후보를 분리한다.
- 설계도에 반영할 가치가 있어 보이는 T1, T2, TTS, "" 화자발언, () 상황설명 후보만 뽑는다.
- 후보는 전체 합계 최대 12개로 제한하고 강한 후보부터 쓴다.
- 변화가 생기는 구간만 기록한다. 1초마다 억지로 나누지 않는다.
- 모든 후보는 Codex 검증 전 초벌값이므로 "needs_codex_verification": true로 쓴다.

# 역할 분리

- T1/T2: 상단 제목 후보다. 영상의 강한 질문, 핵심 대비, 반전 가능성을 짧게 제안한다. 사실이 아니라 해석이면 fact_source를 "inference"로 쓴다.
- TTS: 장면 의미를 풀어 주는 내레이션 후보다. 실제 발언처럼 따옴표 처리하지 않는다.
- "" 화자발언: 실제 사람 음성으로 들리는 말만 쓴다. 화면 자막을 옮겨 화자발언으로 만들지 않는다.
- () 상황설명: 화면 행동, 표정, 움직임, 카드/댓글/사연 표시만 짧게 쓴다. 실제 대사가 아니다.
- onscreen_text_ko: 화면에 실제로 보이는 글자만 쓴다.

# 사실성

- 보이는 것만 visible_fact_ko에 쓴다.
- 들리는 것만 audible_speech_candidate_ko와 speaker_quote_candidates에 쓴다.
- 추론은 interpretation_ko, T1/T2/TTS 후보, uncertainty_ko에만 쓴다.
- 이름, 나이, 기간, 장소, 관계, 직업, 사건 원인은 영상 음성/화면 글자로 확인된 경우만 쓴다.
- 불확실하면 "확인 필요"라고 쓰고 confidence를 0.3으로 낮춘다.
- fact_source는 "visual", "audio", "onscreen_text", "inference", "unknown" 중 하나만 쓴다.

# 유형 선택값

story_type:
S1_reversal_preview
S2_ranking_reorder
S3_tikitaka_variety
S4_observation_situation
S5_emotion_payoff
S6_info_explainer
S7_card_story
unknown

production_type:
full_tts_bgm
bgm_caption_only
narration_plus_speaker
original_audio_caption
tts_intro_original_body
instagram_card_tts
unknown

# 출력 구조

{
  "video_url": "",
  "video_duration_sec": 0,
  "status": "GEMINI_RAW_TIMECODE_NOT_VERIFIED",
  "summary_ko": "",
  "core_event_ko": "",
  "wow_point_ko": "",
  "payoff_ko": "",
  "shorts_type_assessment": {
    "story_type": "unknown",
    "story_type_reason_ko": "",
    "story_type_confidence": 0.3,
    "production_type": "unknown",
    "production_type_reason_ko": "",
    "production_type_confidence": 0.3
  },
  "timeline": [
    {
      "time_label": "00:00-00:00",
      "visible_fact_ko": "",
      "audible_speech_candidate_ko": "",
      "onscreen_text_ko": "",
      "interpretation_ko": "",
      "uncertainty_ko": "",
      "needs_codex_verification": true
    }
  ],
  "t1_candidates": [
    {
      "time_label": "",
      "text_ko": "",
      "basis_ko": "",
      "fact_source": "inference",
      "confidence": 0.3,
      "needs_codex_verification": true
    }
  ],
  "t2_candidates": [
    {
      "time_label": "",
      "text_ko": "",
      "basis_ko": "",
      "fact_source": "inference",
      "confidence": 0.3,
      "needs_codex_verification": true
    }
  ],
  "tts_candidates": [
    {
      "time_label": "",
      "text_ko": "",
      "basis_ko": "",
      "fact_source": "inference",
      "confidence": 0.3,
      "needs_codex_verification": true
    }
  ],
  "speaker_quote_candidates": [
    {
      "time_label": "",
      "quote_ko": "",
      "audio_basis_ko": "",
      "fact_source": "audio",
      "confidence": 0.3,
      "needs_codex_verification": true
    }
  ],
  "situation_caption_candidates": [
    {
      "time_label": "",
      "text_ko": "",
      "visible_basis_ko": "",
      "fact_source": "visual",
      "confidence": 0.3,
      "needs_codex_verification": true
    }
  ],
  "uncertainty_ko": [],
  "final_warning_ko": "이 JSON은 Gemini 초벌 후보 인덱스다. 최종 T1/T2, 대본, 화자발언, 컷타이밍, TTS/상황설명 배치는 Codex가 source.mp4와 ffprobe/STT/OCR/프레임 검증으로 확정해야 한다."
}
```
