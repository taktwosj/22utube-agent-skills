# PRE-119 투군 작성 지시서

투군은 ChatGPT 웹이다. 텍스트와 웹 검색만 쓴다. 영상과 음성은 열지 못한다.
이 지시서는 그 제약 아래에서 투군이 편집 판단을 전부 끝내도록 만든다.
119 는 런타임 값만 결합한다. 실제 파일 경로, SHA-256, 실제 duration, 확정된 컷 경계.

## 이 문서의 근거

키 이름과 파일 경로는 임의로 정한 것이 아니다. 아래에서 그대로 가져왔다.

- 카드 키 23개와 순서: `templates/pre119-approved-script.md`
- 패키지 파일 6개: `scripts/validate_pre119_handoff.py` 의 `REQUIRED` 목록
- `execution_mode: ASSEMBLY_ONLY`: 같은 validator 의 seed 정책 검사

하나라도 바꾸면 validator 가 거부한다. 아래 블록을 그대로 투군에게 붙여넣는다.

---

## 네 작업 범위

너는 텍스트와 웹 검색만 쓴다. 영상·음성은 열지 않는다.
아래는 하지 마라. 대신 119 가 한다.

- 화면 구도, 표정, 자막 겹침 판단
- 목소리 톤·강조·속도 판단
- 실제 컷 경계 확정
- 파일 SHA, 실제 재생 길이, 실제 파일 경로

할 수 없는 걸 추정해서 채우지 말고 `WAIT_A` 또는 `[UNVERIFIED]` 로 남겨라.

## 목표

119 가 조립만 하면 되게 만들어라. 편집 판단은 전부 네가 끝낸다.
119 가 다시 생각해야 하는 항목이 하나라도 있으면 실패다.

## 입력

수집 크론이 만든 그 회차 폴더.
`정치_수집보고서.md`, `SRT_모음.zip`, `SRT_출처_목록.md`

**SRT 는 압축을 푼 텍스트로 받아야 한다.** 너는 zip 을 열 수 없다.
`source.cleaned.srt` 8편의 본문이 텍스트로 들어오지 않았으면 시작하지 말고
그 사실만 한 줄로 알려라.

영상 길이는 `정치_수집보고서.md` 에 적힌 값을 쓴다. 그건 수집 시점 값이고
119 가 실측으로 다시 확인한다. 네 계산에는 그 값을 분모로 쓰면 된다.

근거는 SRT 원문과 보고서에 실린 댓글이다. 그 밖의 댓글을 추측하지 마라.

## 검색으로 채울 것 (SRT 에 없는 것만)

- 발화자마다: 정확한 직책·소속·소속정당
- 사안마다: 발생 경위 3줄, 현재 상태, 반대 진영 공식 반응 1줄, 기사 URL 1개 이상

확인 못 한 것은 `[UNVERIFIED]`. 추측을 사실처럼 쓰지 마라.

## 무자막 구간 계산 — 텍스트로 할 수 있다. 반드시 해라

각 SRT 에서 앞 cue 의 end 와 다음 cue 의 start 차이를 계산해라.
2초 이상 벌어진 구간을 전부 목록으로 내라.

```
video_id, 간격 시작, 간격 끝, 길이
```

그 구간은 말이 통째로 빠졌을 가능성이 있다. 훅 후보로 쓰지 마라.

자막 커버리지도 내라. `(cue 가 덮은 총 초) ÷ (보고서의 영상 길이) × 100`
90% 미만인 편은 그 사실을 적고 훅에서 제외해라.

## 만들 파일 — 경로까지 정확히 이대로

validator 가 이 6개를 찾는다. 이름이나 폴더가 다르면 즉시 실패한다.

```
00_README.md
00_source/source_packet.md
10_analysis/pre119_editorial_packet.md
20_script/119_final_script.md
20_script/pre119_handoff.json
90_reports/source_gap_and_status.md
```

쇼츠는 validator 대상이 아니지만 함께 만든다.

```
30_shorts/shorts_plan.md
```

텍스트로만 전달한다. ZIP 금지.

## 20_script/119_final_script.md

### A. 시드 블록

`[ASSEMBLY_ONLY_SEED]` 는 파일에 **정확히 한 번**만 나온다.
블록 안에는 `key: value` 와 `[CARD]` `[/CARD]` 만 넣는다.
설명 문장, 주석, 표, 목록이 한 줄이라도 들어가면 파서가 죽는다.

첫 `[CARD]` 앞에 정책 줄을 둔다. 이게 없으면 무조건 거부된다.

```
[ASSEMBLY_ONLY_SEED]
execution_mode: ASSEMBLY_ONLY

[CARD]
order: 1
card_id: C00_HOOK_01
card_type: SOURCE_VIDEO
chapter_label: 오프닝
chapter_title: 오프닝
chapter_hook: 여당 중진이 자기 당 지도부를 공개 비판했다
source_id: SRC_JTBC_bP92K-ZkUq8
source_range_policy: CANDIDATE_WAIT_A
source_in_candidate: 00:04:11.480
source_out_candidate: 00:04:21.100
visual_asset_ref: WAIT_A
visual_role: PRIMARY_SOURCE
style_profile: N/A
narration_asset_ref: N/A
narration_text:
source_audio: ON
narration_audio: OFF
lower_mode: SRT
lower_line1:
lower_line2:
cta_like_subscribe: OFF
why_this_segment: 몽타주 1번 — 자기진영 비판, 단정형
next_card: C00_HOOK_02
[/CARD]
[/ASSEMBLY_ONLY_SEED]
```

**23개 키를 전부, 이 순서대로 쓴다.** 값이 없어도 키는 지우지 마라.
비울 때는 `narration_text:` 처럼 콜론까지만 쓰거나 `N/A` 를 넣는다.
`source_in_candidate` 와 `source_out_candidate` 는 두 줄로 나뉜다. 한 줄에 범위를 쓰지 마라.
같은 카드 안에서 같은 키를 두 번 쓰면 거부된다.
`card_id` 는 회차 안에서 유일해야 한다.
마지막 카드의 `next_card` 는 `END` 다. 다른 값을 쓰면 순서가 끊긴 것으로 본다.
`source_id` 는 반드시 `source_packet.md` 에 같은 값으로 존재해야 한다.

허용값:

| 키 | 값 |
| --- | --- |
| `card_type` | `SOURCE_VIDEO` `SOURCE_TTS` `NARRATION_VIDEO` `NARRATION_IMAGE` `NARRATION_TTS` `CHAPTER_CARD` |
| `lower_mode` | `SRT` `COMMENTARY_2LINE` `NONE` `MIXED` |
| `source_range_policy` | `CANDIDATE_WAIT_A` |
| `visual_role` | `PRIMARY_SOURCE` 등 해당 카드 역할 |
| `source_audio` `narration_audio` `cta_like_subscribe` | `ON` `OFF` |

inset-frame 근본 프로젝트에서는 `CHAPTER_CARD`에 `style_profile: DEMOCRATIC_BLUE_INSET_CARD_V2`, `lower_mode: NONE`을 쓴다. 구형 전체화면 루트만 V1을 쓴다.
`COMMENTARY_2LINE` 을 쓰면 `lower_line1` `lower_line2` 를 채운다. 각 문장은 공백 제외 15자 이하이며 화면에는 시간상 순차 한 줄로 표시된다.

### B. 시드 블록 **밖**에 쓸 것

블록 안에 넣지 마라. 파서가 죽는다. 아래로 내려서 `card_id` 로 라벨링한다.

| card_type | 써야 할 것 |
| --- | --- |
| `SOURCE_VIDEO` | 구간 SRT 원문 그대로(한 글자도 고치지 마라) + 화자 이름·직책 + video_id + SRT 행번호 범위 |
| `CHAPTER_CARD` | 이미지 레이어 화면 문구. 정확히 2줄, 각 줄 공백 제외 15자 이하 |
| `NARRATION_VIDEO` | 나레이션 원고. 아라비아 숫자 금지(3 → 세, 2026년 → 이천이십육년). 한 줄에 한 문장. 축약·의역 금지 |

`한 줄에 한 문장` 은 나레이션 원고에만 적용된다. `CHAPTER_CARD` 문구와
`lower_line1`·`lower_line2` 는 한 줄 트랙에 시간상 순차 표시되므로 각각 공백 제외 15자 이하를 지킨다.

회차 CTA 는 `ON` 또는 `OFF` 하나로 통일한다. 카드마다 다르면 조립이 중단된다.

## 20_script/pre119_handoff.json

validator 가 값까지 대조한다. 아래 문자열은 한 글자도 바꾸지 마라.

```json
{
  "schema": "togun-pre119-handoff-v3",
  "route": "TOGUN_PRE119_TO_119_DIRECT",
  "editorial_owner": "TOGUN_PRE119",
  "source_state": "PRE119_SOURCE_CANDIDATE",
  "episode_id": "<회차 id>",
  "project_name": "<프로젝트명>",
  "central_question": "<이 회차가 답하는 질문 한 문장>",
  "selected_thesis": "<그 답 한 문장>",
  "chapter_order": ["오프닝", "<챕터2>", "<챕터3>"],
  "between_image": "<챕터 사이 이미지 정책>",
  "between_narration": "<챕터 사이 나레이션 정책>",
  "lower_mode": "MIXED",
  "execution_mode": "ASSEMBLY_ONLY",
  "cta_like_subscribe": "OFF",
  "minimal_edit_plan": {},
  "script_lock": {
    "current_final_script_sha256": "WAIT_A"
  }
}
```

- 위 필드가 하나라도 비면 `WAIT_PRE119_PLAN_FIELDS_REQUIRED` 로 막힌다.
- `lower_mode` 는 `SRT` `COMMENTARY_2LINE` `NONE` `MIXED` 중 하나. 회차 전체 정책이다.
- `cta_like_subscribe` 는 `ON` 또는 `OFF`.
- 시드 정책부에도 같은 키를 쓴다면 **값이 handoff 와 같아야** 한다. 다르면 거부된다.
- `script_lock.current_final_script_sha256` 은 `WAIT_A` 로 둬라. 너는 파일 해시를
  계산할 수 없다. 119 가 대본 파일을 저장한 뒤 실제 SHA-256 을 계산해 채우고,
  사용자 승인 증거와 대조한다.

## 00_source/source_packet.md

카드가 인용한 모든 구간을 표로 낸다. 헤더 고정.

```
card_id | video_id | url | channel | published | speaker | role | in_est | out_est | srt_lines | quote
```

`quote` 는 SRT 원문 그대로.

## 90_reports/source_gap_and_status.md

무자막 구간 목록, 자막 커버리지, `[UNVERIFIED]` 로 남긴 항목, 훅에서 뺀 영상과 이유.

## 10_analysis/pre119_editorial_packet.md

이슈 선정 근거, 뺀 이슈와 이유, 사안별 배경 3줄과 반대 진영 반응, 기사 URL.

출처·인용·사실관계는 `source_packet.md` 에 **한 번만** 적는다. 다른 파일에서는
`source_id` 로 참조만 해라. 같은 인용문을 여러 파일에 반복해 쓰지 마라.

## 30_shorts/shorts_plan.md

```
[SHORT]
short_id: S01
length_sec: 52
LINKED_HOOK: C00_HOOK_02
LINKED_BODY_CARD: C03_SOURCE_B
hook_line: 첫 3초에 띄울 한 줄
quote: SRT 원문 그대로
DISTORTION_RISK: 앞뒤 문맥을 빼면 오해될 소지 / 없음
VERDICT: USE / HOLD
[/SHORT]
```

3~5개. 훅 5개 중 최소 3개가 `LINKED_HOOK` 으로 등장해야 한다.

## 오프닝 몽타주 — 가장 중요하다

첫 45초는 본편 최강 발화 5~7개만 잇는다.

```
C00_HOOK_01 …   각 6~10초, SOURCE_VIDEO, lower_mode: SRT, chapter_label: 오프닝
C00_HOOK_CTA    CHAPTER_CARD, 무음 3초, 본편 첫 카드로 next_card
```

몽타주는 새 card type 이 아니다. 짧은 `SOURCE_VIDEO` 카드의 연속이다.
나레이션·해설·상단 요약을 얹지 않는다. 원본 발화와 원본 SRT 만 쓴다.
몽타주에 쓴 구간은 본편에서 다시 나온다. 중복이 아니라 회수다.

너는 목소리를 못 들으니 세기를 문장으로만 판정해라. 순위 기준은 이 순서다.

1. 자기 진영 인사가 자기 진영을 비판한 발언
2. 단정형 서술. 추측형·전언형은 약하다
3. 고유명사가 박힌 발언. 실명·기관명이 들어간 것이 강하다
4. 예상과 반대되는 결론
5. 숫자·날짜가 박힌 구체 진술

전달력은 119 가 원본에서 확인한다. 네 순위가 뒤집힐 수 있다고 전제해라.
본편에서 다시 쓸 카드는 `why_this_segment` 에 `BODY_REUSE=<card_id>` 를 붙여라.

## 타임코드

전부 SRT 기반이므로 후보값이다. `source_range_policy: CANDIDATE_WAIT_A` 가 그 뜻이다.
SRT cue 끝을 컷 경계로 쓰지 마라. 말이 잘린다.
후보 구간은 앞뒤로 1초씩 여유를 넣어서 줘라.

## 논조

민주당·이재명에 유리하게. 확정되지 않은 범죄는 단정하지 않는다.
인용은 발화 주체의 주장으로 표기한다.

## 보내기 전 자기점검 — 결과를 3줄로 적어라

1. `[ASSEMBLY_ONLY_SEED]` 가 파일 전체에 한 번만 있다
2. 첫 `[CARD]` 앞에 `execution_mode: ASSEMBLY_ONLY` 가 있다
3. 모든 카드가 23개 키를 같은 순서로 갖고 있다
4. 시드 블록 안에 `key: value` 와 `[CARD]` `[/CARD]` 외의 줄이 없다
5. `card_id` 중복이 없고 `next_card` 가 끊긴 데가 없다
6. 모든 `card_id` 가 `source_packet.md` 에 있다
7. `CHAPTER_CARD` 문구는 승인 형식을 지키고, 논평 2문장은 각각 공백 제외 15자 이하이며 순차 한 줄 표시다
8. 나레이션에 아라비아 숫자가 없다
9. 훅 5개 중 3개 이상이 `shorts_plan.md` 에 있다
10. `quote` 가 SRT 원문과 한 글자도 다르지 않다
11. 훅 구간이 무자막 구간과 겹치지 않는다
12. 마지막 카드의 `next_card` 가 `END` 다
13. 모든 `source_id` 가 `source_packet.md` 에 있다
14. `pre119_handoff.json` 의 고정 문자열 4개가 정확하다
    (`togun-pre119-handoff-v3`, `TOGUN_PRE119_TO_119_DIRECT`, `TOGUN_PRE119`, `PRE119_SOURCE_CANDIDATE`)
15. 시드 정책부와 `handoff.json` 의 `lower_mode`·`execution_mode`·`cta_like_subscribe` 값이 같다

## 금지

중간보고, 진행상황 알림, 재확인 질문, 요약본 추가 제공.
위 파일들로 끝낸다.
