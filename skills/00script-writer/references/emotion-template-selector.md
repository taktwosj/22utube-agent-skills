# Emotion Template Selector

Use this as the first routing step for direct-made Korean scripts when the user
is in writer mode and the primary emotional shape has not already been locked.

This selector is a menu, not an automatic recommender. The operator chooses the
emotion based on channel, timing, trend, and instinct. Do not add automatic
emotion distribution rules.

## Prompt

Ask this before drafting:

```text
어떤 감정으로 쓸까요?

1. 통쾌 - ACTIVE
   사건 -> 억울 -> 빌런 발견 -> 통쾌
   야담, 사이다, 누명, 추리, 폭로

2. 비극 - 자리만
   선택 -> 결과 -> 상실 -> 의미
   죽음, 좌절, 역사 비극

3. 극복 - 자리만
   실패 -> 바닥 -> 재구성 -> 재기
   실화, 재기, 성장

4. 깨달음 - 자리만
   행동 -> 결과 -> 비교 -> 깨달음
   심리, 경제, 마인드셋

5. 희생/효도 - 자리만
   평범 -> 위기 -> 자기희생 -> 뒤늦은 인정
   부모, 효도, 헌신

6. 사랑/우정 - 자리만
   만남 -> 갈등 -> 화해/이별 -> 여운
   애정, 우정, 인연

7. 경고/공포 - 자리만
   일상 -> 위험 -> 신호 -> 예방
   사기, 사고, 건강, 법
```

## Routing

- If the user chooses `1`, load `references/templates/mystery-sacrifice.md` and
  continue with the normal writer harness, Hook-Loop, Intent Anchor, Rhythm
  Rules, and Action Gate.
- If the user chooses `2` through `7`, say that the template is only a
  placeholder. Ask whether to define that template now or proceed with `1`.
- If the user already says the emotional lane clearly, do not ask the menu.
  Route directly.
- If the user asks only for a system report or review, do not ask the menu.
  Use it as an analysis frame.

## Guardrails

- Do not force every script into the active `통쾌` lane.
- Do not tell the operator which emotion must be used unless they explicitly
  ask for a recommendation.
- The selector locks the primary emotion lane. Secondary emotions can exist,
  but they must not replace the selected lane.
- After the selector, still fill the Intent Anchor. The selector does not
  replace `Primary Emotion`, `Information Goal`, `Action Trigger`, `Share
  Target`, or `One-Month Memory`.

