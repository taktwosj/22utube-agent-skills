# 정치 롱폼 소형 원본자막 트랙 설계

## 목표

정치 롱폼의 원본 발언 자막을 하단 2줄 평론과 분리된 수정 가능한 CapCut 텍스트 트랙으로 추가한다. 자막은 평론보다 작고, 실제 발화 타이밍에 맞으며, 기존 영상에 박힌 자막과 화면 중복을 만들지 않는다.

## 승인된 화면 규격

- 캔버스는 `1920x1080`이다.
- 역할 이름은 `source_caption`이며 `track_type=text`, `editability=editable`이다.
- 위치는 하단 2줄 평론 바로 위의 비충돌 영역이다.
- 글자 크기는 CapCut 절대 크기 `8.0`이며 하단 평론과 같은 시각 크기다.
- 흰색 글자와 검은 외곽선을 사용하며 cue 하나당 최대 1줄이다.
- 자막은 평론 구간 약 20초 단위가 아니라 실제 발화 문장별로 나뉜다.
- 무음 또는 발화가 없는 구간의 자연스러운 자막 공백은 허용한다.
- 원본 영상에 박힌 자막이 있으면 먼저 크롭 또는 마스킹하고, 불가능하면 `NEEDS_VISUAL_REVIEW`로 둔다. 같은 자막을 두 겹으로 노출하지 않는다.

## 데이터 계약

Stage 1의 `design_blueprint_draft.json`과 `timeline_design_draft.json`은 동일한 `source_caption_track` 정책 객체를 가진다. 실제 cue별 문자열과 시작·종료 시간은 Stage 2에서 원음 대조와 speech boundary lock이 끝난 뒤 승인 timeline에 기록한다.

`source_caption_track` 필수값:

```json
{
  "status": "CANDIDATE",
  "enabled": true,
  "role": "source_caption",
  "track_type": "text",
  "editability": "editable",
  "text_basis": "verified_source_transcript",
  "timing_basis": "speech_cue_after_speech_boundary_lock",
  "placement": "above_lower_commentary",
  "font_size_absolute": 8.0,
  "max_lines": 1,
  "style": {
    "fill": "#FFFFFF",
    "stroke": "#000000",
    "stroke_required": true
  },
  "natural_gaps_allowed": true,
  "collision_policy": "no_overlap_with_lower_commentary",
  "burned_in_caption_policy": "crop_or_mask_else_needs_visual_review",
  "stage2_lock_required": true
}
```

## Stage 2 조립 계약

speech boundary lock 이후 전체 SRT/TXT와 원음을 대조해 발화 cue를 확정한다. cue는 locked clip 경계를 넘지 않게 자르고, 소스 전환점에서 이전 소스 자막을 종료한다. 승인된 cue마다 CapCut 텍스트 세그먼트 하나만 만들며 root JSON과 `Timelines/*` 미러를 함께 패치한다.

## 검증

- 설계 JSON 두 파일의 `source_caption_track` 객체가 완전히 같아야 한다.
- `role=source_caption`, `track_type=text`, `editability=editable`, 절대 크기 `8.0`, 최대 1줄을 확인한다.
- Stage 2에서는 승인 timeline과 CapCut의 자막 문자열·시작·종료가 cue별로 일치해야 한다.
- 자막과 하단 평론의 화면 충돌, 박힌 자막과의 이중 노출, cue 중복이 없어야 한다.
- frame QA에는 원본 자막과 하단 2줄 평론이 함께 보이는 프레임을 포함한다.

## 범위 밖

이번 변경은 Stage 1 설계와 공통 조립 계약을 갱신한다. speech lock, locked clips, CapCut 프로젝트 생성, 렌더와 업로드 준비 상태는 만들거나 주장하지 않는다.
