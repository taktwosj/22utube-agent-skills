# Shorts Academy Reference

Use this reference for Tikitaka draft decisions in Korean Shorts source-remake
scripting when the user mentions 쇼츠학개론, 마라하기, 한계선, 돈통, 에셋, 결,
가단야, 우라까이, 일치율 0%, 벤치영상, or category constraints. It is
not standalone channel planning and does not authorize SRT, CapCut, or production
asset work.

This reference is distilled from 쇼츠학개론 1-3강 text/PDF analysis and the user's added 한계선/Q&A notes. It is a decision guide, not a replacement for source verification, YouTube policy gates, or the current 11short caption contract.

## Core Doctrine

- Do not start from "make a video"; start from "is the channel/category ceiling high enough?"
- Use data, not taste. 조회수 is the first objective signal that a topic, message, or format has broad demand.
- Build a 돈통/에셋 first: collect Korean channels and benchmark videos in the same 결, then classify them by category, message, hook, and repeatable template.
- A channel's early videos define its first impression to the algorithm. Avoid guideline-risk videos and off-theme tests early.
- Production flow: `한계선 -> 에셋/돈통 -> 결 -> 가이드라인 -> 벤치영상 -> 가단야 -> 마라공식 -> 업로드 루틴`.

## 한계선 판단

Judge a channel/topic ceiling before writing:

1. Estimate the 관심 시청자 모수.
   - A category's ceiling is roughly set when the topic is selected.
   - Example: a "노브랜드 핫템 TOP3" video cannot exceed the audience pool of people who know or care about No Brand.
2. Verify with 조회수.
   - High view counts on similar Korean channels are evidence that the market reacts to that message.
   - Do not trust only the operator's interest or a single viral outlier.
3. Build a grouped asset set.
   - Collect similar channels by category and message.
   - If multiple channels in the same 결 repeatedly get views, the topic is safer.
4. Prefer large-ceiling categories when starting.
   - Common high-ceiling lanes in the lecture notes: 감동, 국뽕, 드라마/영드짜, 예능, 스포츠.
   - Other useful lanes: 동물, CCTV/사건, 생활꿀팁, 정치, 유머, 랭킹, 게임, 애니/3D, 음악, 연예인/팬튜브.

If the ceiling is unclear, do not write a final script. Ask for or collect 5-10 Korean benchmark channels first.

## 돈통 / 에셋 / 결

돈통 is a reusable asset bank of channels/videos that already proved demand.

- Collect channels by similar 소재 and similar viewer emotion.
- Group by 결, not just broad category. `스포츠` is too broad; `손흥민 감아차기`, `야구 국뽕`, `테니스 멘탈 흔들기` are closer to usable 결.
- A lower-view benchmark can still be useful if it matches the channel 결 better than a high-view off-theme video.
- Do not switch a channel's 소재 casually after launch; the algorithm and audience learn the channel's first pattern.

## 마라하기 공식: 일치율 0%

The target is not "copy with different Korean"; it is to change the data surface while preserving the proven message.

우라까이는 every remake's mandatory structure rule. Do not keep the same flow
with only different words. If a factual/process sequence cannot be reordered
without breaking truth, still change the functional flow: hook entry, tension
placement, reaction timing, caption interpretation, cut emphasis, and payoff
recovery.

Three data surfaces must change:

1. Keyword
   - Change title, description, visible captions, and script wording.
   - Replace most source words except unavoidable names, numbers, objects, and verified speech.
2. Sound / Hz
   - Change edit points, TTS placement, source-audio use, SFX, pacing, and pauses.
   - For 11short, TTS should be sparse when the user requested sparse voice: one short opening sentence and one short ending sentence.
3. Pixel / Frame
   - Change crop, resize, timing, color, filter/effect, frame composition, and cut order where allowed.
   - Ranking videos must not preserve the original ranking order; change the order around the verified payoff.

Required flow fields:

```json
{
  "urakkai_required": true,
  "same_flow_allowed": false,
  "flow_urakkai_plan": {
    "original_flow": "...",
    "new_flow": "...",
    "changed_hook_entry": "...",
    "changed_tension_point": "...",
    "changed_payoff_recovery": "..."
  }
}
```

For current 11short work, this rule must obey the active caption constitution: output `상단 + timed 중단 + 중단 TTS 글자만 복사`; do not reintroduce legacy `하단`.

## TTS Storytelling Shorts

If a Shorts remake can be carried by TTS narration, story, 사연, 미담, photo
explainer, 군림보-style narration, or 썰풀이, emotional storytelling framing is
mandatory. Do not treat it as a flat summary plus changed synonyms.

The first line should enter through the strongest source-supported emotional
condition, deadline, loss, desire, contradiction, or irreversible action.

```text
weak: 할아버지가 손자를 만났다
strong: 시한부 할아버지가 마지막으로 손자를 보러 왔다
```

Use the strong version only when the source supports the stronger facts. If the
source does not support `시한부`, `마지막`, family motive, illness, death,
confession, or deadline, do not invent them. Instead, intensify the same verified
meaning through entry order, suspense, viewer question, and payoff recovery.

Required TTS story fields:

```json
{
  "tts_story_mode_required": true,
  "source_supported_emotional_condition": "...",
  "flat_event_summary": "...",
  "emotional_entry_line": "...",
  "changed_scene_entry_order": "...",
  "changed_korean_expression_strategy": "...",
  "viewer_emotion_target": "...",
  "payoff_recovery_line": "..."
}
```

Hard fails:

- the draft opens with a neutral event summary even though TTS can carry a story
- the remake changes only synonyms while keeping the same flow
- the strongest emotional fact is invented rather than source-supported
- the viewer cannot instantly tell who is hurting, what they want, what may be
  lost, and why the moment matters

## 가단야

Apply 가단야 before script lock.

- 가: 가이드라인. Check policy/safety first, especially minors, injury, rescue, real incidents, weapons, sexual content, hate, harassment, and copyright risk.
- 단: 단어. Replace the benchmark wording aggressively while preserving source-supported meaning.
- 야: 야부리. Add hook pressure, viewer reaction, contradiction, comment-coded phrasing, and the message people reacted to.

Use comments as evidence for 야부리 when available. A viral video's top comments often reveal the exact emotion viewers paid attention to: 분노, 감동, 웃참, 공감, 국뽕, 충격, 반전.

## Script Framing Rules

- First identify the proven message: what did viewers react to?
- Then choose the strongest wow point and payoff.
- For source-remake shorts, the source visual remains the main actor. Captions point to what to watch.
- Use `(현장상황설명)` for visible action, state, emotion, atmosphere, or reaction.
- Use `"화자발언"` only for verified source speech/subtitle/reliable transcript. Do not invent quotes for flavor.
- Plain lines are narrator/context captions or sparse TTS candidates.
- The top title should expose category and payoff promise quickly: `대상 + 이상한 상황 + TOP/반전/사건`.

## Composite Classification And Layer Mix

Do not classify a source with one label only. Build a composite label before
drafting, then decide the caption layer mix from source evidence and existing
benchmark-script shape.

Required classification fields:

```json
{
  "source_region": "domestic_korea|overseas|mixed_global|unknown",
  "emotion_intent": "감동|정보|웃음|충격|분노|국뽕|공감|사이다|호기심|스포츠감탄|실용|미담|unknown",
  "channel_family": "...",
  "content_mode": "...",
  "source_surface": "cctv|sports_game|broadcast_variety|drama_movie|game_screen|animation_3d|recipe_process|lifehack_process|photo_tts_explainer|interview_speech|speech_award|pet_moment|rescue_incident|other",
  "composite_label": "해외+정보+랭킹",
  "layer_mix_decision_required": true
}
```

Examples:

- `유명한 돈 잘 버는 스포츠선수 랭킹` = `스포츠 + 정보/돈 + 랭킹형`.
- `방송사고랭킹` = `예능/방송 + 충격/웃음 + 랭킹형`.
- `영화랭킹` = `영짜 + 정보/취향 + 랭킹형`.
- `국내 CCTV 감동 구조` = `국내 + 감동/미담 + CCTV/사건형`.
- `군림보식 인물 소개` = `사진/이미지 + TTS 연속 설명형`.

The composite label affects the script layer mix. Do not decide TTS quantity
from category name alone. Inspect the real source audio, OCR, visible action,
existing source script, and user-supplied sample script first.

Required layer mix fields:

```json
{
  "caption_layer_mix": {
    "tts_density": "none|sparse|balanced|heavy",
    "quoted_speech_density": "none|low|medium|high",
    "situation_caption_density": "low|medium|high",
    "source_audio_priority": "keep|duck|replace|unknown",
    "tts_role": "...",
    "quoted_speech_role": "...",
    "situation_caption_role": "...",
    "layer_mix_basis": "source_script_analysis|direct_source_evidence|user_sample_script",
    "do_not_invent_quotes": true
  }
}
```

Default layer mix by source surface:

| source surface / mode | Default layer mix |
| --- | --- |
| `랭킹형` | Usually sparse TTS for opener/closer or list bridges, with `(상황설명)` and verified `"화자발언"` carrying many beats. Literal ranking order must be remixed. |
| `sports_game` | Use verified commentator/player/referee `"화자발언"` when present, short TTS for setup/payoff, and `(상황설명)` for movement, pressure, score context, and reaction. Preserve source audio when it carries excitement. |
| `cctv` | Quoted speech is usually none or low. Use `(상황설명)` plus restrained TTS for context, cause, pursuit, rescue, or payoff. Never invent dialogue just because the scene has people. |
| `photo_tts_explainer` / `군림보` | Photos, still images, or simple visual references support continuous TTS explanation. `tts_density=heavy`, `quoted_speech_density=none|low`, `situation_caption_density=low|medium`. The script is mostly plain narration; use `( )` only for necessary visual pointers. |
| `game_screen` / Roblox / Minecraft | Use `(상황설명)` for in-game action and mechanic changes, verified player/chat quotes only when source-supported, and TTS for setup, rule explanation, and payoff. |
| `recipe_process` / `lifehack_process` | TTS or step narration can be balanced/heavy. Use `(상황설명)` for process states and result shots. Quote only on-camera/source speech. |
| `drama_movie` / `broadcast_variety` | Quoted speech can be high, but only verified source speech/subtitle/transcript. Use `(상황설명)` for atmosphere and reaction; TTS is usually a sparse connector. |
| `pet_moment` / `rescue_incident` | Quote density is usually low. Use high `(상황설명)` and sparse/balanced TTS for setup, emotional turn, and payoff. |
| `interview_speech` / `speech_award` / `politics` | Verified quotes may be high. TTS frames context and consequence. Fact/policy checks are mandatory before emotional framing. |

## Channel Family Map

Use the user's channel-family labels as the first classification gate. This is
not the same as `content_mode`: a video can be `동물 + 랭킹형`, `스포츠 + 반전형`,
`영짜 + 티키타카형`, or `게임 + 사건형`.

Record these fields before drafting:

```json
{
  "source_region": "...",
  "emotion_intent": "...",
  "channel_family": "...",
  "content_mode": "...",
  "source_surface": "...",
  "composite_label": "...",
  "layer_mix_decision_required": true,
  "caption_layer_mix": "...",
  "order_rule": "...",
  "source_use_risk": "...",
  "ceiling_note": "...",
  "urakkai_required": true,
  "same_flow_allowed": false,
  "flow_urakkai_plan": "...",
  "benchmark_channel_family_match": true
}
```

User channel families:

| channel_family | Main asset bank | Default script bias | Hard caution |
| --- | --- | --- | --- |
| `한짜` | Korean school, local, community, everyday archive, Korean situation clips | Situation read, light explanation, social reaction | Keep the Korean context clear; do not drift into generic variety. |
| `국뽕` | Korea-pride, national pride, Korean athlete/soldier/product/history praise | Emotion pressure, pride payoff, comment-coded hook | Fact-check aggressively; avoid inflated or hateful claims. |
| `해짜` | Overseas/world story, translated foreign clips, global curiosity | Foreign context -> Korean viewer reaction -> payoff | Separate translation, inference, and verified source. |
| `스포츠` | Game highlights, athletes, skill, comeback, funny sports moments | Tension -> move/result -> reaction | Do not invent scores, records, injuries, or intent. |
| `동물` | Pet/wild animal behavior, rescue, cute mistake, reaction clips | Visible behavior + `(현장상황설명)` heavy | Do not claim inner psychology as fact; rescue/abuse needs restraint. |
| `인물` | Interesting people, odd jobs, rich/poor, family/social figures | Identity setup -> contradiction -> reveal/payoff | Verify names/claims; avoid defamation or unsupported motive. |
| `드짜` | Drama scene remake/recap/reaction | Dialogue/situation tension, 티키타카, emotional read | Distributor-controlled or uncleared drama footage is BLOCK unless user-cleared. |
| `영짜` | Movie scene remake/recap/reaction | Scene question -> conflict -> payoff | Distributor-controlled or uncleared movie footage is BLOCK unless user-cleared. |
| `예능` | Variety/reality show moments, funny interaction, awkward reaction | 티키타카, reaction caption, post-line atmosphere | Preserve verified speech meaning; do not invent quoted lines. |
| `정치` | Political figures, policy conflict, public issue commentary | Fact -> contradiction -> viewer question | High policy/defamation risk; separate fact, inference, opinion. |
| `애니/3D` | Anime, animation, 3D, virtual character, stylized scene | Visual novelty + simple story pressure | IP/source-use risk; keep claims inside visible source. |
| `연예인/팬튜브` | Idol, celebrity, fan moment, behind clip | Fandom context -> moment -> reaction | Rumor, private life, minors, and harassment risk are high. |
| `군림보` | Photo/still-image explainer, personality/background summary, list-style image narration | Continuous TTS explanation over photos/images; simple visual support | Treat as `photo_tts_explainer`; do not force dialogue or heavy `(상황설명)` when the source is just photos plus TTS. |
| `군사` | Military, weapon, soldier, tactics, defense story | Object/capability -> tension -> result | Weapon/geopolitical claims need high factual discipline. |
| `동기부여/명언` | Motivation, quote, mindset, success/failure lesson | One concrete takeaway | Weak ceiling unless the figure, pain, or visual proof is strong. |
| `게임` | Game ranking, player legend, patch, funny bug, gaming incident | Setup -> mechanic/conflict -> payoff | Use exact game terms; avoid claims unsupported by source/community evidence. |
| `랭킹` | Ranked list, TOP-N, best/worst, compilation | Count/list pressure, strongest payoff last | Ranking order must be remixed; set `source_order_allowed=false`. |
| `유머` | Funny clip, skit, absurd moment, fail, reaction | Setup -> beat -> laugh/reaction | Do not over-explain the joke; cut timing is part of the rewrite. |

If a channel family and content mode conflict, source truth wins first, then the
channel family, then the content mode. Example: a `동물` clip that is also TOP4
must keep visible animal behavior accurate while still remixing the ranking
order.

## Content Mode Notes

- `랭킹형`: reorder source order, keep the strongest payoff last, and make the
  top line instantly genre-readable. This is the only mode where order remix is
  mandatory by default, but it is not the only mode where 우라까이 is mandatory.
- `티키타카/예능형`: preserve real speech meaning; the comedy often comes from
  reaction and post-line atmosphere, not only the words.
- `반전형`: keep setup/payoff truth, but change reveal timing, hook wording, and
  reaction captioning.
- `과정형`: do not break cause-effect order if it makes the scene confusing;
  change cut points, entry question, tension placement, wording, speed, SFX,
  crop, and payoff framing instead. Same factual order can remain only when the
  functional viewing flow is clearly different.
- `사건/미담형`: trust first. Separate fact, inference, and emotional read.
  Keep jokes restrained.
- `관찰/리액션형`: explain what the viewer should notice with
  `(현장상황설명)`. Do not replace visible evidence with narrator opinion.
- `지식/설명형`: turn abstract information into one concrete object or number.

## Pre-Draft Checklist

Before drafting or revising a Shorts script, answer:

- What is the channel/category ceiling?
- Which benchmark channel/video proves demand?
- What is the 결?
- What is the proven viewer reaction/message?
- What is the wow point?
- What is the payoff?
- What is the composite label: source region + emotion/intent + family + mode + source surface?
- What caption layer mix is justified by source evidence: TTS, verified quotes, and `(상황설명)`?
- If TTS can carry the story, what is the source-supported emotional entry line instead of the flat event summary?
- What changes keyword, sound, and pixel/frame similarity?
- What is the policy risk tier?
- Does the output follow current `상단 + 중단 + 중단 TTS 글자만 복사`?

If any of ceiling, benchmark evidence, source truth, or policy is missing, mark the script as DRAFT or REWRITE_REQUIRED, not PASS.
