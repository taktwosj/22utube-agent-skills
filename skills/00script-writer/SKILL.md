---
name: 00script-writer
description: YouTube script writer and retention-design skill for Korean channels. Use when the user asks for 대본작가, 작가모드, 체류율 설계, 기억앵커, 유튜브 대본, 쇼츠/미드폼/롱폼 script creation or review, 쇼츠학개론, 마라하기 공식, 한계선, 돈통/에셋, 결, 가단야, 우라까이, 일치율 0%, 벤치영상, 채널기획, channel-family labels such as 한짜/국뽕/해짜/드짜/영짜/랭킹/유머/군림보, angle pivot/remake reframing, pre-click state mapping, channel anchors, rhythm polish, evidence/safety passes, post-publish feedback, channel-specific script formulas, decisive scene image prompts, CC/remake shorts caption design, Warren Buffett/quote scripts, mindset, history, finance, scam-prevention, sassy/revenge shorts, or when a topic must be filtered before writing so the output is not a generic AI script.
---

# Script Writer

## Mandatory arajun Style Memory Gate - 2026-06-22

For 11short/00-tikitaka/000short Shorts caption work, load the local style
memory before drafting or polishing visible text:

```text
$env:UTUBE_ROOT\11short\style_bank\STYLE_MEMORY_CONTRACT.md
$env:UTUBE_ROOT\11short\style_bank\arajun_shorts_voice_profile.md
$env:UTUBE_ROOT\11short\style_bank\final_script_corpus_index.json
```

Use 3-5 recent genre-matched final scripts as the tone/rhythm reference. This
gate is about wording style and cadence only; source truth, policy, verified
speech, and current user direction remain higher authority. If unavailable,
report `WAIT_STYLE_REFERENCE` and do not call the script final/locked.

## User Script Corpus Anti-AI Gate - 2026-06-22

For 11short/00-tikitaka/000short visible Korean text, the user's saved
`final_script_ko.txt` corpus is the default style source. Use it to remove
generic AI-writing smell before any script lock, SRT, CapCut text, upload text,
or visible-final wording.

Before drafting or polishing:

1. Load the style memory files above.
2. Select 3-5 recent genre-matched corpus entries, preferring
   `has_top_middle_tts_contract=true`.
3. Extract `style_sample_lines` from `top_sample`, `middle_sample`, and
   `tts_sample`, and record the chosen episode ids or paths in the work report.
4. Learn only rhythm, line length, reaction shape, and hook/payoff cadence.
   Do not copy corpus lines verbatim unless the user explicitly wants a
   recurring phrase and the source supports it.
5. If the corpus cannot be read or no matching sample is available, mark
   `WAIT_STYLE_REFERENCE`; do not call the text final, locked, or ready.

Current corpus lines that define the user's short-form rhythm:

```text
style_sample_lines:
- 5위도 위험함. 1위는 더 위험함.
- 근데 진짜 위험한 건, 공이 사람 쪽으로 되돌아오는 순간입니다.
- (결론부터 먼저 보여줌)
- 웃겨 보였지만, 이유가 있었습니다
- 경찰 몽타주 랭킹이라는데, 마지막은 그림보다 표정이 더 웃깁니다.
- (실종된 아빠를 찾는다는데 단서가 딸의 그림 한 장)
- 사람 등근육 아님
- 그냥 밥 먹는 중입니다
- 고양이들이 물건 앞에서 당황한다는데요.
- 마지막은 발재간까지 터졌습니다.
```

AI-smell rewrite rule:

- Reject generic openings such as `이 영상은`, `지금부터 보여드리겠습니다`,
  `여기 보시면`, `놀라운 사실은`, `믿기 힘들겠지만`, and
  `많은 사람들이`.
- Reject report-style filler such as `상황을 설명하자면`, `해당 장면에서는`,
  `이 과정에서`, `결과적으로`, `한편`, and repeated neat connectors like
  `하지만/그러나/또한/그리고`.
- Reject captions where every beat is a complete polished explanation. Shorts
  text should alternate scene-first lines, reaction captions, verified speech,
  and short TTS/payoff lines.
- Rewrite toward visible objects and actions first: person, object, number,
  place, contradiction, movement, or sound. Use `( ... )` for the viewer-facing
  reaction or air in the room, and plain text for sparse narration.
- Keep imperfect human rhythm when it helps: fragments, one-word punches,
  direct reactions, mild slang, and short reversals are allowed if source truth
  and policy remain safe.
- Do not invent facts, emotions, insults, motive, dialogue, or source speech
  just to make the line feel human.

Before any final/lock wording, output or save:

```text
style_sample_lines:
- episode_id/path:
- chosen rhythm lines:
anti_ai_style_gate: PASS / REWRITE_REQUIRED / WAIT_STYLE_REFERENCE
```

If `anti_ai_style_gate` is `REWRITE_REQUIRED`, rerun the style-corpus pass and
`humanize-korean` style cleanup before handoff. Humanize may polish rhythm only;
it must not change source truth, verified quotes, timing, facts, names, numbers,
or the current 11short caption contract.

## Current 11short Caption Contract Override v2.0

For 11short/00-tikitaka/000short source-remake caption work, this section is the latest authority and overrides older `하단`, `하단 원문`, first-bottom-line, bottom-TTS, and three-layer output rules in this file.

Current default visible script structure is:

```text
상단
2줄 제목

중단
[0~3초]
"검증된 실제 발화"
(상황/감정/반응)
일반 텍스트
```

`중단` has three text forms:

- `" ... "` = actual verified source speech/source subtitle/reliable transcript only.
- `( ... )` = emotion, stage direction, situation, state, viewer reaction, impact, sound cue, or creative tone.
- plain text = our visible explanation, OCR-style label, context sentence, or narration-like caption.

There is no separate `하단` layer in current 11short source-remake work. The hook/memory anchor is the first strong `중단` cue. If generated/user-supplied voice or TTS is requested, derive the voice text from timed `중단`; do not create a separate bottom script section.

Notation constitution:

- `[00:00-00:03]`, `[몇초]`, or bracketed timing means the source/video segment marker for the writer/operator; it is never copied into CapCut as visible text.
- Only these three text forms become CapCut `중단` text: plain text such as `소녀는 소년에게 다가갔다`, verified quoted speech such as `"야 이 새끼야!"`, and parenthesized reaction captions such as `(순간 움찔하는 소년)`.
- A plain narration sentence is plain timed `중단` caption text by default. If voice/TTS is requested, derive the voice line from that same `중단` text.
- `"안녕하세요"` or any double-quoted line means verified source dialogue/speech/subtitle only. Never invent quoted speech.
- `(이거 괜히 뻘쭘하네)` or any parenthesized line means caption-only reaction/emotion/situation text for timed `중단`.
- In all current 11short jobs, write only `상단` and timed `중단` as the script package.

11short remake rewriting and edit-point rules:

- Replace most words from the benchmark/source script so the Korean caption wording fits the new video flow.
- Paraphrase source speech naturally in Korean while preserving meaning and support from the source; do not invent unsupported speech or facts.
- Change edit points accurately around the verified `wow point` and the timed `중단`/voice-derived line when voice is requested.
- The hook must get shock pressure from both the `wow point` and the top title/subtitle wording. A soft summary hook fails.
- If the user provides already changed footage, a recut order, or Korean 우라까이/caption direction, treat it as the creative authority unless it violates source truth, safety, or harness contracts.
- Preserve the user's chosen flow, wow point, and caption intent. The writer pass should polish retention, readability, source accuracy, timing, and policy without replacing the whole concept from scratch.
- For CapCut handoff, surface only the changes needed to make the project natural: clean cuts, readable timed `중단`, natural Korean paraphrase, stable title/middle timing, audio/SFX/BGM timing, and no awkward overlaps.

11short functional-structure rewrite rule:

- For 11short 우라까이 scripts, reject numeric-only `1-2-3-4-5` source beat
  rearrangement as an incomplete design pass.
- The script must first identify functional roles such as 원인, 오해, 갈등, 미끼,
  티저, 반전, 정체 공개, 감정 상승, 웃음 포인트, 감동 포인트, 화해, 결과, 회수,
  엔딩.
- Default 우라까이 output should provide three versions: `A. 반전 선공개형`,
  `B. 갈등 증폭형`, and `C. 감동 회수형`.
- Each version must keep the current `상단 + timed 중단` structure and each timed
  block must use `[편집 00:00-00:03 | 원본 00:36-00:42]` when source timing is
  known.
- Source timecodes are not writer invention. If the user says they will provide
  an intermediate timecode check, the writer outputs the rough script first with
  Codex-proposed source ranges, then attaches `구간 초단위 확인표` and marks the
  item `PROPOSED_SOURCE_TIMECODE` / `USER_TIMECODE_CHECK_REQUIRED` instead of
  pretending the source ranges are final.
- After the user confirms with `1번 맞음` or corrects ranges such as
  `1번 00:22-00:30`, the writer may lock the selected structure with exact
  `[편집 ... | 원본 ...]` pairs. Before that, do not hand off a CapCut-ready
  script, `SCRIPT_LOCK`, or production `PASS`.
- Treat the user's ranges as correction values for the rough script blocks, not
  as permission to rebuild the concept or swap segment order unless the user says
  to change the order.
- Each version must end with `TTS용 자막`: only plain narration lines, excluding
  verified quoted speech, parenthesized situation captions, and timestamps.
- The writer/persona gate should judge the selected or recommended version for
  hook pressure, text-only comprehension, audio-off comprehension, and payoff
  clarity. If no version reaches threshold, mark `REWRITE_REQUIRED`.

Humanizer/tool priority for 11short:

- `humanize-korean` or any humanizer may polish only style and rhythm after the
  writer structure is decided. It sits below source evidence, YouTube/policy
  safety, 우라까이 structure, and the current 11short caption contract.
- It must not change verified quotes, speaker meaning, source timing, facts,
  names, numbers, policy-sensitive wording, or the separation between quoted
  speech, parenthesized situation captions, and plain TTS/narration.
- Extra memory tools such as `agentmemory` are not writer authority. Repeated
  failure rules must be promoted through skills/harnesses or an explicitly
  user-approved memory store, not silently stored during a writing pass.

## Core Identity

This skill is not a normal script generator. It is a retention and memory-design gate for YouTube content factories.

Do not start by writing a full script. First decide whether the topic can become a memorable video product.

Use Korean by default.

## Mandatory Writer Harness Checklist

For any script, Shorts caption/narration package, midform/longform narration,
hook/title package, upload text, serious rewrite, review, or finalization,
start with this visible checklist and update it before calling anything final:

```text
[Writer Harness Checklist]
- lane/channel:
- output type:
- duplicate/topic check:
- 00script-writer design pass:
- hook + first-30s hold gate:
- memory anchor:
- evidence/safety tier:
- youtube policy gate:
- policy risk tier: LOW / MEDIUM / HIGH / BLOCK
- agent/persona reader gate:
- voice/display/SRT contract:
- n8n status board:
- harness/check script:
- blocking failures:
- final status: DRAFT / REWRITE_REQUIRED / PASS
```

Hard rules:

- Do not call a script/caption package `final`, `ready`, `approved`, or
  production-ready until the checklist is resolved.
- The visible agent/persona gate is mandatory after a complete draft and before
  finalization. Use the scale rule below: 5 randomly selected personas for
  default writer mode, Shorts, midform, and longform. Use real sub-agents when
  available; if agent limits apply, run them in batches. If sub-agents are
  unavailable, mark `local simulation`.
- For script-only planning, do not fake n8n or harness results. Mark
  `n8n status board: N/A - script-only` and `harness/check script: WAIT - no
  episode production folder yet`.
- If the request creates or changes images, prompts, TTS, SRT, CapCut,
  HyperFrames, render, thumbnail, upload package, or FINAL status, show the
  shared n8n/harness board and block the next stage on any failure.
- If a required harness or check script is missing or does not cover a new rule,
  report that as a blocker or update the harness before continuing.
- Run the YouTube Policy Gate at four points: before drafting, after the first
  draft, before title/thumbnail/upload metadata, and before final PASS.
- For movie/drama source-use, follow root `AGENTS.md`. If the user explicitly
  confirms they checked the source and it is usable/cleared for the current job,
  mark source-use as `USER_CLEARED_SOURCE` and do not block solely because the
  footage is movie/drama. Continue separate YouTube safety and advertiser
  suitability checks.
- `policy risk tier: BLOCK`, `platform safety verdict: FAIL`, or any hard-block
  item from `references/youtube-policy-gate.md` blocks finalization. A
  `REWRITE_REQUIRED` verdict requires revision and a rerun before continuing.
- Platform-allowed content is not automatically monetization-safe. Mark
  advertiser risk separately when the topic may trigger limited or no ads.

## YouTube Policy Gate

Load `references/youtube-policy-gate.md` for any script, caption package,
visible text, title, thumbnail text, description, upload package, or production
handoff that could touch safety, trust, copyright, monetization, or metadata
risk.

This gate checks intent, context, metadata, sources, external links, minors,
real victims, regulated goods, misinformation, and copyright. It must not be
delegated to retention personas. Personas judge comprehension and watch intent;
the policy QA gate judges YouTube safety and monetization risk.

EDSA context must be inside the script, audio, captions, or visible video when
the topic is high-risk. A title, tag, pinned comment, or channel description
alone is not enough for hate, violent organizations, child safety, self-harm,
or graphic violence.

Do not preserve dangerous procedural detail just because the script says "do not
try this." Remove or generalize the method, location, supplier, weapon part,
dosage, exploit step, purchase link, contact route, or target information.

## Agent Scale Rule

Use this default unless the user explicitly asks for a different gate size:

```text
Default writer mode: 5 random personas
Light Shorts: 5 random personas
Midform / longform: 5 random personas
Explicit user request for 10-persona gate: 10 personas
```

Five-persona random gate:

Randomly choose 5 unique personas from this pool:

```text
10대 남 / 10대 여
20대 남 / 20대 여
30대 남 / 30대 여
40대 남 / 40대 여
50대 남 / 50대 여
```

Each persona answers the same hook, text-only comprehension, audio-off, and
retention questions.

Five-persona scoring:

- 3 of 5 PASS/YES: proceed.
- 2 or fewer PASS/YES: revise the hook/captions/overlays using the concrete
  complaints, then rerun with the remaining 5 personas from the pool.
- If the rerun gets 3 of 5 PASS/YES or better, proceed.
- If the rerun is still 2 or fewer PASS/YES, mark `REWRITE_REQUIRED` and block
  production.

Ten-persona scoring:

- Use this only when the user explicitly asks for a full 10-persona gate.
- Use the existing 70 percent rule: 7 of 10 for each persona metric.
- Longform and midform may still load `references/action-gate.md` for its
  questions, but the default required scale remains random 5 personas.

## Emotion Template Selector v6 Add-On

For direct-made Korean writer-mode scripts, especially midform or longform, use
`references/emotion-template-selector.md` before drafting when the user has not
already locked the emotional lane.

This selector is the one allowed short choice menu in writer mode. Do not
auto-distribute emotions by channel, season, or trend. The operator chooses the
emotion; the system executes the selected template.

Current active route:

- `1. 통쾌`: load `references/hook-loop-structure.md` and
  `references/templates/mystery-sacrifice.md`, then continue through Intent
  Anchor, Rhythm Rules, and the required reader/persona gate.

Placeholder routes:

- `2. 비극`
- `3. 극복`
- `4. 깨달음`
- `5. 희생/효도`
- `6. 사랑/우정`
- `7. 경고/공포`

If the user chooses a placeholder route, state that the template is not defined
yet and ask whether to define it now or proceed with `1. 통쾌`. Do not force
every script into the active route.

## Longform / Midform v3 Planning Rule

For longform and midform scripts, load these references in this order:

1. `references/emotion-template-selector.md` when the emotional lane is not
   already locked.
2. `references/category-presets.md`
3. `references/intent-anchor.md`
4. `references/hook-loop-structure.md`
5. `references/action-gate.md`
6. `references/templates/mystery-sacrifice.md` only when the user chooses
   `1. 통쾌` or clearly asks for yadam/sida/wrongful-accusation structure.

Before drafting:

- Define Pre-Click State.
- If needed, ask the Emotion Template Selector menu and route the script.
- Define Intent Anchor:
  - Primary Emotion
  - Information Goal
  - Action Trigger
  - Share Target
  - One-Month Memory
- Define Hook-Loop Structure.
- Check Category Preset, but do not let category preset override the
  video-specific Intent Anchor.
- Define Decisive Scene.
- Define Memory Anchor.
- Define Hook Structure.
- Define Evidence / Safety Tier.
- Define YouTube Policy Gate and EDSA context if the topic is sensitive.

Do not draft until Primary Emotion, Information Goal, and Action Trigger are set.

After drafting:

- Run the Action Gate questions through the default random 5-persona gate unless
  the user explicitly requests a full 10-persona review.
- Each metric passes when at least 3 of 5 personas give a concrete or positive
  answer. Use 7 of 10 only for explicit full 10-persona requests.
- The script enters production when at least 4 of 5 metrics pass.
- If Q3 Memory Anchor or Q4 First-30-Second Retention fails, revise even if 4
  of 5 metrics pass.
- Always paste the full script into each Action Gate prompt.
- Do not use references such as "above script" or "previous script".
- If a persona returns "script not provided" or "cannot verify full text",
  invalidate that response and rerun with the full script.

## Mandatory First Pass

For any script creation or serious rewrite, output a compact design pass before the script:

```text
작가모드 설계
- 제작모드:
- 끝까지 볼 독자:
- 버릴 독자:
- 클릭 감정:
- 기억앵커:
- 큰 오픈루프:
- 초반 60초 보상표:
- 진행판정:
```

Keep this short. Do not create choice hell. Auto-select the best option and give the reason in one line. Offer alternatives only when the user asks.

If the user only asks for review, score against the same fields and lead with failures.

## Hard Gate

Apply this before drafting:

```text
Can the viewer remember one concrete number, object, sentence, action, or image after watching?
```

If no, do not write the full script. Propose up to three memory anchors. If none pass, say the topic should be parked or reframed.

Anchor pass conditions:

- appears in the first 30 seconds
- is one word, one number, one object, or one action
- can be encountered again in real life or inside the channel's repeated format
- connects to the actual solution or payoff
- returns in the ending

Examples:

- 보이스피싱: 가족 암호, "우리 암호 뭐야?"
- 부탁 거절: 휴대폰 캘린더, "일정 확인하고 말할게"
- 삼전 급등: 매수 버튼 앞 3초
- 노년의 가난: 축의금 봉투
- 형제 갈등: 연락처에서 멈춘 손가락
- 워렌 버핏 명언: "그리고 제 계좌는요"

## Hook And 30-Second Hold Gate

Before drafting, the writer must explicitly design the hook structure. A script is not ready for persona review until this exists:

```text
Hook structure
- Hook material: what exact scene, claim, object, number, contradiction, or line starts the video?
- First 3s stop reason: why does the viewer stop immediately?
- First 30s hold reason: what question, tension, clue, or promise makes the viewer stay past 30 seconds?
- Reward path: what does the viewer receive before 30s, and what remains open after 30s?
- Memory anchor: what object/line/number/action should remain?
```

The complete draft sent to the agent/persona gate must include this hook structure plus the first 30 seconds of script/captions. Do not ask agents or personas to judge isolated title candidates only.

The final script/caption pass cannot be `PASS` unless the chosen gate meets its scale threshold: 3 of 5 for default writer mode, Shorts, midform, and longform. Use 7 of 10 only when the user explicitly requests a full 10-persona gate. For videos shorter than 30 seconds, use "watch to the end" instead.

## Decisive Scene Gate

Before drafting, find the contradiction scene that can carry the whole video:

- What contradiction makes the viewer stop?
- What visible action, object, number, or sentence shows it without explaining the emotion?
- Can the scene be written poetically first, then unpacked clearly?
- Is the scene physically believable?
- Can the script keep following the same person, object, or anchor until the ending?

If the answer is weak, do not draft yet. Reframe the opening around a stronger contradiction, scene, or anchor.

## Workflow

1. **Classify production mode**
   - Direct-made script: history, finance, mindset, quotes, sassy/revenge, scam prevention.
   - CC/remake/observation shorts: source video is the main actor; captions point to what to watch.
   - Factory format design: user wants a repeatable channel formula, not one script.
   - Review: diagnose why an existing script is generic, forgettable, or weak.

2. **Choose the viewer to keep**
   - Do not satisfy everyone.
   - State who is being kept and who is being intentionally ignored.
   - For split audiences such as "삼전 폭등", choose one: missed buyer, current holder, trapped holder.

3. **Map click emotion**
   - Identify what the viewer already feels after seeing the title/thumbnail.
   - Catch defensive thoughts first: "그건 나도 아는데 못 하겠다고."

4. **Route the topic**
   - 사건/역사/인물: enter through an irreversible moment.
   - 설명/경제/심리 concepts: enter through broken intuition.
   - 실전 가이드: enter through the most common mistake.
   - 트렌드/뉴스: enter through the late-realization moment.
   - CC observation shorts: enter by pointing at the exact thing to watch.

5. **Build one big open loop**
   - One main question must pull the whole video.
   - Small loops can exist, but do not create five unrelated mysteries.

6. **Build the 10-second reward loop**
   - Every 10-20 seconds: question, clue, number, reversal, concrete action, or screen cue.
   - Every 30-60 seconds: deliver a small reward and create the next reason to stay.

7. **Write with rhythm**
   - Long sentence, short sentence, question, pause.
   - Do not repeat the same ending three times in a row.
   - One sentence should carry one idea.
   - Replace abstractions with scenes.

8. **Recover the anchor**
   - End by returning to the first anchor and making the viewer do or remember one thing.
   - Generic "좋아요 구독" is weak. Give a channel-specific reason to subscribe.

9. **Run the visible parallel persona gate**
   - For any script creation, serious rewrite, or script finalization, run the scaled retention/readability gate after the first complete draft and before presenting a final script.
   - Default writer mode, Shorts, midform, and longform use 5 randomly selected personas from 10대~50대 남/여. If the user explicitly asks for 10, use 10.
   - The gate must judge the writer's hook structure, not only the wording. At least 3 of 5 random personas must answer that they would watch for 30 seconds or more; use 7 of 10 only for explicit full 10-persona requests.
   - Use real parallel sub-agents when the runtime exposes them and the user has authorized the saved default parallel-persona workflow. Show the user a live progress board immediately after spawning agents.
   - For `11short-production-agent` work, real sub-agents are mandatory whenever `spawn_agent` or an equivalent sub-agent tool is available. Do not use `local simulation` as a substitute when real sub-agents can be spawned.
   - If sub-agents are unavailable, still output the same progress board and perform the scaled reviews locally, clearly marked as `local simulation`.
   - Do not hide this step inside prose. The user must be able to see which agents/personas passed, rewrote, or found confusing lines.
   - Load `references/parallel-persona-gate.md` for the exact scale, prompts, progress board, scoring, and rewrite rules.

## Output Modes

### Full Script

Use this when the user asks for a complete script:

1. 작가모드 설계
2. 초반 60초
3. 본대본
4. 엔딩/CTA
5. 자가검수

If the user wants speed, keep the design pass short and write the full script in the same answer.

### First 60 Seconds Only

Use this when the hook or concept is uncertain. Write only the opening minute first.

### Factory Formula

Use this when the user is building a repeatable content factory. Output:

```text
포맷명:
반복 구조:
고정 말버릇:
기억앵커 계열:
댓글 유도:
재사용 가능한 템플릿:
버릴 소재:
```

### Review

Use blunt scoring:

```text
총평:
점수:
치명적 문제:
살릴 앵커:
버릴 부분:
수정 처방:
```

## CC / Remake Shorts Rule

For CC/remake/observation shorts, the first job is to identify the real situation and genre frame. Do not start by decorating captions.

If the user mentions 쇼츠학개론, 마라하기, 한계선, 돈통, 에셋, 결, 가단야,
우라까이, 일치율 0%, 벤치영상, 채널기획, channel-family labels such as
한짜/국뽕/해짜/드짜/영짜/랭킹/유머/군림보, or asks to learn/apply those
lecture rules, load `references/shorts-academy.md` before the design pass.

Required order:

1. Extract the source audio, dialogue, captions, OCR, visible action, and audience reaction.
2. Decide the story frame: mistaken assumption, reaction comedy, emotional reveal, information surprise, prank, rescue, comparison, etc.
   Also record the composite label: `source_region + emotion_intent +
   channel_family + content_mode + source_surface`.
   Decide `caption_layer_mix` / `source_layer_mix` before writing: TTS density, verified quote
   density, situation-caption density, source-audio priority, and basis.
   For `군림보`, use `source_surface=photo_tts_explainer`: photos/images plus
   continuous TTS explanation, not dialogue-heavy Tikitaka.
3. If the frame is ambiguous, present 2-3 frames and recommend one before writing.
4. Build a new Korean scenario from the source meaning, not a direct copy.
5. Write the spoken narration first, then derive short visible captions from it.
6. Place video cuts to support the new scenario flow.

Before step 2, classify how the source is understood:

```text
source understanding route
- text_dialogue_dependent: film, variety, interview, news, foreign-language captions, or any clip where text/dialogue carries the point.
- action_intuitive: Instagram-style action, mime, fail, prank, animal behavior, or any clip that works even when the viewer does not know the language.
- drama_dialogue: characters' relationship and dialogue both matter.
- comment_meme: comments, celebrity context, movie/game meme, or audience reaction is the payoff.
- information_explainer: facts, tips, tech, history, money, medical/legal/finance-adjacent content.
- rescue_emotion: rescue, recovery, family love, adoption, elder/child emotion.
- incident_reversal: sudden reveal, mistaken assumption, near miss, stand-up, fall, or danger/reversal timing.
- process_change: before/after, cooking, repair, cleaning, restoration, makeover.
```

Ask the user before production only when the route changes the product: funny vs. emotional, comment-reaction vs. video-action, patriotic vs. informational, satisfying revenge vs. neutral explanation, or any sensitive interpretation risk. If the route is obvious, state the chosen route and proceed.

The source visual is still the hook. The script should point, zoom, pause, and ask:

- "여기 보세요"
- "오른쪽입니다"
- "아직 안 멈춥니다"
- "여러분이면 먼저 갑니까?"

Narration rule:

- If the user asks for voice/audio/TTS/result video, write a real narration script, not only bottom captions.
- The narration explains the situation beat by beat: setup, mistaken assumption, escalation, reversal, payoff.
- Visible captions are not full subtitles. They are compressed support lines for the spoken scenario.
- When the source has many captions or dialogue lines, preserve the meaning but change sentence order, word choice, rhythm, and framing. Avoid copying the original wording.
- Use similar-language substitution: swap nouns/verbs/endings with natural Korean alternatives while keeping the same situation.
- Avoid weak invented claims. Every visible caption should be grounded in a visible action, source line, or reaction.
- Do not label a person's condition from appearance alone. Use `도움이 필요한 줄`, `못 움직이는 줄`, `다들 착각함`, or similar uncertainty framing unless the source explicitly states the condition.

## Shorts Hook Caption Rule

For Shorts, visible text must be a hook layer, not only an explanation layer. The default mode is `B안 웃긴훅형` unless the source route or user request calls for restrained emotion or exact translation.

Bottom yellow caption:

- Purpose: a hooked read of the current visual beat.
- It must still explain enough for audio-off comprehension, but the wording should contain a viewer reaction, contradiction, escalation, reversal, or payoff.
- Avoid dry recap lines such as `댓글창이 마크로 가득했습니다`, `아이가 간식을 건넸습니다`, `무도 기억이 뒤에서 나왔습니다`, or `상황을 설명하는 중`.
- Rewrite those into lines such as `닭 한 마리에 댓글창 폭주`, `현실 닭은 아직 상황 모름`, `간식 하나에 예능 본능 발동`, `근데 이 형 기억력도 진짜임`.

Middle overlay:

- Purpose: punch line, comment reaction, decisive translation, or core contradiction.
- It should not repeat the bottom caption. If the meaning overlaps, change the angle: bottom explains the beat; middle delivers the reaction or hook.
- Keep it one line for the default 11short middle style. Exception: when the user explicitly asks for English/Korean comment reaction, use two lines: original/comment line plus Korean interpretation.
- For text/dialogue-dependent sources, middle overlays may be translation-first, but phrase the Korean like a viewer-facing hook instead of a dictionary translation.

When a caption set feels flat, produce three variants before selecting:

```text
A안 안전설명형:
B안 웃긴훅형:
C안 강한밈형:
선택:
```

Select `B안 웃긴훅형` by default. Select `A안` only for sensitive, factual, rescue, medical/legal/financial, or emotional clips where joking would weaken trust. Select `C안` only when the clip is clearly meme/comment/comedy and the wording does not create policy or dignity risk.

## Script Line Role Notation Rule

When writing Shorts scripts or caption packages, use this notation so the production agent can separate emotion/context, character dialogue, and narrator explanation.

- `( ... )` means emotion, stage direction, situation, state, viewer reaction, or creative tone. It is not a spoken line by default.
- `" ... "` means actual source speech from the video. Keep it matched to the source audio/meaning; do not invent or freely rewrite quoted lines for remix flavor.
- Plain text means our narrator/voiceover's situational explanation.
- If a beat contains all three, order it as: parenthetical emotion/context, narrator explanation, quoted actual source speech.
- Do not write narrator lines inside quotes. Do not write character dialogue as plain text unless it is a summary rather than a line.

Example:

```text
(팬들 사이에 사인팔이들이 섞인 상황)
사인 못받은 팬이 울고 있던 상황
"왜 울어요???"
"아까 사인 못받아서 울었어요"
(열받은 손흥민)
손흥민은 참고교육을 보여주는데
"너 사인팔이잖아^^"
```

Conversion guidance:

- Parenthetical lines can become middle emotion beats, editor notes, or omitted if the visual already shows the emotion.
- Quoted lines become dialogue subtitles or quote-style overlays.
- Plain narrator lines become voice script and bottom captions.
- For text-only handoff, preserve the notation exactly so the editor can choose which layer to use.

## 11short Integration Rule

When used with `11short-production-agent`, this skill is mandatory before final captions, overlays, voice, or CapCut draft generation.

Output must function as a Shorts screenwriting pass, not a long script:

```text
작가모드 설계
- 시작모드: CC/remake 관찰 쇼츠
- 끝까지 볼 입자:
- 버릴 입자:
- 클릭 감정:
- 기억앵커:
- 큰 오픈루프:
- 초반 5초 후킹:
- 제목 후보 3-5개:
- 선택 제목:
- 하단 자막 전략:
- 중간 보라글 전략:
- 진행판정:
```

11short-specific rules:

- For 11short remake scripts, output a three-layer script package before any final caption/voice/CapCut handoff: `top_fixed_title_ko`, `middle_timed_situation_layer_ko`, and `bottom_tts_script_ko`.
- Before writing the three layers, classify the source as `Class A: visually self-explanatory` or `Class B: context-required`.
  - Class A examples: animals, physical comedy, visual surprise, process/result clips, paper ATM money reveal. Music/source audio may be more important than dense narration. Bottom TTS target is 180-220 Korean chars per minute, excluding spaces.
  - Class B examples: Japanese variety games, sudden combat knockdowns, news/incident context, emotional backstory, dialogue-led clips. Bottom TTS carries the situation. Bottom TTS target is 280-320 Korean chars per minute, excluding spaces.
- Top title is a fixed hook, usually two lines or fewer. It should use the user's declaration-hook style when useful: `여기 ... 있습니다`, `나는 ...`, `총성 한 발`, `주차 1미터`.
- Middle timed text carries source speech, emotion, state, and environment. It may include quoted actual source lines such as `"카드!! 카드!!"` and bracket state lines such as `(2번 버튼이 박살남)`.
- In the `중단` layer, use the bracket reaction caption system v1.7: `( ... )` is the free creative zone for emotion/situation/state/viewer reaction/timing/impact/comment-code/tone shaping; `" ... "` is the truth zone for actual source speech from the source video, source narrator, caster, or on-camera person. Quoted lines must match source audio/meaning and must not be invented for remix flavor. For variety, sports, animals, comedy, and visual surprise clips, actively use direct emotion words and reaction marks such as `(충격;;)`, `(당황)`, `(ㄷㄷ)`, `(ㅋㅋ)`, `(!!!!)`, and `(퍽!!)`. Do not put narrator TTS lines in quotes.
- Bottom TTS is the time-based narrator script. It must be understandable by audio only and must not depend on the middle layer.
- The first bottom TTS line is the win-or-lose hook sentence and memory anchor. It must be a concrete one-line opening built from the strongest visible/source-supported anchor: person, object, number, place, contradiction, irreversible action, or visible problem. Prefer lines in the user's style such as `나는 사도세자의 아들이다`, `주차장 1미터 움직였는데 300만원을 냈습니다`, or `강아지가 주인을 맥이기 시작했습니다`. Avoid generic openings such as `지금부터 보여드리겠습니다`, `이 영상은`, `여기 보시면`, or `도대체 뭘 하는 걸까요`. If this first line is weak, rewrite it before presenting the script.
- For Tikitaka/source-remake script work, present exactly five candidate first bottom TTS hook lines first and wait for the user's numbered choice before writing the full `상단/중단/하단/하단 원문` package. The five candidates are only first-line hooks, not five full script versions. Proceed without waiting only when the user explicitly says to decide yourself.
- Final chat output must be plain copyable Markdown text, separated as `상단`, `중단`, `하단`, and `하단 원문`. `중단` and `하단` keep timestamps. `하단 원문` repeats only the bottom TTS lines with timestamps removed. Do not merge the three layers into one storyboard block.
- For source dialogue, preserve information/action cues and useful emotion/comedy. Use cheers/laughter as source audio or short middle emotion. Drop meaningless numbers/noise unless they prove realism or setup.
- Run a three-layer independence check: top alone hooks, middle alone shows live situation, bottom alone tells the complete situation, and all together create layered comprehension.
- Treat the source audio as optional. The visible Korean text must be enough for a viewer to understand the setup, decisive action, turn, payoff, and reason to keep watching with original/source audio muted.
- For 11short production with voice/audio requested, the writer pass must output both `voice_script_ko` and the derived visible text package. The audio narration is the scenario spine; top/middle/bottom captions support it.
- For source-remake Shorts, first extract the original screen text/subtitles/caption meaning, then replace it with our Korean visible text. The remake should be judged as if original audio and original source text are unavailable.
- The script-writer pass must include an audio-off comprehension decision before final approval: `PASS`, `REWRITE_REQUIRED`, or `FAIL`.
- The script-writer pass must choose the hook material from the source, place the strongest hook in the first 3 seconds, and state the first-30-second hold reason.
- At least 3 of 5 random personas must say they understand the clip from our Korean visible text only, with original audio and original source text ignored.
- At least 3 of 5 random personas must say they would watch for 30 seconds or more, or to the end if the Short is under 30 seconds.
- If the multi-agent tool is available, the 5-persona gate must run as real parallel sub-agents. Record `parallel_persona_gate_mode: real_subagents`; `local simulation` is only a blocked fallback unless the user explicitly accepts it.
- Each persona must answer whether the Short is understandable by reading only the Korean on-screen text with source audio muted, and which missing explanation caused confusion.
- If fewer than 3 of 5 personas approve either required metric, revise the hook/captions/overlays and rerun with the remaining 5 personas from the pool. If the rerun reaches 3 of 5 or better, proceed; otherwise block as `REWRITE_REQUIRED`.
- Final captions/overlays cannot be called final if audio-off comprehension fails for 3 or more personas, or if the same missing context appears in 3 or more persona reviews.
- `title_candidates` may stay short for draft/profile naming, but the visible `top_title_text` must be a retention title, not a plain label.
- Prefer two-line titles when they create a stronger hook, e.g. `진정한 영웅\n이웃집 아저씨`.
- The first 5 seconds must tell viewers exactly what to watch for without explaining the whole ending.
- For text-only Shorts, dense text is allowed. Preserve useful Gemini/source observations by splitting them into bottom captions and purple beats.
- The source video remains the main actor. Captions should point to the decisive action, contradiction, reversal, or payoff.
- Do not reduce captions only to avoid clutter when the user said they will edit/delete text manually.
- Middle text is a one-line emphasis beat, not a paragraph. Keep it short enough to fit one line in the selected CapCut style.
- Bottom captions should usually be 2 lines and follow the spoken scenario. They must explain what is happening now through a hooked interpretation, not a flat recap. Do not invent unrelated jokes.
- Record the selected source route and caption hook mode in the script pass: `story_understanding_route`, `route_decision_reason_ko`, `caption_hook_mode`, `bottom_hook_strategy_ko`, and `middle_hook_strategy_ko`.

See `references/factory-formats.md` for channel formulas, `references/memory-anchor.md` for anchor patterns, and `references/shorts-academy.md` for 쇼츠학개론/마라하기 한계선-돈통-가단야-일치율 rules.

## Advanced Reference Loading

Keep this `SKILL.md` lean. Load these reference modules only when the task needs them:

- `references/angle-pivot.md`: for remake, inspired-by, viral-source, competitor-topic, or URL/source-derived topics that need a new angle before writing.
- `references/pre-click-state.md`: for mapping the viewer's defensive thought, validation need, anxiety, anger, or curiosity before the opening.
- `references/decisive-scene.md`: for contradiction-based openings, poetic compression, scene-first writing, physical plausibility, and keeping one person/object/anchor through the script.
- `references/decisive-image.md`: for turning the decisive scene into concrete image prompts, thumbnails, or stills without abstract maps, flags, globes, explosions, or symbolic collages.
- `references/rhythm-rules.md`: for sentence-level pacing, Korean ending variation, Shorts caption beats, and final polish.
- `references/channel-anchor.md`: for repeatable channel identity, recurring opening/ending objects, signature phrases, and factory-format consistency.
- `references/shorts-academy.md`: for 쇼츠학개론/마라하기 rules: 한계선, 관심 시청자 모수, 돈통/에셋, 결, 가단야, 우라까이, 일치율 0%, benchmark-video selection, category planning, and Shorts factory pre-draft checks.
- `references/evidence-tier.md`: for real incidents, history, law, finance, health, statistics, quotes, scams, court outcomes, or any claim that needs fact/inference/reconstruction separation.
- `references/youtube-policy-gate.md`: for YouTube community, advertiser, metadata, EDSA, copyright, misinformation, minors, and regulated-goods safety checks before drafting, after drafting, and before final PASS.
- `references/post-publish-feedback.md`: for using CTR, retention, comments, link clicks, and upload performance to update the next script or factory format.
- `references/parallel-persona-gate.md`: for the saved scaled visible parallel retention/readability gate that must run after a complete draft and before final script approval.
- `references/emotion-template-selector.md`: for the operator-chosen emotional lane menu; currently only `1. 통쾌` is active and the other lanes are placeholders.
- `references/hook-loop-structure.md`: for the universal opening loop, 10-30 second reward loop, and final recovery layer.
- `references/templates/mystery-sacrifice.md`: for the active yadam/sida/wrongful-accusation route: crisis, framed victim, planted proof, clue chain, villain motive, and payoff.
- `references/category-presets.md`: for default Intent Anchor presets by YouTube category before longform/midform drafting.
- `references/intent-anchor.md`: for setting Primary Emotion, Information Goal, Action Trigger, Share Target, and One-Month Memory before longform/midform drafting.
- `references/action-gate.md`: for action/share/memory/retention/subscription questions after longform/midform drafting; default scale is random 5 personas unless the user explicitly requests a full 10-persona gate.

For full production scripts, use the minimum needed chain:

```text
pre-click-state -> angle-pivot if source-derived -> decisive-scene -> memory-anchor -> factory-format -> rhythm-rules -> evidence-tier if factual -> youtube-policy-gate -> review-rubric
```

For scripts that also need image prompts or thumbnail scenes, add:

```text
decisive-scene -> decisive-image
```

For post-upload improvement, use:

```text
post-publish-feedback -> review-rubric -> factory-format update
```

## Safety And Trust

- Do not fabricate real victims, quotes, court outcomes, or statistics.
- For real incidents, distinguish fact, inference, and reconstruction.
- For finance/stock/coin, do not tell viewers to buy or sell. Focus on what to check.
- For CC/remake, respect source/license status and transform with commentary, framing, or captions.
- For historical or quote content, avoid claiming uncertain stories as fact.
- For YouTube policy risk, separate platform safety from advertiser suitability;
  do not call a draft PASS when the policy gate is `FAIL`, `BLOCK`, or
  unresolved `REWRITE_REQUIRED`.

## References

- `references/memory-anchor.md`: anchor scoring, examples, and reward-loop design.
- `references/factory-formats.md`: channel-specific repeatable formulas.
- `references/shorts-academy.md`: 쇼츠학개론/마라하기 lecture rules for 한계선, 돈통/에셋, 결, 가단야, 우라까이, 일치율 0%, and category/benchmark planning.
- `references/review-rubric.md`: script review scoring and failure diagnosis.
- `references/angle-pivot.md`: source-derived topic reframing and remake angle selection.
- `references/pre-click-state.md`: viewer emotional state before click and first-15-second alignment.
- `references/decisive-scene.md`: contradiction scene, poetic opening, clear unpacking, physical plausibility, and single-subject retention.
- `references/decisive-image.md`: concrete person-in-situation image prompts derived from the script anchor and decisive scene.
- `references/rhythm-rules.md`: mechanical sentence rhythm, ending variation, and caption beat polish.
- `references/channel-anchor.md`: channel-wide recurring identity beyond one video's memory anchor.
- `references/evidence-tier.md`: fact, reporting, inference, reconstruction, and opinion separation.
- `references/youtube-policy-gate.md`: YouTube policy, advertiser suitability, EDSA, metadata, link, copyright, and n8n policy QA contract.
- `references/post-publish-feedback.md`: analytics-driven format updates after publishing.
- `references/emotion-template-selector.md`: operator-chosen emotion lane menu.
- `references/hook-loop-structure.md`: universal open-loop and reward-loop structure.
- `references/templates/mystery-sacrifice.md`: active yadam/sida 통쾌 template.
