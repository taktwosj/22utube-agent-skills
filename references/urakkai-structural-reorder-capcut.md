# 우라까이 구조 재배치와 CapCut 검증

## 정의

우라까이는 원본 장면의 서사 순서를 의미 있게 바꾸는 작업이다. 제목·크롭·TTS·색상·자막만 바꾸고 장면 순서를 유지하면 리패키징일 뿐 우라까이가 아니다.

```text
INVALID: 1→2→3→4→5 + 제목/TTS/크롭 변경
VALID:   3→4→1→2→5
VALID:   5A→2→1→3→4→5B→6
```

## Stage 02 원본 구간 번호화

원본을 1초 단위가 아니라 사건·발언·감정·행동이 변하는 구간으로 나눈다.

각 구간에 반드시 기록한다.

- 원본 순번
- source start/end
- 화면 사건
- 원본 발언 요지
- 서사 기능: setup, conflict, proof, action, result, close

결과 구간을 훅과 본론에서 나눠 써야 하면 같은 구간을 통째로 복제하지 말고 `5A`, `5B`처럼 겹치지 않는 source range로 분할한다.

## Stage 03~05 구조 제안

사람눈 설계도 본문에 아래를 먼저 보여준다.

```text
원본 구조: 1→2→3→4→5→6
최종 구조: 5A→2→1→3→4→5B→6
```

그리고 각 구간의 `source range → target range`와 재배치 이유를 표로 제시한다. 사용자가 구조를 승인하기 전 TTS 생성·CapCut 조립으로 넘어가지 않는다.

## 질문·답과 인과 의존성 검수

장면 하나를 훅으로 옮길 때 순번만 바꾸지 말고 **대화·인과 의존성**을 먼저 그린다.

- 질문→답, 주장→반박, 행동→결과, 지시어→대상, 설정→회수는 서로 의존하는 구조다.
- 답·결과만 앞으로 옮겨 원래 위치에 질문·원인만 홀로 남으면 실패다. 최소 선행 구조를 훅과 함께 이동하거나, 원래 위치의 질문까지 제거·재연결해야 한다.
- 예: `왜 아니야? → 여기 국도라고`에서 답만 선행하면 후반에 답 없는 질문이 남는다. 이 경우 질문과 답을 묶어 선행하고 둘 다 원래 위치에서 제거한다.
- 구조 생략을 `의도적 회수`라고 이름 붙이는 것만으로 문맥 단절이 해결되지는 않는다. 수정 순서를 실제 대사대로 다시 읽어 모든 질문에 답이 있고 모든 지시어가 대상을 갖는지 확인한다.
- 훅 이동 후에는 `중복 source`, `누락 source`, `dangling question`, `orphan reaction`, `broken pronoun/reference`를 별도 검사한다.

## Production plan 계약

각 VIDEO clip에는 다음 필드가 필요하다.

```json
{
  "key": "5A",
  "source_range_us": [20760000, 23560000],
  "target_range_us": [0, 2800000],
  "audio": "mute"
}
```

필수 규칙:

1. 최종 VIDEO order signature가 원본 signature와 달라야 한다.
2. target range는 0부터 최종 duration까지 승인된 gap/overlap 외에는 연속이어야 한다.
3. source range는 원본 duration 안에 있어야 한다.
4. source range 중복은 승인된 teaser 반복이 아니면 FAIL한다.
5. 무음 훅을 제외한 A10 segment는 대응 VIDEO의 source/target range와 일치해야 한다.
6. builder는 승인 순서를 재해석하거나 원본 순서로 복원하지 않는다.
7. TTS는 구조 전환용 훅·브리지이며 장면 재배치를 대신하지 않는다.

## 오디오 처리

- A9 TTS는 실제 WAV 생성 후 측정 길이를 사용한다.
- 훅 VIDEO가 2.8초이고 TTS가 2.77초라면 A9는 2.77초, VIDEO는 승인된 2.8초를 유지할 수 있다.
- 훅 원본 음성은 `mute` 또는 승인된 `duck`을 명시한다.
- 본문 A10은 재배치된 각 VIDEO segment와 같은 source/target range로 이동한다.
- 원본 첫 대사를 TTS로 삭제하지 말고 필요하면 뒤쪽 맥락 구간으로 이동한다.

## 독립 validator

builder receipt를 믿지 말고 최종 draft를 다시 읽어 다음을 검사한다.

- VIDEO segment 개수와 source start order
- A10 segment 개수와 VIDEO 대응 관계
- 승인 order signature 일치
- T1/T2 문구와 전체 노출 구간
- A9/A9_TEXT start·duration·문구
- TTS 파일 존재·SHA·decode·무음
- media path 존재
- root_meta 등록 1개
- active draft 금지 파일 0개
- manifest가 선언한 mirror pair 일치

mirror는 보통 다음 두 group으로 검사한다.

```text
GROUP_A: root draft_content == timeline draft_content
GROUP_B: root template-2.tmp == timeline template-2.tmp
```

네 파일 전체를 하나의 hash로 묶지 않는다.

## 실제 CapCut 눈검수

최소한 다음 위치를 캡처한다.

1. 0초: 결과 훅과 A9_TEXT/TTS 파형
2. 두 번째 segment 내부: conflict
3. 뒤로 이동한 원본 1번 내부: context
4. 비교·검증 segment
5. 결과 완성 segment
6. 결말 segment

각 화면에서 T1/T2 유지, 장면 내용, baked-in 자막 충돌, segment 경계를 확인한다. 마지막에는 CapCut을 종료한 후 draft를 다시 읽어 order·ID·duration·media·mirror pair를 재검증한다.

## 오류 코드

```text
URAKKAI_STRUCTURE_UNCHANGED
URAKKAI_ORDER_MISMATCH
URAKKAI_SOURCE_RANGE_OVERLAP
URAKKAI_TARGET_RANGE_GAP
URAKKAI_AUDIO_VIDEO_MAPPING_MISMATCH
URAKKAI_DEPENDENCY_BROKEN
```

구조 오류가 있으면 실패본을 부분 수정해 다음 입력으로 쓰지 않고, 승인 설계와 실제 자산을 보존한 채 근본 ZIP에서 clean rebuild한다.
