# 사용자 최종 교정 SRT 잠금

## 적용 조건

사용자가 자동자막 또는 1차 자막을 직접 교정해 SRT를 제공하거나 교정 목록과 함께
“반영해서 최종 진행”이라고 지시하면 이 계약을 적용한다. 사용자 교정본은 이후
자막 제작과 CapCut 텍스트의 최종 권위다.

## 처리 순서

1. 사용자 파일을 episode의 `30_audio_srt` 아래 최종 교정 SRT로 복사한다.
2. 원본 파일과 episode 사본의 SHA-256이 같은지 확인한다.
3. 사용자가 지정한 교정 목록을 JSON으로 기록한다.
4. `validate_final_corrected_srt.py`로 이전 오타, 제거 표기, 반복 문장을 검사한다.
5. 검증된 SRT의 cue 수, 줄바꿈, 문장부호, 시작·종료 시간을 잠근다.
6. CapCut에는 번인 자막이 없는 깨끗한 영상과 편집 가능한 텍스트 자막을 사용한다.
7. 두 줄 cue는 문구를 고치지 않고 두 개의 시간상 연속 한 줄 cue로 분할한다.
8. 한 줄 트랙의 연속 cue를 다시 합쳐 최종 SRT와 전문·시간을 대조한다.

## 교정 목록 예시

```json
{
  "replacements": [
    {"from": "20분한테", "to": "20명한테"},
    {"from": "인사 혁신 처장", "to": "인사혁신처장"},
    {"from": "인유한", "to": "인요한"},
    {"from": "증축로는", "to": "증축으로는"},
    {"from": "초기에지이", "to": "초기에는 이"},
    {"from": "한점 전부터", "to": "한참 전부터"},
    {"from": "제가발", "to": "재개발"},
    {"from": "정권 재창도", "to": "정권 재창출도"},
    {"from": "수사,기소", "to": "수사·기소"},
    {"from": "재건축,재개발", "to": "재건축·재개발"}
  ],
  "remove_tokens": ["[콧방귀]", "[웃음]", ">>"],
  "max_occurrences": {"정리하겠습니다": 1}
}
```

## 잠금 규칙

- 사용자 교정본을 다시 자동 교정, 축약, 요약, 의역하지 않는다.
- 사용자 교정본의 가운데점 `·`, 띄어쓰기, 고유명사와 문장부호를 보존한다.
- `[콧방귀]`, `[웃음]`, `>>`처럼 제거 지시된 표기는 화면 자막에 남기지 않는다.
- 결론부의 `정리하겠습니다` 같은 연속 반복은 사용자 교정본에 남은 횟수를 넘기지
  않는다.
- 마지막 cue가 프로젝트 끝을 10ms 이하로 넘는 경우에만 종료점을 프로젝트 끝으로
  clamp할 수 있다. 본문과 시작점은 바꾸지 않는다.
- 교정 SRT와 CapCut 재구성 자막이 다르면
  `FAIL_FINAL_CORRECTED_CAPTION_FIDELITY`로 중단한다.

## 필수 게이트

```text
USER_CORRECTED_SRT_LOCK=PASS
USER_CORRECTED_SRT_SHA256=PASS
USER_CORRECTION_RULES=PASS
FINAL_CORRECTED_CAPTION_COUNT=PASS
FINAL_CORRECTED_CAPTION_FIDELITY=PASS
NO_SPEAKER_MARKERS_VISIBLE=PASS
NO_NOISE_TAGS_VISIBLE=PASS
CONCLUSION_OPENING_SINGLE_INSTANCE=PASS
```
