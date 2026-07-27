# 원본 자막 교정 예외 (SOURCE_SPEECH_CAPTION_FIDELITY v2)

## 왜 바뀌었나

v1은 "표시 자막 == 원본 자막" 100% 일치를 요구했다. 그 원본이 **유튜브 자동자막**이라
자동자막 자체의 오류까지 그대로 화면에 나갔다.

실제로 걸린 것들:

```text
후무총리         -> 국무총리   (ASR 오인식)
>> 대통령의…      -> 화자 표기 잔재
[음악] [박수]     -> 비발화 표기
클립 in-point 이전에 시작한 진행자 멘트 꼬리
```

v1 계약에서는 실행자가 이걸 못 고친다. 그래서 기준선을 바꾼다.

```text
v1: 기준선 = 원본 원문
v2: 기준선 = 원본 원문 + 승인 교정
```

**실행자 임의 교정은 여전히 금지다.** 바뀐 것은 "프로젝트 GPT가 확정한 교정을
계약 위반이 아니라 정상 경로로 통과시킨다"는 점뿐이다.

## 승인 권한

```text
교정 확정 권한 = PROJECT_GPT
발견·제안 권한 = 실행자 (Claude / Codex)
적용 권한      = 실행자, 단 승인된 항목만
```

실행자는 오류를 발견하면 **고치지 말고** 예외 후보로 올린다.
프로젝트 GPT가 승인한 것만 적용한다.

## 예외 카테고리

| category | 정의 | 예 |
|---|---|---|
| `ASR_TYPO` | 자동자막 오인식. 발화 자체는 정확 | `후무총리` → `국무총리` |
| `SPEAKER_MARKER` | 화자 표기 기호 제거 | `>>` `[진행자]` |
| `NONVERBAL` | 비발화 표기 제거 | `[음악]` `[박수]` `[웃음]` |
| `BOUNDARY_TRIM` | 클립 구간 밖 발화 꼬리 제외 | in-point 이전 시작 cue |
| `SEGMENTATION` | 표시 단위 재구성. 문구는 불변 | 롤링 자막 분리·병합 |

`SEGMENTATION`과 `BOUNDARY_TRIM`은 문구를 바꾸지 않으므로 기준선 비교에서
텍스트가 아니라 **범위**만 조정한다.

## 산출 파일

`30_audio_srt/source_caption_exceptions_v1.json`

```json
{
  "schema_version": "source-caption-exceptions-v1",
  "authority": "PROJECT_GPT",
  "status": "APPROVED",
  "baseline_source": "10_analysis/transcripts/Sxx.srt",
  "exceptions": [
    {
      "id": "EX-001",
      "category": "ASR_TYPO",
      "source_id": "S05",
      "source_cue_index": 42,
      "original": "후무총리 그냥 덕담 차원을 넘어서는",
      "corrected": "국무총리 그냥 덕담 차원을 넘어서는",
      "reason": "자동자막 오인식. 문맥상 국무총리.",
      "evidence": "같은 영상 07:12 화면 하단 자막과 앞뒤 문장",
      "approved_by": "PROJECT_GPT",
      "approved_at": "2026-07-26T00:00:00+09:00"
    }
  ]
}
```

필수 필드: `id` `category` `source_id` `source_cue_index` `original` `corrected`
`reason` `approved_by`. `evidence`는 `ASR_TYPO`에서 필수다.

## 검증 절차

```text
1. 원본 SRT에서 선택 cue를 뽑아 정규화 연결 -> RAW
2. 승인 예외를 순서대로 적용                -> BASELINE
3. 표시 cue를 정규화 연결                    -> RENDERED
4. RENDERED == BASELINE 이어야 PASS
5. 예외 목록에 없는 차이가 하나라도 있으면 FAIL_SOURCE_SPEECH_CAPTION_FIDELITY
```

정규화는 공백과 줄바꿈만 제거한다. 가운데점 `·`, 문장부호, 고유명사는 그대로 비교한다.

## 보고

```text
적용한 예외 수와 카테고리별 집계
예외 목록에 없는데 차이가 난 항목 (있으면 FAIL)
승인 대기 중인 예외 후보
```

예외가 없는 에피소드는 `exceptions: []`로 두고 v1과 동일하게 동작한다.

## 실행자 금지 사항

```text
승인 없이 원본 자막 문구 수정
예외 파일을 실행자가 직접 승인 상태로 만들기
카테고리를 임의로 넓혀 정치적 표현을 바꾸기
발화 내용 자체를 바꾸는 교정 (오인식 교정과 다르다)
```

마지막 항목이 핵심이다. `후무총리 -> 국무총리`는 **들린 것을 바로잡는 것**이고,
발언 취지를 바꾸는 수정은 카테고리에 없다. 그런 요청이 오면 `WAIT_ROOT_CAUSE`로
멈추고 사용자에게 확인한다.
