# 나레이션

대본 승인 뒤 B 작업자 한 명이 수행한다. 입력은 승인 대본의 나레이션 문장이다. 출력은 narration audio/video와 narration SRT뿐이다. source, Resources, root, target, CapCut draft, `episode_cards.json`을 수정하지 않는다.

ASSEMBLY_ONLY에서 승인 대사와 동일하고 실제 audio/SRT·SHA·duration이 PASS이면 다시 합성하지 않는다.

## 순서

1. 기존 승인 Supertone 설정이 있으면 승인 나레이션 문장만 합성한다.
2. 파일 존재·audio stream·duration을 확인한다.
3. 실제 audio를 시간축 정본으로 정렬한다.
4. narration SRT의 누락·중복·역순·겹침을 확인한다.
5. 표시 자막을 평균 15자/줄, 최대 2줄로 분할한다.

목표 초수·40:60 비율은 사용자 절대 LOCK이 아니면 `[EST]`다. 강제 배속·과도한 time-stretch·무음 패딩·승인되지 않은 대사 추가를 하지 않는다.

```text
TARGET_CHARS_PER_LINE = 15
MAX_LINES             = 2
TARGET_CHARS_PER_CUE  = 30
HARD_MAX_LINE_CHARS   = 18
```

승인 대사의 단어·문장 내용을 바꾸지 않는다. `COMMENTARY_2LINE` 시간대에는 narration SRT를 동시에 넣지 않는다.

실패가 난 실제 API·audio integrity·alignment·SRT·caption layout만 다시 실행한다.
