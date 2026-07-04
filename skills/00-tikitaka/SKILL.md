---
name: 00-tikitaka
description: Use only when the user explicitly asks for Tikitaka Korean Shorts source analysis, remake scripting, 티키타카 하자, 우라까이, hook candidates, 상단/timed 중단 draft creation, Gemini raw intake for Shorts URLs, or Gemini Shorts source notes. Do not use for SRT, CapCut, production packages, or polishing-only existing scripts.
---

# 00 Tikitaka

## Gemini Raw Intake First

When the user says `티키타카 하자` without source notes, ask for the Shorts URL
first:

```text
URL 주소 주면 Gemini 분석합니다.
```

When the user provides a YouTube Shorts/Reels/TikTok URL for Tikitaka intake,
run Gemini raw analysis before writing Tikitaka script. Use the exact system
prompt in `references/gemini_raw_intake_prompt.md`, verify the output includes
`final_warning_ko`, and save the copied Gemini output as Markdown with
`scripts/save_gemini_raw_md.ps1`.

Use this Google AI Studio UI sequence when browser/manual execution is needed:

1. Open `https://aistudio.google.com/u/1/prompts/new_chat` in Chrome and wait 5s.
2. Click `Optional tone and style instructions for the model`, wait 2s, click
   the same `Optional tone and style instructions for the model` area again,
   then wait 2s.
3. Paste the full prompt from `references/gemini_raw_intake_prompt.md` into the
   system instructions field.
4. Click the close icon twice, waiting 2s after each click.
5. Click the main `Enter a prompt` textarea, wait 1s, click it again, wait 2s.
6. Paste the user-provided Shorts URL, wait 1s, then click the
   `keyboard_return` / Run button.
7. If `permission denied` or `internal error` appears within 30s, repeat only
   steps 5-6 with the same URL. Try at most 3 total submissions.

Do not use the old `+ Create new instruction` -> `0701경` preset-selection path
for this Gemini raw intake flow.

Default save folder:

```text
%USERPROFILE%\OneDrive\22utube\22factory_20260628\01_shorts_factory\germini
```

Default filename shape:

```text
YYYYMMDD_<shorts_title>_gemini_raw.md
```

Do not use Google Docs by default. Treat the saved Gemini JSON as raw source
notes only; it is not verified timing, OCR, STT, source dialogue, or final
script truth.

For Tikitaka work that needs an actual draft, do not stop at Gemini raw notes.
Download or confirm `source.mp4`, then verify the important beats with source
evidence: duration, frame checks, OCR/STT when needed, and raw-vs-source
timecode mismatch notes. Keep any unverified Gemini ranges as
`PROPOSED_SOURCE_TIMECODE`.

## Ownership Matrix

- `00-tikitaka`: Shorts source analysis, remake script draft, hook, top/timed-middle, and script handoff only.
- `00script-writer`: polish/review an existing script draft only.
- `000short-production-agent`: SRT, layout JSON, CapCut, validation, exports, upload packages, and other production assets only.
- `22utube-production-agent`: shared factory policy only.

## Escalation Rule

Do not move to the next owner unless the user explicitly asks for that owner's
stage.

Adjacent intent is not permission to escalate. A Tikitaka request does not imply
production, `production_allowed`, `SCRIPT_LOCK`, `PASS`, export, upload,
completion, audio generation, SRT generation, layout JSON, or CapCut work.

If the user already has a draft and asks only for wording, rhythm, retention,
or writer review, route to `00script-writer` instead of rewriting it here.

## Default Boundary

Default state is `DRAFT_EYE_REVIEW`.

This skill owns only Korean Shorts remake scripting:

- hook candidates
- `우라까이`
- `상단`
- timed `중단`
- copy text that may later be used by a voice tool

Voice-copy text is part of the draft script only. This skill does not create
voice, audio files, SRT files, layout JSON, render plans, CapCut drafts, exports,
upload packages, or production packages.

## Supertone TTS Handoff

When the user says the script will become TTS/voice in a YouTube production,
make the handoff obvious, but do not generate audio from this skill.

- The production-side default TTS route is Supertone via:
  `${env:WORKSPACE_ROOT}\22factory_20260628\00_asset_tools\tools\make_supertone_tts.py`.
- On Windows, the safe launcher is `py -3.14`, not bare `python`.
- The script reads `SUPERTONE_API_KEY`, `SUPERTONE_VOICE_ID`,
  `SUPERTONE_PITCH`, `SUPERTONE_SPEED`, and `SUPERTONE_MODEL` from environment
  variables; never paste, print, or store the API key in chat, files, JSON,
  CapCut drafts, reports, or Git.
- On `home_windows`, User-scope Supertone variables may exist even when the
  current Codex process does not show them. The shared script checks Windows
  User environment as a fallback.
- Default voice/model are whatever the environment variables specify
  (`SUPERTONE_VOICE_ID` is currently the Chunsik setup on home_windows).
- If the user explicitly asks to generate audio, route to
  `000short-production-agent`; do not silently use Edge TTS, ElevenLabs,
  browser TTS, or any fallback provider.

If the user asks to make the video, create SRT/layout, build CapCut, render,
export, package upload files, or continue production, switch to
`000short-production-agent`.

If the user asks to polish an already-written script without production, switch
to `00script-writer`.

If the user asks about folder/root/rule policy, read `22utube-production-agent`
as a reference only.

## Active Root

For current 22utube work, check:

```text
${env:WORKSPACE_ROOT}\22factory_20260628\AGENTS.md
```

For new Tikitaka/Shorts script work, create or use an episode folder under:

```text
22factory_20260628\01_shorts_factory\episodes\SH_YYYYMMDD_slug
```

Legacy `11utube/11short` paths are read-only reference or explicit repair
targets unless the user asks for legacy work.

## Input Authority

Treat Gemini Shorts JSON, model summaries, pasted analysis, comments, and user
notes as source notes for remake scripting. They are not production truth.

Do not invent verified source timing, source dialogue, OCR, or scene order from
Gemini alone. Mark any proposed source range as
`PROPOSED_SOURCE_TIMECODE` until the user confirms it or a source-evidence tool
verifies it.

If source verification is needed before script confidence, use `watch` or the
current source-evidence workflow before claiming final timing.

## Output Contract

Default chat output:

```text
상단
...

중단 초벌대본
[블록 1 | 편집 00:00-00:03 | 원본 제안 00:00-00:00 | 상태 PROPOSED_SOURCE_TIMECODE]
...

구간 오디오 정책표
1구간 | caption_type=speaker_quote | source_audio=on | tts=off | bgm=optional_duck
2구간 | caption_type=tts_narration | source_audio=off | tts=on | bgm=optional
...

중단 TTS 글자만 복사
...

상태
- script_status: DRAFT_EYE_REVIEW
- production_status: WAIT_EXPLICIT_000SHORT_REQUEST
```

Use `1/2/3/4/5` labels only as temporary source-range confirmation IDs, not as
the creative structure. The creative structure must be functional: hook,
misread, escalation, reversal, payoff, or another stated role.

## Segment Audio Policy Contract

Tikitaka must decide the segment audio policy at script time, before production
starts. `000short-production-agent` must validate and implement this plan; it
must not be the first place where quote/TTS/source-audio policy is guessed.

For every timed `중단` block, include one explicit row in `구간 오디오 정책표`.

Allowed values:

```text
caption_type:
- speaker_quote        = original/source speaker line, shown with "..."
- tts_narration        = generated voice narration
- situation_caption    = visual/situation explanation, shown with (...)
- tts_plus_source      = TTS while source audio remains intentionally audible
- ranking_item         = ranking/TOP-N beat

source_audio:
- on     = original/source video audio must be audible
- off    = original/source video audio must be muted
- duck   = original/source video audio remains low under TTS/BGM

tts:
- on
- off

bgm:
- optional       = no BGM is forced; user may choose it later
- optional_duck  = no BGM is forced; if user later chooses BGM, duck it here
- on             = BGM is explicitly required by the user or locked plan
- off            = no BGM in this segment
- duck           = required BGM remains low in this segment
```

Default mapping:

```text
"화자발언" / speaker_quote      -> source_audio=on,   tts=off, bgm=optional_duck
TTS 나레이션 / tts_narration    -> source_audio=off,  tts=on,  bgm=optional
(상황설명) / situation_caption  -> source_audio=off,  tts=off, bgm=optional
TTS+원본현장음 / tts_plus_source -> source_audio=duck, tts=on,  bgm=optional_duck
랭킹형 / ranking_item           -> source_audio=off by default; use on only for verified quote/reaction beats
```

BGM is never mandatory by default. Use `bgm=on` or `bgm=duck` only when the user
explicitly chose a BGM/SFX asset, asked for a specific music mood, or the locked
production plan names a BGM file. Otherwise keep BGM as `optional` or
`optional_duck` so production can continue without adding music.

If the user gives a remix such as `원본 1-2-3-4-5 -> 우라까이 4-3-1-5-2`,
audio policy follows the remixed timeline order, not the original source order.
Every row must keep both:

```text
source_order: original source segment id such as 1,2,3,4,5
timeline_order: remixed position such as 4,3,1,5,2
```

Example:

```text
구간 오디오 정책표
1구간 | source_order=4 | timeline_order=1 | caption_type=speaker_quote | source_audio=on | tts=off | bgm=optional_duck
2구간 | source_order=3 | timeline_order=2 | caption_type=tts_narration | source_audio=off | tts=on | bgm=optional
3구간 | source_order=1 | timeline_order=3 | caption_type=speaker_quote | source_audio=on | tts=off | bgm=optional_duck
4구간 | source_order=5 | timeline_order=4 | caption_type=tts_plus_source | source_audio=duck | tts=on | bgm=optional_duck
5구간 | source_order=2 | timeline_order=5 | caption_type=tts_narration | source_audio=off | tts=on | bgm=optional
```

When production is likely to continue, also provide a copyable JSON handoff:

```json
{
  "tikitaka_segment_audio_plan": [
    {
      "segment_id": "seg_001",
      "source_order": 4,
      "timeline_order": 1,
      "edit_range": "00:00-00:03",
      "source_range_status": "PROPOSED_SOURCE_TIMECODE",
      "caption_type": "speaker_quote",
      "source_audio_policy": "on",
      "tts_policy": "off",
      "bgm_policy": "optional_duck",
      "visible_text_role": "speaker_quote"
    }
  ]
}
```

Hard fails:

- timed `중단` blocks exist but `구간 오디오 정책표` is missing
- `"..."` speaker quote block has `source_audio=off`
- TTS narration block keeps source audio `on` without explicit
  `caption_type=tts_plus_source`
- remixed order is shown, but `source_order` and `timeline_order` are not both
  recorded
- production handoff is requested, but no machine-readable
  `tikitaka_segment_audio_plan` is provided

## Shorts 5-Type Production Matrix

Before writing the draft, classify the video into one of 5 production types.
The type determines the entire audio/mute/TTS/caption policy.

```text
유형 | 구조                         | 원본음성        | TTS         | 자막       | BGM
A    | TTS 나레이션형               | ❌ 전체 음소거   | ✅ 전체      | ✅ (보조)  | ✅
B    | 자막설명형                    | ❌ 전체 음소거   | ❌ 없음      | ✅ 전체    | ✅
C    | 초반 화자 → TTS 전개형        | ✅ ""구간만 ON  | ✅ ()구간    | ✅         | ✅
D    | 초반 TTS → 화자 전개형        | ✅ ""구간만 ON  | ✅ 초반/()   | ✅         | ✅
E    | 랭킹형                        | ❌ (보통 음소거) | ✅ 또는 자막 | ✅         | ✅
```

### Muting Decision Rule

```text
원본 음성 ON  → 해당 구간이 "" 화자발언으로 표기되어 있을 때
원본 음성 OFF → "" 가 아닌 구간 (TTS/자막/BGM만 쓸 때)
예외          → "" 구간이더라도 원본 음질이 너무 나쁘면 TTS로 대체 (작가 판단)
```

### Per-Type Mute Detail

- **A (TTS 나레이션형)**: 전체 음소거. 단, "" 표기된 인물 말이 중간에 있으면
  그 구간만 원본 음성 켬.
- **B (자막설명형)**: 전체 음소거. ""도 보통 자막으로만 처리.
- **C (초반 화자→TTS)**: "" 구간 원본 음성 ON (필수), ()/TTS 구간 OFF.
  ""와 ()가 번갈아 나올 때마다 음소거 토글.
- **D (초반 TTS→화자)**: C와 같은 원리. "" 구간만 원본 음성 ON.
- **E (랭킹형)**: 보통 음소거 + TTS/자막. 단, 각 순위 안에 "" 발언이 있으면
  그 구간만 켬.

## Dual Writer Mode (우라까이/와우포인트/유형 확정)

When confirming wow point, urakai structure, and production type, use two
real CLI-based writer agents to debate before locking.

### CLI Tools

- **Writer A (Codex CLI / GPT 5.5)**: aggressive hook, emotional escalation,
  retention-first, willing to dramatize for engagement.
  ```bash
  codex exec "당신은 GPT 5.5 작가모드입니다. ... <분석 지시> ..." 2>&1
  ```
- **Writer B (Claude CLI / GLM 6.2)**: fact-grounded, structural balance,
  risk-aware, prioritizes coherence and policy safety.
  ```bash
  claude -p --bare --dangerously-skip-permissions "당신은 GLM 6.2 작가모드입니다. ... <분석 지시> ..." 2>&1
  ```

### Debate Protocol

1. **Round 1**: Both CLIs receive the same video context independently.
   Each outputs: type recommendation, wow point, urakai, disagreement point.
2. **Round 2**: Share Round 1 outputs cross-wise. Each CLI responds:
   동의/부분동의/유지 with reasoning.
3. **Synthesis**: The orchestrator resolves cross-convergence (both writers
   moving to each other's position = middle ground) into a final decision.

Both writers must output:
- recommended production type (A/B/C/D/E) with reasoning
- wow point confirmation or correction
- urakai structure recommendation
- one concrete disagreement point

The final decision is the synthesis of both perspectives. If they disagree on
type, the higher-audio-fidelity type wins unless the source has no usable
speech at all.

## Draft Workflow

1. State the frame: what situation the remake is using and why.
2. **Classify production type (A/B/C/D/E)** using the 5-type matrix.
3. Map source notes into functional beats.
4. Write hook candidates if requested or useful.
5. **Run dual writer mode** to confirm wow point, urakai, and type.
6. Produce `상단 + timed 중단` with type-appropriate audio policy.
7. Provide the copy-only voice text block as script text, not as audio work.
8. Keep status at `DRAFT_EYE_REVIEW` unless the user explicitly asks for the
   next owner.

## Shorts TTS Storytelling Mode

If a Shorts remake can be told as TTS narration, story, or 썰풀이, this mode is
mandatory, not optional.

This mode is not separate from 우라까이. 우라까이는 the baseline condition: the
remake must not keep the same expression, scene-entry order, emotional angle, or
payoff wording. The TTS story gate decides how aggressively the same visual
source must be reframed through a stronger writer premise.

Do not start as a flat event summary. Lead with the strongest hookable
emotional premise, deadline, loss, desire, misunderstanding, or irreversible
action. In Tikitaka writer mode, the hook is allowed to use a plausible dramatic
premise that is not directly verifiable when it is needed to make the story work,
especially for TTS-heavy videos with little or no source speech.

If the user says `후킹 쎄게`, `작가모드`, `우라까이`, or directly corrects the
agent to make the opening more provocative, treat that as a hard routing signal:
choose `hook_first_writer_premise` unless the video is clearly an information,
news, politics, medical, legal, safety, accident, crime, finance, or other
fact-first lane. Ask the user only when the lane is genuinely unclear.

```text
weak: 할아버지가 손자를 만났다
strong: 시한부 할아버지가 마지막으로 손자를 보러 왔다
```

The strong version is a writer premise, not source evidence. Use it when it fits
the visual/emotional arc and creates a better hook. Do not flatten the opening
just because the premise is not independently verified.

For example, if the source only proves "a soldier met his daughter at a
graduation ceremony", do not write the flat version first. Build a hookable
story premise such as:

```text
못 만날 줄 알았던 딸이,
수료식장에 와 있었습니다.
```

or:

```text
수료식만 끝나면 다시 기다려야 할 줄 알았습니다.
그런데 뒤돌자마자, 딸이 품에 안겼습니다.
```

This is valid Tikitaka story framing even when the source does not prove the
father literally heard "she cannot come." The public script may use the premise
to create curiosity; internal reports must still avoid calling it verified
source evidence.

Avoid only inventions that create a materially different or harmful claim, such
as crime accusations, medical diagnoses, death, abuse, political/news claims,
or other high-risk facts that would change the video's basic meaning. For
ordinary emotional/family/TTS story hooks, prefer dramatic premise over flat
fact-reporting.

Required TTS story fields:

- `tts_story_mode_required: true|false`
- `truth_mode: fact_first|hook_first_writer_premise`
- `source_supported_emotional_condition`
- `writer_premise_for_hook`
- `writer_premise_status: verified|plausible_unverified|fictionalized_hook`
- `flat_event_summary`
- `emotional_entry_line`
- `changed_scene_entry_order`
- `changed_korean_expression_strategy`
- `viewer_emotion_target`
- `payoff_recovery_line`

For emotional story/remake Shorts, prefer:

- person before explanation
- loss or deadline before background
- concrete action before abstract feeling
- one emotional question before the answer
- final line that returns to the first emotional anchor

Do not over-explain visible action when TTS is the main carrier. Use captions to
hit the emotional angle and leave simple visuals to do their own work.

Hard fails:

- flat event summary when TTS narration can carry the story
- synonym-only Korean replacement
- same source flow with only different words
- refusing a strong hook only because the emotional premise is not directly
  verifiable in a TTS-heavy ordinary story
- invented high-risk facts such as illness, death, crime, abuse, political/news
  claims, or other materially harmful claims unless the source actually supports
  them
- emotionally strong wording where a first-time viewer cannot tell who wants
  what and what may be lost

## Required Gates Before Stronger Claims

- Do not claim `SCRIPT_LOCK` from this skill alone.
- Do not claim production allowed.
- Do not claim source-verified truth from raw Gemini notes.
- Do not skip human Korean cleanup before any final visible Korean text.
- Do not proceed past missing source evidence when the script depends on exact
  timing, OCR, or dialogue.
- Do not call a TTS-capable story/remake draft eye-ready unless the TTS
  storytelling mode has been considered and, when applicable, the emotional
  entry line is source-supported and non-flat.

## Reference Routing

- For hook review, read `references/pre_script_hook_review.md`.
- For Shorts craft rules, read `references/shorts-academy.md`.
- For old contract details or legacy repair only, read
  `references/archived-full-skill-20260629.md`.

Keep this `SKILL.md` as the active router. Do not re-expand it with legacy
examples, PASS templates, production reports, CapCut details, or long handoff
instructions.
