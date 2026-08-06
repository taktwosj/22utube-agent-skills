# MARA Creative Urakkai Review Rubric

Load with `references/stage04-external-review-contract.md` for every Stage 04 `URAKKAI` review. The reviewer reads the episode's `*_ORIGINAL_CAPCUT_GRID.md` and its Stage 03 urakkai design (`*_MARA_STAGE03.md` or `20_script/URAKKAI_BLUEPRINT.md`) together and judges them against this rubric.

## Review purpose

This is not summarizing the source or polishing sentences. Judge whether the draft became an independent short story — new message, new protagonist, new goal, new obstacle, new relationship, new emotional line, new reversal, new ending — while still using the original footage as material.

Review adversarially. Do not defend the existing design. Argue from retention and emotional payoff.

## 1. Fact and creation boundary

Keep three fields separate:

- `SOURCE_OBSERVATION`: people, objects, actions, speech, and screen content actually visible or audible in the source.
- `CREATIVE_URAKKAI`: the invented goal, obstacle, emotional line, reversal, and ending.
- `FICTIONAL_RECONSTRUCTION`: relationships, motives, identities, and background not confirmed by the source.

Inventing family ties, prior promises, jobs, or purposes is allowed. FAIL only when invented relationships or motives are recorded as if they were source facts. Never penalize a draft merely for containing invention.

## 2. MARA_MESSAGE

Check that the message is not a restatement of the source, that the viewer's final emotional payoff is explicit, that one sentence carries the center, that the whole script moves toward that one message, and that the message is repaid as scene emotion rather than stated as a lesson. If the message is weak, propose two stronger replacements.

## 3. 가단야 structure

- 가: a strong opening situation or question
- 단: the protagonist's goal and the escalation of the obstacle
- 야: a reversal or emotional ending that defies expectation

Judge whether 0–3s is a real hook — a result, conflict, crisis, or strong reaction — instead of a plain introduction.

## 4. Independent narrative

Reading only the new A9 script, these must be clear: protagonist, what they want, an obstacle that can fail, an unresolved question that holds the viewer, a reversal that flips the information, and an ending that repays the emotion. If any is unclear, name the exact sentence where the narrative breaks.

## 5. Paraphrase test (any one is FAIL)

- source lines swapped for synonyms
- only the endings of source captions changed
- source events retold in chronological order
- only the last 1–2 seconds moved forward while the rest keeps source order
- transformation claimed from color grading, cropping, zoom, or speed alone
- the source's message and conclusion kept intact

Judge whether message, narrative, order of information reveal, script, and screen arrangement are substantively different from the source.

## 6. VIDEO reorder review

Compare the new script against the target VIDEO order:

- the screen actually supports the new script's meaning
- the script is not new while the footage keeps source order
- a result used as the hook is not replayed whole in the body
- no reorder breaks cause and effect
- gaze, hand movement, and direction of motion do not contradict the new story
- the script does not assert action that is absent from screen
- enough on-screen cues support the invented premise

For any sentence that is hard to realize on screen, propose both a replacement sentence and a replacement shot placement.

## 7. Wow point

"Interesting" or "touching" is not enough. A valid wow point flips one of: the identity of a relationship, the purpose of an action, who the protagonist is, an apparent failure into success, the value of an ordinary place or object, or the meaning of the opening shot at the ending. If it is weak, propose two alternate reversals that the existing footage can support.

## 8. A9 writer narration

Check sentence by sentence: the first sentence starts the event immediately, narration never reveals the conclusion ahead of the screen, information is not repeated, abstract emotional description is not excessive, each sentence makes the next shot a question, the last sentence repays the central message emotionally, invented settings stay internally marked, and no sentence is long enough to break TTS breathing.

Report each problem sentence as:

```text
기존 문장:
문제:
수정 문장:
수정 이유:
필요 화면:
```

## 9. T1 · T2 · A9_TEXT · STATE

- `T1`: the core title that catches the first look
- `T2`: supports T1 or holds the question until the ending
- `A9_TEXT`: on-screen phrasing synchronized with the writer narration
- `STATE`: a short non-sentence phrase describing the present action or situation

Check that T1 and T2 do not repeat each other, that the titles do not expose the whole ending, that `A9_TEXT` is not long enough to cover the frame, that `STATE` carries no commentary or forced emotion, and that the titles match the script's central message.

## 10. Audio policy

The design must declare exactly one:

- `TTS_ONLY_MUTE_SOURCE`: every VIDEO muted, new A9 TTS required, A10/A11/A12 empty.
- `A10_RETAINED_SYNC`: original speaker audio retained, verified external vocal stem required, VIDEO muted, A10 synchronized with VIDEO source/target ranges, A12 empty.

Mixing original voice and new TTS without evidence is FAIL.

## Prohibited reviewer behavior

- Do not add invented facts to the original grid.
- Do not "correct" an unconfirmed relationship into a stated fact.
- Do not deduct points merely because the draft contains invention.
- Do not reduce the fix to light rewording of source sentences.
- Do not PASS on cut-order changes alone.
- Do not assume reviewer authority over user approval or FINAL.
- Do not keep a source screen order that no longer matches the new script.

## Output format

1. **Verdict** — exactly one of `PASS_CANDIDATE`, `REVISE_REQUIRED`, `WAIT_SOURCE_RECHECK`, `REJECTED_MARA_INSUFFICIENT`.
2. **Core judgment** — strongest point, biggest problem, reason the viewer watches to the end, emotional payoff at the ending.
3. **Item table** — PASS/FAIL, evidence, and fix needed for: MARA_MESSAGE, 가단야, 주인공·목표, 장애·미해결 질문, 반전·결말, 원본과 독립성, VIDEO 재배열, 사실·창작 경계, A9 대본, T1·T2·STATE, 오디오 정책.
4. **Must-fix list** — at most five, ordered P0 through P4 by severity.
5. **Improved final draft** — when a fix is needed, rewrite all of: MARA_MESSAGE, creative premise, protagonist/goal/obstacle/unresolved question/reversal/ending, target VIDEO order, full A9 narration, T1, T2, A9_TEXT, STATE, and the fact/creation boundary table.
6. **Final state** — `USER_APPROVAL_REQUIRED=true`, `NEXT_STATE=WAIT_USER_URAKKAI_APPROVAL`.

The reviewer may improve the design but never approves it. Final selection and approval belong to the user.
