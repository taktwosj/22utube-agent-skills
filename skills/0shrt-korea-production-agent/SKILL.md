---
name: 0shrt-korea-production-agent
description: 0쇼츠 한국사 제작 에이전트. Dedicated workflow for 11utube/0shrt Korean history Shorts production. Use when the user asks to make, continue, fix, review, or gate 0shrt/0쇼츠 Korean history Shorts, standard Korean narration shorts, GPT Image2 history scenes, 0shrt CapCut drafts, visible local CapCut project registration, YouTube Shorts upload text, Supertone TTS/SRT packages, Joseon-history BGM, CapCut emotion_pack effects, manga/flash/wind/stamp/SFX overlays, or work under 11utube/0shrt/history-chunsik/episodes.
---

# 0쇼츠 역사춘제작 에이전트

This skill overrides the general `22utube-production-agent` for `${env:UTUBE_ROOT}\0shrt` work.

## Global Gates

This skill obeys the 11utube global gates in `11utube/00_TOP_LEVEL_DIRECTIVE.md`.

- Any new script, serious rewrite, or script finalization must pass `00script-writer` 작가모드, the YouTube Policy Gate, and the visible random 5-persona retention/readability gate before it is called final. If fewer than 3 of 5 approve, rewrite from the feedback and run the remaining 5 personas as the second pass; final PASS still requires 3 of 5 on that pass.
- Any Image2 prompt/image, TTS, SRT, CapCut, render, upload package, or final report must show the shared `A. n8n 실행` / `B. 하네스 검증` board.
- If n8n is not used or unreachable, mark it as `WAIT - local run`; never fake a pass.
- 0shrt harness/QC is the PASS/FAIL authority and blocks the next stage when it fails.

## Portable Paths

Use `${env:UTUBE_ROOT}` as the 11utube root on every PC. If it is not set, most repo scripts fall back to their own file location, but shared office setups should set it once:

```powershell
$env:UTUBE_ROOT = "$env:UTUBE_ROOT"
$env:WORKSPACE_ROOT = "$env:WORKSPACE_ROOT"
```

Do not hardcode a machine-specific user home path or drive alias in new scripts or examples. Use `${env:UTUBE_ROOT}\...` for paths under `11utube`.

## Required Context

Before producing, editing, generating images/audio, or creating CapCut drafts, read these files when present:

```text
${env:UTUBE_ROOT}\AGENTS.md
${env:UTUBE_ROOT}\00_TOP_LEVEL_DIRECTIVE.md
${env:UTUBE_ROOT}\shared_script_reading_rules.md
${env:UTUBE_ROOT}\0shrt\agent.md
${env:UTUBE_ROOT}\video\VIDEO_LAYOUT_SPEC.md
${env:UTUBE_ROOT}\n8n\N8N_AGENT_PARALLEL_TODO.md
${env:UTUBE_ROOT}\n8n\VISUAL_PHASE_WORKFLOW_SPEC.md
```

If those files conflict with the locked rules below, the locked rules below win for 0쇼츠.

## Mandatory Intent Brainstorm Gate

For any 0shrt production, rewrite, TTS/SRT, Image2, CapCut, or harness request, run this gate before editing files or generating assets. This is the step that translates the user's rough request into an executable production brief.

Do not run it for a simple factual question, folder-open request, one-off command, or status check. If the user says `브레인스톰`, `brainstorm`, `찰떡같이 이해`, or gives a messy production request, run it even if the rest of the task is not fully specified.

Report this first:

```text
Brainstorm
- 사용자 의도:
- 채널/프로필:
- 입력 소스:
- 결과물:
- 보이스/모델:
- 자막 원칙:
- 역사/사투리/발음 주의:
- 금지/주의:
- 애매한 점:

Harness TODO
- [ ] draft
- [ ] audio
- [ ] imagegen
- [ ] capcut
- [ ] final/all
```

Proceed after posting the gate unless the user objects or a listed ambiguity blocks production. Keep the visible TODO list below updated during the work.

## Current Locked Defaults

These are the current 0쇼츠 production defaults. Treat them as profile rules, not suggestions.

- Target length is roughly 55-70 seconds for history Shorts. Do not over-compress a clear script just to force it under 60 seconds unless the user explicitly asks for a strict one-minute cut.
- Voice is body-only Chunsik/Chungcheong dialect narration. Keep the current voice ID unless the user changes the speaker.
- BGM is chosen randomly from valid music files in `${env:UTUBE_ROOT}\video\배경음`. Do not use obvious SFX files such as typewriter, whoosh, boom, hit, impact, thunder, footsteps, or other very short effect sounds as BGM.
- BGM starts at `0.0s`, track name is `shorts_background_music_joseon_history`, draft volume is `0.05623413251903491`, and CapCut UI volume must read `-25.0 dB`.
- Do not use `잔잔은은피아노` for this profile.
- Do not add typewriter SFX: no `타자음3초`, no `shorts_typewriter_sfx`.
- Do not add middle purple overlay in 0쇼츠. Purple middle cards belong to other formats, not this profile.
- Captions are bottom-only, max 2 lines, max 10 Korean-visible characters per line for CapCut drafts.
- Voice and displayed caption text must match. Do not let CapCut show a different subtitle than the narration.
- Display captions must use viewer-readable text, not TTS pronunciation text. Years, centuries, and quantities must stay as display forms such as `1795년`, `14세기`, `500여 석`; only the TTS/voice field may use spoken forms such as `천칠백구십오년`.
- When a line needs a pronunciation override, write the source as `1795년[[천칠백구십오년]]`. The displayed caption/SRT/CapCut text must keep `1795년`; the audio text may use `천칠백구십오년`.
- If CapCut wraps a caption into too many lines, fix the generated line breaks/text box width before delivery so the UI already opens as 2 lines without manual resizing.
- Top title comes from `title.txt`; never use `shorts-01.txt` or body script as the top title.
- FFmpeg fallback renders must follow the same 0shrt CapCut text look: yellow Anemone/Cafe24 Ohsquare top title, bottom-only white Anemone/Cafe24 Ohsquare captions inside a black panel with a cyan border. Do not use legacy Eunhasu/Pretendard white-only ASS styles for 0shrt history Shorts.
- Official GPT Image2 is mandatory for generated scenes. Do not use built-in image generation, placeholder art, or rough local image substitutes.
- For emotional CapCut effects, use the local 0shrt emotion pack and reference file listed in `CapCut Emotion Effects`.

## Working TODO

Whenever this skill is used, show and maintain a visible TODO list with `update_plan` before doing substantive work. This is mandatory even for script-only work, because the user must be able to see which gate is running and what is blocked.

Maintain this checklist during production:

```text
[ ] Source/facts saved
[ ] Script writer cut gate passed
[ ] Final script saved
[ ] Upload title/description/tags saved
[ ] Official GPT Image2 scenes generated
[ ] Image2 manifest synced
[ ] Body-only Chunsik dialect TTS/SRT built
[ ] CapCut local project/draft created and registered in the CapCut project list
[ ] BGM/audio tracks verified in draft
[ ] CapCut project name/path reported
[ ] 0shrt harness passed
[ ] Visual snapshot eye-check completed
```

Do not mark items complete before running the relevant command or eye-check.

For script-mode-only work, use this shorter TODO:

```text
[ ] Domestic/reference source check
[ ] Named person / yadam / tradition basis classified
[ ] 3 script angles drafted
[ ] Script writer cut gate applied
[ ] Final script saved only after PASS/KEEP
```

Update TODO statuses as each stage changes. Do not wait until the end to report progress.

## Episode Contract

Create one folder per Short:

```text
${env:UTUBE_ROOT}\0shrt\history-chunsik\episodes\{YYMMDD-topic}
```

Core files:

```text
00_source_analysis_gemini.md
01_analysis_digest.md
02_script_candidates.md
03_final_script.txt
04_video_plan.md
05_approval_gate.md
06_image2_prompts.md
07_youtube_upload.txt
08_audio_plan.json
title.txt
shorts-01.txt
```

`07_youtube_upload.txt` is the source for title, description, tags, and fixed comment.

Upload tags must be comma-separated for copy/paste into YouTube. Print and save tags as one line like:

```text
tag1, tag2, tag3,
```

Do not output upload tags as a space-only hashtag line. Put a comma after every tag, including the final tag.

## YouTube Upload Text

For 역사춘/Korean history uploads, the `내용`/description section in `07_youtube_upload.txt` must use this structure:

```text
이 영상은 {인물/사건}을 다룬 한국사 콘텐츠입니다.

핵심 질문:
{왜 이 사건이 벌어졌는가?}

핵심 답:
{권력/배신/기록/형벌/궁중 갈등 관점에서 한 줄 정리}

사실축:
- 기록으로 확인되는 내용

해석축:
- 해석이 갈릴 수 있는 부분

연출축:
- 이해를 돕기 위해 재구성한 대사와 장면
```

Fill `{인물/사건}` with the covered historical person or event. Fill the question and answer with episode-specific text, not generic placeholders. Keep `사실축`, `해석축`, and `연출축` separate so viewers can distinguish verified records, disputed interpretation, and dramatized reconstruction.

When the video project is complete, the final chat response must print the YouTube upload content so the user can check it immediately:

```text
제목
{final title}

내용
이 영상은 {인물/사건}을 다룬 한국사 콘텐츠입니다.

핵심 질문:
{왜 이 사건이 벌어졌는가?}

핵심 답:
{권력/배신/기록/형벌/궁중 갈등 관점에서 한 줄 정리}

사실축:
- 기록으로 확인되는 내용

해석축:
- 해석이 갈릴 수 있는 부분

연출축:
- 이해를 돕기 위해 재구성한 대사와 장면
```

Do not finish a completed CapCut/video-project turn with only the project path. Include the upload title and description in the chat.

## Script And Voice

- Tone: Chunsik/Chungcheong dialect by default. Prefer natural endings such as `~슈`, `~쥬`, `~유`, `~당께유`, `~헌당께유`, or `~허네유`.
- Use only verified facts. Do not invent extra historical claims.
- `03_final_script.txt` and `shorts-01.txt` must contain the final body script only.
- Do not include fixed Chunsik intro voice such as `춘식이여유. 별일 없쥬?`.
- Do not include fixed outro voice such as `오늘 말씀드린 거...`, `구독과 좋아유...`.
- Use `py -3 ...\0shrt\production\make_chunsik_capcut_package.py EP --no-intro-outro`.

The generated file is still named `audio/full_with_outro.mp3` for pipeline compatibility, but its content must be body-only Chunsik dialect audio.

## Supertone Model Default

- Supertone 음성 API를 사용할 때 기본 우선 모델은 Sona Speech 2 `sona_speech_2`이다.
- Supertonic 3 `sona_speech_2t`는 사용자가 명시적으로 Supertonic 3를 요구할 때만 쓴다.
- 구버전 `supertonic_api_1`은 사용자가 명시적으로 `supertonic1` 또는 `Supertonic API 1`을 요구할 때만 쓴다.
- Supertone API 호출 후에는 남은 `credit_balance`를 보고하고, API 키는 절대 출력하지 않는다.

## Script Mode Story Engine

The default story engine is an unexpected person, not the obvious king, famous general, or textbook battle summary.

Before choosing a script angle, check domestic history references first. Prefer:

```text
한국민족문화대백과사전
우리역사넷 / 국사편찬위원회
한국사데이터베이스
```

Use these source URLs as the default research entry points before considering a custom MCP server:

```text
한국민족문화대백과사전: https://encykorea.aks.ac.kr
우리역사넷: https://contents.history.go.kr
한국사데이터베이스: https://db.history.go.kr
공공데이터포털: https://www.data.go.kr
DBpia OpenAPI: https://api.dbpia.co.kr/openApi/about/guide.do
```

Default source workflow:

```text
1. Search the topic/person on 한국민족문화대백과사전.
2. Cross-check with 우리역사넷 or 한국사데이터베이스.
3. Extract named people, documents, punishment, betrayal, dispute, and later anecdotes.
4. Classify each story basis as 기록 / 야담 / 설화 / 후대 일화 / 연출 재구성.
5. If a source cannot be linked or named, mark it weak and do not use it as 사실축.
```

If the `history-research` MCP server is available, use it before generic web search:

```text
1. source_status
2. fetch_history_page or encykorea_search
3. extract_named_people
4. aks_people_search for candidate real named people
```

If the MCP is not available or API keys are missing, fall back to the source URLs above and record the missing MCP/key status in the source memo.

Record the checked source names and URLs in `00_source_analysis_gemini.md` or `01_analysis_digest.md`.

## Reader Zero Mode

Always write history scripts for a viewer who knows nothing about the person, title, battle, office, or incident. The user should not have to ask "who is that?" after the first lines.

Before any poetic hook, metaphor, or twist, make the basic situation understandable:

```text
1. Who is this person? Give a one-line identity.
2. Why does this person matter? Give one concrete status/action.
3. What danger or conflict is happening?
4. Whose action changes the outcome?
```

Hard rule:

- Do not open with an unexplained name, battle, office, faction, document, poem, or quote.
- Do not open with a metaphor that only makes sense after the viewer already knows the event.
- If the first 10 seconds do not explain the minimum context, rewrite before saving.
- When introducing a historical office/title, translate it into plain meaning on first use. Example: `익대공신 1등, 쉽게 말해 왕을 지킨 최고 공신`.
- Every final script must pass the "middle-school stranger test": a viewer with zero prior knowledge can answer who, why important, what conflict, and what changed.

Use this shape when the topic includes an unfamiliar person:

```text
조선에 {나이/신분/직책} {핵심 인물}이 있었심더.
이 사람은 {왜 중요한지 한 줄}.
그런데 {위기/죽음/배신/처벌}은 {전쟁터/궁궐/문서/고변}에서 시작됐심더.
그 일을 움직인 사람이 {두 번째 인물}이었심더.
```

`05_approval_gate.md` must include these Reader Zero fields inside `SCRIPT_WRITER_GATE`:

```text
reader_zero_mode:
context_bootstrap:
unexplained_name_check:
first_10_seconds_clear:
```

Before writing the final script, choose the episode's entry character from one of these angles:

- an overlooked witness
- a court lady, eunuch, servant, messenger, clerk, soldier, prisoner, exile, widow, merchant, monk, doctor, interpreter, or low-ranking official
- a person who had little official power but saw the truth first
- a person whose small action exposed the larger power conflict
- a person punished, erased, used, or abandoned by the main historical figures

Named-person rule:

- The default entry character should be a source-backed real named person.
- Anonymous roles such as "a soldier", "a clerk", "a translator", or "a court lady" are allowed only as dramatized scene framing, not as the factual core of the episode.
- If no useful real named secondary person exists, check whether a minimally credible transmitted story, yadam, folktale, local tradition, or later anecdote exists.
- A yadam/tradition angle can be used only if the script clearly says it is "전해지는 이야기", "야담에 가까운 이야기", "후대에 덧붙은 이야기", or "기록과는 구분되는 이야기".
- If neither a source-backed named person nor a usable transmitted story exists, do not force the topic. Move to another historical incident with a stronger angle.
- If using an anonymous composite role anyway, mark it clearly under `연출축` and do not present it as a recorded person.

Do not open with the obvious subject unless the user explicitly asks for a textbook-style explainer. For example:

```text
Weak: 을지문덕은 살수대첩에서 수나라를 물리쳤다.
Better: 수나라 병사 하나는 강을 건너기 전부터 이미 알고 있었다. 이 전쟁은 끝났다는 걸.

Weak: 장희빈은 숙종 시대의 후궁이었다.
Better: 궁녀 하나가 밤마다 같은 약그릇을 들고 지나갔다. 며칠 뒤, 중전의 이름이 사라졌다.

Weak: 세조는 조카 단종의 왕위를 빼앗았다.
Better: 한 신하는 이름을 적는 순간 손을 멈췄다. 그 명단에 살아남을 사람이 없었기 때문이다.
```

Script mode must produce at least three angles before finalizing:

```text
A안: 의외의 목격자 관점
B안: 기록/문서/명단 관점
C안: 처벌/배신/버려진 사람 관점
```

Gate the script before production. Reject and rewrite if it sounds like a schoolbook summary, a famous-person biography, or a generic victory explanation.

## Script Writer Cut System

Before saving `03_final_script.txt`, run a script-writer cut gate. This gate exists to kill weak, obvious, textbook-style drafts before production.

The script-writer cut gate includes the YouTube Policy Gate from `00script-writer/references/youtube-policy-gate.md` and the saved random 5-persona visible parallel retention/readability gate from `00script-writer/references/parallel-persona-gate.md`. Before `03_final_script.txt` is saved, show the user the policy verdict, persona progress board, and summary. A script cannot be marked final if the policy gate returns `BLOCK`, `FAIL`, or unresolved `REWRITE_REQUIRED`, or if the persona gate returns `REWRITE_REQUIRED` or `REPLAN`.

Harness enforcement is mandatory. `validate_episode_harness.py` and `check_script_contract.py` must fail unless `05_approval_gate.md` contains `SCRIPT_WRITER_GATE`, `youtube_policy_gate_complete`, `policy_risk_tier`, `platform_safety_verdict`, `status: PASS`, and `material_decision: KEEP`.

Use three statuses:

```text
CUT: throw away this angle
REWRITE: keep the seed but rewrite the hook/POV/conflict
PASS: allowed to become the final script
```

Cut immediately if any of these are true:

- The entry person is anonymous while the user requested real-history/person-driven material.
- The entry person or story cannot be tied to either a domestic history reference, primary-source summary, yadam, folktale, local tradition, or clearly labeled later anecdote.
- The whole story is predictable, familiar, and obvious from the first setup.
- The draft can be summarized as "famous person did famous thing."
- The first 3 seconds have no unexpected person, object, document, witness, punishment, or danger.
- The middle has no reversal, pressure, betrayal, mistake, document, order, or consequence.
- The ending only says "so this was a great victory" or "that is why this person is famous."
- The story explains history but does not make the viewer wonder what happens next.
- The script sounds like a school textbook, encyclopedia paragraph, or generic YouTube history summary.

Every candidate in `02_script_candidates.md` must include a cut memo:

```text
ANGLE:
ENTRY PERSON:
HOOK:
CONFLICT:
REVERSAL:
ENDING STING:
CUT MEMO: CUT / REWRITE / PASS - reason
```

`05_approval_gate.md` must include the final gate result:

```text
SCRIPT_WRITER_GATE:
obvious_version_cut:
reader_zero_mode:
context_bootstrap:
unexplained_name_check:
first_10_seconds_clear:
entry_person:
entry_person_source:
story_basis: 기록 / 야담 / 설화 / 후대 일화 / 연출 재구성
anonymous_or_real_named:
first_3_seconds:
mid_reversal:
ending_sting:
fact_risk:
youtube_policy_gate_complete: true
policy_risk_tier: LOW / MEDIUM / HIGH
platform_safety_verdict: PASS
monetization_verdict: GREEN / LIMITED_ADS_RISK / NO_ADS_RISK
edsa_context: NONE / WEAK / CLEAR_IN_SCRIPT / CLEAR_IN_AUDIO_VIDEO
policy_hard_blocks: 없음
policy_required_rewrites: 없음
material_decision: KEEP / MOVE_TOPIC
status: PASS / REWRITE
```

Do not continue to Image2, TTS, or CapCut unless `status: PASS`, `material_decision: KEEP`, `youtube_policy_gate_complete: true`, `platform_safety_verdict: PASS`, and `policy_risk_tier` is not `BLOCK`. If the best version is only `REWRITE`, rewrite and re-gate. If there is no source-backed named-person angle and no usable transmitted story/yadam/tradition, set `material_decision: MOVE_TOPIC` and pick a different incident. Never let a weak or policy-unsafe script pass just because assets are ready.

When using yadam, folktale, tradition, or later anecdote:

- Mention the status in the narration at least once.
- Put it under `해석축` or `연출축` in `07_youtube_upload.txt`, not under `사실축`.
- Do not phrase it as confirmed fact.
- Prefer lines like `기록으로 딱 잘라 확인되진 않지만, 이런 이야기가 전해져유.` or `이건 정사라기보다 후대에 붙은 이야기로 봐야 해유.`

## Image2 Rules

Use official GPT Image2 only. Do not use local placeholder images or built-in image generation.

Preferred route:

```powershell
node ${env:UTUBE_ROOT}\0shrt\production\chatgpt_cdp_image2_continue.mjs EP scene_01 ... scene_07
py -3 ${env:UTUBE_ROOT}\tools\chatgpt_image2_manifest.py EP --sync-video-assets
```

Required image layout:

- Shorts source images are square, at least 1024x1024.
- Default scene count is 7.
- Files live at `images/image2/scene_01.png` through `scene_07.png`.
- Also sync to `images/capcut/shorts` and `video/images/image2`.
- Generated images normally contain no readable text.
- Exception: if the user explicitly asks for in-image text, the prompt must require exact text and the result must be eye-checked.

For memorial tablets or named objects:

- Put names in the generated image, not as a rough post-edit, when the user requests image-native text.
- For vertical Shorts crops, all important named objects must fit inside the central 9:16 safe area.
- Eye-check spelling, order, placement, and crop visibility before CapCut.
- If GPT misspells Korean, regenerate the scene.

Sakyuksin tablet order is locked when used:

```text
박팽년 / 성삼문 / 이개 / 하위지 / 유성원 / 유응부
```

## Audio And BGM

0쇼츠 audio must be body-only standard Korean voice plus BGM in CapCut. No fixed intro/outro voice and no typewriter SFX.

Use:

```powershell
py -3 ${env:UTUBE_ROOT}\0shrt\production\make_chunsik_capcut_package.py EP --no-intro-outro
```

Locked BGM:

```text
source: random valid music file from ${env:UTUBE_ROOT}\video\배경음
start: 0.0s
volume: 0.05623413251903491
CapCut UI volume: -25.0 dB
track name: shorts_background_music_joseon_history
```

Typewriter SFX is not part of the 0쇼츠 profile. Do not add `타자음3초` or `shorts_typewriter_sfx`.

Voice audio and BGM materials must use a CapCut-visible audio format (`type: extract_music`) so they show in the media bin and timeline.

The old BGM volume `0.31103286147117615` is obsolete for 0쇼츠. If an existing draft uses it, lower it to `0.05623413251903491` / `-25.0 dB`.

## CapCut Draft

N8N harness mode is mandatory for CapCut. Do not create CapCut projects by hand-written JSON, ad hoc Python draft builders, profile-shell MP4s, placeholder card drafts, or direct edits to `root_meta_info.json`.

Create/register local drafts only with:

```powershell
py -3 ${env:UTUBE_ROOT}\tools\n8n_capcut_draft.py --episode-dir EP --mode shorts --audio EP\audio\full_with_outro.mp3 --srt EP\audio\main_capcut.srt --target-name DRAFT_NAME --force-new-draft
```

Required production order:

```powershell
py -3 ${env:UTUBE_ROOT}\0shrt\production\validate_episode_harness.py EP --stage imagegen
py -3 ${env:UTUBE_ROOT}\0shrt\production\validate_episode_harness.py EP --stage audio
$capcutImages = Join-Path "EP" "images\capcut\shorts"
New-Item -ItemType Directory -Force -Path $capcutImages | Out-Null
Get-ChildItem "EP\images\image2" -Filter "scene_*.png" | Sort-Object Name | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $capcutImages $_.Name) -Force }
py -3 ${env:UTUBE_ROOT}\tools\n8n_capcut_draft.py --episode-dir EP --mode shorts --audio EP\audio\full_with_outro.mp3 --srt EP\audio\main_capcut.srt --target-name DRAFT_NAME --force-new-draft
py -3 ${env:UTUBE_ROOT}\0shrt\production\validate_episode_harness.py EP --stage capcut
py -3 ${env:UTUBE_ROOT}\tools\capcut_visual_snapshot.py --episode-dir EP --mode shorts
```

If `imagegen` or `audio` harness fails because Image2 scenes, TTS, SRT, BGM, or synced assets are missing, stop. Do not make a placeholder CapCut project.

`n8n_capcut_prepare.py` reads stills from `images/capcut/shorts`, not directly from `images/image2`. Treat the staging copy above as mandatory before `n8n_capcut_draft.py`; missing this folder is a hard setup error, not a reason to build a shell/profile project.

After N8N draft creation, inspect `video/capcut_draft_manifest.json` and `draft_content.json`.

CapCut work is not complete until it is a real local CapCut project, not just an episode profile JSON, preview MP4, or manifest. The draft must:

- Create a project folder under the active CapCut draft root, normally `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\DRAFT_NAME` on Windows.
- Register or update the draft in CapCut's project index (`root_meta_info.json`) so it appears in the CapCut home/project list after refresh or restart.
- Keep `video/capcut_draft_manifest.json` pointing to the exact `draft_dir`, `draft_content.json`, and `draft_name`.
- Be verified with JSON parsing plus `validate_episode_harness.py EP --stage capcut`.
- Be reported to the user with the exact CapCut project name and local path.

Reusable/test profile shells are not allowed in this production skill unless the user explicitly asks for a non-production test draft. Even then, label it as `TEST_ONLY`, do not call it a profile, and do not present it as a finished CapCut project.

Required audio tracks in the draft:

```text
voice_shorts_audio
shorts_background_music_joseon_history
```

Each track must have visible segments. If CapCut UI does not show audio in the timeline, treat the draft as failed even if files appear in the media bin.

## Text Layout Rules

Top title, captions, and overlays are separate surfaces:

- Top title: short hook only, normally 8-16 Korean-visible characters. It stays near the top and never contains body narration.
- Body captions: bottom only. Use explicit line breaks or text-box width so they render as max 2 lines in CapCut.
- Middle overlay: disabled for 0쇼츠 by default. Do not create `emo_overlay_purple_*` tracks.
- Ending thanks message, if requested, is still a bottom caption unless the user explicitly asks for an end card.
- Before final delivery, inspect visual snapshot or CapCut UI and confirm no caption appears at the top/middle and no caption exceeds 2 lines.

## CapCut Emotion Effects

Effect use is part of the default 0shrt profile. When a Short has a clear emotion transition, actively use the local effect pack instead of leaving the draft visually flat. Keep the hard 0shrt rules: no typewriter SFX, no purple middle overlay, bottom captions only, max 2 caption lines, and BGM at `0.05623413251903491` / `-25.0 dB`.

Read `references/capcut_emotion_effects.md` before building or fixing effects. Use this beat map unless the user gives a stronger direction:

```text
opening shock: speed/burst lines + boom SFX
pressure or bad omen: vignette/cloud/dark wash
injustice or sadness: rain/blue wash + rain ambience
reversal: scattered wind overlays + whoosh SFX
truth or evidence: lightning/burst flash + thunder/lock SFX
verdict or punishment: Joseon verdict stamp + stamp/boom SFX
relief or ending: gold wash/chime or black lesson card
```

Wind is never a single centered sticker. Build wind as 8-12 separate overlay segments/tracks using `visual/03_VIS_바람휘리릭.mov` or the black-background fallback. Stagger starts, scatter positions, vary scale, rotation, and alpha so it looks hand-placed and dramatic.

For debug or user testing, create grouped CapCut test profiles:

```text
0SHRT_EFFECT_TEST_01_VISUAL_MOOD
0SHRT_EFFECT_TEST_02_SFX_ONLY
0SHRT_EFFECT_TEST_03_STAMP_MODERN_TOP15
0SHRT_EFFECT_TEST_04_STAMP_MODERN_ALL50
0SHRT_EFFECT_TEST_05_STAMP_JOSEON_ALL20
0SHRT_EFFECT_TEST_06_FULL_COMBO_EMOTION
0SHRT_EFFECT_TEST_07_WIND_SCATTER_RANDOM
```

When the user asks for CapCut image effects, manga effects, flash, grayscale, tilt, shake, emotional scene effects, the 감정선 효과 시스템, fire text, neon text, or repeated laugh/pop text, read `references/capcut_emotion_effects.md` first.

Implementation priority:

1. Use native JSON transform/keyframes for zoom, pan, rotation/tilt, shake, opacity, freeze-frame timing, and title/caption motion.
2. Use generated overlay assets for flash, speed lines, halftone, vignette, black cards, red aura, gold light, stamp marks, manga marks, sweat drops, and vote cards.
3. Use CapCut sample-copy only for real CapCut effects/transitions/filters already present in a user-created free sample draft. Do not invent unknown effect material structures.
4. For grayscale or color wash, prefer a preprocessed duplicate image/video asset unless a verified CapCut adjust/filter sample exists.
5. Strong effects are allowed only at emotion change points; do not stack more than one strong visual effect in the same beat unless the user explicitly asks.

Current local effect pack:

```text
${env:UTUBE_ROOT}\0shrt\assets\emotion_pack
${env:UTUBE_ROOT}\0shrt\assets\effect_bank
```

Core files to use:

```text
emotion_symbol_presets_40.md
stamp_result_presets.md
stamp_preview_contact_sheet.png
text_effect_presets.md
text_effect_presets.json
visual/01_VIS_비오는오버레이.mp4
visual/02_VIS_번개플래시.mp4
visual/02B_VIS_노란버스트집중선.mp4
visual/03_VIS_바람휘리릭.mov
visual/03B_VIS_바람휘리릭_검은배경.mp4
visual/04_VIS_먹구름.mp4
visual/stamps/modern/*.png
visual/stamps/modern_top15/*.png
visual/stamps/joseon/*.png
visual/stamps/joseon_top5/*.png
sfx/01_SFX_빗소리.mp3
sfx/02_SFX_바람휘리릭.mp3
sfx/03_SFX_천둥쾅.mp3
sfx/04_SFX_충격음_boom.mp3
sfx/05_SFX_도장_stamp.mp3
sfx/06_SFX_사이다_chime.mp3
```

Reusable effect-bank overlays:

```text
assets/effect_bank/video/fire/BANK_FIRE_OVERLAY_BLACK.mp4
assets/effect_bank/video/fire/BANK_FIRE_TEXT_SAMPLE_MUSCLE_PAIN_BLACK.mp4
assets/effect_bank/video/laugh/BANK_LAUGH_RING_KKK_GREEN.mp4
assets/effect_bank/video/laugh/BANK_LAUGH_POP_KKK_GREEN.mp4
assets/effect_bank/video/text/BANK_TEXT_POP_TIRED_GREEN.mp4
```

Effect implementation rules:

- Effects must be dramatic motion assets, not static stickers that merely appear.
- Each emotion symbol needs entrance motion, impact motion, and exit motion.
- Use MP4 overlays with Screen/Lighten or opacity 20-40%.
- Use `03_VIS_바람휘리릭.mov` for thick blue wind swirl; if alpha fails in CapCut, use `03B_VIS_바람휘리릭_검은배경.mp4`.
- Use `02B_VIS_노란버스트집중선.mp4` for comic evidence/reveal bursts.
- Stamp text must be a result/verdict, not an emotion label.
- Stamp animation is `150% -> 95% -> 105% -> 100%` over `0.15s`, synced to `sfx/05_SFX_도장_stamp.mp3` or `sfx/04_SFX_충격음_boom.mp3`.
- Modern stamp folders contain 50 full-result stamps and a TOP15 shortcut folder.
- Joseon stamp folders contain 20 history stamps and a TOP5 shortcut folder: `파직`, `유배`, `사약`, `폐위`, `부관참시`.

## Harness And Visual Check

Run gates after each production stage:

```powershell
py -3 ${env:UTUBE_ROOT}\0shrt\production\validate_episode_harness.py EP --stage audio
py -3 ${env:UTUBE_ROOT}\0shrt\production\validate_episode_harness.py EP --stage imagegen
py -3 ${env:UTUBE_ROOT}\0shrt\production\validate_episode_harness.py EP --stage capcut
py -3 ${env:UTUBE_ROOT}\tools\capcut_visual_snapshot.py --episode-dir EP --mode shorts
```

Do not continue past a failed stage. Report the failing line, fix it, and rerun.

Visual snapshot eye-check is mandatory. Check:

- Top title is short and not body text.
- Captions are bottom only, max 2 lines, and each line is max 10 Korean-visible characters for CapCut drafts.
- No middle purple overlay appears in 0쇼츠.
- Important objects and text are not cropped.
- In-image Korean text is spelled correctly.
- Audio track expectations are reflected in `draft_content.json`.
- BGM is randomly selected from valid files in `video\배경음`, starts at `0.0s`, and volume is `0.05623413251903491` / `-25.0 dB`.

## Known Failure Patterns

- `shorts-01.txt` used as top title: fix title inference so `title.txt` wins.
- Blank memorial tablets when names are required: regenerate with exact text instructions.
- Horizontal post-edited names on vertical tablets: regenerate image-native vertical text.
- BGM appears in media bin but not timeline: use `extract_music` material/segment format.
- BGM volume `0.31103286147117615`: too loud for current 0쇼츠; use `0.05623413251903491` / `-25.0 dB`.
- Fixed single BGM reuse: wrong for this 0쇼츠 profile; choose a valid random BGM from `video\배경음`.
- `타자음3초` or `shorts_typewriter_sfx`: wrong for this 0쇼츠 profile; remove it.
- `emo_overlay_purple_*`: wrong for this 0쇼츠 profile; remove it.
- Captions showing as 3-5 lines: wrong; rewrite/split captions or set text-box width so CapCut shows max 2 lines.
- Captions placed above the image or in the middle: wrong; body captions must stay at the bottom.
- Captions showing spoken-number text such as `천칠백구십오년`, `십사세기`, or similar TTS pronunciation strings: wrong; display captions must show `1795년`, `14세기`, etc.
- Fixed Chunsik intro/outro voice or Chunsik dialect captions: wrong for current 0쇼츠 profile; build with `--no-intro-outro` and write standard Korean narration.

## Shared Production Console Requirement

This dedicated Shorts skill must also obey the shared `22utube-production-agent` production console and progress-board rules.

- Use `phaseMap: 0shrt_original_production`; do not use the 11short `analysis/assets/capcut` checklist as this skill's gate.
- n8n board phases are script, Image2 prompts/images, TTS/SRT, CapCut/render, report. Harness phases are script, imagegen, audio, capcut, final/all plus ffprobe/frame QA when rendering.
- Required evidence is 0shrt-style production evidence: final script, `asset_manifest.json`, `image2_manifest.json`, `images/image2/scene_*.png`, `audio/main_capcut.srt`, `audio/full_with_outro.mp3`, `video/capcut_draft_manifest.json`, `validation_report.json`, `evidence_pack.json`, and `final_report.md` when those final files are produced.
- Every YouTube production status report must start with the compact `[ 진행판 ]` board: n8n execution, harness validation, current blocker, and next action.
- The visible TODO/status report must include the full `A. n8n 실행` / `B. 하네스 검증` board from `22utube-production-agent`; do not replace it with prose-only status.
- Keep Shorts target locked as `target: youtube_shorts` and `instagram_status: not_requested` unless the user explicitly changes the target.
- Build the YouTube Shorts master first unless the user explicitly says the current deliverable is Instagram/Reels. If the user says `인스타`, `인스타용`, `인스타로 만들어`, or `릴스`, switch to the fixed Instagram layout instead of the normal YouTube layout.
- Instagram/Reels requests must read and follow `$env:UTUBE_ROOT\11short\INSTAGRAM_LAYOUT_CONTRACT.md`. Use the local CapCut reference draft `$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\인스타용` when available; keep the top-left circular cat video and bottom-right 3-animal image fixed; copy the saved top/middle/bottom text style and position values from that reference. Mark the standard YouTube/0shrt caption harness as `N/A - instagram custom layout` for the Instagram draft and still run draft/ffprobe/frame QA.
- Before user review and harness PASS, file names and reports must say `REVIEW` or `DRAFT`, never `FINAL`.
- Use `$env:UTUBE_ROOT\tools\production_console` for scene-level review/editing.
- Save scene edits inside the current episode/work folder as `production_console.json`; do not create a new production root.
- If the user splits a cut or image, update `production_console.json` first, then regenerate or relink audio, SRT, prompt, image, and layout assets from that updated scene plan.
- Update `production_console.json` at every major stage: script, audio, Image2, CapCut, render, ffprobe, frame QA, and final gate. If `http://127.0.0.1:47831/api/episode` is available, use it to load/save the episode status.
- If the work is local and n8n was not invoked, mark n8n as `WAIT` with `local run; n8n webhook not invoked`. If Compound has no linked log, mark it as `WAIT - compound log not linked`.
- The console summary must include title, content summary, tags, total duration, voice model/version, voice_id by role, target, `instagram_status`, output video path, n8n state, harness state, Compound state, blocker, and next action.
