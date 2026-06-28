# Action Gate

## Purpose

Use this after a complete longform or midform draft. Do not ask 10 personas
whether they "feel" the intended emotion. Ask them to predict action, sharing,
memory, early retention, and subscription intent.

Action prediction is the primary validation layer for longform and midform
scripts.

This is the full 10-persona gate. Use it only when the user explicitly requests
a full 10-persona review. Default writer mode, Shorts, midform, and longform use
the 5-agent gate in `parallel-persona-gate.md` instead.

## Personas

Use these 10 personas:

1. 20대 남자
2. 20대 여자
3. 30대 남자
4. 30대 여자
5. 40대 남자
6. 40대 여자
7. 50대 남자
8. 50대 여자
9. 60대 남자
10. 60대 여자

## Prompt Requirements

Paste the full script into each persona prompt. Do not write "the above script",
"previous script", or "same script as before".

If a persona answers that the full script is unavailable, unclear, or cannot be
verified, invalidate that response and rerun the same persona with the full
script pasted directly.

All 10 personas must evaluate the same script text.

## Standard Questions

```text
Q1. 끝까지 본 후 24시간 안에 할 가능성이 높은 행동 1개는?
    행동이 없으면 "없음"이라고 답한다.

Q2. 누구에게 공유할 것 같은가?
    대상이 없으면 "없음"이라고 답한다.

Q3. 한 달 뒤 기억에 남을 단어 / 사물 / 장면 1개는?
    기억나지 않을 것 같으면 "없음"이라고 답한다.

Q4. 초반 30초 안에 이탈할 것 같은가?
    Yes / No로 답한다. Yes라면 몇 초에 이탈할지 적는다.

Q5. 이 채널을 구독할 의향은 1~5점 중 몇 점인가?
    1점: 절대 안 누름
    3점: 비슷한 주제면 볼 수 있음
    5점: 바로 누를 가능성 높음
```

## Persona Output Format

```text
페르소나:
Q1 24시간 행동:
Q2 공유 대상:
Q3 한 달 뒤 기억:
Q4 30초 이탈:
Q5 구독 의향:
가장 강한 훅:
가장 약한 구간:
수정 요청 1개:
판정: PASS / REWRITE / FAIL
```

## 70 Percent Rule

Metric pass:

- Q1 passes when at least 7 of 10 personas give a concrete action other than
  "없음".
- Q2 passes when at least 7 of 10 personas name a concrete share target other
  than "없음".
- Q3 passes when at least 7 of 10 personas remember the intended anchor or a
  tightly related word/object/scene.
- Q4 passes when at least 7 of 10 personas answer that they would not leave
  within the first 30 seconds.
- Q5 passes when the average subscription score is 3.0 or higher.

Production entry:

- 5 of 5 metrics pass: Excellent. Enter production.
- 4 of 5 metrics pass: Good. Enter production after fixing the single weakness
  if it is cheap.
- 3 of 5 metrics pass: Rewrite, then rerun the gate.
- 2 or fewer metrics pass: Replan or park the topic.

Critical exception:

- If Q3 Memory Anchor fails, revise even if 4 of 5 metrics pass.
- If Q4 First-30-Second Retention fails, revise even if 4 of 5 metrics pass.

## Failure Diagnosis

Q1 action failure:

- Problem: the Action Trigger is weak or absent.
- Fix: add one concrete ending action. Use a real verb such as check, compare,
  save, share, reserve, comment, or try.

Q2 share failure:

- Problem: the target viewer is too broad or the video is not useful to a
  specific person.
- Fix: narrow Share Target and connect the story to that person's problem.

Q3 memory failure:

- Problem: the Memory Anchor is weak or multiple anchors compete.
- Fix: keep one object, number, sentence, or scene and repeat it in the opening,
  middle, and ending.

Q4 early-retention failure:

- Problem: the first scene is slow, explanatory, or lacks contradiction.
- Fix: place the decisive contradiction in the first 3 seconds and delay
  background explanation.

Q5 subscription failure:

- Problem: the viewer may watch the video but does not see a repeatable channel
  value.
- Fix: add a channel-specific lens, recurring promise, next-episode reason, or
  series identity.

## Skip Conditions

Do not force the full Action Gate for every task.

Skip or reduce the gate when:

- The request is a quick idea list, title list, or brainstorming-only pass.
- The output is a short caption set that will be manually edited.
- The task is a CC/remake observation Short where source visuals carry the main
  hook. Use the 11short audio-off comprehension gate instead.
- A series format already passed the gate and the current episode only swaps
  examples without changing the promise.

For new midform/longform topics, serious rewrites, and finalization, use these
Action Gate questions when useful, but the default required persona scale is the
random 5-persona gate unless the user explicitly requests a full 10-persona
review.
