# 02 원본표

Source analysis에서 장면·전사·화자·화면 문구가 바뀌는 지점으로 `B01…BN`을 나눈다. 순서를 바꾸거나 개선안을 넣지 않는다.

1. 관찰 근거, source beat, 대화 의존성, 원본 순서를 `20_script/original-blueprint.md`에 기록한다.
2. [원본 5분류 대본 계약](../references/original-source-transcript.md)을 읽고 `templates/original-capcut-grid.md`로 별도 정본 `20_script/original-capcut-grid.md`를 만든다.
3. 15행 표보다 먼저 모든 B구간에 `(상황설명)`, `"화자발언"`, `<나레이션>`, `TTS화자발언`, `TTS나레이션`을 정확히 이 순서로 쓴다. 부재는 `없음`이다.
4. 가로 머리글을 `B01 <source start>–<source end>` 형식으로 연속 작성하고 앞의 5분류 블록 ID·시간과 정확히 맞춘다.
5. 세로축은 고정 15행을 순서대로 모두 작성한다.
6. 모든 교차 셀을 실제 값, `없음`, 또는 `비움`으로 채운다. 빈 칸과 placeholder를 남기지 않는다.
7. 원본에 없는 것은 `없음`, 최종 조립에서 의도적으로 비울 것은 `비움`으로 구분한다.
8. 판단하지 못한 값은 `미확인`으로 표시하되 다음 단계로 넘기지 않는다.

Stage 02를 끝내기 전에 실행한다. validator는 canonical state·intake v2·`original-source-evidence.json`을 자동으로 읽으며 새 계약에서 누락·SHA drift·분류 불일치를 거부한다.

```text
python -B scripts/validate_capcut_grids.py \
  --original <episode_root>/20_script/original-capcut-grid.md \
  --original-only
```

원본표 전체를 대화창에 출력한다. 파일 링크나 요약으로 대체하지 않는다.
