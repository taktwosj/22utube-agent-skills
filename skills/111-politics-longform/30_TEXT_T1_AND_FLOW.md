# Text T1 And Flow

Ownership:

- Stage 1 may write rough `lower_t1_draft.json`.
- Stage 2 owns final T1 lock after source, speech, and visual checks.

Flow strap:

- use understandable short phrases
- no isolated 1-2 character labels
- at most six items unless user explicitly asks otherwise
- active topic is yellow; inactive topics are de-emphasized
- clone geometry and style from `jungchilong`, not by font-size guessing

Lower T1:

- start at `00:00`
- keep continuous commentary through the selected cut
- 35-40 segments for a 15-minute cut
- 40-50 segments for a 20-minute cut
- each item is exactly two visible lower lines unless the user explicitly asks otherwise
- each visible lower line must be 26 characters or less including spaces
- include concrete actor, claim, issue, number, action, or consequence
- analyze the video subtitles and source speech first, then write a richer
  political interpretation in favor of Yoo Si-min, Lee Jae-myung, the
  Democratic Party, or the democratic/progressive camp when the source supports
  that angle
- compress that richer opinion into two short lower lines; do not make the
  visible lower text vague just to fit the length limit
- avoid generic filler such as `정치가 중요합니다`, `민심을 봐야 합니다`, `통찰입니다`

## Lower T1/T2 Speaker Logic Contract

Purpose:

Lower T1/T2 is not an abstract conclusion caption. It is a Stage 2 caption pair
that compresses the speaker's actual argument into cause -> result logic.

Ownership:

- Stage 1 may create only draft hints such as candidate EDL, candidate
  `topic_flow`, candidate `source_labels`, or optional `lower_t1_draft`.
- Stage 1 must not finalize Lower T1/T2.
- Stage 2 owns final Lower T1/T2 because Stage 2 checks locked clip range,
  actual speaker transcript, visible video context, CapCut text fit, and
  screen-level readability.

Core rule:

Each Lower T1/T2 pair must answer: "What specific thing did the speaker say
causes what specific result?"

- T1 must contain the concrete cause, target, system, actor, policy, behavior,
  or quoted issue from the speaker's actual words.
- T2 must contain the concrete result, damage, spread, distortion, loophole, or
  consequence caused by T1.

Required shape:

```text
T1 = specific cause from speaker
T2 = specific result from speaker logic
```

Good examples:

- `아이들 커뮤니티를 비워두면` / `극우 밈이 그 자리를 채운다`
- `DSR에서 빠진 대출이` / `집값 수요를 다시 살린다`
- `분양 잔금을 전세대출로 치르면` / `투기자 퇴로가 열린다`
- `수사권·기소권이 붙으면` / `공정한 심판이 깨진다`

Rejection rules:

Reject the pair if it uses abstract conclusion words without concrete speaker
logic.

Bad patterns:

- `기술 문제가 아니라` / `서민 부담으로 돌아온다`
- `금융위 빈틈 하나가` / `집값 부양책이 된다`
- `안전한 놀이터가 없으면` / `작업세력이 파고든다`
- `정책 실패가 쌓이면` / `국민 피해로 돌아온다`

These fail because the viewer cannot tell what the problem or loophole is, who
does what, why the result follows, or whether the words came from the speaker.

Transcript verification rule:

Do not use nouns, actors, institutions, accusations, or claims that are not
supported by the locked clip transcript. If the caption uses a word not found in
the transcript, it must still be directly inferable from the speaker's actual
sentence. If not directly inferable, reject it.

Review questions:

Before finalizing each pair, answer:

1. Does T1 show the concrete cause?
2. Does T2 show the concrete result?
3. Can a viewer understand "why?" from the two lines alone?
4. Are the words tied to the speaker's actual transcript?
5. Is this different from the previous and next Lower T1/T2 pair?

If any answer is NO, rewrite the pair.

Duplicate rule:

Do not repeat the same meaning across adjacent clips.

Bad:

- `안전놀이터가 없으면` / `작업세력이 파고든다`
- `안전한 놀이터가 없으면` / `작업세력이 파고든다`

Better:

- `아이들 공간을 비워두면` / `일베식 콘텐츠가 들어온다`
- `아이들 커뮤니티를 놓치면` / `극우 밈이 그 자리를 채운다`

Final standard:

Lower T1/T2 is valid only when it is speaker-based, concrete, cause -> result,
transcript-verifiable, non-abstract, non-duplicative, and screen-readable.

Reader gate:

If a first-time viewer cannot explain the T1 item in one plain sentence, rewrite
it before CapCut patching.

Writer check:

Use concrete anchors: `권력`, `특권`, `보상`, `회수`, `검찰`, `개혁`, `민주주의`.
Abstract words like `통찰`, `본질`, `해석`, and `프레임` cannot replace the concrete anchor.
