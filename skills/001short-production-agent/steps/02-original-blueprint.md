# 02 원본표

Source analysis에서 장면·전사·화자·화면 문구가 바뀌는 지점으로 `B01…BN`을 나눈다. 순서를 바꾸거나 개선안을 넣지 않는다.

1. 관찰 근거, source beat, 대화 의존성, 원본 순서를 `20_script/original-blueprint.md`에 기록한다. 각 `Bxx`에는 `situation_action`, `lead_speaker`, `delivery_mode`, `narrative_function`, `split_basis` 다섯 필드를 모두 별도로 쓴다.

   - `situation_action` ↔ `상황·행동`
   - `lead_speaker` ↔ `주도 화자`
   - `delivery_mode` ↔ `전달 방식`
   - `narrative_function` ↔ `서사 기능`
   - `split_basis` ↔ `구조 분리 근거`
2. [원본 5분류 대본 계약](../references/original-source-transcript.md)을 읽고 `templates/original-capcut-grid.md`로 별도 정본 `20_script/original-capcut-grid.md`를 만든다.
3. 15행 표보다 먼저 모든 B구간에 `(상황설명)`, `"화자발언"`, `<나레이션>`, `TTS화자발언`, `TTS나레이션`을 정확히 이 순서로 쓴다. 부재는 `없음`이다.
4. 가로 머리글을 `B01 <source start>–<source end>` 형식으로 연속 작성하고 앞의 5분류 블록 ID·시간과 정확히 맞춘다.
5. 세로축은 고정 15행을 순서대로 모두 작성한다.
6. 모든 교차 셀을 실제 값, `없음`, 또는 `비움`으로 채운다. 빈 칸과 placeholder를 남기지 않는다.
7. 원본에 없는 것은 `없음`, 최종 조립에서 의도적으로 비울 것은 `비움`으로 구분한다.
8. 판단하지 못한 값은 원본을 다시 확인한다. `미확인`, `TBD`, `placeholder`가 남아 있으면 validator가 Stage 03 진입을 거부한다.

다섯 관찰 필드와 원본 5분류 대본은 모두 원본 관찰 정본이다. Stage 03의 해석이나 새 편집 의도로 덮어쓰지 않는다. `original-blueprint.md`와 `original-capcut-grid.md`의 `Bxx` 집합은 정확히 같아야 한다.

Stage 02를 끝내기 전에 실행한다. 첫 validator는 다섯 관찰 필드의 누락·placeholder를 거부한다. 둘째 validator는 canonical state·intake v2·`original-source-evidence.json`을 자동으로 읽으며 누락·SHA drift·분류 불일치를 거부한다.

```text
python -B scripts/validate_original_blueprint.py \
  --original-blueprint <episode_root>/20_script/original-blueprint.md

python -B scripts/validate_capcut_grids.py \
  --original <episode_root>/20_script/original-capcut-grid.md \
  --original-only
```

원본표 전체를 대화창에 출력한다. 파일 링크나 요약으로 대체하지 않는다.
