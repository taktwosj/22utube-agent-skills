# PRE-119 승인 완료 대본 — 119 최초 입력

이 파일 하나에 사람이 읽는 세로 대본과 기계가 잠그는 `ASSEMBLY_ONLY_SEED`를 함께 작성한다. 사용자 승인 뒤에는 문구·카드 순서·상단 제목·하단 모드를 바꾸지 않는다.

## 구성 선택

| 구성 | between_image | between_narration | 사용할 카드 |
|---|---|---|---|
| 영상만 연속 | NO | NO | `SOURCE_VIDEO` |
| 영상 + 나레이션 | NO | YES | `SOURCE_VIDEO` + `NARRATION_VIDEO` 또는 `NARRATION_IMAGE` |
| 영상 + 나레이션 + HTML 챕터 이미지 | YES | YES | 위 카드 + `CHAPTER_CARD` |

오프닝 몽타주는 구성과 무관하게 항상 넣는다. 아래 `## 오프닝 몽타주`를 먼저 작성한 뒤
본문 카드를 이어 붙인다.

필요 없는 예시 `[CARD]` 블록은 승인 전에 삭제하고, 남은 카드의 `order`, `card_id`, `next_card`를 연속으로 다시 맞춘다.

## 오프닝 몽타주

첫 45초는 본편에서 가장 센 발화만 잘라 붙인 몽타주다. 시청자가 본편을 볼지 여기서 결정한다.

- 본편 카드에서 이미 쓰기로 한 구간 중 6~10초짜리 5~7개를 고른다.
- 시간 순서가 아니라 세기 순서로 배치한다. 가장 센 발화가 첫 카드다.
- 나레이션·해설·상단 요약을 얹지 않는다. 원본 발화와 원본 SRT만 쓴다.
- 몽타주에 쓴 구간은 본편에서 다시 나온다. 중복이 아니라 회수다.
- 마지막에 3초 CTA `CHAPTER_CARD` 하나를 붙이고 본편 첫 카드로 넘긴다.

후킹 선택 기준은 세기지 옳음이 아니다. 적대 진영을 비판하는 발화는 결론이 예측되므로
약하다. 아군 내부의 이탈·경고·자기 비판 발화가 같은 길이에서 더 강하다. 둘 다 있으면
후자를 몽타주 앞쪽에 둔다.

몽타주 카드는 새 card type이 아니라 짧은 `SOURCE_VIDEO` 카드의 연속이다. `chapter_label`은
전부 `오프닝`으로 같게 두고, `why_this_segment`에 몇 번째 세기인지 적는다.

`ASSEMBLY_ONLY_SEED`에서는 `C00_HOOK_01` 블록을 세기 순서로 5~7개 반복하고 `card_id`를
이어 붙인 뒤, 마지막에 `C00_HOOK_CTA`를 놓고 본문 첫 카드로 넘긴다. 시드 블록 안에는
`key: value`와 `[CARD]`·`[/CARD]`만 넣는다. 설명 문장을 넣으면 파서가 거부한다.

## 화면 슬롯

- 상단 챕터 제목: 모든 본문 카드의 `chapter_label`. `chapter_title`과 같은 승인 문구를 쓴다.
- 원본 영상 자막: `SOURCE_VIDEO + lower_mode=SRT` → `SOURCE_TTS`.
- 나레이션 TTS 자막: `NARRATION_VIDEO|NARRATION_IMAGE + lower_mode=SRT` → `NARRATION_TTS`.
- 논거·의견 2줄: `lower_mode=COMMENTARY_2LINE`과 `lower_line1`, `lower_line2`.
- HTML 챕터 이미지: `CHAPTER_CARD`, `style_profile=DEMOCRATIC_BLUE_CENTER_INFO_CARD_V1`, `lower_mode=NONE`.
- 하단 슬롯은 같은 시간에 한 종류만 사용한다.

## 세로 시간순 승인 대본

### 01 `<chapter_label>` — `<source start–end>`
- 화면: `<원본 영상에서 보이는 장면>`
- 원음: `<실제 화자 발언 또는 없음>`
- 나레이션: `<승인 문장 또는 없음>`
- 상단 챕터 제목: `<chapter_label>`
- 하단: `<원본 SRT | 나레이션 TTS | 논거·의견 2줄 | 없음>`
- 논거·의견 1줄: `<문구 또는 없음>`
- 논거·의견 2줄: `<문구 또는 없음>`
- 다음 카드: `<card_id | END>`

위 블록을 실제 카드 순서대로 반복한다. 한 줄에는 한 beat만 쓴다.

## ASSEMBLY_ONLY_SEED

[ASSEMBLY_ONLY_SEED]
execution_mode: ASSEMBLY_ONLY
time_policy: USE_ACTUAL_DURATION
target_runtime_lock: false
replan_allowed: false
source_research_allowed: false
approved_asset_recheck: false
lower_slot_exclusive: true
cta_default: OFF
between_image: YES
between_narration: YES
lower_mode: MIXED
cta_like_subscribe: OFF

[CARD]
order: 1
card_id: C00_HOOK_01
card_type: SOURCE_VIDEO
chapter_label: 오프닝
chapter_title: 오프닝
chapter_hook: <이 발화가 가장 센 이유>
source_id: <승인 source id>
source_range_policy: CANDIDATE_WAIT_A
source_in_candidate: <HH:MM:SS.mmm>
source_out_candidate: <6~10초 뒤>
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
why_this_segment: 몽타주 1번 — 세기 1순위
next_card: C00_HOOK_02
[/CARD]

[CARD]
order: 6
card_id: C00_HOOK_CTA
card_type: CHAPTER_CARD
chapter_label: 오프닝
chapter_title: 오프닝
chapter_hook: <구독·좋아요 요청 문구>
source_id: N/A
source_range_policy: N/A
source_in_candidate:
source_out_candidate:
visual_asset_ref: WAIT_C
visual_role: CHAPTER_TRANSITION
style_profile: DEMOCRATIC_BLUE_CENTER_INFO_CARD_V1
narration_asset_ref: N/A
narration_text:
source_audio: OFF
narration_audio: OFF
lower_mode: NONE
lower_line1:
lower_line2:
cta_like_subscribe: OFF
why_this_segment: 몽타주 종료 CTA — 무음 3초
next_card: C01_SOURCE
[/CARD]

[CARD]
order: 7
card_id: C01_SOURCE
card_type: SOURCE_VIDEO
chapter_label: <상단에 계속 노출할 챕터 제목>
chapter_title: <chapter_label과 같은 승인 문구>
chapter_hook: <이 구간의 핵심 질문>
source_id: <승인 source id>
source_range_policy: CANDIDATE_WAIT_A
source_in_candidate: <HH:MM:SS.mmm>
source_out_candidate: <HH:MM:SS.mmm>
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
why_this_segment: <이 원본 구간을 쓰는 이유>
next_card: C02_NARRATION
[/CARD]

[CARD]
order: 8
card_id: C02_NARRATION
card_type: NARRATION_VIDEO
chapter_label: <상단에 계속 노출할 챕터 제목>
chapter_title: <chapter_label과 같은 승인 문구>
chapter_hook: <나레이션이 설명할 논거>
source_id: <배경 영상 source id>
source_range_policy: CANDIDATE_WAIT_A
source_in_candidate: <HH:MM:SS.mmm>
source_out_candidate: <HH:MM:SS.mmm>
visual_asset_ref: WAIT_A
visual_role: NARRATION_BACKGROUND
style_profile: N/A
narration_asset_ref: WAIT_B
narration_text: <승인된 나레이션 문장>
source_audio: OFF
narration_audio: ON
lower_mode: SRT
lower_line1:
lower_line2:
cta_like_subscribe: OFF
why_this_segment: <나레이션이 필요한 이유>
next_card: C03_COMMENTARY
[/CARD]

[CARD]
order: 9
card_id: C03_COMMENTARY
card_type: SOURCE_VIDEO
chapter_label: <상단에 계속 노출할 챕터 제목>
chapter_title: <chapter_label과 같은 승인 문구>
chapter_hook: <이 구간의 논거>
source_id: <승인 source id>
source_range_policy: CANDIDATE_WAIT_A
source_in_candidate: <HH:MM:SS.mmm>
source_out_candidate: <HH:MM:SS.mmm>
visual_asset_ref: WAIT_A
visual_role: PRIMARY_SOURCE
style_profile: N/A
narration_asset_ref: N/A
narration_text:
source_audio: ON
narration_audio: OFF
lower_mode: COMMENTARY_2LINE
lower_line1: <논거·의견 첫 줄>
lower_line2: <논거·의견 둘째 줄>
cta_like_subscribe: OFF
why_this_segment: <논평과 원본을 함께 쓰는 이유>
next_card: C04_CHAPTER
[/CARD]

[CARD]
order: 10
card_id: C04_CHAPTER
card_type: CHAPTER_CARD
chapter_label: <다음 챕터 상단 제목>
chapter_title: <chapter_label과 같은 승인 문구>
chapter_hook: <HTML 카드 중앙 핵심 문구>
source_id: N/A
source_range_policy: N/A
source_in_candidate:
source_out_candidate:
visual_asset_ref: WAIT_C
visual_role: CHAPTER_TRANSITION
style_profile: DEMOCRATIC_BLUE_CENTER_INFO_CARD_V1
narration_asset_ref: N/A
narration_text:
source_audio: OFF
narration_audio: OFF
lower_mode: NONE
lower_line1:
lower_line2:
cta_like_subscribe: OFF
why_this_segment: <챕터 전환 이미지를 넣는 이유>
next_card: END
[/CARD]
[/ASSEMBLY_ONLY_SEED]

## 승인 뒤 금지

- 카드 추가·삭제·재정렬
- `chapter_label`, 대본, 논평, CTA 재작성
- source 재선정과 정치 이슈 재조사
- 목표 시간을 맞추기 위한 강제 retime

119는 승인 뒤 실제 path·SHA-256·duration·검증된 source range·SRT·rendered image·target timing만 결합한다.
