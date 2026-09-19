# 투군 오류 찾기 요청문

원고를 쓰고 `check_narration.py`가 PASS한 뒤, TTS 전에 투군에게 오류만 찾게 한다.
투군은 조언자이지 gate가 아니다. 글의 평가·문체·구성 의견은 받지 않는다.

## 호출

두 단계로 보낸다(2026-09-17 사용자 지시).

1. `ask_togun` MCP 로 보낸다.
2. 도구가 없거나 `WAIT_LIVE_TOGUN_PROJECT` 등으로 실패하면 사용자에게 다시 묻지 않고 아래 브라우저 탭으로 같은 요청문을 보낸다.

```text
project        politics_119          (등록값: politics_119 / politics_119_debate / shorts_001 / code_work_order)
task_id        <episode_id>-narration-check   같은 task_id 는 같은 대화를 잇는다. 재검사도 같은 값
response_mode  errors_only
caller_device  도구 설명에 적힌 인증 장치값 그대로
question       아래 붙여 쓰는 프롬프트
context_text   narration/<block>.txt 전체, 블록 이름을 앞에 붙여 순서대로
context_refs   비운다. 값을 넣으면 서버가 422 로 거절한다. 파일 첨부 경로가 없다
```

답은 `answer` 본문에 표로 온다. `uncertainties` 가 있으면 `UNVERIFIED` 항목으로 같이 적는다.

- 브라우저 탭: `https://chatgpt.com/g/g-p-69bec5d5e6d481918a435189a9a3e2a7-tugun/project`. 사용자의 로그인된 실제 브라우저에서 연다. 열린 투군 탭이 있으면 그 탭을 쓰고, 없으면 새 채팅을 연다. 하위 에이전트에 위임하지 않는다.
- 여러 줄 원고는 한 메시지로 들어가야 한다. 줄바꿈마다 전송되면 입력창에 텍스트를 한 번에 넣고 보내기 버튼을 누른다.
- 넣기: `#prompt-textarea` 를 먼저 비우고(남은 초안이 앞에 붙은 적 있음) ClipboardEvent paste 로 넣는다. 보내기는 화면 좌표 클릭이 확실하다.
- 기다리기: 짧은 간격 폴링은 "요청이 너무 많습니다"를 부른다. 1~2분 간격으로 본다. 웹 검색으로 7분 넘게 걸릴 수 있다.
- 읽기: 답 본문 innerText 는 출처 칩만 나올 수 있다. `table` 셀 텍스트로 읽고 링크 href 는 뽑지 않는다.
- 같은 회차 재검사는 그 회차의 대화에 잇는다.
- 받은 답은 `work/togun_error_check.md`에 그대로 저장한다.

## 붙여 쓰는 프롬프트

아래 블록 뒤에 `narration/<block>.txt`를 블록 이름과 함께 순서대로 붙인다.

```text
아래는 정치 롱폼 나레이션 원고다. 오류만 찾아라.
찾을 것: 인명, 직책, 소속, 정당, 날짜, 숫자, 사건명, 표기.
하지 말 것: 글의 평가, 문체·구성 의견, 재작성, 방향 제안, 요약.
확인은 웹 검색으로 하고 근거 URL을 붙여라. 확인 못 하면 교정 칸에 UNVERIFIED 라고만 써라.
출력은 아래 표 하나뿐이다. 오류가 없으면 "오류 없음" 한 줄만 써라.

블록 | 줄 | 원문 | 교정 | 근거 URL
```

## 반영

- 작성자가 항목마다 원문과 근거 URL을 직접 대조한 뒤 원고를 고친다. 투군 표를 그대로 적용하지 않는다.
- `UNVERIFIED` 항목은 우리 주장이면 원고에서 빼고, 상대 발언 인용이면 그대로 둔다.
- 고쳤으면 `check_narration.py`를 다시 돌린다. 통과한 원고만 TTS로 보낸다.
- 투군이 방향·문체를 건드린 제안은 무시한다. 척추가 정한 방향은 바뀌지 않는다.
