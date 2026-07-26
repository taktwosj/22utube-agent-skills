# SRT 기계 검증 (P03)

전부 `0`이어야 통과. 하나라도 0이 아니면 `FAIL`이며 다음 단계로 넘어가지 않는다.
저장된 과거 PASS를 재사용하지 않는다 — 현재 실행 출력만 근거로 쓴다.

## 10항목

| # | 항목 | 검사 |
|---|---|---|
| 1 | cue 시간축 역전 | `end > start`, 그리고 다음 cue `start >= 이전 end` |
| 2 | 중복 cue | 같은 시작·종료·텍스트 조합 중복 |
| 3 | 빈 cue | 공백 제거 후 길이 0 |
| 4 | 음성 끝 초과 cue | 마지막 cue `end <= 오디오 시간축 정본 총 길이` |
| 5 | 나레이션 문장 누락 | 권위 대본 나레이션 문자열 커버리지 100% |
| 6 | 대본 문장 임의 수정 | 정규화 후 대본 원문과 문자 단위 일치 |
| 7 | 원본 클립 순서 불일치 | SRT 등장 순서 == 대본 문서 순서 |
| 8 | 원본 클립 자막 구간 누락 | 선정 클립 전부가 SRT에 존재 |
| 9 | 원본 cue 순서 불일치 | 클립 내부 cue가 원본 SRT 순서 유지 |
| 10 | 선정 구간 밖 cue 혼입 | 클립 타임코드 범위 밖 cue 없음 |

## 원본 자막 기준선

`SOURCE_SPEECH_CAPTION_FIDELITY`의 기준선은 원본 원문이 아니라
**원본 원문 + 프로젝트 GPT 승인 교정**이다.
승인 교정은 `30_audio_srt/source_caption_exceptions_v1.json`에만 기록된다.
목록에 없는 차이가 하나라도 있으면 `FAIL_SOURCE_SPEECH_CAPTION_FIDELITY`.
자세한 것은 [source-caption-exceptions.md](source-caption-exceptions.md).

## 정규화 규칙 (5·6·`SOURCE_SPEECH_CAPTION_FIDELITY` 공통)

비교 전 정규화는 **공백과 줄바꿈만** 제거한다.
문장부호·가운데점 `·`·고유명사는 정규화 대상이 아니다 — 그대로 비교한다.
`수사·기소`를 `수사, 기소`로 바꿔 비교하면 안 된다.

## 허용되는 것 / 아닌 것

```text
허용 : 화면 폭에 맞춘 기술적 줄바꿈, speech boundary 기준 cue 분할
금지 : 문구 재작성, 축약, 요약, 의역, 문장부호 자동 교정, 어미 변경
```

## 산출

```text
30_audio_srt/final_srt_draft_v1.srt
30_audio_srt/subtitle_qc_package_v1.json
90_reports/srt_validation_report_v1.json
```

검증 보고서에는 항목별 실제 카운트를 기록한다. `0`이라고 쓰기만 하고
실행하지 않은 항목은 `NOT RUN`이다.

## 상태

```text
전부 0                      -> WAIT_PROJECT_GPT_SUBTITLE_QC
1개 이상 위반               -> FAIL (수정 후 전체 재검증)
정렬 수단 확보 실패         -> SRT_ALIGNMENT = BLOCKED
                               REASON = ALIGNMENT_METHOD_UNDEFINED
교정본 미검증               -> PROJECT_GPT_CORRECTED_SRT_LOCK != PASS,
                               최종 자막 생성 금지
```
