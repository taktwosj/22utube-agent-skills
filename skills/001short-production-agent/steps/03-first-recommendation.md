# 03 우라까이표

검증된 원본표에서 최종 장면 순서와 표현 방식을 결정한다.

1. 구조 추천, 훅, target order, 오디오 정책을 `20_script/first-recommendation.md`에 기록한다.
2. `templates/urakkai-capcut-grid.md`를 사용해 별도 정본 `20_script/urakkai-capcut-grid.md`를 만든다.
3. 가로 머리글을 `V01 <target start>–<target end> Bxx` 형식으로 연속 작성한다.
4. 세로축은 원본표와 같은 고정 15행을 같은 순서로 모두 작성한다.
5. 모든 교차 셀을 실제 값, `없음`, 또는 `비움`으로 채운다. 빈 칸과 `미확인`을 남기지 않는다.
6. `A9`는 실제 나레이션 오디오, `A9_TEXT`는 그 음성과 같은 자막이다. 소리 없는 설명문은 `STATE_LASER`에 둔다.
7. 원본 화자를 유지할 때만 A10과 A10_TEXT를 사용한다.

우라까이표 전체를 원본표 다음에 대화창에 출력한다. 파일 링크나 요약으로 대체하지 않는다.
