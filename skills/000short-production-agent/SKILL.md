---
name: 000short-production-agent
description: Dedicated mandatory workflow for 11utube/11short YouTube Shorts remake work. Use when the user mentions 11short, 11쇼츠, 쇼츠공장, 쇼츠 리메이크, YouTube Shorts source analysis, Gemini shorts JSON, 티키타카 대본, 티키타카 시작, 쇼츠학개론, 마라하기 공식, 한계선, 돈통/에셋, 결, 가단야, 우라까이, 일치율 0%, 벤치영상, 채널기획, channel-family labels such as 한짜/국뽕/해짜/드짜/영짜/랭킹/유머, top/middle text overlays, 중단 중심 대본, quoted/bracket/plain middle captions, 11short CapCut drafts, visible local CapCut project registration, OCR overlays, original source audio tracks, explicitly requested Supertone/TTS voices for shorts, shorts_remake_harness.py, Mac mini 11short production, or any work under 11utube/11short.
---

# 11short Production Agent

This skill is the enforced workflow for `11utube/11short`. It overrides the general `22utube-production-agent` for all 11short remake tasks.

## Mandatory arajun Style Memory Gate - 2026-06-22

Before creating or changing any 11short script, SRT, layout, CapCut text, TTS
copy, or final report, load the local style memory contract:

```text
$env:UTUBE_ROOT\11short\style_bank\STYLE_MEMORY_CONTRACT.md
$env:UTUBE_ROOT\11short\style_bank\arajun_shorts_voice_profile.md
$env:UTUBE_ROOT\11short\style_bank\final_script_corpus_index.json
```

Select 3-5 recent genre-matched final scripts from
`final_script_corpus_index.json` and use them as the tone/rhythm reference. Do
not copy their wording; copy only the user's established Shorts cadence:
short reaction beats, natural Korean middle captions, parenthesized situation
captions, verified-speech restraint, and brief TTS when the source mix calls for
it. Source video evidence, OCR/STT/direct frames, policy safety, and the user's
latest instruction still outrank style memory.

Every generated `status.json`, handoff manifest, or final report must record:

```json
"style_bank_loaded": true,
"style_contract": "STYLE_MEMORY_CONTRACT.md",
"style_reference_paths": []
```

If the style files cannot be read or no suitable reference can be selected, set
status `WAIT_STYLE_REFERENCE` and do not claim `SCRIPT_LOCK`, `FINAL_LOCK`,
`upload_ready`, or production `PASS`.

## Factory Contract v5.0 - Source-Verified Validation - 2026-06-13

This is the current highest-priority contract for the user's Shorts factory.
It overrides older sections in this file, older episode folders, older harness
wording, and older chat instructions that treat Gemini/VLM/GPT output as source
truth or treat `final_report` wording as production PASS.

Read these split contract files before production:

```text
01_WORK_ORDER_TEMPLATE.md
02_PIPELINE_RULES.md
03_CAPCUT_LAYOUT_CONTRACT.md
04_HARNESS_REQUIREMENTS.md
05_CODEX_EXECUTION_PROMPT.md
06_CAPCUT_CUT_ASSEMBLY_CONTRACT.md
references/shorts-academy.md when Tikitaka/Shorts Academy remake strategy is in scope
schemas/
adapters/capcut_draft_normalizer.md
```

Current authority chain:

```text
input/video_url.txt
-> input/analysis_hint_raw.txt
-> source/source.mp4
-> source/ffprobe_report.json
-> evidence/scene_segments.json
-> evidence/whisper_segments.json
-> evidence/ocr_segments.json
-> evidence/audio_vad_segments.json
-> evidence/source_evidence.json
-> evidence/target_phrase_check.json when a source phrase matters
-> evidence/crosscheck_report.json
-> decisions/segment_decision_table.json
-> decisions/shorts_academy_gate.json when Tikitaka/Shorts Academy remake strategy applies
-> decisions/capcut_layout_plan.json
-> capcut/normalized_draft.json
-> reports/validation_report.json
-> reports/evidence_pack.json
-> reports/final_report.md
```

Hard rules:

- Gemini JSON, VLM analysis, GPT output, and user rough analysis are
  `analysis_hint` only. They are never source evidence.
- Source truth starts at `source/source.mp4`.
- PASS is granted only by file-based validation, especially
  `reports/validation_report.json` and draft/normalized-draft checks.
- `segment_decision_table.json` is required before CapCut production.
- If a phrase such as `테슬라야`, `존중해`, or any user-mentioned speech matters,
  `target_phrase_check.json` is required. Timestamp-free phrases are not
  preserved source speech.
- PaddleOCR is the primary OCR route. EasyOCR fallback is allowed only when the
  fallback is recorded. Do not claim PaddleOCR ran if it did not.
- Current visible script is still `상단 + timed 중단`; bottom text is forbidden.
- TTS, when requested, must be split by segment. A single full-body voiceover is
  recovery input only, not a valid final production layout.
- Spoken/source-emotion scenes must preserve original audio unless the user
  explicitly approves muting or replacement.
- `upload_ready=YES` requires validation PASS plus user approval and
  source/remake-rights risk confirmation. Validation PASS alone is not upload
  readiness.
- If a job enters from `00-tikitaka` or uses Shorts Academy language such as
  쇼츠학개론, 마라하기 공식, 한계선, 돈통/에셋, 결, 가단야, 우라까이,
  일치율 0%, 벤치영상, 채널기획, or channel-family labels such as
  한짜/국뽕/해짜/드짜/영짜/랭킹/유머/군림보, read `references/shorts-academy.md`
  and record `shorts_academy_gate=PASS|N/A` with evidence before CapCut or
  final PASS. Missing or incomplete gate evidence is `WAIT` or
  `REWRITE_REQUIRED`, not PASS.

## Mandatory Channel/Template Proposal Gate - 2026-06-25

Before source download, watch/direct-frame analysis, SRT/layout, TTS, CapCut
draft creation, or final report for any 11short job, resolve the upload channel
and CapCut template. This is not a late CapCut choice; it is the first
production routing decision.

Routing authority:

```text
$env:UTUBE_ROOT\tools\youtube_channel_router\channel_routing_rules.json
```

Use this order:

1. If `00-tikitaka` handoff files, `status.json`, or
   `production_gate_contract.json` already contain `recommended_upload_channel`
   and `recommended_capcut_template`, verify them against source evidence and
   keep them unless they contradict the source or the user overrides them.
2. Otherwise read `channel_routing_rules.json` and infer from source title,
   Gemini/raw analysis, watch evidence, comments, and user prompt.
3. If the routing file is missing, use the fallback defaults below.
4. A user-explicit channel/template override wins. Record
   `routing_source=user_override` and `user_override=true`.

Fallback defaults:

- `우니웃니` -> `블랙기본`: shopping, 생활꿀팁, 살림템, 상품실험, 신비템,
  쿠팡파트너스. Generic `정보/지식` only routes here when it is about a
  product, tool, household problem, or product test.
- `난감동란` -> `인스타템플릿`: 웃긴 장면, 해외유머, 웃긴 해짜, 예짜, 예능,
  웃긴 랭킹, 몸개그, challenge/fail/comedy/reversal clips.
- `별별지구인g9` -> `인스타템플릿`: 인물 랭킹, 정보 위주, 지식정보, 지식,
  정보, brand/craft/world/person/object backstory.

Required visible start-board fields:

```text
- 추천 업로드 채널:
- 추천 템플릿:
- 주제/카테고리 판정:
- 추천 이유:
- 제외/보류 채널:
- 라우팅 확신도:
```

Required file/report fields whenever `status.json`,
`production_gate_contract.json`, `analysis.json`, or a final report is written:

```json
{
  "recommended_upload_channel": "",
  "recommended_capcut_template": "",
  "detected_topic": "",
  "detected_category": "",
  "routing_reason": "",
  "routing_confidence": "high|medium|low",
  "routing_source": "channel_routing_rules.json|tikitaka_handoff|fallback|user_override",
  "user_override": false,
  "excluded_channel_reason": ""
}
```

Template execution rule:

- `우니웃니` must use `블랙기본`.
- `난감동란` must use `인스타템플릿`.
- `별별지구인g9` must use `인스타템플릿`.
- If the selected local CapCut base/template is missing, set
  `template_status=WAIT_TEMPLATE_MISSING`, report the missing template name,
  and do not silently substitute another base. Use an alias such as
  `블랙템플릿` for `블랙기본` only after the operator explicitly maps that
  local template name.

## Meccha Chameleon / Hidden Picture Upload Description Rule

For game Shorts production, insert the required block only when all conditions
below are true:

1. The job is a game Shorts job.
2. The user prompt, source title, metadata, analysis, upload title, tags, or
   normalized topic identifies the game/source as Meccha/Mecha Chameleon or
   `메카 카멜레온`.
3. The same job context is specifically a hide-and-seek / hidden-picture /
   object-finding Meccha Chameleon video.

Do not insert this block for `숨은그림찾기` alone, generic hide-and-seek content,
generic game content, or a Meccha/Mecha Chameleon video that is not in the
hide-and-seek / hidden-picture lane. If the scope is uncertain, omit the block
until the source or user confirms that exact combination.

Condition keywords:

```text
meccha chameleon
mecha chameleon
Meccha Chameleon
Mecha Chameleon
메카 카멜레온
AND one of:
숨은그림찾기
숨은 그림 찾기
숨바꼭질
숨박꼭질
hide and seek
hidden picture
object finding
```

Insert this block inside `내용` before the final `출처:{source_url}` line. Do not
replace the source line, and do not shorten the player/source list. This rule
applies to `upload_text.md`, copy-ready final reports, handoff packages, and
any YouTube Shorts upload-text response.

```text
메카 카멜레온의 황당한 순간, 웃긴 장면, 실패, 최고의 그림과 프로 아티스트

이 영상에는 메카 카멜레온의 실패 장면, 웃긴 순간, 최고의 그림과 프로 아티스트, 황당한 순간, 최고의 장소, 팁과 요령, 하이라이트 등 250가지가 담겨 있습니다! 이 메카 카멜레온 웃긴 순간 영상 제작에 많은 시간을 투자했으니, 재밌게 보셨다면 좋아요와 구독 부탁드립니다! :)

🎮 주요 플레이어: chuukooky: https://redarca.de/Lj3zS
aimsey: https://redarca.de/5jQXV
alcolive: https://redarca.de/SpBr8
dizzy: https://redarca.de/b6jX6
heyyouvideogame: https://redarca.de/WxPrK
rprx: https://redarca.de/QJtq0
nikkisia: https://redarca.de/7aCNO
northernlion: https://redarca.de/UPXqL
yukinasagi: https://redarca.de/kMYbj
miaiow: https://redarca.de/dmwFh
smajor: https://redarca.de/FxoD2
niekbeats: https://redarca.de/M2YFm
ellum: https://redarca.de/JBWFN
elasticdroid: https://redarca.de/Y2kNh
slackatk: https://redarca.de/N3I3p
gmart: https://redarca.de/JqENZ
squeex: https://redarca.de/OGMB6
impulsesv: https://redarca.de/ILPeM
criken: https://redarca.de/yBAfI
covent: https://redarca.de/BjwOp
jennybeartv: https://redarca.de/QXMu8
caseoh_: https://redarca.de/smBYn
Miaru: https://redarca.de/2JuM0
jennmcallister: https://redarca.de/ifctg
minky: https://redarca.de/pqW5T
bnans: https://redarca.de/6HVzY
wayneradiotv: https://redarca.de/1ytgC
flackblag: https://redarca.de/rLW9T
grian: https://redarca.de/I4vbK
ethannestor: https://redarca.de/rR7LX
theburntpeanut: https://redarca.de/adjsP
Blaggers: https://redarca.de/iH4qx
smii7y: https://redarca.de/r2moJ
cochard: https://redarca.de/9WhK4
sodapoppin: https://redarca.de/L0TcH
pearlescentmoon: https://redarca.de/Z7pp3
ludwig: https://redarca.de/5I8NY
bonsaibroz: https://redarca.de/wyndw
antonychenn: https://redarca.de/xY9rC
hakonoriginal: https://redarca.de/KDW5z
SodaGang6: https://redarca.de/GCFr5
geminitay: https://redarca.de/jKzvv
스키즐맨: https://redarca.de/svZd5
발키래: https://redarca.de/Tj8Yr
제리코: https://redarca.de/3TPm3
엑스초코바: https://redarca.de/RHvVN

© 귀하의 영상 삭제를 원하시면 takktwo@naver.com으로 이메일을 보내주세요.
```

## Shorts Academy Production Gate

This gate makes Tikitaka/Shorts Academy rules carry into the Shorts factory.
Run it before production gate, segment decisions, SRT/layout, render plan,
CapCut draft creation, harness, or final report when the job comes from
`00-tikitaka`, `00script-writer`, or user wording such as 쇼츠학개론, 마라하기
공식, 한계선, 돈통/에셋, 결, 가단야, 우라까이, 일치율 0%, 벤치영상,
채널기획, or channel-family labels such as 한짜/국뽕/해짜/드짜/영짜/랭킹/유머/군림보.

Production-side enforcement:

- Read `references/shorts-academy.md`; do not rely on memory of the lecture
  notes.
- Save the gate result in `decisions/shorts_academy_gate.json` and mirror the
  summary into `status.json`, `production_gate_contract.json`,
  `render_plan_pre_capcut.json`, or `capcut_timeline_manifest.json` whenever
  those files exist.
- Required fields are `shorts_academy_reference_applied`,
  `shorts_academy_gate`, `channel_ceiling_checked` or `ceiling_status`,
  `asset_bank_basis`, `channel_texture_basis`, `benchmark_message`,
  `source_region`, `emotion_intent`, `channel_family`, `content_mode`,
  `source_surface`, `composite_label`, `layer_mix_decision_required`,
  `caption_layer_mix` / `source_layer_mix`, `gadanya_check`, `similarity_break_plan`,
  `urakkai_required`, `same_flow_allowed`, and `flow_urakkai_plan`.
- `caption_layer_mix` / `source_layer_mix` must specify TTS density, verified quote density,
  parenthesized situation-caption density, source-audio priority, layer basis,
  and `do_not_invent_quotes=true`.
- Verified original/source dialogue must be used as much as possible in
  `source_speech_*` rows. Do not replace verified dialogue with invented
  Korean quotes; if the meaning needs compression, paraphrase it naturally and
  keep it marked as verified source speech.
- Added creative lines must go to plain TTS/narration or `(상황설명)/(감정설명)`
  captions only. Do not create new `"..."` 화자발언 unless the source actually
  says it or the user explicitly clears it.
- `군림보` must be treated as `source_surface=photo_tts_explainer`: photos or
  simple images plus continuous TTS explanation, not forced dialogue-heavy
  Tikitaka.
- `gadanya_check` must cover guideline, word rewrite, and 야부리/comment
  pressure before SCRIPT_LOCK or production PASS.
- Every applicable remake must set `urakkai_required=true` and
  `same_flow_allowed=false`. Same source flow with only changed words is
  `REWRITE_REQUIRED`, even when order remix is not possible.
- `flow_urakkai_plan` must show how the new hook entry, tension point,
  reaction timing, caption interpretation, cut emphasis, or payoff recovery
  differs from the source/benchmark flow.
- `similarity_break_plan` must show keyword rewrite in the script, audio/timing
  change when audio is used, and pixel/frame change through crop, speed, order,
  or cut design. SFX, BGM, transition effects, and decorative text effects are
  optional; absence of those effects must not fail the gate.
- `source_word_synonym_rewrite_status=PASS` is required: except for verified
  quotes, names, numbers, and unavoidable nouns, source/benchmark wording must
  be rewritten with different Korean words, synonyms, sentence order, and
  caption rhythm. Keeping the same translated sentence skeleton is
  `REWRITE_REQUIRED`.
- Ranking/TOP-N jobs still require `structure_remix_required=true`,
  `source_order_allowed=false`, and a recorded implemented order that differs
  from the benchmark/source order.
- The gate does not override source-truth, policy, harness, or the current
  `상단 + timed 중단` caption contract. Verified quoted speech remains
  source-only; parenthesized situation captions remain caption-only.
- If the gate is missing or weak, set `shorts_academy_gate=WAIT` or
  `REWRITE_REQUIRED`, patch the decisions/render files, and do not report
  CapCut/final PASS.

## Legacy Factory Contract v4.0 - superseded by v5.0

Historical compatibility notes only. The `Factory Contract v5.0` source-verified
validation contract above is the only current highest-priority contract.
For ordinary current 11short factory work, do not follow this section when it
conflicts with v5.0.
Do not continue into later legacy sections to recover old `하단`, user-supplied-only,
single-mp3, Gemini-first, or one-off builder behavior unless the user explicitly
asks for legacy recovery/debugging.

Current mandatory skill chain:

```text
000brainstorm
-> 000short-production-agent
-> watch/source direct-frame verification
-> 00-tikitaka
-> 00script-writer
-> 000short-production-agent CapCut/harness
```

Current input contract:

```text
YouTube URL + optional existing Gemini analysis
-> source.mp4
-> source_evidence + watch/direct-frame
-> Gemini raw crosscheck
-> Codex-verified analysis
-> 상단 + timed 중단 + 중단 TTS 글자만 복사
-> writer/humanize/SCRIPT_LOCK
-> requested TTS as per-line clips
-> SRT/layout/render_plan
-> remake_transform gate
-> order_integrity gate
-> CapCut
-> harness
```

Hard rules:

- `00tube` is not a production root. Do not create or route new jobs there.
- Gemini is raw intake/interpretation only. `source.mp4`, source evidence, OCR/STT, scene cuts, and watch/direct-frame are fact authority.
- Codex is the primary execution worker for 11short production on this Windows
  machine. Do not assume Mac mini Hermes plugin, memory, Compound, Honcho, or
  Paperclip state applies to Windows without checking the local Windows paths,
  commands, and environment variables first.
- Current script/output structure is only `상단 + timed 중단 + 중단 TTS 글자만 복사`. `하단`, `하단 원문`, bottom narration, and bottom-TTS script layers are legacy and forbidden for current Shorts-factory CatCup work.
- Current Shorts-factory CatCup internal-project template is `shorts_internal_project_template_v1` inside the internal project file. Text tracks are fixed and must not be reordered:
  - `T1`: `소제목1`, top title line 1.
  - `T2`: `소제목2`, top title line 2.
  - `T3`: TTS/narration caption, plain middle sentence.
  - `T4`: speaker utterance 1, verified original source quote only, written with `" "`.
  - `T5`: speaker utterance 2, verified original source quote only, written with `" "`.
  - `T6`: situation/action/emotion/effect caption in parentheses, e.g. `(퍽)`, `(어리둥절)`, `(순간 정적)`; default excluded from TTS.
- Current Shorts-factory CatCup video/audio tracks are fixed:
  - `V7`: template background, ranking-middle, or transition clip.
  - `V8`: real source-clip edit/assembly video.
  - `A9`: original source voice/audio, BGM, or ranking default bed.
  - `A10`: TTS, sound effects, or preconfigured effect sounds.
- Script output must use this shape only:
  - `상단`: first show the exact text for `T1`, then the exact text for `T2`.
  - `중단`: timed cues such as `[00:00.000-00:02.800]` with each caption explicitly assigned to `T3`, `T4`, `T5`, or `T6`.
  - `중단 TTS 글자만 복사`: copy only the `T3` sentences that will be read by TTS.
- Role routing is strict: plain explanation/narration is `T3`; verified real speaker quotes are `T4`/`T5`; parenthesized situation/action/emotion/effect captions are `T6`. `T6` may overlap `T3`/`T4`/`T5` when it explains the same beat.
- Audio/TTS/BGM/SFX may be placed only on `A9`/`A10`. If adding audio changes the `T1`-`T6` order or role mapping, the draft is FAIL.
- CapCut validation must inspect the actual `draft_content.json` track order and role assignment, not only manifests or filenames. Required evidence: text tracks in `T1,T2,T3,T4,T5,T6` order and media/audio tracks matching `V7,V8,A9,A10` intent.
- Template color family rule: white template = Instagram template; black template = general black template.
- CapCut template authority is the sample project/draft folder, not a settings JSON. Git tracks rules, scripts, and `manifests/capcut-template-set.json`; OneDrive stores template bundles and production data.
- Job/settings JSON may contain only replacement values such as template id, output draft name, source video, visible text, and audio. It must never generate a new `draft_content.json` structure from scratch.
- Current CatCup template defaults are `black` with `catcup_reference_layout_profile="black_template_master_v1"` and `insta white` with `catcup_reference_layout_profile="insta_white_template_master_v1"`. `insta white` is the display name of the local draft folder `260625-ig-contortion-top3-urakkai-instagram-tts`.
- For either default, copy the whole draft folder first, preserve `subdraft`, `Resources/combination`, preset audio placeholder relationships, sticker/effect rows, track count, and z-order, then replace only source/text/timing/audio values. The internal `test.mp4` is template placeholder media and must be replaced in generated drafts.
- The shared template/preset asset bundle lives at `${env:UTUBE_ROOT}\22factory_20260628\00_asset_tools\first`. Before claiming another Windows/macOS machine is synced, run `${env:UTUBE_ROOT}\22factory_20260628\00_asset_tools\sync_capcut_asset_tools.ps1` or `sync_capcut_asset_tools.sh` and verify the local `Presets`, referenced `Cache`, and the two template master drafts are present.
- Do not use `260625-ig-contortion-top3-urakkai-instagram-tts-fixed`; any `Default`, `T1`, or `T2` visible placeholder text in the active draft is FAIL.
- If `##_draftpath_placeholder_##` media paths remain, report `portable_bundle=false`; do not claim Mac/Windows/Claude/Hermes portability until the full resource bundle is verified.
- Current CatCup drafts must set `catcup_track_contract_version="shorts_internal_project_template_v1"`, `catcup_text_tracks=["T1","T2","T3","T4","T5","T6"]`, `catcup_media_tracks=["V7","V8","A9","A10"]`, and `bottom_layer_forbidden=true`.
- Current CatCup drafts must also set `creative_additions_use_tts_or_situation_only=true` and `source_word_synonym_rewrite_status=PASS`. If `verified_source_speech_present=true`, at least one of `T4`/`T5` must be active.
- Segment audio is per clip, not global. Verified source speech, source-audio-locked beats, and beats marked `source_audio_policy=keep_source_audio` keep original video volume. Caption/TTS-only beats use `source_audio_policy=mute_source_audio`.
- Current harness must validate the semantic video track contract for every current 11short urakkai/CapCut job. `capcut_timeline_manifest.json.video_track_contract` must be `caption_video_plus_situation_speaker_video`; missing or different values are FAIL.
- TTS voice identity must be recorded and checked from the requested `voice_id`; do not call a generated voice "다니엘", "춘식이", or any other label by name only.
- If the user asks for 우라까이/final structure/script generation and does not explicitly say script-only, analysis-only, or no CapCut, the job is not done at script/TTS/SRT. Create and register a visible local CapCut draft in the active draft root during the same run, then report the exact `draft_name` and draft path.
- If source footage is not yet available but the user still asked for production/project work, create a working CapCut draft from the available TTS/SRT/assets instead of stopping at a TTS folder. Mark the visual track as placeholder/working media in the report and patch the same draft when the real source arrives.
- A source-order caption-only draft is not Shorts-factory completion unless the user explicitly approves `user_approved_simple_caption_draft=true`.
- For ranking/TOP-N remake videos, the ranking order must be remixed by default. Do not preserve the original rank sequence such as `5->4->3->2->1` or `1->2->3->4->5`; set `structure_remix_required=true`, `source_order_allowed=false`, and record an implemented order that differs from the original ranking order.
- If `analysis.selected_remix_order` or `structure_remix_required=true` exists, `render_plan_pre_capcut.json` and `capcut_timeline_manifest.json` must record the implemented order and match it.
- CapCut text/visual layout checks are production blockers when a draft is
  reported as usable. Selected template provenance, project openability,
  JSON parse, missing media paths, role-separated text tracks, preserved
  template font/color/position/animation for the selected preset, caption
  fit/safe-zone, and stale placeholder media must be checked before the
  user-facing final report. Decorative SFX, BGM, transitions, and text effects
  remain optional unless the user requested them.
- After creating any CapCut draft, run a post-CapCut usability gate against the
  actual local draft folder under the active CapCut draft root. The gate must
  verify `draft_content.json`, `draft_meta_info.json`, and
  `draft_virtual_store.json` parse successfully; the reported `draft_name`
  matches the registered folder; all referenced video/audio/text/sticker media
  paths exist; selected-template placeholder media and stale nested draft
  metadata were removed or intentionally retained with evidence; the real
  `source.mp4` is imported; text role rows are separate editable tracks; and
  template style fields were preserved except for approved content/timing
  changes. If this gate is not `PASS`, the final report status is `FAIL` or
  `WAIT`, not completed.
- Use the OneDrive Paperclip progress board for cross-machine 11short work:
  `$env:UTUBE_ROOT\11short_handoff`. This is the
  current shared work-state layer before any official Paperclip API/MCP
  integration. Honcho stores durable rules; the OneDrive board stores temporary
  job state, locks, evidence, and handoff files.
- Mac mini, home Windows, and office Windows are all allowed production
  machines. Do not assume Mac mini is management-only or Windows is
  production-only. The invariant is: one project can be edited by only one
  machine at a time.
- Before modifying a shared handoff project, read `handoff_manifest.json` and
  `job_state.json`. Work only when `locked_by` is empty or already belongs to
  your peer. Claim the project by setting `locked_by`, `locked_at`,
  `lock_reason`, and an editing/building status before creating or changing
  CapCut, SRT, TTS, render, or validation artifacts.
- Valid OneDrive Paperclip statuses are: `drafting`, `analysis_ready`,
  `assets_ready`, `ready_for_capcut`, `capcut_building`,
  `editing_on_macmini`, `editing_on_home_windows`,
  `editing_on_office_windows`, `capcut_created`, `capcut_harness_pass`,
  `all_harness_pass`, `upload_ready`, `uploaded`, and `blocked`.
- Canonical peers are `hermes-macmini`, `codex-macmini`,
  `hermes-home-windows`, `codex-home-windows`, `hermes-office-windows`, and
  `codex-office-windows`. `codex-windows` is temporary only until the current
  Windows machine is identified as home or office.
- For shared project state, use
  `py -3 $env:UTUBE_ROOT\tools\paperclip_progress\paperclip_progress.py`
  to list, initialize, claim, release, complete, block, or validate handoff
  projects when practical. Manual JSON edits must preserve the same lock and
  status contract.

## Tool And Memory Integration Guard v1.0

Use this section when optional workflow plugins, memory tools, or text-polish
tools are mentioned during 11short production.

- Superpowers can help with planning, debugging, test-first code edits, and
  review of automation changes. It is not a substitute for source evidence,
  watch/direct-frame verification, 11short harnesses, or CapCut openability
  gates.
- Use Superpowers on Codex first when the active Codex session exposes a
  `superpowers:*` skill. If local plugin files exist under the Codex plugin
  cache but `superpowers:*` is not callable in the current session, record
  `superpowers_state=INSTALLED_CACHE_CONFIRMED_SESSION_SKILL_NOT_EXPOSED`,
  continue with the normal 11short gates, and retry in a fresh session when
  available. If neither the cache nor a callable skill exists, record
  `superpowers_state=WAIT_INSTALL`. Do not claim a Superpowers review, TDD
  pass, or verification-before-completion pass unless its skill actually ran.
- Superpowers is a work-discipline layer for 11short automation, not a Shorts
  script or video-making authority. Route it by task type:
  - `using-superpowers`: start of a fresh Codex session or any 11short
    automation/skill change, to select the right discipline skill.
  - `verification-before-completion`: highest-priority completion guard before
    any "done" report. It must check real files, validation state, CapCut draft
    path/openability, media paths, and source-audio preservation.
  - `systematic-debugging`: use for failures such as ffmpeg/render errors, SRT
    drift, TTS duration mismatch, missing Gemini JSON, OneDrive path mismatch,
    mojibake, missing source audio, or broken CapCut drafts. Do not guess-fix.
  - `writing-plans`: use before changing 11short automation, parsers, SRT/TTS
    generators, CapCut draft creation, OneDrive sync, harnesses, or shared
    skills. Steps must include files touched, verification commands, and
    rollback/recovery notes.
  - `test-driven-development`: use for code/harness changes that prevent repeat
    failures, such as bottom-caption bans, verified-quote enforcement, CapCut
    draft path/openability checks, mojibake scans, and `final_script_ko` gates.
    It is not required for ordinary script-only writing.
  - `requesting-code-review`: use after modifying automation, harnesses,
    CapCut builders, Gemini parsers, SRT/TTS generators, OneDrive sync scripts,
    or 11short skills. Review specifically for bottom-caption leakage,
    unverified quotes, completion without draft, source-audio loss, and
    compatibility with the current factory contract.
  - `subagent-driven-development`: use for large factory refactors, bulk URL
    batches, or multi-part analysis/script/SRT/CapCut/test-pack work. It is
    usually overkill for one ordinary Short.
  - `brainstorming`: use for new formats, new channel templates, photo/TTS
    explainer modes, or major pipeline redesign. Do not force it on routine URL
    analysis, existing-template production, or simple file cleanup.
- If Superpowers is unavailable in the current session, still follow the same
  routing intent with native Codex planning, debugging, tests, and completion
  verification, but report that the actual Superpowers skill did not run.
- gstack is optional and project-scoped. Use it for larger product/tool
  planning or browser QA experiments only after the normal 11short pipeline is
  stable; do not let gstack routing override the current skill chain.
- Karpathy-style coding guidelines and Understand-Anything/codebase-graph tools
  are deferred for ordinary Shorts production. Treat them as future automation
  engineering references only, not active 11short production dependencies.
- Compound Engineering, when installed and available, may be used only as a
  post-task review and failure-criteria candidate extractor. It must not be
  treated as source truth, a PASS authority, a CapCut validator, or a long-term
  memory database. A Compound finding is a candidate until Codex verifies it
  against files/harnesses and the operator accepts it as a repeated rule.
- If Compound is not installed, not exposed as a callable skill, or has no
  linked log, mark `compound_state=WAIT - unavailable/not linked`. Do not block
  ordinary 11short production only because Compound is unavailable.
- Do not install or use `agentmemory` or another extra memory layer for 11short
  operating rules unless the user explicitly requests it for the current
  machine. The active durable authorities are local skills, shared
  `codex_skills_source`, Codex memories when available, and any user-approved
  Honcho/Hermes rule store. Avoid split-brain memory.
- Honcho/Paperclip setup, if requested, must never print API keys or tokens.
  Check only set/unset/length status, back up existing Codex/Claude/Hermes
  config first, and exclude secrets, cookies, sessions, and personal/customer
  private data from sync.
- `humanize-korean` or any humanizer may be used only as a final wording polish
  pass under this order: `source evidence > YouTube/policy safety > 우라까이
  structure > current 11short caption contract > humanizer style polish`.
  It must not change verified quotes, speaker meaning, facts, names, numbers,
  timestamps, policy-sensitive wording, or source-supported claims. If the
  humanizer changes those, revert or rewrite manually.
- Do not install or route to a separate `claude-video` plugin for current
  11short work. Use the existing `watch` skill and the current
  `watch/source_evidence/Gemini crosscheck` path as the video-analysis route.
  Reconsider `claude-video` only if the user explicitly asks for a future
  comparison test.

## Legacy Contract And Quarantine v3.0 - superseded by v5.0

Historical compatibility notes only. The `Factory Contract v5.0` source-verified
validation contract above wins. Do not treat this section as current authority
when it conflicts with v5.0, including on `하단`, `guide_ko.srt`, user-supplied
voice gates, Gemini-first flows, or one-off CapCut builders.

Current active pipeline:

```text
URL + optional existing Gemini analysis
-> source.mp4
-> source_evidence + watch/direct-frame verification
-> Codex-verified analysis
-> 00-tikitaka final script: 상단 + timed 중단 + 중단 TTS 글자만 복사
-> SCRIPT_LOCK
-> requested voice/TTS generation when explicitly requested
-> SRT/layout/render_plan
-> CapCut draft using existing factory/reference
-> harness
```

Conflict-resolution rules:

- Do not follow older instructions that require `상단 / 중단 / 하단 / 하단 원문` as the current script structure. Current script structure is `상단 + timed 중단 + 중단 TTS 글자만 복사`.
- Do not create or require a separate `하단` layer for current 11short work. `중단 TTS 글자만 복사` is a copy/generation source derived from timed `중단`, not an independent bottom script layer.
- `guide_ko.srt` may exist only as a compatibility/export file when an older harness or CapCut helper requires it. The current visible caption authority remains `onscreen_ko.srt` / `onscreen_layout.json` derived from timed `중단`.
- The default no-TTS/user-supplied voice rule applies only when the user has not requested generated voice. If the user explicitly requests Supertone/Daniel/TTS or any generated voice, generate or place that voice before CapCut; do not stop and ask the user to provide the same TTS package.
- For current 11short factory jobs, use Supertone Daniel body voice by default after SCRIPT_LOCK: `voice_profile=daniel`, `voice_id=ca0b75f0fc2ee0ab6fa54d`, `speed=1.2`, `pitch_shift=1.2`, and the current project’s selected model setting. Use Chunsik or another voice only when the user explicitly requests that voice for the current job.
- `source_audio_only`, silent, or no-TTS CapCut mode is allowed only when the user explicitly says to skip generated voice, says not to use Daniel/TTS, or the job is marked `voice_generation_mode=no_tts|skip_tts|source_audio_locked`.
- When a short is under 30 seconds and source evidence/watch have already passed, do not create a new large one-off builder. Use existing helpers and the single user-named reference project unless a missing capability is proven.

## URL Mode Selection Override v1.0

When the user provides a YouTube URL for 11short work, ask for mode before production starts:

```text
1. 감독모드
2. 자동모드
```

Rules:

- `1` 감독모드: after each stage, report generated/changed files, PASS/FAIL/WAIT, and next-stage risk, then stop until the user approves continuing.
- `2` 자동모드: continue through the workflow, but still report each stage in order with PASS/FAIL/WAIT.
- Even in 자동모드, do not proceed past any failed harness, policy FAIL, missing SCRIPT_LOCK, missing required voice/SRT/audio, or other hard gate.
- If the user sends only `1` during a run, immediately switch to 감독모드.
- If the user sends only `2` during a run, switch to 자동모드, while still enforcing all hard gates.

## URL Source-Evidence Factory Override v2.0

This section overrides older URL-only staged-intake text in this file that asks for `1번 제미나이 분석본`, `2번 GPT1`, `3번 GPT2`, and `4번 GPT3` as the default next input.

Current factory order for ordinary YouTube URL/source intake:

```text
URL/source download
-> Codex local source_evidence generation
-> Gemini evidence-based analysis
-> 00-tikitaka / writer gates
-> 000short production
```

Primary user input contract:

```text
URL + user-provided existing Gemini analysis
-> save Gemini as raw hypothesis/intake
-> download/source_evidence/watch-direct-frame verification
-> cross-check Gemini claims against source evidence
-> create Codex-verified final analysis
-> script/production
```

Rules:

- If the user provides both a URL/source and an existing Gemini analysis, treat that as the preferred normal intake. Do not ask for Gemini again and do not generate a new Gemini prompt before validation.
- Save the user-provided Gemini content as raw intake, not final truth. Suggested names: `user_gemini_analysis_raw.md` or `user_gemini_analysis_raw.json`.
- The added Codex function is validation: check whether the provided Gemini analysis matches `source.mp4`, frames, OCR, transcript/STT, scene cuts, and watch/direct-frame observations.
- Produce or maintain a cross-check record that separates `supported`, `contradicted`, `uncertain`, and `needs_manual_review` claims.
- The final production 기준 is the Codex-verified normalized analysis, not the unverified Gemini text. Suggested final artifact names: `analysis.json` and/or `source_verified_analysis.json`.
- After `source.mp4` is downloaded or located, the next default gate is `Codex source_evidence 생성`, not `1번 제미나이 분석본 접수`.
- In 감독모드, stop after source download with `next gate: Codex source_evidence 생성`.
- In 자동모드, continue to source-evidence generation automatically and report the stage result.
- Use `source_evidence.json`, frames, OCR, transcript/STT, scene cuts, and `source.mp4` as the fact authority before Gemini interpretation.
- Gemini is the interpretation/synthesis stage. It must use local evidence and must not override `source_evidence.json` facts.
- After `source_evidence.json` passes, Gemini has three allowed routes:
  - user provides an existing Gemini analysis
  - Codex creates `gemini_request.md` for the user to paste into Gemini
  - Codex runs Gemini directly when API mode is explicitly configured
- `WAIT_USER_GEMINI_ANALYSIS` is a soft interpretation wait. It must not block Codex from running `watch/direct-frame` source analysis when the user chooses 감독모드, asks to inspect each step, or says to continue without Gemini.
- If Gemini is not ready, report `Gemini: WAIT` and continue with source-truth work only: scene-by-scene visual reading, action flow, OCR correction, wow-point candidates, and risk notes. Do not call the result final until Gemini or an explicit Gemini-skip decision is recorded.
- External staged inputs such as `1번 제미나이 분석본`, `2번 GPT1`, `3번 GPT2`, and `4번 GPT3` are legacy/opt-in only. Ask for them only when the user explicitly says they are using the external GPT-project handoff or provides those numbered inputs.
- Do not write `next_required_input: 1번 제미나이 분석본` for an ordinary URL-only factory run.

## Fast Path And Anti-Overbuild Rule v1.0

When the source video is short, especially under 30 seconds, do not expand production into a broad repo search or a new large one-off CapCut builder unless the existing factory path is proven impossible.

Rules:

- If `source_evidence`, Gemini intake/crosscheck, and `watch/direct-frame` already passed, do not rerun or re-investigate those stages unless the user explicitly asks for re-analysis.
- If `script_lock_status` is not `SCRIPT_LOCK`, the only next task is script lock recovery. Do not inspect CapCut templates, create CapCut builders, generate layout files, or run harnesses before the lock is restored.
- If the user explicitly requires Supertone/Daniel TTS or any generated voice, do not switch to `source_audio_only`, silent, or no-TTS CapCut mode. Generate/verify the requested voice first, then build CapCut.
- If the user names a reference project or draft, use only that reference for layout/audio-track extraction unless it is missing or unreadable. Do not compare many old projects by default.
- Prefer existing factory scripts in this order:
  1. `make_supertone_voice_from_final_script.py` for Daniel/Supertone voice
  2. existing SRT/layout/render-plan helpers in the episode or 11short root
  3. `create_capcut_draft_from_template.py`
  4. the single user-named reference draft/project for style and track structure
- Do not create a new 500+ line custom `build_*_project.py` for an ordinary short if the existing factory/reference route can do the job. If a custom builder is truly required, state the missing factory capability first and keep the builder narrowly scoped.
- In 감독모드, if a stage takes more than 5 minutes without producing the expected output file, stop and report the exact blocker instead of continuing to search or generate more scaffolding.

## Current Caption Contract Override v2.0

This section is the latest authority and overrides older `하단`, `하단 원문`, `하단 첫마디`, bottom-caption, and bottom-TTS rules that may remain in this file, referenced files, older handoff prompts, or legacy project documents.

Current default script structure:

```text
상단
2줄 제목

중단
[0~3초]
"검증된 실제 발화"
(상황/감정/반응)
일반 텍스트
```

Rules:

- The current visible/script system has no separate `하단` layer.
- The hook/memory anchor is now the first strong `중단` cue, not a first `하단` line.
- Do not ask for `하단 첫마디 후보 5개` in the current default workflow.
- Do not require or output `하단`, `하단 원문`, `guide_ko.srt`, `bottom_tts_script_ko`, or `voice_body.txt` as script layers. If voice/TTS is requested, derive technical voice files from timed `중단`; do not add a bottom script section.
- `중단` is the single timed visible-caption authority and is written with three forms:
  - `" ... "` = verified source speech/source subtitle/reliable transcript only. Do not invent or rewrite unverified speech inside quotes.
  - `( ... )` = creative situation, emotion, reaction, viewer read, sound/impact cue, or tone cue.
  - plain text = direct visible explanation, OCR-style label, context sentence, or narration-like caption shown as middle text.
- A single timed `중단` beat may contain multiple middle rows at the same time, such as `(상황설명)` + `"검증된 대사"` + plain/TTS explanation. These are separate middle rows, not a separate bottom layer.
- If TTS is enabled, only the rows explicitly marked as TTS/plain voice lines are read. Verified quote rows and parenthesized situation rows may be visual-only unless explicitly marked for voice.
- For production files, map `중단` to `onscreen_ko.srt`, `onscreen_layout.json`, and the CapCut middle overlay track.
- If old tools require `guide_ko.srt` for compatibility, create it only as `N/A`, empty compatibility, or a duplicate display artifact explicitly marked as compatibility. It must not become an independent bottom narration layer.
- Instagram/Reels production follows the same middle-only caption meaning unless the user explicitly requests a different legacy layout.

Notation constitution:

- `[00:00-00:03]`, `[몇초]`, or bracketed timing means the source/video segment marker for the writer/operator; it is never copied into CapCut as visible text.
- Only these three text forms become CapCut `중단` text: plain text such as `소녀는 소년에게 다가갔다`, verified quoted speech such as `"야 이 새끼야!"`, and parenthesized reaction captions such as `(순간 움찔하는 소년)`.
- A plain narration sentence is plain timed `중단` caption text by default. If voice/TTS is requested, derive the voice line from that same `중단` text.
- `"안녕하세요"` or any double-quoted line means verified source dialogue/speech/subtitle only. Never invent quoted speech.
- `(이거 괜히 뻘쭘하네)` or any parenthesized line means caption-only reaction/emotion/situation text for timed `중단`.
- In all current jobs, write and produce only `상단` and timed `중단` as the script package; technical voice/export files may be generated from `중단` only when explicitly requested.

Middle text type constitution:

- `중단` is one CapCut middle text authority, but it contains two different edit functions:
  - script/TTS line: spoken or narration-like line that the voice/TTS can read
  - non-script situation caption: visual-only reaction, SFX, emotion, or situation note
- If the beat is a script/TTS beat, put the spoken line in timed `중단`. It may be plain narration text, or verified quoted source speech if the source actually says it.
- If the beat is not a script/TTS beat, put a parenthesized caption in timed `중단`: `(퍽)`, `(가소롭군)`, `(뭐지..??)`, `(순간 얼어붙음)`, `(한 대 맞고도 멀쩡함)`.
- For impact/action beats, use short parenthesized SFX or reaction captions instead of long narration: `(퍽)`, `(쿵)`, `(기스도 안 남)`, `(아무렇지 않음)`.
- For emotion beats where the character reacts without clear speech, use parenthesized inner-read captions: `(가소롭군)`, `(뭐지..??)`, `(이게 안 먹혀?)`.
- Use a quoted line such as `"더 때려봐라"` only when it is verified source speech, confirmed subtitle, or a user-cleared character line. If it is only our interpretation, write it as a parenthesized reaction instead.
- Do not create a separate bottom layer for these. Script/TTS lines and non-script situation captions both live in timed `중단`.

Middle color/style constitution:

- Current CatCup placement profiles are `black_template_master_v1` for `black`
  and `insta_white_template_master_v1` for `insta white`.
- Top title: fixed full-duration two-line headline at the very top. Use black
  text on a white top banner for both lines.
- Plain unquoted middle text is the TTS/narration line. It must be white by default.
- TTS/narration style follows the second user reference image: white outlined
  text, no black caption box by default.
- Quoted speaker utterance text, such as `"더 때려봐라"`, is a 화자발언 line. Do not style it white.
- Use speaker colors for quoted utterances:
  - 남자 화자: red-family color
  - 여자 화자: blue-family color
  - unknown/mixed speaker: assign a non-white speaker color and record the reason
- Parenthesized situation/effect/emotion text, such as `(퍽)` or `(뭐지..??)`, is visual-only unless explicitly voiced. Do not style it white.
- Parenthesized situation/emotion style may follow the third user reference
  image, but color and `animation.role=wobble_shake` / `흔들흔들` are optional
  polish. Missing effects must not fail the gate.
- `ㅋㅋㅋ`, `ㅎㅎㅎ`, or similar laugh/reaction captions stay on the
  `situation_emotion` track. Cyan color and text animation are optional polish.
- Use effect-matched colors for parenthesized captions:
  - impact/SFX: green or strong effect color
  - emotion/inner-read: pink, green, or another non-white reaction color
  - caution/shock: yellow or red-family highlight when needed
- The CapCut middle-text plan should record `middle_text_type`, `speaker_gender` when known, `include_in_tts`, and `text_color_role` or `text_color`.
- In CapCut drafts, split timed middle text into editable type tracks by default:
  - `( ... )` reaction/status/emotion/SFX captions on one text track
  - `" ... "` verified speaker utterances on one text track
  - plain `대본`/TTS narration lines on one text track
- Keep all three middle text tracks visually at the middle caption position unless the user requests separate screen positions. The split is for editing control and track clarity, not for creating separate visible layers.

## Legacy Voice/TTS Handoff Constitution v1.0 - overridden unless explicitly requested

This section is legacy. For current factory work, the `Factory Contract v5.0`
source-verified validation contract above wins.
Use the rules below only when the user explicitly chooses an external
user-supplied SRT/audio/ZIP handoff route.
Do not stop and ask the user to provide TTS/SRT/ZIP when the current job
explicitly requests Supertone/Daniel/API voice generation.
If the user explicitly says not to use Daniel/TTS, mark the job `no_tts` and
allow CapCut without generated voice.

Default voice mode:

```text
tts_generation_mode=user_supplied_only
```

Rules:

- Do not generate TTS/voice by default. Do not use Edge TTS, ElevenLabs, Supertone, Kokoro, browser TTS, or any other voice provider unless the user explicitly asks for that provider in the current job.
- ElevenLabs is allowed by default only for source-dialogue/STT analysis when this workflow requires checking the original video's in-video speech. This is not TTS generation.
- Legacy external handoff only: when the user explicitly requests user-supplied SRT/audio/ZIP, run the report-first sequence and build CapCut only after that package is received.
- Legacy external handoff only: after the final `중단 TTS 글자만 복사` block is ready, ask the user to provide the TTS/SRT/audio package before building the final CapCut draft.
- The required ask is: `TTS 만들 글자입니다. 이걸로 음성/SRT/ZIP 만들어서 주세요. 받으면 캣컵 프로젝트 만들겠습니다.`
- If the user already provided TTS WAV/MP3/SRT/ZIP, use those exact user-supplied files as the voice authority.
- If an API key is present but lacks `text_to_speech` or voice permissions, mark `voice_status=WAIT_USER_TTS_OR_VALID_KEY`. Do not silently fall back to another voice.
- User-supplied TTS should be placed as editable per-line audio clips matching the timed plain `tts:` middle lines. Do not collapse TTS into one long full-duration audio clip unless the user explicitly requests a single aligned audio file.
- TTS line count, order, text, and timing must match the visible plain `tts:` middle captions. If they do not match, stop and report the mismatch instead of forcing the draft.
- Parenthesized `(상태/효과/반응)` captions are visual-only and must not be included in the TTS package unless the user explicitly asks to voice them.

Script meaning gate before requesting TTS:

- The TTS-only text must explain the cause-and-effect of the story without requiring hidden context from the source video.
- Run the simple `그래서 뭔데? / 왜 그렇게 됐는데?` check on the TTS-only block. If the viewer cannot answer it from the TTS text, rewrite before asking the user for voice.
- Do not erase the core cause just to sound safe. For verified sensitive incidents, use restrained but clear wording such as `성추행 정황`, `몹쓸 짓`, `피해 사실`, or another source-supported phrase. Avoid graphic detail, but do not hide the reason the event happened.
- For police, hospital, rescue, accident, or justice-result hooks, the TTS must state the triggering cause before the resolution. Example structure: `문제 발생 -> 목격/확인 -> 보호/대응 -> 결과`.

CapCut audio gate:

- A CapCut draft is not audio-ready just because an audio file appears in the media bin or `materials.audios`.
- Audio volume normalization is mandatory for every active audio source in a 11short CapCut draft. Source speech audio and user TTS/caption voice must be normalized or explicitly target-leveled before the draft is called usable. BGM and SFX are checked only when they are actually used.
- Required evidence before/after CapCut:
  - `audio_normalization_required=true`
  - `audio_normalization_status=PASS`
  - `audio_normalization_method=capcut_volume_normalize|ffmpeg_loudnorm|both|target_level_mix`
  - `normalized_audio_assets` lists every active source speech and user voice/TTS file or segment, plus BGM/SFX only when those optional assets are actually used.
  - `audio_normalization_report_path` or equivalent loudness/peak report exists when ffmpeg or external normalization was used.
- Legacy external handoff only: for Gemini/초벌/우라까이 remake intake, a CapCut draft is blocked until both gates are true:
  - `elevenlabs_dialogue_analysis_status=PASS` or `NO_DIALOGUE`, with a saved source-dialogue report.
  - `user_srt_audio_gate_status=RECEIVED` or `PASS`, with either a user ZIP package or matching SRT plus audio files.
- Audio is ready only when the expected active source/TTS clips exist as `tracks[type=audio].segments` on the timeline. SFX/BGM clips are expected only when the manifest says they were used.
- Before reporting a CapCut draft usable, verify:
  - no missing media paths for audio/video materials
  - timeline video covers `0..project_end` without unintended black/blank tail
  - TTS track has one segment per user-supplied voice line
  - source audio is present only where it is needed, or the replacement aligned source-audio track is present
  - when using split-audio assembly, `source original audio needed` exists as a real audio track for source-speech beats and `tts voice from user SRT` exists as a separate real audio track for user TTS beats
  - project duration matches the final visual/TTS end, not an arbitrary original-source duration
- Do not mute embedded source video audio unless there is an explicit replacement source-audio track or the beat is intentionally silent.
- Default current 11short audio assembly is `source_original_audio_track_plus_user_tts_track`: active source video segments may be muted only because the matching source speech has been extracted into an editable source-audio track. Do not lower all source audio under the whole edit and call it done.
- If CapCut is open, do not patch the active draft JSON and call it final. Create a new draft from a known-openable base or tell the user to close CapCut before patching.

Remake rewriting and edit-point rules:

- Replace most words from the benchmark/source script so the Korean caption wording fits the new video flow.
- Paraphrase source speech naturally in Korean while preserving meaning and support from the source; do not invent unsupported speech or facts.
- Change edit points accurately around the verified `wow point` and the timed `중단`/voice-derived line when voice is requested.
- The hook must get shock pressure from both the `wow point` and the top title/subtitle wording. A soft summary hook fails.
- If the user provides already changed footage, a recut order, or Korean 우라까이/caption direction, treat it as the creative authority unless it violates source truth, safety, or harness contracts. Do not rebuild the idea from scratch.
- Preserve the user's chosen flow, wow point, and caption intent. Patch only the parts needed for source accuracy, readability, timing, or policy.
- The production agent's responsibility is to make the CapCut draft natural: clean cut joins, readable timed `중단`, natural Korean source-speech paraphrase, non-awkward caption timing, consistent top/middle text, required active audio timing, and no jarring overlaps. SFX/BGM/transition effects are optional polish, not required completion gates.
- If the user's direction has a blocker, report the exact blocker and the smallest needed fix instead of replacing the whole concept.

Movie/drama source-use override:

- Follow the root `AGENTS.md` source-use rule.
- If a movie/drama clip is obviously distributor-controlled, uncleared, or uncertain, mark source-use as `BLOCK`.
- If the user explicitly says they checked the source and it is usable/cleared for the current job, record `source_use_status=USER_CLEARED_SOURCE` and do not block solely because it is movie/drama footage.
- User-cleared source-use does not skip YouTube safety checks. Continue checking and reporting separate platform risk for violence, weapons, self-harm, sexual content, hate/harassment, minors, advertiser suitability, and any other content risk.
- In the work/status files, note the user's clearance statement in plain Korean, for example: `사용자가 사용 가능 여부 확인 후 제공한 소스`.

## YouTube Restriction Guideline Production Gate v1.0

Use the user's YouTube exposure-restriction chart as a mandatory 11short production gate. Run it after source download/watch or direct-frame analysis, after caption/script changes, before `production_gate_result.json`, and before upload text. If the source is URL-only, mark uncertain items as `WAIT` or `MEDIUM/HIGH` until the downloaded `source.mp4` is checked.

Required production evidence in `production_gate_contract.json` or `status.json`:

```json
{
  "youtube_restriction_guideline_gate_complete": true,
  "youtube_restriction_policy_risk_tier": "LOW|MEDIUM|HIGH|BLOCK",
  "youtube_restriction_platform_verdict": "PASS|REWRITE_REQUIRED|FAIL",
  "youtube_restriction_flagged_categories": [],
  "youtube_restriction_rewrite_required": [],
  "youtube_restriction_hard_blocks": [],
  "youtube_restriction_note_ko": ""
}
```

Pre-CapCut blocking rules:

- `youtube_restriction_guideline_gate_complete` must be true before `validate_production_gate.py` can allow CapCut creation.
- `youtube_restriction_policy_risk_tier=BLOCK`, `youtube_restriction_platform_verdict=FAIL`, non-empty `youtube_restriction_hard_blocks`, or unresolved `youtube_restriction_rewrite_required` blocks CapCut, final report, and `upload_ready`.
- `REWRITE_REQUIRED` means repair the script/caption/crop/thumbnail/upload text, rerun the gate, then continue.
- `MEDIUM` or `HIGH` may proceed only when `platform_verdict=PASS`, the risk is explained in Korean, and the final visible text avoids shock, exploitation, or unsupported claims.

Chart categories to scan:

- 아동/미성년자: under-18 drinking, smoking, vaping, fireworks misuse, unsupervised firearms, fear/crying, emotional suffering, or purposeless dangerous/confusing behavior. Do not use child distress as the hook.
- 동물/마약/자살자해/혐오/테러전쟁: human-induced animal fights; non-standard cruelty outside ordinary hunting, food processing, or medical treatment; poison/explosive/non-standard hunting; animal abuse, neglect, staged rescue, or glorification; predator-prey blood/body closeups; animal-pain thumbnails; drug/self-harm/hate/terror/war framing.
- 폭력/선정: violence incitement or glorification toward a person/group; perpetrator-shot violence; sexual assault scenes; shock-first accidents, assault, corpse, blood, or injury without context; blood/injury/corpse as the screen center; violence as the video's main purpose; firearm/war scenes; direct sensitive body exposure; direct sex depiction or strong implication; sexual jokes or sexual conversation as the center; bed/kiss scenes that may limit exposure depending on intensity.

Animal and emotional Shorts handling:

- Natural animal behavior, animal affection, caretaking, or ordinary cute/emotional moments are allowed when there is no distress, injury, abuse, staged rescue, or blood/body focus.
- Do not infer an animal's exact inner state as fact. Use source-visible wording such as `사람처럼 안긴`, `먼저 품으로 간`, or `울컥하게 만든 장면`; avoid unsupported lines such as `이별을 알고 울었다`, `버림받는 줄 알았다`, or `놓치기 싫어 발버둥쳤다`.
- For serious/emotional animal clips, keep captions restrained, avoid mocking/SFX-heavy treatment, and keep source audio or quiet music when it supports the verified emotion.
- If crop, zoom, thumbnail, or first frame makes animal pain, injury, fear, blood, or shock look central, revise the visual plan even if the source itself is usable.

## Legacy Gemini/Rough/Urakkai External-Handoff Sequence v1.0 - superseded by v5.0

Use this section only when the user explicitly chooses the external
user-supplied SRT/audio/ZIP handoff route. For current ordinary factory work,
follow `Factory Contract v5.0`: save Gemini/VLM/GPT as `analysis_hint`, run
source evidence, target phrase checks, segment decisions, layout plan,
normalized draft, validation report, and evidence pack.

Legacy sequence:

1. Create or reuse the episode work folder.
2. Download or locate the real source video as `{work}\source.mp4`; JSON alone is never enough.
3. Run watch/direct-frame analysis for visual timing and OCR.
4. Extract or use the source audio and run ElevenLabs/Scribe source-dialogue analysis for every in-video spoken line, subtitle-like speech, and speaker turn that could affect `"..."` quoted captions.
5. Normalize the report into:
   - `( ... )` = screen composition, visual state, emotion/reaction, or non-spoken cue.
   - `" ... "` = verified original speaker dialogue/source speech only.
   - plain text = the user's TTS/script line candidate.
6. Produce the final report/script package for the user. Do not create SRT, generated voice, or CapCut yet.
7. Ask the user to create and provide the SRT/audio/ZIP package from the report.
8. Only after that package is present and verified, create/register the CapCut draft.

Mandatory records before `production_gate_result.json` can PASS:

```json
{
  "source_download_status": "PASS",
  "watch_direct_frame_status": "PASS",
  "elevenlabs_dialogue_analysis_required": true,
  "elevenlabs_dialogue_analysis_status": "PASS|NO_DIALOGUE",
  "source_dialogue_analysis_provider": "ElevenLabs Scribe",
  "source_dialogue_analysis_path": "source_dialogue_elevenlabs.json",
  "final_report_before_capcut": true,
  "final_report_status": "USER_REVIEWED_OR_DELIVERED",
  "requires_user_srt_audio_before_capcut": true,
  "user_srt_audio_gate_status": "RECEIVED|PASS",
  "user_srt_path": "voice_body_split.srt",
  "user_audio_path": "voiceover_body.mp3"
}
```

Legacy external-handoff hard stops only:

- If ElevenLabs/Scribe cannot run or the source has unverified speech, stop at `BLOCKED_ELEVENLABS_DIALOGUE_ANALYSIS` and report the blocker. Do not invent `"..."` dialogue.
- If the final report has not been delivered to the user, stop at `WAIT_FINAL_REPORT`.
- If the user has not provided SRT and voice/audio/ZIP, stop at `BLOCKED_UNTIL_USER_SRT_AUDIO`. Do not create a silent, placeholder, or partial CapCut draft.
- If the user explicitly says `소리 없이`, `무음`, `SRT/음성 없이 CapCut`, or `원본음성만`, record `requires_user_srt_audio_before_capcut=false` and `user_srt_audio_gate_status=N/A_USER_CONFIRMED_NO_VOICE`; otherwise the user SRT/audio gate is required.

## Current Edit Assembly Constitution v1.0

This section is the latest authority for how 11short CapCut drafts are assembled. It overrides older rules that treated production as only `12345 -> 54123` source-order remixing.

Default edit assembly mode:

```text
edit_assembly_mode=scenario_first_montage
```

Core workflow:

1. Use `watch` or direct-frame analysis first to split the source into a reusable source beat library.
2. Build the Korean scenario/script timeline second. The script timeline may contain narration/caption beats before a final source clip is assigned.
3. Build a timeline skeleton from the scenario:
   - important source clip / wow preview
   - blank, neutral, or caption-only TTS beat
   - context video
   - reaction video
   - payoff video
4. Assign source ranges to each scenario beat after the script logic is clear.
5. Create the CapCut draft from `scenario_timeline` plus `clip_assignments`, not from a blind contiguous source order.

Duration constitution:

- Do not force the remake draft to match the original source duration. If the source is 30 seconds, the remake must not automatically be 30 seconds.
- Lowering similarity and making the edit natural is more important than preserving the exact source length.
- Exact source-duration matching is allowed only when the user explicitly asks for it, or when a platform/template constraint makes it unavoidable. Record the exception as `same_duration_exception_reason`.
- The script/caption timeline should be as long as the Korean scenario needs, then visual clips are filled around that timing.

Watch segmentation rule:

- `watch`/direct-frame analysis must produce a source beat library with short, reusable ranges: action beats, dialogue beats, reaction beats, OCR/title beats, transition beats, and payoff beats.
- A source beat can be split, reused, trimmed, slowed, or placed later when the scenario needs it.
- A scenario beat may intentionally be `blank`, `caption_only`, or `neutral` when the TTS/중단 line needs breathing room before matching footage is placed over it.
- The old `selected_remix_order` field is legacy/simple-mode only. Use it only when the job explicitly asks for a simple order remix.
- For current 11short 우라까이 production, require a functional story structure
  from the script side before building SRT/layout/CapCut. Do not accept a script
  plan that only says `1-2-3-4-5` or only lists reordered source numbers.
- The expected Tikitaka/script handoff is:
  - `original_function_structure`: source ranges mapped to roles such as 원인,
    오해, 갈등, 미끼, 티저, 반전, 정체 공개, 감정 상승, 웃음 포인트, 감동 포인트,
    화해, 결과, 회수, 엔딩
  - `remake_versions`: three candidates by default: `A_반전_선공개형`,
    `B_갈등_증폭형`, and `C_감동_회수형`
  - `selected_remake_version` when the user or writer locks one version for
    production
  - timed `중단` blocks containing both edit time and source time:
    `[편집 00:00-00:03 | 원본 00:36-00:42]`
  - `tts_lines` derived only from plain narration `중단` lines, excluding
    verified quoted speech and parenthesized situation captions
- If three versions are present and no selected version is marked, stop before
  SRT/layout/CapCut and ask for or infer the selected version only when the
  user's latest instruction clearly authorizes a default. Record the choice in
  `status.json` or `analysis.json`.
- For normal 11short production, write:
  - `edit_assembly_mode`
  - `source_beat_library`
  - `scenario_timeline` or `scenario_beats`
  - `clip_assignments`
  - `beat_role`: `hook_visual`, `narration_blank`, `caption_only`, `context_video`, `dialogue_video`, `reaction_video`, `payoff_video`, or another clear role
  - `source_range` and `target_range` when a source clip is placed
  - `asset_type=blank/caption_only/neutral` when no source clip is intentionally placed yet

Caption/TTS placement:

- `중단` remains the visible/timed caption authority for every scenario beat.
- A TTS or caption-only beat is still a timed `중단` beat. It is not `하단`.
- Empty visual space for TTS is an edit decision, not a new script layer.

## Script-Aligned Timeline Mapping Constitution v1.0

This is not a fixed clip order rule. It is a mandatory beat-mapping rule: the Korean script/timed `중단` beat is the edit key, and every visual/audio segment must attach to that beat through the same `script_beat_id` or `scenario_beat_id`.

Beat types:

- `( ... )` means situation/reaction/emotion/effect visual context. It may use a source video segment, neutral clip, or caption-only space. It is visual/caption-only unless the user explicitly asks to voice it.
- `" ... "` means verified original source dialogue only. Keep or extract the matching source speech audio for that beat; do not replace it with invented TTS.
- Plain `중단` text means user TTS/caption voice by default. Place the user-supplied SRT/audio segment under the matching visual beat.

Required CapCut structure:

- There is no mandatory order such as situation first, speech second, voice third. The sequence follows the script.
- For every script beat, create a mapping row that can be audited as:
  - `script_beat_id`
  - `target_range`
  - `visual_role` / `video_role`
  - source video segment or intentional `asset_type=blank/caption_only/neutral`
  - source speech audio segment when the beat contains verified `"..."` dialogue
  - user caption/TTS audio segment when the beat contains plain TTS text
- If a beat has user TTS/caption voice, the full TTS audio time range must be covered by video. Do not leave a blue voice segment with no source/situation/neutral video above it. Fill that "missing tooth" with the best matching situation video, a held source clip, a neutral source moment, or an intentional caption-only/blank visual asset.
- A visual segment without a script beat is an orphan and fails the gate.
- A source speech audio segment without the matching quoted beat is an orphan and fails the gate.
- A user TTS/caption voice segment without the matching plain script beat is an orphan and fails the gate.
- A user TTS/caption voice segment whose target range is not visually covered is an orphan-like gap and fails the gate.
- Parenthesized situation captions, quoted source speech, and plain TTS lines can be adjacent or mixed across the timeline, but each must remain tied to the correct `script_beat_id`.

Text display layout:

- Visible text is arranged as three editable CapCut text rows/tracks, not as one mixed caption blob.
- Row 1 is the big hook/dialogue-style line. It can be a created hook such as `푸바오는 자신을 키워준 사육사를 잊지 못했습니다.`; it is not limited to verified source speech.
- Row 2 is the emotion/reaction/situation line, usually parenthesized: `(감정, 상황설명)`.
- Row 3 is the user TTS/narration caption.
- A beat can use one, two, or all three rows. Put each row as its own editable text clip/track segment so the user can move it easily in CapCut.
- Verified source dialogue is separate source-analysis data. If the source actually says something, it may be used in row 1, but row 1 is not automatically or exclusively source dialogue.
- Do not use this as a separate `하단` script layer. It is the visible `중단`/overlay display contract split into three text roles.

Required evidence fields:

```json
{
  "script_aligned_timeline_required": true,
  "script_aligned_timeline_status": "PASS",
  "three_line_text_layout_required": true,
  "three_line_text_layout_status": "PASS",
  "script_aligned_timeline_structure": [
    {
      "script_beat_id": "b01",
      "target_range": "0.000-2.000",
      "display_text_lines": [
        {"line_index": 1, "text": "푸바오는 사육사를 잊지 못했습니다."},
        {"line_index": 2, "text": "(먼저 알아본 듯 다가가는 푸바오)"},
        {"line_index": 3, "text": "중국으로 떠난 푸바오가 한국 사육사를 다시 만난 순간입니다."}
      ],
      "visual_role": "situation_video",
      "voice_audio_role": "caption_voice",
      "tts_visual_fill_status": "PASS",
      "visual_covers_tts_audio": true
    },
    {
      "script_beat_id": "b07",
      "target_range": "12.000-14.000",
      "middle_text": "\"너가 잘못한거 몰라?\"",
      "middle_text_type": "source_speech",
      "display_text_lines": [
        {"line_index": 1, "text": "\"너가 잘못한거 몰라?\""},
        {"line_index": 2, "text": "(운전자가 창문 너머로 따지는 순간)"},
        {"line_index": 3, "text": "사고 뒤에도 말싸움은 멈추지 않았습니다."}
      ],
      "visual_role": "source_speech_video",
      "source_speech_audio_required": true
    }
  ]
}
```

For multi-clip TTS coverage, use `visual_coverage_segments`:

```json
{
  "script_beat_id": "b03",
  "target_range": "4.000-7.200",
  "voice_audio_role": "caption_voice",
  "tts_visual_fill_status": "PASS",
  "visual_coverage_segments": [
    {"video_segment_id": "v03a", "target_range": "4.000-5.500"},
    {"video_segment_id": "v03b", "target_range": "5.500-7.200"}
  ]
}
```

CapCut media and cut-fill rule:

- The original full downloaded source video must be imported into the CapCut project media bin whenever a draft is created. It must be the real full `source.mp4` with an audio stream still present, not a split clip, extracted audio, pre-render, or generated replacement. Record it as `original_source_media`.
- A separate extracted `source_original_audio.mp3` is useful for editable audio tracks, but it does not replace importing the original source video with audio into the media bin.
- The edit content starts at `0.0s`. Do not intentionally place the whole edit around `20s` or leave a leading empty work gap unless the user explicitly requests that for the current draft.
- Default CapCut assembly should keep the original `source.mp4` as the main reusable media and split it inside CapCut by using multiple timeline segments with different `source_timerange` values. Do not pre-render a separate MP4 for every cut by default.
- Pre-render separate clean MP4 clips only when the user explicitly allows it or when CapCut-native source segmentation is truly impossible. If the user must manually stretch cut edges, timing, or source context later, do not pre-render; use `source.mp4` timeline segments.
- If separate MP4 clips are pre-rendered, preserve the original audio stream in each split clip unless the user explicitly asks for silent clips. In review drafts, keep those video segment volumes audible by default so source speech can be checked before TTS mixing.
- Rebuild the CapCut media bin from the actual current assets only: SFX/BGM that are in use, the full original source, and any current split clips. Do not leave stale template media such as old opening voice, old `source_intro_audio_fade`, old SRT, or missing extracted audio in `draft_materials`.
- Default video track layout is two editable source-video rows:
  - `자막영상`: plain `대본`/TTS visual slots. Parenthesized situation/emotion captions may attach here when they support the TTS beat.
  - `상황·화자음성영상`: verified quoted source-speech, original-audio, source situation, and source-emotion slots. Parenthesized situation/emotion captions may attach here when they support the original beat.
- `capcut_timeline_manifest.json` must set `video_track_contract=caption_video_plus_situation_speaker_video` and include a non-empty `video_track_manifest`. Each entry must record `visual_track=caption_video|situation_speaker_video`, `target_start`, `target_end`, and `source_audio_policy`.
- Both video tracks must still use `source.mp4` as the material. Split by `source_timerange` on each segment so the user can extend, trim, or recover surrounding source context directly in CapCut.
- `original_source_media` in the production contract and timeline manifest must point to `source.mp4`, set `imported_to_capcut_media=true`, and set `has_audio_stream=true`.
- If no matching visual exists for a TTS beat, mark the slot as `blank`, `caption_only`, or `neutral` plus `needs_user_fill=true`; do not silently substitute unrelated footage or claim full PASS.
- Default current plain TTS caption position is CapCut UI `Y=-960` (`clip.transform.y=-0.5` in 1080x1920 draft JSON). Apply this only to the `자막영상` / `middle script TTS plain` caption track. Do not force `"화자음성"` or `(상태/감정)` caption tracks to `Y=-960` unless the user explicitly asks.
- Do not place generated `main_*.mp4`, `spare_*.mp4`, or pre-rendered cut files in the active CapCut timeline/media bin unless the user explicitly permits baked clips for that job.
- For each scenario beat, place the best matching visual material over the script beat.
- Default is one matching visual clip per scenario beat.
- Split a scenario beat into 2-3 visual clips only when the beat is too long, the visible person/speaker changes, the action changes, or the caption meaning needs a different matching visual.
- If one clip covers the beat, use crop, scale, pan, or keyframe zoom within that clip instead of forcing extra cuts.
- Match the visual subject to the caption/script subject. If the line is about the man, use the man's shot; if the line is about the woman, use the woman's shot.
- When one scenario beat changes subject, for example man -> woman, split the visual at that subject change and assign the matching source clip to each part.
- If no matching visual can be found, do not force an unrelated clip. Leave that beat as `blank`, `caption_only`, or `neutral`, and mark it as `needs_user_fill=true` so the user can insert the right shot later.
- Reusing a similar source range is allowed when it supports the script beat and the similarity report records the reuse.
- Use crop, scale, pan, keyframe zoom-in/zoom-out, and left/right/up/down framing adjustments to keep the subject centered and the action readable.
- If a source clip is split but not used in the main edit, keep it available for manual editing:
  - put used clips in the main/front assembly order
  - put unused split clips at the back of the timeline, in a disabled/muted spare track, or in a clearly labeled spare media section
  - record those clips as `unused_split_clips`
- Do not discard usable source fragments only because they are not in the first draft. The user may pull them into the edit manually.

Visual crop, subtitle fit, and source-audio constitution:

- If the source video contains top/bottom black bands, burned source captions, channel OCR, source title text, or bottom source credits, remove them from the visible main edit whenever it can be done without losing the main subject. Use crop, zoom, pan, or pre-rendered clean vertical edit clips. Do not leave visible original text bands just because the source file is already 9:16.
- The original full source video must still be imported into the CapCut media bin even when the main edit uses cropped per-beat clean clips.
- Default current 11short middle font size is `10` in middle-only projects unless the user explicitly changes it.
- Default current 11short plain TTS caption position is CapCut UI `Y=-960`. Store it as JSON `clip.transform.y=-0.5` for 1080x1920 projects. This default applies only to our TTS/plain caption track.
- Every middle caption must fit as one readable line. If a middle line overflows left/right at size `10`, split it into sequential shorter middle captions. Do not let CapCut text run outside the frame.
- Verified source speech such as `"주사 맞으실게요"` must be placed as quoted `중단` text with the matching source audio kept on that clip.
- Do not mute the whole edited video. Use per-beat audio:
  - quoted verified source speech: place the matching original source audio as an editable `source original audio needed` audio segment, or keep that clip's source audio audible when no extracted replacement exists
  - plain TTS/narration `중단`: place the user-supplied TTS audio on a separate `tts voice from user SRT` track and mute the active video segment's embedded source audio
  - parenthesized reaction/SFX captions: use source audio only when it carries useful reaction/context; otherwise keep it visual-only
- Do not treat source-video volume ducking as the final audio structure. If the edit has both original speech and our TTS, separate them: `원본-원본음성` beats get source-audio snippets, `수정본-우리 TTS자막` beats get user TTS snippets.
- `중단 TTS 글자만 복사` must include only the plain middle lines intended for generated/user TTS. Exclude quoted source-speech lines when source audio is kept, and exclude parenthesized visual-only captions unless the user explicitly asks to voice them.

Speech timing / STT constitution:

- Default current v5 STT order is: YouTube native captions via `yt-dlp`, local Whisper/faster-whisper/whisper.cpp, then frame-only approximate timing with explicit `stt_status=unavailable`.
- Do not run ElevenLabs/Scribe just because `ELEVENLABS_API_KEY` exists. Use it only when the user explicitly requests ElevenLabs/Scribe for source-dialogue analysis or when a documented job contract says paid external STT is allowed.
- Save STT outputs in the episode work folder as `speech_timeline.json` and `source_speech_transcript.json`. Include segment timestamps and word timestamps when the provider returns them.
- Use the STT timeline as the primary authority for `"..."` verified speaker utterance segments, quoted middle captions, and source-audio cut boundaries.
- Use watch/direct-frame analysis for visual subject/action selection, but snap speech cuts to the STT timing with small editable handles of about 0.15-0.30s unless the user requests exact hard cuts.
- Never write or mirror the raw API key into skill files, reports, CapCut JSON, or handoff folders. Only reference the environment variable name `ELEVENLABS_API_KEY`.
- If paid STT was explicitly requested and fails, fall back to local Whisper/faster-whisper only after recording the failure and cost/status decision.

Mirroring:

- Mirroring is a final user-side operation unless the user explicitly asks Codex to do it.
- Do not require mirroring in any 11short harness or gate.
- Do not mark a draft FAIL only because mirroring has not been applied.

Report wording:

- Production reports must describe the actual scenario-first montage structure: source beat library, scenario timeline, and clip assignments.
- Do not describe a scenario-first project only as `selected_remix_order`.

## Current Completion Report Contract Override v3.0

This section is the latest authority for completed 11short/CapCut production replies. It overrides older final-report blocks that mention `쉼표테그`, `초단위 중단내용+하단내용`, `하단 대본복사용`, or evidence-heavy report stacks as the default user-facing completion format.

When this skill creates or reports a 11short CapCut project, first output a
short required `CapCut 검수` summary, then output the copy-ready final report
together with the CapCut project name in this exact order. This is the final
user-facing report shape:

```text
CapCut 검수
draft_name: {exact_registered_capcut_draft_name}
draft_path: {absolute local CapCut draft folder}
selected_template: {일반템플릿 / 인스타템플릿 / 블랙템플릿 / user-selected template}
openability_gate: PASS / FAIL / WAIT
media_link_gate: PASS / FAIL / WAIT
style_preservation_gate: PASS / FAIL / WAIT
role_track_gate: PASS / FAIL / WAIT
frame_layout_QA: PASS / FAIL / WAIT
harness: analysis={PASS/FAIL/WAIT}, assets={PASS/FAIL/WAIT}, capcut={PASS/FAIL/WAIT}, all={PASS/FAIL/WAIT}

제목
{YouTube Shorts upload title ending with exactly one lowercase #shorts}

내용
{description line 1}
{description line 2}

출처:{source_url}

테그
{tag1},{tag2},{tag3},

상단
{CapCut top title line 1}
{CapCut top title line 2, including color notes such as [노랑] only when needed}

중단
[00:00.000-00:02.800]
감정: {visible middle caption / reaction / plain text}
화자{speaker_name_if_any}:
대본:

[00:03.000-00:05.000]
감정: {visible middle caption / reaction / plain text}
화자{speaker_name_if_any}:
대본:

중단 TTS 글자만 복사
{TTS/voice line 1 only}
{TTS/voice line 2 only}
{TTS/voice line 3 only}

캣컵 복사하기
{exact_registered_capcut_draft_name}
```

Rules:

- This report is mandatory with every completed 11short CapCut project. The CapCut project copy block is not optional.
- The `CapCut 검수` block is mandatory after CapCut draft creation. If any
  required gate is `FAIL` or `WAIT`, state the blocker above the copy-ready
  report and do not describe the project as usable, completed, PASS, or
  upload-ready.
- `캣컵 복사하기` must contain the exact registered CapCut draft name when a draft exists, and the draft name must be inside a Markdown fenced `text` code block so the user can copy it.
- If the CapCut draft is blocked or not created yet, state the blocker above the report and still put the planned draft name under `캣컵 복사하기`.
- `중단 TTS 글자만 복사` must come immediately after the timed `중단` block and before `캣컵 복사하기`.
- The final user-facing report must not append platform copy blocks after `캣컵 복사하기` unless the user explicitly asks for platform-specific upload copy.
- The actual Markdown shape for the two final copy blocks is:

````text
중단 TTS 글자만 복사
```text
{TTS/voice line 1 only}
{TTS/voice line 2 only}
{TTS/voice line 3 only}
```

캣컵 복사하기
```text
{exact_registered_capcut_draft_name}
```
````

- Use `테그`, not `태그` or `쉼표테그`, for this 11short copy-ready report. Tags are comma-separated without spaces and each tag ends with a comma.
- The title must end with exactly one lowercase plural `#shorts`.
- `중단` is the timed visible middle-caption report. Do not add `하단`, `하단 원문`, `하단 대본복사용`, or bottom-caption sections.
- `중단 TTS 글자만 복사` is a copy-only list of the timed `중단` lines that should be spoken by TTS/voice. It is not a separate `하단` or independent TTS script layer.
- Exclude visual-only parenthesized situation captions from `중단 TTS 글자만 복사` by default: `(퍽)`, `(가소롭군)`, `(뭐지..??)`, `(순간 얼어붙음)`.
- Include plain TTS/narration middle lines by default.
- Include quoted speaker/source lines only when that line is explicitly intended for generated TTS/voice. If the original source audio carries the speech, do not duplicate it in TTS copy.
- Include parenthesized lines in TTS only when the user explicitly asks for SFX/reaction captions to be voiced.
- If there is verified source speech, put it in the `화자...:` or `대본:` field only when verified by source audio/subtitle/transcript. If there is no verified speech, leave those fields blank like the example.
- Keep extra technical gate/evidence summaries concise and place them above this
  copy-ready report only when needed. The required `CapCut 검수` block is not
  optional after CapCut draft creation. Do not insert evidence blocks between
  the copy-ready report sections.

## Mandatory Subskill Routing And Visible Board

When this skill is triggered for any 11short source analysis, URL remake, Gemini JSON review, `analysis.json` preparation, assets/SRT/layout work, CapCut draft creation, or final report, treat `watch` and `00script-writer` as mandatory routed subskills even if the user only names `000short-production-agent`.

Before file edits, media generation, API calls, n8n runs, harness runs, or production work, show this compact Korean board to the user:

```text
[11short Routing]
- active skill: 000short-production-agent
- routed skills: watch=WAIT/RUNNING/PASS/SKIP(reason), 00script-writer=WAIT/RUNNING/PASS/BLOCKED
- source analysis mode: Gemini raw / watch direct / Gemini+watch crosscheck
- final authority: Codex watch/direct-frame analysis + shorts_remake_harness.py, not Gemini alone
- target format: youtube_shorts / instagram_reels
- 추천 업로드 채널:
- 추천 템플릿:
- 주제/카테고리 판정:
- 추천 이유:
- 제외/보류 채널:
- 라우팅 확신도:
- next gate:
```

Routing rules:

- `watch` is mandatory for URL, local video, uploaded video, source-analysis review, and Gemini JSON correction requests. Download or locate the source first, then run or inspect watch/direct-frame output before accepting the timeline.
- Gemini is an assistant for raw OCR, speech, and situation extraction. Gemini output alone is never final authority for timestamps, event order, coverage, or CapCut timing.
- If `watch` cannot run, mark `watch=BLOCKED` in the routing board, explain the blocker, and do not call the analysis final.
- `00script-writer` is mandatory before finalizing top title, hook placement, Korean captions, OCR-cover overlays, voice/display text, SRT, upload title, or any script-like visible text.
- The writer pass must visibly check hook strength, first 3-5 second hold, memory anchor, YouTube policy risk, audio-off comprehension, and the random 5-persona readability/retention gate.
- For 11short production, the script/writer gate threshold is 4 of 5 PASS. Do not create screen timing, SRT files, layout files, voice files, or CapCut drafts from a script with fewer than 4 approvals.
- The writer pass must output a copy-ready `final_script_ko` package whenever it analyzes or rewrites a Short's text. Analysis-only requests may skip production files, but must still print the final script unless the user explicitly asks for situation explanation only.
- Do not mark `complete`, `PASS`, `final`, `ready`, or `upload_ready` until every routed skill and required harness gate is PASS, or explicitly `SKIP(reason)` for a question-only task with no production output.

Locked execution order for production requests:

1. Resolve and show `[11short Routing]` with the mandatory channel/template proposal.
2. Intake/download source and preserve source audio when required.
3. Run Gemini raw extraction only as support when useful.
4. Run `watch` or direct-frame crosscheck and make it the timestamp authority.
5. Normalize `analysis.json` with full timeline coverage.
6. Run `00script-writer` design pass for hook, text, captions, retention, and copy-ready final script output.
7. Lock the script with the five writer/persona gate at 4 of 5 PASS.
8. Derive the original-to-remake structure report and big screen timeline from the locked script.
9. Run the YouTube Policy Gate and record its JSON fields.
10. Run audio-off comprehension gate and random 5-persona gate.
11. Run `shorts_remake_harness.py --stage analysis`.
12. Build assets, SRT, overlays, and layout from the locked script and screen plan.
13. Run `shorts_remake_harness.py --stage assets`.
14. Build `render_plan_pre_capcut.json` and complete `production_gate_contract.json`.
15. Run `scripts/validate_production_gate.py` and save `production_gate_result.json`.
16. Build/register CapCut draft only when `production_gate_result.json` is `PASS`.
17. Build `capcut_timeline_manifest.json` from the created draft/timeline.
18. Run `scripts/validate_capcut_timeline_order.py` and save `post_capcut_timeline_gate_result.json`.
19. Run `shorts_remake_harness.py --stage capcut` and `--stage all`, then visual check.
20. Report only the actual PASS/FAIL state.

Every production status report must also show the shared board:

```text
[ 진행판 ]
- n8n 실행:
- 하네스 검증:
- 현재 단계:
- 현재 blocker:
- 다음 조치:

A. n8n 실행
- status:
- last run:
- notes:

B. 하네스 검증
- analysis:
- assets:
- capcut:
- all:
```

For question-only or flow-explanation tasks, do not run production tools unnecessarily. Still state that this is `N/A - explanation only` in the routing board or progress board when the user asks how the pipeline works.

## Super Harness Hard Gates And Scrollback Log

For every 11short remake production task, keep a visible checkpoint log in chat so the user can scroll back and audit the whole process. Update it after each major step; do not wait until the end.

```text
[작업 체크포인트 #{number}]
- active skill: 000short-production-agent
- 현재 단계:
- 지금 하는 일:
- 방금 완료:
- 다음 단계:
- blocker:
- 증거 파일:
- 상태: WAIT / RUNNING / PASS / FAIL / BLOCKED

[000short-production-agent TODO]
- [ ] watch/direct-frame 확인
- [ ] analysis.json 생성/정규화
- [ ] final_script_ko / Tikitaka lock intake
- [ ] render_plan_pre_capcut.json 생성
- [ ] production_gate_contract.json 완성
- [ ] validate_production_gate.py PASS
- [ ] onscreen_ko.srt 생성
- [ ] onscreen_layout.json 생성
- [ ] assets harness PASS
- [ ] CapCut draft 생성
- [ ] capcut_timeline_manifest.json 생성
- [ ] validate_capcut_timeline_order.py PASS
- [ ] capcut harness PASS
- [ ] all harness PASS
- [ ] visual preview 확인
- [ ] 최종 원본대비변경보고서 작성
```

Pre-CapCut production gate:

- Use bundled script: `scripts/validate_production_gate.py`.
- Run it immediately before any CapCut draft creation.
- Save output to `{work}\production_gate_result.json`.
- If the script exits non-zero or `status` is not `PASS`, set CapCut creation to `BLOCKED` and do not call any CapCut factory.
- Never trust `production_allowed` from an input contract. `production_allowed=true` may appear only in `production_gate_result.json` created by the validator.

Required command shape:

```powershell
py -3 {skill_dir}\scripts\validate_production_gate.py "{work}" "{work}\production_gate_contract.json" --out "{work}\production_gate_result.json"
```

The gate must fail when any of these is true:

- In legacy/simple `edit_assembly_mode=order_remix`, `remix_candidates` has fewer than 3 candidate orders.
- In legacy/simple `edit_assembly_mode=order_remix`, `selected_remix_order` is not one of `remix_candidates`.
- In legacy/simple `edit_assembly_mode=order_remix`, `selected_remix_order` equals `original_beat_order` without an explicit approved exception.
- In legacy/simple `edit_assembly_mode=order_remix`, repeated or removed/compressed beats exist without declaration.
- In legacy/simple `edit_assembly_mode=order_remix`, `render_plan_pre_capcut.json` is missing or its actual order differs from `selected_remix_order`.
- In current `edit_assembly_mode=scenario_first_montage`, `source_beat_library`, `scenario_timeline`/`scenario_beats`, or `clip_assignments` are missing.
- In current `edit_assembly_mode=scenario_first_montage`, scenario beats do not identify their visible/timed `중단` text, beat role, and target timing.
- In current `edit_assembly_mode=scenario_first_montage`, clip assignments do not map each scenario beat to either a source range or an intentional `blank`/`caption_only`/`neutral` visual beat.
- In current `edit_assembly_mode=scenario_first_montage`, the render plan still looks like an unassigned `12345` default order instead of a scenario timeline.
- `writer_agent_source` is `INLINE_FALLBACK`, `VISIBLE_WRITER_BATTLE`, or anything other than real agent mode.
- `writer_agent_mode_status` is not `REAL_RUN`.
- `writer_persona_pass_count` is below 4 of 5.
- `script_lock.json` is missing, has no `SCRIPT_LOCK`, or was not generated by a validator.
- `watch_direct_frame_report` is missing or not `PASS`.
- `harness_report_analysis` or `harness_report_assets` is missing or not `PASS`.

Post-CapCut timeline gate:

- Use bundled script: `scripts/validate_capcut_timeline_order.py`.
- Run it after the CapCut draft is created and after `capcut_timeline_manifest.json` is written from the created draft/timeline.
- Save output to `{work}\post_capcut_timeline_gate_result.json`.
- If the post gate fails, `upload_ready=false` and the final report status is `BLOCKED`.
- In legacy/simple `edit_assembly_mode=order_remix`, a `3-preview + 12345` timeline is not accepted unless that exact repeated order was the selected and validated `selected_remix_order`.
- In current `edit_assembly_mode=scenario_first_montage`, the timeline must preserve `scenario_timeline`/`scenario_beats` and `clip_assignments`; it is not validated by `selected_remix_order`.

Required command shape:

```powershell
py -3 {skill_dir}\scripts\validate_capcut_timeline_order.py "{work}" "{work}\production_gate_result.json" "{work}\capcut_timeline_manifest.json" --contract-json "{work}\production_gate_contract.json" --out "{work}\post_capcut_timeline_gate_result.json"
```

For legacy/simple `edit_assembly_mode=order_remix`, the CapCut factory must receive the selected order from `production_gate_result.json`; do not let the factory rebuild default `12345` internally:

```python
gate_result = run_production_gate(work_dir)
create_capcut_draft(job_dir=work_dir, beat_order=gate_result["selected_remix_order"])
```

For current `edit_assembly_mode=scenario_first_montage`, the CapCut factory must receive the scenario timeline and assignments:

```python
gate_result = run_production_gate(work_dir)
create_capcut_draft(
    job_dir=work_dir,
    scenario_timeline=gate_result["scenario_timeline"],
    clip_assignments=gate_result["clip_assignments"],
)
```

Final status rules:

- `production_gate_result.json PASS` permits CapCut creation only.
- `post_capcut_timeline_gate_result.json PASS` plus `capcut/all harness PASS` permits `upload_ready=true`.
- Harness PASS is necessary but not sufficient when either production gate is missing.
- Human-written words such as `SCRIPT_LOCK`, `PASS`, or `upload_ready` are not evidence.

Keep this report block live-updated in every production status reply:

```text
[보고서 초안 업데이트]

원본대비변경요약
- 원본 흐름:
- 최종 흐름:
- 실제 변경된 컷:
- 유지한 컷:
- 제거/압축한 컷:
- 반복 사용한 컷:
- 왜 이렇게 바꿨는지:

일치도 0% 목표 세팅
- 순서 변경:
- 첫 장면 변경:
- 문장 골격 변경:
- 원본 단어 치환:
- OCR/중단 문구 변경:
- 하단 설명 방식 변경:
- 크롭/줌/팬/색보정/BGM/SFX:
- 원본과 여전히 같은 부분:

검수상태
- watch/direct-frame:
- production gate:
- script agent mode:
- SCRIPT_LOCK:
- analysis harness:
- assets harness:
- capcut harness:
- post timeline gate:
- all harness:
- visual preview:
- blocker:
```

## URL-To-CapCut Default Completion Contract

If the user provides a YouTube Shorts, YouTube watch, Instagram Reels, TikTok, or local video URL/path in a 000short/11short context, treat the URL itself as a full production request unless the user explicitly says `분석만`, `검토만`, `프롬프트만`, `JSON만`, `대본만`, or `설명만`.

Default URL deliverable:

- Download or locate the source video.
- Run Gemini only as raw extraction support when useful.
- Run `watch` or direct-frame analysis and make it the timing authority.
- Create normalized `analysis.json`.
- Create `status.json`.
- Create `onscreen_ko.srt` and `onscreen_layout.json` when the production flow uses captions or overlays. Create `guide_ko.srt` only as a clearly marked compatibility artifact when an older helper requires it.
- Create `render_plan_pre_capcut.json`, `production_gate_contract.json`, and `production_gate_result.json`.
- Build/register a visible local CapCut draft/project file.
- Create `capcut_timeline_manifest.json` and `post_capcut_timeline_gate_result.json`.
- Run `shorts_remake_harness.py --stage analysis`, `--stage assets`, `--stage capcut`, and `--stage all`.
- Report the CapCut draft name/path, original-to-remake changes, production gate state, post timeline gate state, and actual PASS/FAIL state.

Stopping after download, Gemini JSON, frame analysis, watch notes, or `analysis_candidate_direct.json` is not acceptable for a URL production request. Those are intermediate states only.

If the CapCut project cannot be created, do not silently stop at analysis. Mark the task `BLOCKED`, show the `[ 진행판 ]`, name the missing file/tool/gate, and state the exact next command or fix needed.

For a URL-only request, the current default `next gate` in `[11short Routing]` is `Codex source_evidence 생성` after source download. The staged intake contract below is legacy/opt-in only and must not be used unless the user explicitly asks to use the external GPT-project handoff.

## Legacy URL-Only Staged Intake Contract (Opt-In Only)

When the user explicitly says they are using the old external GPT-project handoff, and provides only a YouTube Shorts, YouTube watch, Instagram Reels, TikTok, or local video URL/path in a 000short/11short production context, assume the user intends Shorts production. Do not use this legacy flow for ordinary URL-only factory runs.

Run this order:

1. Start `000brainstorm` as the intent gate.
2. Download or locate the source video immediately and preserve it as the production source (`source.mp4` when creating a work package).
3. Show `[11short Routing]` and the shared progress board with `URL/source` marked as `PASS`, `WAIT`, or `BLOCKED`.
4. Only in this explicit legacy flow, accept these staged production inputs if the user provides them:
   - external input 1: user-provided Gemini analysis (`1번 제미나이 분석본`)
   - external input 2: GPT1 shorts-script analysis
   - external input 3: GPT2 sentence conversion result
   - external input 4: GPT3 Marahagi/policy review
5. After all four inputs are received, ask the target format question:
   - `제작 형식 선택해주세요.`
   - `1. 인스타`
   - `2. 기본`
6. If the user chooses `1. 인스타`, set `target format: instagram_reels` and follow `11short/INSTAGRAM_LAYOUT_CONTRACT.md`.
7. If the user chooses `2. 기본`, use the CapCut preset/template `일반템플릿` and follow the normal 11short layout.
8. Current template gate: when the user says only `만들어`, `프로젝트까지`, `쇼츠공장 돌려`, or otherwise asks for generic 11short production without naming a template, ask which CapCut preset/template to use before creating the draft. Offer `일반템플릿`, `인스타템플릿`, or a user-named future template such as `정치템플릿`. Do not assume Instagram.
8. Run final intake verification before production:
   - source video is present or the source blocker is explicit
   - Gemini raw is treated as observation only, not final authority
   - GPT1 structure/script analysis is considered as direction, not final authority
   - GPT2 sentence conversion is considered as rewrite history
   - GPT3 Marahagi/policy review is considered as the latest text and safety review
   - verified real dialogue is not rewritten inside quotation marks unless watch/direct-frame confirms it
   - invented dialogue is removed or converted to situation captions
   - audio-off comprehension, YouTube policy, and persona/readability gates are ready to run
9. Only after the final intake verification should production continue to watch/direct-frame analysis, normalized `analysis.json`, SRT/layout/audio files, CapCut draft creation, and harness gates.

If any staged input is missing, ask only for the next missing input. Do not ask for all four at once unless the user explicitly requests the full template.

If the user already provides all four inputs in one message, do not ask again. Summarize which inputs were received, then ask only the target format question.

In this staged flow, `00-tikitaka` is skipped by default because the script has already been produced in the GPT project. Use `00-tikitaka` only if the user explicitly asks to rewrite the script, rerun Tikitaka, or generate a new script from raw Gemini/comments.

## User-Facing Tone Rule

When reporting to the user, use Korean formal polite speech ending in `-습니다` / `-합니다`.

- Do not use 반말, 명령조, or casual endings in assistant updates, final reports, checklists, status messages, or error reports.
- Use direct but respectful engineering language: `확인했습니다`, `수정했습니다`, `진행하겠습니다`, `FAIL입니다`, `PASS입니다`.
- This user-facing tone rule does not automatically change visible Shorts captions or character dialogue. Caption tone still follows the content strategy unless the user explicitly asks to make the video captions formal.

## Global Gates

Hard additions for 11short remakes:

- The viewer must understand the Short with the original/source audio muted. The audio-off comprehension gate blocks final analysis, captions, overlays, voice, and CapCut generation.
- When `00script-writer` is used and real sub-agents are available, the random 5-persona gate must use real sub-agents. `local simulation` is not acceptable when `spawn_agent` or an equivalent sub-agent tool is available.
- A harness PASS is not enough if the audio-off gate or real persona gate is missing.

This skill obeys the 11utube global gates in `11utube/00_TOP_LEVEL_DIRECTIVE.md`.

- Any new narration/caption script, serious rewrite, or final script approval must pass `00script-writer` 작가모드, the YouTube Policy Gate, and the visible random 5-persona retention/readability gate with 4 of 5 PASS before it is called final.
- Any source analysis, assets, TTS, SRT, CapCut, render, upload package, or final report must show the shared `A. n8n 실행` / `B. 하네스 검증` board adapted to the 11short phase map.
- If n8n is not used or unreachable, mark it as `WAIT - local run`; never fake a pass.
- `shorts_remake_harness.py` is the PASS/FAIL authority and blocks the next stage when it fails.

## Portable Paths

Use `${env:UTUBE_ROOT}` as the 11utube root on every PC. If it is not set, most repo scripts fall back to their own file location, but shared office setups should set it once:

```powershell
$env:UTUBE_ROOT = "$env:UTUBE_ROOT"
$env:WORKSPACE_ROOT = "$env:WORKSPACE_ROOT"
```

Do not hardcode a machine-specific user home path or drive alias in new scripts or examples. Use `${env:UTUBE_ROOT}\...` for paths under `11utube`.

## Skill Folder Contract

New work folders made by this skill must be created under:

```text
${env:UTUBE_ROOT}\11short\000short-production-agent\episodes\{date-profile}
```

Keep shared scripts, harnesses, templates, BGM, and tools at `${env:UTUBE_ROOT}\11short`. Do not create new episode work directly under `${env:UTUBE_ROOT}\11short`.

## OneDrive Handoff Package Mode

Use OneDrive handoff packages when 11short work is split between a designer machine and a project-writer machine, such as Mac mini analysis/assets on one side and Windows CapCut draft creation on the other. The shared source of truth is the handoff package, not a live CapCut draft folder.

Canonical root:

```text
${env:UTUBE_ROOT}\11short_handoff
```

Each package must use this structure:

```text
${env:UTUBE_ROOT}\11short_handoff\{episode_id}\
  handoff_manifest.json
  work\
    source.mp4
    analysis.json
    onscreen_ko.srt
    onscreen_layout.json
    render_plan_pre_capcut.json
    production_gate_contract.json
    production_gate_result.json
    capcut_timeline_manifest.json
    post_capcut_timeline_gate_result.json
    source_original_audio.mp3
    status.json
  capcut_jobs\
    macmini\
    home_windows\
    office_windows\
```

The designer role stops after `analysis` and `assets` PASS, writes all portable work files under `work\`, and sets `handoff_manifest.json` status to `ready_for_capcut`. The project-writer role scans handoff packages, locks one package, creates a fresh local CapCut draft from the package files, runs `capcut` and `all` harness gates, then updates the manifest.

Do not copy a live CapCut draft as the canonical cross-machine source unless the user explicitly asks for recovery or forensic inspection. CapCut draft roots are machine-local and may contain local paths, cache state, platform-specific metadata, or app index state.

Tikitaka production input packages are valid earlier-stage handoffs. When a package has `tikitaka_input_manifest.json` or `work\status.json` with `package_type=tikitaka_production_input`, do not require `handoff_manifest.json`, `guide_ko.srt`, `onscreen_ko.srt`, `onscreen_layout.json`, or `voice_body.txt` at intake. Treat it as a pre-production package from `00-tikitaka`: validate `work\final_script_ko.txt`, secure `source.mp4` or `source_url`, run the Tikitaka intake gate, then create or normalize the downstream production files before CapCut.

Tikitaka input package shape:

```text
${env:UTUBE_ROOT}\11short_handoff\{episode_id}\
  tikitaka_input_manifest.json
  work\
    final_script_ko.txt
    status.json
    analysis_raw_gemini.json
    analysis.json
    source.mp4
    source_url.txt
    comments_top_liked.json
    audience_signal_analysis.md
    tikitaka_decision_log.md
    production_gate_contract.json
    script_lock.json
  capcut_jobs\
    macmini\
    home_windows\
    office_windows\
```

For Tikitaka packages, `final_script_ko.txt` is the text authority. `analysis_raw_gemini.json` and `analysis.json` are observation aids only; verify timing, speech, OCR, and scene order with watch/direct-frame checks before writing SRT, voice text, layout, or CapCut files.

`handoff_manifest.json` must use relative package paths and include these fields:

```json
{
  "package_version": "11short_handoff_v1",
  "status": "ready_for_capcut",
  "created_by": "macmini",
  "created_at": "",
  "source_url": "",
  "episode_id": "",
  "draft_name": "",
  "work_dir": "work",
  "paths_are_relative": true,
  "analysis_pass": true,
  "assets_pass": true,
  "required_files_ok": true,
  "production_gate_pass": false,
  "post_capcut_timeline_gate_pass": false,
  "locked_by": null,
  "locked_at": null,
  "lock_reason": null,
  "capcut_created": false,
  "capcut_created_by": null,
  "capcut_created_at": null,
  "capcut_draft_name": null,
  "capcut_harness_pass": false,
  "all_harness_pass": false,
  "upload_ready": false,
  "uploaded": false,
  "required_files": [],
  "notes": ""
}
```

Allowed `status` values:

```text
drafting
analysis_ready
assets_ready
ready_for_capcut
capcut_building
capcut_created
capcut_harness_pass
all_harness_pass
upload_ready
uploaded
blocked
```

Allowed machine names for `created_by`, `locked_by`, and `capcut_created_by` are `macmini`, `home_windows`, `office_windows`, and `unknown`.

Locking is per episode package. Before building a CapCut draft, set `locked_by`, `locked_at`, `lock_reason`, and status `capcut_building`. Do not overwrite a non-stale lock unless the user explicitly requests force takeover. Release or update the lock after failure or completion while preserving unrelated manifest fields.

When the user asks to check upload/build status, scan `${env:UTUBE_ROOT}\11short_handoff\*\handoff_manifest.json`, validate `package_version` or `schema_version`, `status`, required files, lock fields, `analysis_pass`, `assets_pass`, `production_gate_pass`, and `post_capcut_timeline_gate_pass` when a draft exists, then report buildable packages first. A package is buildable only when it is not locked, required files exist, analysis/assets are PASS, and pre-CapCut gate inputs are present. A package is upload-ready only when post-CapCut timeline gate, capcut harness, and all harness are PASS.

When the user asks to make a specific project file from handoff, acquire that package lock first, validate the pre-CapCut gate, create/register the local CapCut draft from `work\` files only after PASS, then validate the post-CapCut timeline gate and harnesses:

```powershell
py -3 {skill_dir}\scripts\validate_production_gate.py "{work}" "{work}\production_gate_contract.json" --out "{work}\production_gate_result.json"
py -3 ${env:UTUBE_ROOT}\11short\shorts_remake_harness.py "{work}" --stage capcut --draft-name "{draft_name}"
py -3 {skill_dir}\scripts\validate_capcut_timeline_order.py "{work}" "{work}\production_gate_result.json" "{work}\capcut_timeline_manifest.json" --contract-json "{work}\production_gate_contract.json" --out "{work}\post_capcut_timeline_gate_result.json"
py -3 ${env:UTUBE_ROOT}\11short\shorts_remake_harness.py "{work}" --stage all --draft-name "{draft_name}"
```

Then update `production_gate_pass`, `capcut_created`, `capcut_created_by`, `capcut_created_at`, `capcut_draft_name`, `post_capcut_timeline_gate_pass`, `capcut_harness_pass`, `all_harness_pass`, and `upload_ready` according to the actual results. Never mark `upload_ready` when the pre-gate, post-gate, CapCut harness, final harness, or visual preview failed.

## Required Context

Before planning, reviewing, editing, or creating a CapCut draft, read these files when present:

```text
${env:UTUBE_ROOT}\AGENTS.md
${env:UTUBE_ROOT}\11short\agent.md
${env:UTUBE_ROOT}\11short\SHORTS_REMAKE_CONTRACT.md
${env:UTUBE_ROOT}\11short\GEMINI_SHORTS_ANALYSIS_PROMPT.md
${env:UTUBE_ROOT}\11short\GEMINI_YOUTUBE_MASTER_ANALYSIS_PROMPT.md
${env:UTUBE_ROOT}\11short\README.md
```

Read `${env:UTUBE_ROOT}\11short\supertone_11short_tts.py` and `${env:UTUBE_ROOT}\video\SUPERTONE_API_KEY_LOCATION.md` only when the user explicitly requests voice generation. Do not check Supertone balance or key setup for default 11short remake work.

## Korean Encoding Discipline

Always read and write Korean production documents as UTF-8. In PowerShell, set `$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()` before reading Korean files, and use `Get-Content -Encoding UTF8` for Markdown, JSON, SRT, and prompt files. In Python subprocesses, set `PYTHONIOENCODING=utf-8`.

Do not treat unreadable Korean as acceptable terminal display noise. First re-read the file with UTF-8. If the stored text itself is still unreadable after that, rewrite the affected user-facing labels and instructions in clean Korean before continuing.

## Current Production Defaults

- Default style/factory reference: when it exists, use the local CapCut draft `$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\0613 FIRE` as the base production reference. It is the current standard for bars, text tracks, effects, motion defaults, source audio, BGM, and text-only structure.
- If calling `capcut_factory_profile.py` manually, pass `--factory "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\0613 FIRE"` unless the user explicitly asks for another reference or the draft is missing.
- Title style must be more editorial and emotional than a short label. Prefer two-line top titles when they clarify the hook, e.g. `진정한 영웅\n이웃집 아저씨`, not only `이웃영웅`.
- Prefix the CapCut top title with the matching lane marker when the lane is clear: `(감동)` for emotional/support/recovery/help clips, and `난감_` for prank, awkward, embarrassment, or chaotic comedy clips.
- Upload titles must be spoken hook titles, not summary labels. For food or reaction clips, prefer direct viewer language such as `자 1000칼로리 들어갑니다` over tidy labels like `기름빵 한 입에 끝나는 맛`.
- The first visible seconds should show the strongest money-shot moment. If the payoff is later in the source, pull a 0.5-2.0 second preview to the front, then return to the chronological flow.
- Dense text is allowed. Do not treat many bottom captions or middle overlays as a problem when they help the viewer understand the video by reading only.
- Preserve as much useful Gemini analysis as possible in visible text: visible OCR translation, action cause/result, emotional beat, reversal, payoff, warnings, and context. Split into more timed captions instead of deleting meaning.
- Do not make a short-summary version by default. Produce a detailed editable draft; the user will cut excess text during editing.
- Current text layout lock: top title uses CapCut UI Y `+1300`, font size `15`; middle explanatory text uses the user-selected one-line emphasis style with Glow and Shadow both enabled; bottom yellow captions use CapCut UI Y `-1400`, font size `15`.
- Middle text must be one line. Use only the user-approved center emphasis presets/styles for this job; rotate the selected pink/yellow/green-style looks when available. If a middle line does not fit, shorten it instead of splitting it into two lines.
- Bottom captions are usually two lines and should follow the narration/scenario. They must explain the current visual beat or reversal; avoid weak invented captions that are not grounded in visible action, source speech, or reaction.
- For broad upload descriptions, summarize the whole clip's setup, repeated actions, audience reaction, and payoff. Do not describe only one moment. Always include `출처:{url}` in the `내용` block.

## Shared SFX Library

The reusable 11short SFX library is:

```text
${env:UTUBE_ROOT}\22factory_20260628\00_asset_tools\first\marahagi_sfx
```

Use it when the user asks for effect sounds, comedic beats, punch hits, transitions, surprise sounds, water/liquid sounds, UI alerts, or when Tikitaka provides optional SFX cue notes.

Rules:

- Treat the OneDrive `22factory_20260628\00_asset_tools\first\marahagi_sfx` folder as the shared source for reusable Marahagi/Shorts Academy SFX files.
- Do not edit CapCut's global sound-effect database. Register selected SFX inside the local CapCut draft as separate audio materials/tracks.
- When SFX is used, also add the selected SFX files to the local CapCut project's media/material bin whenever the draft schema allows it, so the user can reuse them manually from the media panel.
- Record selected SFX as both:
  - `sfx_timeline`: exact placed SFX cues on the timeline
  - `sfx_media_bin`: selected SFX files imported/registered in project media for manual reuse
- If a selected SFX cannot be added to the media bin because of a draft-schema limitation, still place it on the audio track and record `sfx_media_bin_status=TRACK_ONLY_SCHEMA_LIMIT`.
- Keep SFX optional unless the user explicitly asks to insert them. SFX must not mask source speech or required narration.
- If adding SFX to a draft, re-run the `capcut` and `all` harness gates and do a visual/audio preview check.

## Scenario-First Remake Rule

The first creative decision is the source video's story frame, not the text style.

- Inspect source audio, captions, OCR, visible action, and reactions before writing.
- Classify the source country/culture lane before writing: `한국`, `일본`, `미국`, or `기타/불명`. Use visible language, location signals, platform metadata, comments, and cultural objects. Do not overclaim when uncertain.
- Classify the genre lane before writing: comedy, variety, food/process, animal, rescue_emotion, relationship/drama, incident_reversal, information_explainer, music/dance, or other.
- Check whether the people in the video have direct actor/character speech. This is separate from music, narration added by the uploader, and source BGM.
- If direct actor speech exists, preserve the meaning and naturally paraphrase/replace words as much as possible. Do not cover it with unrelated narration at the same moment.
- If no direct actor speech exists and there is no source narration, set `creative_seasoning_allowed=true` and use our Korean narration, middle beats, and subtitle pressure to season the video.
- Creative seasoning is allowed only within visible truth: no fake diagnosis, fake relationship, hidden dialogue, guaranteed result, or offscreen backstory.
- The original flow must be split into a detailed `source_beat_library` before caption writing. A simple numbered order such as `12345 -> 51234` is only a legacy/simple remix shortcut, not the default CapCut assembly method.
- Treat GPT/Gemini structure recommendations as macro flow guidance. The production agent must still use `watch`/direct-frame analysis to split the actual source into small reusable visual, dialogue, reaction, OCR, and payoff beats before building the CapCut draft.
- The final flow is a `scenario_timeline` with `clip_assignments`: important video, blank/caption-only TTS space, context video, reaction video, payoff video, and any other needed edit beat.
- Set the target script/caption duration to 90% of source duration. Example: if the source is 40 seconds, the text/narration target is 36 seconds. Keep the video length as needed, but avoid writing narration that fills 100% of the source.
- Decide the frame: mistaken assumption, reaction comedy, emotional reveal, prank, comparison, information surprise, rescue, or another concrete mode.
- If the frame is ambiguous, show 2-3 possible readings and recommend one before producing. If the frame is obvious, state the selected frame and proceed.
- Build a new Korean scenario from the source meaning. Change sentence order, word choice, rhythm, and framing so it does not overlap the original wording.
- Do not infer sensitive conditions as fact from appearance. Use uncertainty wording such as `도움이 필요한 줄`, `못 움직이는 줄`, or `다들 착각함` unless the source explicitly states the condition.
- Before writing captions, decide the source's understanding route: `text_dialogue_dependent`, `action_intuitive`, `drama_dialogue`, `comment_meme`, `information_explainer`, `rescue_emotion`, `incident_reversal`, or `process_change`.
- State the selected route briefly before production. Ask the user only when the emotional lane is genuinely ambiguous, such as funny vs. emotional vs. patriotic vs. satisfying, when cultural meaning is unclear, when comment reactions may be more important than the video itself, or when sensitive interpretation risk exists.
- The final production concept must include:
  - `source_country_ko`
  - `genre_lane_ko`
  - `source_actor_voice_exists`
  - `source_voice_strategy`
  - `creative_seasoning_allowed`
  - `source_segment_map`
  - `source_beat_library`
  - `edit_assembly_mode=scenario_first_montage`
  - `scenario_timeline` or `scenario_beats`
  - `clip_assignments`
  - `original_source_media`
  - `original_source_media.has_audio_stream=true`
  - `timeline_content_start_sec=0.0`
  - `script_aligned_timeline_required=true`
  - `script_aligned_timeline_status=PASS`
  - `script_aligned_timeline_structure`
  - `three_line_text_layout_required=true`
  - `three_line_text_layout_status=PASS`
  - `middle_text_track_order_top_to_bottom=["tts","source_speech","situation_emotion"]`
  - `video_track_order_top_to_bottom=["caption_video","situation_speaker_video"]`
  - `tts_visual_fill_required=true`
  - `audio_normalization_required=true`
  - `audio_normalization_status=PASS`
  - `unused_split_clips`
  - `framing_adjustments`
  - `selected_remix_order` only for legacy/simple `order_remix`
  - `target_total_duration_sec`
  - `target_script_duration_sec`
  - `story_understanding_route`
  - `story_frame_ko`
  - `voice_script_ko`
  - `top_title_text`
  - `middle_one_line_beats`
  - `middle_tts_copy_lines`
  - `cut_plan_reason_ko`

## Source Understanding Route Rule

Classify every source by where the viewer gets meaning before deciding the caption strategy.

- `text_dialogue_dependent`: foreign-language captions, interviews, film/variety explanations, news, or any clip where the viewer is lost without reading/translating. Timed middle captions carry the key translation, interpretation, or situation beat.
- `action_intuitive`: Instagram-style action, mime, prank, fail, animal behavior, or any clip that is funny even with no language. Do not over-translate. Use timed middle captions or caption-only scenario beats to add a hooked situation read.
- `drama_dialogue`: people talking, relationship conflict, family emotion, staff/customer scenes, or any clip where dialogue plus relationship context matters. Use dialogue subtitles plus our situational explanation. Keep speaker intent clear.
- `comment_meme`: celebrity, film/game meme, viral comment reaction, or any source where comments are the payoff. Middle overlays should show comment text or translated comment beats. Bottom captions explain why the comments are exploding.
- `information_explainer`: fact, technique, history, finance, tech, or life-tip clips. Do not invent claims. Preserve source meaning, uncertainty, and source lines.
- `rescue_emotion`: animal rescue, family love, recovery, adoption, elder/child emotion. Use restrained emotional captions; avoid cheap overstatement.
- `incident_reversal`: sudden stand-up, fall, near miss, reveal, mistaken assumption, or danger/reversal timing. Cut precisely at the transition and make the first 2-3 seconds preview the payoff or contradiction.
- `process_change`: before/after, cleaning, restoration, cooking, repair, makeover. Compress the middle process; make before/after contrast the anchor.

Default autonomy:

- If one route is obvious, choose it and proceed.
- If two routes are viable, recommend one and continue unless the choice changes the channel tone or safety risk.
- Ask the user before production when the same source can reasonably become two different products, for example `감동` vs `웃김`, `댓글반응` vs `영상 자체`, or `국뽕` vs `정보형`.

Record the choice in `analysis.json` or `status.json`:

```json
{
  "source_country_ko": "한국/일본/미국/기타/불명",
  "source_country_evidence_ko": "",
  "genre_lane_ko": "",
  "genre_lane_reason_ko": "",
  "source_actor_voice_exists": false,
  "source_narration_exists": false,
  "source_voice_strategy": "actor_voice_paraphrase / creative_seasoning_narration / source_audio_locked",
  "creative_seasoning_allowed": true,
  "creative_seasoning_reason_ko": "",
  "source_segment_map": ["1=도입", "2=상황", "3=충격", "4=점층", "5=payoff"],
  "edit_assembly_mode": "scenario_first_montage",
  "source_beat_library": [
    {
      "beat_id": "S1",
      "source_range": "00:00.000-00:02.400",
      "beat_role": "context_video",
      "summary_ko": "원본에서 상황을 보여주는 짧은 재료 컷"
    }
  ],
  "scenario_timeline": [
    {
      "scenario_beat_id": "B1",
      "target_range": "00:00.000-00:03.000",
      "beat_role": "hook_visual",
      "middle_text": "첫 장면에서 바로 멈추게 만드는 중단 문구",
      "middle_text_type": "tts_script",
      "include_in_tts": true,
      "text_color_role": "white"
    },
    {
      "scenario_beat_id": "B2",
      "target_range": "00:03.000-00:05.500",
      "beat_role": "caption_only",
      "middle_text": "(퍽)",
      "middle_text_type": "sfx_caption",
      "include_in_tts": false,
      "text_color_role": "green_effect"
    }
  ],
  "clip_assignments": [
    {
      "scenario_beat_id": "B1",
      "source_beat_id": "S3",
      "source_range": "00:09.500-00:12.000",
      "target_range": "00:00.000-00:03.000",
      "beat_role": "hook_visual"
    },
    {
      "scenario_beat_id": "B2",
      "asset_type": "caption_only",
      "target_range": "00:03.000-00:05.500",
      "beat_role": "caption_only"
    }
  ],
  "selected_remix_order": "legacy/simple order_remix only",
  "source_duration_sec": 40.0,
  "target_total_duration_sec": 33.5,
  "same_duration_exception_reason": "",
  "target_script_duration_sec": 36.0,
  "target_script_duration_ratio": 0.9,
  "timeline_content_start_sec": 0.0,
  "original_source_media": {
    "path": "source.mp4",
    "imported_to_capcut_media": true,
    "has_audio_stream": true
  },
  "script_aligned_timeline_required": true,
  "script_aligned_timeline_status": "PASS",
  "three_line_text_layout_required": true,
  "three_line_text_layout_status": "PASS",
  "middle_text_track_order_top_to_bottom": ["tts", "source_speech", "situation_emotion"],
  "video_track_order_top_to_bottom": ["caption_video", "situation_speaker_video"],
  "tts_visual_fill_required": true,
  "script_aligned_timeline_structure": [
    {
      "script_beat_id": "B1",
      "target_range": "00:00.000-00:03.000",
      "display_text_lines": [
        {"line_index": 1, "text": "첫 장면에서 바로 멈추게 만드는 문구"},
        {"line_index": 2, "text": "(상황/감정 설명)"},
        {"line_index": 3, "text": "TTS 자막 문장"}
      ],
      "visual_role": "situation_video",
      "voice_audio_role": "caption_voice",
      "tts_visual_fill_status": "PASS",
      "visual_covers_tts_audio": true
    }
  ],
  "audio_normalization_required": true,
  "audio_normalization_status": "PASS",
  "audio_normalization_method": "ffmpeg_loudnorm",
  "normalized_audio_assets": [
    {"role": "source_speech", "path": "source_original_audio_normalized.mp3"},
    {"role": "user_tts", "path": "voiceover_body_normalized.mp3"}
  ],
  "unused_split_clips": [
    {
      "source_beat_id": "S4-unused-tail",
      "source_range": "00:13.500-00:15.000",
      "reason_ko": "첫 조립에는 안 썼지만 사용자 수동 편집용으로 뒤에 보관"
    }
  ],
  "framing_adjustments": [
    {
      "scenario_beat_id": "B1",
      "adjustment_ko": "손가락과 총알이 중심에 오도록 확대 후 약간 우측 이동"
    }
  ],
  "story_understanding_route": "",
  "route_decision_reason_ko": "",
  "user_confirmation_needed": false,
  "user_confirmation_reason_ko": ""
}
```

## Hooked Caption Writing Rule

The default caption mode is `hooked_interpretation`, not safe explanation. Captions must make the viewer feel the situation, not merely label it.

- Bottom yellow captions are the hooked read of the current beat: reversal, viewer reaction, contradiction, escalation, or payoff. They should be understandable with audio off, but they should not read like a dry summary.
- Middle text is the punch line, comment reaction, core contradiction, or decisive translation. It must not simply repeat the bottom caption. Keep it one line unless the user explicitly requests English/Korean two-line comment text.
- For text/dialogue-dependent sources, translation accuracy is the first priority, but the Korean line should still be phrased like a watchable hook.
- For action-intuitive sources, do not explain the obvious action. Add the audience's funny interpretation.
- Weak captions such as `댓글창이 마크로 가득했습니다`, `아이가 간식을 건넸습니다`, or `무도 기억이 뒤에서 나왔습니다` are rewrite candidates unless the user explicitly asks for plain explanation.
- Preferred captions look like `닭 한 마리에 댓글창 폭주`, `현실 닭은 아직 상황 모름`, `간식 하나에 예능 본능 발동`, or `근데 이 형 기억력도 진짜임`.
- When the caption feels flat, generate three alternatives before using it: `A안 안전설명형`, `B안 웃긴훅형`, `C안 강한밈형`. Default to `B안 웃긴훅형`.

Record this in `analysis.json` or `status.json`:

```json
{
  "caption_hook_mode": "hooked_interpretation",
  "bottom_hook_strategy_ko": "",
  "middle_hook_strategy_ko": "",
  "flat_caption_rewrite_complete": true
}
```

## Three-Layer Shorts Script Rule v1.4

Use this rule before writing or converting 11short captions, overlays, TTS text, or CapCut handoff notes. A remake script is not a single caption list. It is a three-layer package.

```text
[Top] fixed title
[Middle] timed situation, emotion, state, environment, and useful character speech
[Bottom] TTS/narrator situation script
```

First classify the source by how much the viewer understands from the visual alone:

```text
Class A: visually self-explanatory
- The viewer understands the main action within 5 seconds without captions.
- Examples: animals, physical comedy, visual surprise, process/result clips, paper ATM money reveal.
- Music/source audio may carry the mood. Bottom TTS stays minimal.
- Bottom TTS target: 180-220 Korean chars per minute, excluding spaces.

Class B: context-required
- The viewer needs situation, rules, relationship, or stakes explained to feel the hook.
- Examples: Japanese variety games, sudden combat knockdowns, news/incident context, emotional backstory, dialogue-led clips.
- Bottom TTS carries the story logic. Music is secondary.
- Bottom TTS target: 280-320 Korean chars per minute, excluding spaces.
```

Top fixed title:

- Keep it visible through the video unless the user says otherwise.
- Prefer two lines or fewer.
- It must be the hook object, person, contradiction, or promise, not a file label.
- Use the user's declaration-hook style when possible: `여기 ... 있습니다`, `나는 ...`, `총성 한 발`, `주차 1미터`.

Middle timed situation layer:

- This layer is not the full narration. It shows what the viewer should feel or notice now.
- Include useful actual source speech in double quotes: `"카드!! 카드!!"`.
- Include emotion/state/environment in short text or parentheses: `(가족 전원 환호)`, `2번 버튼이 박살남`, `키패드 소리까지 진짜 같음`.
- Preserve source dialogue that triggers an action, reveals the turn, or carries emotion. Drop or compress meaningless numbers/noise.
- Do not repeat the bottom line unless the repeated wording is intentionally used as a punch line.

Legacy bottom TTS/narrator layer archive - do not use for current v5 jobs:

- Current v5 jobs do not have a separate `하단` or bottom narrator layer.
- The timed `중단` layer is the visible caption authority and, when TTS is requested, the TTS source.
- Keep this older section only as historical reference for old drafts that already contain bottom captions.

Legacy bottom first-line anchor hook rule v1.8 - superseded by v5:

- The first bottom TTS line is the win-or-lose hook sentence. Treat it as the script's memory anchor, not as a normal intro.
- Spend the most writing effort on this one line before drafting the rest of the bottom script.
- It must carry one concrete anchor: person, object, number, place, contradiction, irreversible action, or visible problem.
- Do not apply the five-candidate wait gate in current v5 factory jobs. Draft `상단` and timed `중단` directly from evidence and the user's selected mode.
- Do not draft or require `하단` or `하단 원문` in current v5 jobs.
- The five candidates should be only the first bottom line candidates, not five full script versions.
- Prefer a declarative one-line hook that feels like a story already started: `나는 사도세자의 아들이다`, `주차장 1미터 움직였는데 300만원을 냈습니다`, `강아지가 주인을 맥이기 시작했습니다`.
- The first line should usually avoid generic lead-ins such as `지금부터 보여드리겠습니다`, `이 영상은`, `여기 보시면`, `한번 보세요`, or `도대체 뭘 하는 걸까요`.
- For source-remake Shorts, the first line must be grounded in the strongest visible or source-supported thing. Do not use a clever interpretation if the source does not visibly support it.
- For very short Class A clips, the first bottom line can be the only full sentence before the payoff. The remaining lines may be sparse.
- If the first bottom line is weak, do not call the script pass complete. Rewrite the first line before judging the rest.

First-line test:

```text
Can the viewer remember this one sentence after the Short ends?
Does it contain the single most important visible anchor?
Does it make the next visual beat necessary?
Could it work as the opening sentence if all other captions were removed?
```

Required first-line choice format:

```text
하단 첫마디 후보 5개
1. ...
2. ...
3. ...
4. ...
5. ...

My recommendation: ...
Reason: ...
Your choice:
1
2
3
4
5
```

Source dialogue handling:

```text
1. Information/action cue -> preserve or paraphrase visibly.
2. Character emotion/comedy -> preserve when it improves warmth, tension, or payoff.
3. Ambience/cheer/laughter -> usually preserve as source audio or short middle emotion.
4. Meaningless numbers/noise -> drop unless it proves realism or setup.
```

Middle bracket reaction caption system v1.7:

Use this inside the `중단` layer for remix, variety, sports, comedy, animals, everyday surprise, and other fast reaction Shorts. This is the user's bracket caption system.

```text
( ... ) = free creative zone: emotion, situation, state, viewer reaction, timing, impact, comment-code, sound effect, or tone shaping.
" ... " = truth zone: actual words heard in the source video, source narrator, caster, or on-camera person. Keep the wording matched to the source speech; do not freely rewrite it.
Plain text = avoid in middle unless the line is a very short label. Prefer parentheses for creative middle situation captions.
```

The middle layer should alternate bracket reaction captions and quoted source speech when both exist:

```text
(권희동의 2타점 적시타!!)
(멘탈이 서서히 나가는데...)
"코치: 의지야 바꿀게"
(짜증을 내더니)
(퍽!!)
(코치를 밀침 ㄷㄷ)
```

Middle bracket functions:

- React on behalf of the viewer: `(당황;;)`, `(아니 벌써??)`, `(ㄷㄷ)`, `(ㅋㅋ)`.
- Use direct emotion words when useful: `(충격;;)`, `(분노 폭발)`, `(짜증을 내더니)`, `(할 말을 잃은 감독)`.
- Mark timing and escalation: `(그리고 다음 타자...)`, `(그러자 3회인데)`, `(결국...)`.
- Add impact with short sound/impact text: `(!!!!)`, `(퍽!!)`, `(쾅!!)`.
- Use comment/audience codes when they fit the source: `(이정도면 카이스트 ㄷㄷ)`, `(나라사랑카드 ㅋㅋ)`.
- Keep each middle beat short enough to read quickly. Middle is reaction and live interpretation, not bottom narration.

Truth/free-zone rule:

```text
Quoted speech = trust. It must match source audio/meaning and should not be invented for remix flavor.
Bracket captions = differentiation. They can be rewritten freely to choose curiosity, emotion, comedy, shock, or warmth.
More quoted lines -> documentary/source-faithful tone.
More bracket lines -> remix/reaction tone.
```

Middle tone variants from the same source:

```text
Curiosity: `(이게 종이로 만든 ATM???)`, `(진짜 작동???)`
Emotion: `(아빠를 위한 아들의 정성)`, `(이게 사랑이지...)`
Comedy: `(아빠 힘조절 실패 ㅋㅋ)`, `(2번 박살 ㅋㅋㅋ)`
Shock: `(종이로 ATM을 만들었다고??!)`, `(작동까지 진짜 함???)`
Mixed: shock -> comedy -> curiosity -> emotion by beat.
```

Category routing:

```text
Use strongly: variety, sports, animals, everyday comedy, visual surprise, reaction clips.
Use lightly: family warmth, rescue emotion, satisfying process clips.
Avoid as the main style: yadam/sida mystery, serious news, legal/medical/finance, sensitive tragedy.
```

Legacy three-layer independence check - archive only:

```text
Current v5 check:
Top alone: creates the fixed hook/title.
Timed middle alone: shows situation, verified speech, reaction, and TTS-derived caption beats.
Optional per-beat TTS: follows timed middle entries marked include_in_tts=true.
There is no separate bottom script layer.
```

Current final chat output format:

- Output as plain copyable Markdown text only. Do not use decorative boxes, tables, or merged storyboard blocks unless the user explicitly asks.
- Keep the layers separate in this order: `상단`, `중단`, then `중단 TTS 글자만 복사`.
- `상단` contains only the fixed title text.
- `중단` contains timed visible middle text with timestamps. Bracketed time markers are operator timing only and are never copied into CapCut visible text.
- `중단 TTS 글자만 복사` repeats only the timed `중단` entries marked for TTS, with timestamps removed, so the user can copy or generate voice.
- Do not output `하단`, `하단 원문`, bottom captions, or bottom-TTS script layers for current v5 jobs.

### Current Tikitaka-to-Production File Mapping v5.0

When a job has a `00-tikitaka` final script, that script is the visible text and voice-script authority. Production file names may follow the local factory convention, but the layer meaning must not be changed.

Use this mapping:

```text
상단
-> analysis.json top_title_text
-> CapCut top fixed title

중단
-> analysis.json onscreen_overlays[]
-> work/onscreen_ko.srt
-> work/onscreen_layout.json
-> CapCut middle overlay layer

중단 TTS 글자만 복사
-> optional per-beat TTS source when voice is requested
-> tts_segments.json / voice_segments.srt / generated audio_###.mp3 files
-> CapCut audio clips aligned to the matching timed `중단` beats
```

Rules:

- `final_script_ko.txt` must be locked before timing files are created. If `SCRIPT_LOCK` evidence is missing, stop at `WAIT - agent result missing` or `SCRIPT_REWRITE`; do not create production files.
- Required Tikitaka evidence: `writer_persona_generation_complete=true`, `chief_editor_integration_complete=true`, `final_persona_recheck_complete=true`, `writer_persona_gate_complete=true`, `script_lock_status=SCRIPT_LOCK`, `production_gate_contract.json` exists, `script_lock.json` exists, `writer_persona_pass_count>=4`, and `writer_persona_hard_veto=false`.
- Screen timing is a production placement layer derived by `000short-production-agent` from the locked script and verified source video. Do not let auto SRT generation rewrite the Tikitaka script or decide the story structure.
- `중단` must follow the bracket reaction caption system: `( ... )` is the creative emotion/situation/reaction zone, `" ... "` is source-speech truth, and plain text is only for very short labels.
- Do not create `guide_ko.srt` or bottom narration for current v5 jobs.
- Do not move timed `중단` lines into a bottom layer.
- If voice is generated or user-supplied, split by timed `중단` beat, not by an arbitrary fixed count. The split count is unlimited and equals the selected TTS beats.
- If generated voice is OFF, keep `voice_status=OFF/WAIT_USER_TTS` and do not fake MP3 files.
- If `analysis.json`, Gemini output, or older handoff files disagree with `final_script_ko.txt`, use `final_script_ko.txt` as the text authority and update `analysis.json`, `onscreen_ko.srt`, `onscreen_layout.json`, and optional TTS segment files from it.
- Record `tikitaka_mapping_complete=true` and `tikitaka_final_script_file` in `status.json` or `analysis.json` before handoff or CapCut creation.
- For Tikitaka jobs, run the Shorts Academy Production Gate before SRT/layout,
  render plan, or CapCut creation. Record `shorts_academy_gate=PASS` or an
  explicit `N/A` reason in `decisions/shorts_academy_gate.json`; otherwise
  return to `00-tikitaka`/script repair instead of continuing production.

### Tikitaka SCRIPT_LOCK Gate

`000short-production-agent` must not create production outputs from a Tikitaka folder unless all conditions are true:

```text
- final_script_ko.txt exists
- status.json exists
- writer_persona_generation_complete = true
- chief_editor_integration_complete = true
- final_persona_recheck_complete = true
- writer_persona_gate_complete = true
- script_lock_status = SCRIPT_LOCK
- production_gate_contract.json exists
- script_lock.json exists and was generated by a validator
- writer_persona_pass_count >= 4
- writer_persona_hard_veto = false
- shorts_academy_gate = PASS, or N/A with a concrete reason recorded in
  decisions/shorts_academy_gate.json
```

If any condition is missing or false, stop immediately and return the folder to `00-tikitaka` rewrite mode.

Do not create:

```text
- SRT files
- voice files
- CapCut JSON/XML/project files
- visual prompts
- screen plans
- cut split plans
- upload packages
```

After SCRIPT_LOCK, map the final script like this:

```text
상단
-> analysis.json.top_title_text
-> CapCut top fixed title

중단
-> analysis.json.onscreen_overlays[]
-> onscreen_ko.srt
-> onscreen_layout.json
-> CapCut middle overlay

하단
-> not used in current v5

하단 원문
-> not used in current v5
```

Rules:

- `final_script_ko.txt` is the visible text and voice-script authority.
- Do not ask the five bottom first-line candidates again if `final_script_ko.txt` already exists.
- Do not rewrite the Tikitaka script unless source validation fails.
- Production may split, re-time, or reflow lines for SRT and CapCut readability.
- Production must not change the layer meaning.
- `00-tikitaka` does not need to create `voice_body.txt` in current v5. Derive optional TTS segment text from timed `중단` entries only when voice is requested.
- If validation fails, return to `00-tikitaka` rewrite mode instead of silently changing the script.

### Tikitaka Intake Validation And Repair Gate v1.0

Use this gate when a production input folder from `00-tikitaka` is received. Treat `final_script_ko.txt` as the text authority, but do not blindly trust timing, quotes, source facts, or Gemini-derived analysis.

Required intake check before SRT, voice files, layout files, or CapCut draft:

```text
[ ] final_script_ko.txt exists
[ ] final_script_ko.txt has 상단 / timed 중단 / optional 중단 TTS 글자만 복사 in exact order
[ ] timed 중단 is the visible caption authority
[ ] optional TTS copy has no timestamps
[ ] status.json exists
[ ] writer_persona_generation_complete = true
[ ] chief_editor_integration_complete = true
[ ] final_persona_recheck_complete = true
[ ] writer_persona_gate_complete = true
[ ] script_lock_status = SCRIPT_LOCK
[ ] production_gate_contract.json exists
[ ] script_lock.json exists and was generated by a validator
[ ] writer_persona_pass_count >= 4
[ ] writer_persona_hard_veto = false
[ ] source.mp4 exists or source_url exists
[ ] analysis_raw_gemini.json or analysis.json exists, or status.json says analysis is missing
[ ] status.json next_skill is 000short-production-agent when status.json exists
```

Input status handling:

- `ready_for_000short`: `final_script_ko.txt` exists, SCRIPT_LOCK evidence is complete, `source.mp4` or `source_url` exists, and `analysis_raw_gemini.json` or `analysis.json` exists.
- `ready_for_000short_needs_analysis`: `final_script_ko.txt` exists, SCRIPT_LOCK evidence is complete, `source.mp4` or `source_url` exists, and both `analysis_raw_gemini.json` and `analysis.json` are missing. Run Gemini/watch analysis before production normalization.
- `blocked_input_missing`: `final_script_ko.txt` is missing, or both `source.mp4` and `source_url` are missing, or there is no script/source/analysis clue that lets the factory continue.
- `rewrite_required_script_lock_missing`: `final_script_ko.txt` exists, but SCRIPT_LOCK evidence, writer persona results, chief editor integration, final recheck, pass count, or hard-veto fields are missing/failed. Do not create SRT/layout/CapCut. Return to `00-tikitaka` rewrite mode.

Verification authority:

```text
Text authority:
1. final_script_ko.txt from 00-tikitaka

Timing / visual authority:
1. watch or direct-frame analysis
2. source.mp4
3. Gemini only as raw support

Production validation authority:
1. shorts_remake_harness.py
2. audio-off comprehension gate
3. persona/readability gate
```

Gemini is raw observation only. Do not treat Gemini as final authority for event order, exact speech, OCR, timing, or CapCut placement.

Allowed repairs without asking the user again:

- Fix timestamps to match `source.mp4`.
- Split long timed `중단` lines for `onscreen_ko.srt` readability.
- Split or shorten `중단` lines for one-line overlay fit.
- Remove or rephrase unverified quoted speech.
- Convert uncertain `"actual speech"` into bracket reaction captions.
- Correct obvious OCR or subtitle mistranslations.
- Fix source-event order if Gemini was wrong.
- Verify or repair `source_audio_mode`.
- Remove hallucinated audio evidence and inferred scene sounds.
- Keep music lyrics separate from character speech.
- Normalize Gemini raw overstatement before `analysis.json`, SRT, or CapCut text.
- Use `viewer_confusion_risks` to add missing context to timed `중단` captions.
- Fix line wrapping for CapCut layout.
- Fix `analysis.json` fields required by harness.
- Adjust SRT cue timing to avoid unreadable captions.
- If the Tikitaka package is missing SCRIPT_LOCK evidence or agent result fields, stop and return to `00-tikitaka`; do not invent or infer missing agent results inside production.
- After SCRIPT_LOCK is verified, derive the production screen plan, cut plan, and SRT cue mapping from the locked script and verified source video.

Protected Tikitaka decisions:

- selected working reason
- selected hook frame
- selected reorder strategy
- selected caption tone
- selected first `하단` line
- SCRIPT_LOCK result and writer persona hard-veto state
- top title concept

Do not change protected decisions unless source validation hard-fails them. If a protected decision must change because the source video disproves it, record:

```json
{
  "tikitaka_repair_required": true,
  "repair_reason_ko": ""
}
```

Then rewrite only the minimum necessary lines.

Quoted speech rule:

- Any `중단` line wrapped in double quotes must be verified against source audio, source subtitle, OCR, or a reliable transcript.
- If the quote is not verified, convert it to a bracket reaction caption.
- Do not invent quoted speech for remix flavor.

Example:

```text
Before:
"조금만 더 뿌릴게요"

After:
(제작진: 조금만 더 간다)
```

Repair record:

```json
{
  "tikitaka_input_validated": true,
  "tikitaka_final_script_file": "final_script_ko.txt",
  "tikitaka_text_authority_preserved": true,
  "script_lock_status": "SCRIPT_LOCK",
  "writer_persona_generation_complete": true,
  "chief_editor_integration_complete": true,
  "final_persona_recheck_complete": true,
  "writer_persona_gate_complete": true,
  "writer_persona_pass_count": 4,
  "writer_persona_hard_veto": false,
  "production_gate_contract_file": "production_gate_contract.json",
  "production_gate_precheck_status": "NOT_RUN_UNTIL_RENDER_PLAN_AND_ASSETS_PASS",
  "tikitaka_repairs_made": true,
  "tikitaka_repair_summary_ko": [],
  "quote_verification_complete": true,
  "source_audio_mode_verified": true,
  "audio_hallucination_repair_complete": true,
  "music_lyric_mapping_complete": true,
  "gemini_raw_overstatement_repair_complete": true,
  "timing_repair_complete": true,
  "srt_mapping_complete": true
}
```

Required final output skeleton:

```text
상단
...

중단
[0~3초]
...

중단 TTS 글자만 복사
...
```

ATM reference pattern:

```text
Top:
세상에 하나뿐인
ATM 기계

Middle beats:
(만 원이 끝없이 나오는 중)
(이게 종이로 만들어진 ATM???)
(키패드도 종이)
(카드 투입구도 종이)
"오팔육이삼일..."
"어 왜 안 나와?"
(신기해서 꾹 눌렀다 박살남 ㅋㅋ)
"카드!! 카드!!"
(아들 다급)
(만 원이 줄줄이!!!)
"워어어어어!!!"
(가족 환호 ㄷㄷ)
(이과 아들의 아빠 생일 선물)
(이정도면 카이스트 ㄷㄷ)

Bottom TTS beats:
"여기 세상에 하나뿐인 ATM 기계가 있습니다"
"이 기계, 종이로 만들어졌습니다"
"키패드도 카드 투입구도 전부 종이입니다"
"신기해서 너무 세게 눌렀습니다"
"아들이 카드를 넣으라고 했습니다"
"그러자 만 원이 끝없이 나왔습니다"
"이과 아들이 만든 아빠 생일 선물입니다"
```

Record the decision in `analysis.json` or `status.json` when files are created:

```json
{
  "timed_middle_script_rule_version": "v5.0",
  "middle_bracket_reaction_rule_version": "v1.7",
  "visual_context_classification": "class_a_visual_self_explanatory",
  "top_fixed_title_ko": "",
  "middle_timed_situation_layer_ko": [],
  "middle_tts_copy_ko": [],
  "source_dialogue_decisions_ko": [],
  "timed_middle_contract_check": "PASS"
}
```

## Script Line Role Notation Rule

When writing 11short scripts, storyboard text, SRT source notes, or CapCut handoff notes, use the user's role notation so the editor can immediately tell who is speaking.

- Parentheses are emotional/stage expression, situation, state, viewer reaction, or creative tone: `(열받은 손흥민)`, `(경멸하는중...)`, `(팬들 사이에 사인팔이들이 섞인 상황)`.
- Double quotes are actual words spoken in the source video. Keep them matched to the source audio/meaning: `"어 왜 안 나와?"`, `"카드!! 카드!!"`.
- Plain text without quotes or parentheses is our narrator/voiceover's situational explanation: `사인 못받은 팬이 울고 있던 상황`, `손흥민은 참고교육을 보여주는데`.
- Do not mix roles in one line unless necessary. If one beat needs all three, write them in this order: emotion/context in parentheses, narrator explanation as plain text, then quoted actual source speech.
- For CapCut conversion, narrator explanation normally becomes bottom captions or voice narration, quoted dialogue becomes dialogue subtitles or middle overlays, and parenthetical emotion becomes a short middle beat only when it improves the hook.

Example format:

```text
(팬들 사이에 사인팔이들이 섞인 상황)
사인 못받은 팬이 울고 있던 상황
"왜 울어요???"
"아까 사인 못받아서 울었어요"
(열받은 손흥민)
```

## Foreign-Language Text Unpack Rule

For Japanese or other foreign-language Shorts where the story is carried by on-screen captions, the translation is the main product, not decoration.

- Every meaningful visible foreign-language line must be represented in `onscreen_overlays` with `source_text` and natural Korean `ko_overlay_text`.
- Do not replace a full Japanese explanation with a short vibe caption. If the viewer cannot understand the story by reading the Korean text only, the draft is incomplete.
- Translate top tickers, large center captions, lower-third captions, punchline captions, and narrator-story text. CTA clutter such as like/follow prompts may be minimized unless it carries the actual story beat.
- When there is too much text, split it into more timed middle overlays and bottom captions. Do not delete meaning just to reduce visual density.
- Never summarize away a source claim, setup, rebuttal, or punchline just to make the screen cleaner. Create the full translation/editing pass first.
- Bottom captions should explain the story beat or implication in Korean while middle overlays cover or reinterpret the original visible text. A Japanese text-heavy source should usually have dense bottom captions plus dense middle overlays.
- For rumor, news, allegation, crime, medical, financial, or legal content, preserve claim status in Korean: use words such as `보도`, `혐의`, `주장`, `논란`, `석방`, `부상 없음`, or `확인 필요` instead of converting uncertain claims into facts.

## Audio-Off Comprehension Gate

Every 11short remake must pass this gate before `analysis.json`, captions, overlays, voice text, SRT, or CapCut draft generation is called final.

Default assumption: the original/source audio may be muted by the platform, editor, or viewer. The Korean visible text package must carry the setup, action, turn, payoff, and reason to keep watching without relying on source speech, source music, or foreign-language OCR.

PASS requires all of these:

- A viewer can explain what happened, why it matters, and what changed by reading Korean top/bottom/purple text only.
- All meaningful source dialogue, OCR, captions, signs, and implied reactions are either translated or explained in Korean visible text.
- Source claims are not compressed into vague mood captions when the clip needs context to be understood.
- The first 3-5 seconds tell the viewer what to watch for while preserving the open loop.
- Dense text is allowed when it prevents confusion. Do not delete meaning just to make the screen cleaner.

Record this in `analysis.json` or `status.json` before CapCut:

```json
{
  "audio_off_comprehension_gate_complete": true,
  "audio_off_understandable_ko": "",
  "source_audio_dependency_ko": "",
  "must_read_story_beats_ko": [],
  "caption_density_decision_ko": "",
  "text_only_comprehension_score": 0,
  "video_cut_text_timing_decoupled": true
}
```

If `text_only_comprehension_score` is below 80, or if the viewer needs original audio to understand the setup/turn/payoff, stop and rewrite captions/overlays before producing the draft.

## Source Text Replacement And Hook Rebuild Gate

For source-remake 11short work, the first production step is not summarizing. It is extraction and replacement.

Required process:

1. Inspect the original Short and extract all meaningful on-screen text, subtitles, captions, OCR, dialogue cues, signs, labels, and implied text beats into work files before writing the remake.
2. Convert that material into Korean visible text: top title, bottom captions, middle overlays, and OCR-cover replacement text.
3. Run `00script-writer` to find the strongest hook from the source material.
4. Put that hook in the first 3 seconds. Use hook-forward editing when the strongest moment is not at the start.
5. Rebuild the rest through adaptation: mirror only when allowed, zoom/reframe for the key subject, split/merge visual beats, and cover original screen text with our Korean text when the source text carries meaning.
6. Persona testing must ignore original audio and original text. Agents judge only our Korean visible text package.

Required records in `analysis.json` or `status.json`:

```json
{
  "source_text_extraction_complete": true,
  "source_text_inventory_path": "",
  "source_text_replacement_mode": "cover_original_with_our_korean_text",
  "hook_frontloaded_3s": true,
  "hook_material_ko": "",
  "first_30s_hold_reason_ko": "",
  "persona_our_text_only_understanding_yes": 0,
  "persona_30s_hold_yes": 0,
  "persona_threshold_required": "4_of_5",
  "persona_gate_size": 5,
  "persona_gate_pool": "10s_to_50s_male_female_random"
}
```

PASS requires both:

- At least 4 of 5 randomly selected personas understand the clip using only our Korean visible text, with original audio and original source text ignored.
- At least 4 of 5 randomly selected personas say they would watch for 30 seconds or more, or to the end if the Short is under 30 seconds.

If either count is below 4, stop and rewrite the hook/captions/overlays from the concrete feedback. Then run the remaining 5 personas as the second pass before generating or updating the CapCut draft. If the second pass reaches 4 of 5 or better, proceed. If it is still below 4 of 5, keep the job blocked as `REWRITE_REQUIRED`.

## Video Cut And Text Timing Separation

Do not let dense caption timing create fake video cuts. Text/overlay segment boundaries are not visual cut boundaries.

- Detect and preserve real source cut/transition boundaries separately from caption/SRT timings.
- If a generated CapCut draft splits source video whenever text changes, patch or rebuild the video track so visual cuts happen only at real scene transitions, hook-forward inserts, or intentional editorial cuts.
- Never cut in the middle of an uncompleted visual transition just because a bottom caption or middle overlay changed.
- Record the decision in `analysis.json` or `status.json` as `video_cut_text_timing_decoupled: true` with a short Korean note.

## Real Parallel Persona Gate For 11short

When `00script-writer` is used for 11short and a multi-agent/sub-agent tool such as `spawn_agent` is available, the random 5-persona gate must use real sub-agents. `local simulation` is not acceptable when real sub-agents are available.

Persona pool:

```text
10대 남 / 10대 여
20대 남 / 20대 여
30대 남 / 30대 여
40대 남 / 40대 여
50대 남 / 50대 여
```

Randomly choose 5 unique personas for the first pass. If fewer than 4 of 5 approve any required metric, apply the concrete rewrite requests and run a second pass with the remaining 5 personas from the pool.

Required record:

```json
{
  "parallel_persona_gate_mode": "real_subagents",
  "parallel_persona_gate_complete": true,
  "parallel_persona_agents": [],
  "parallel_persona_second_pass_agents": [],
  "parallel_persona_gate_size": 5,
  "parallel_persona_gate_pool": "10s_to_50s_male_female_random",
  "persona_threshold_required": "4_of_5"
}
```

If real sub-agent tools are unavailable, the required five persona result blocks must still be produced explicitly in the work report or status files. If the result blocks are missing, mark `WAIT - agent result missing` or `BLOCKED`; do not call the script/caption pass final and do not create SRT, layout, voice, or CapCut files.

## Mandatory Script-Writer Pass

Every 11short production must run the `00script-writer` retention pass before finalizing `analysis.json`, captions, overlays, voice text, or CapCut draft generation.

This is mandatory even for URL-only remakes and text-only Shorts. The pass is not a long narration request; it is the hook/title/screenwriting gate for the Short.

Use `00script-writer` in `CC/remake/observation shorts` mode and record the result in `analysis.json` or `status.json`:

```json
{
  "script_writer_mode": "cc_remake_observation_shorts",
  "script_writer_pass_complete": true,
  "youtube_policy_gate_complete": true,
  "policy_risk_tier": "LOW",
  "platform_safety_verdict": "PASS",
  "monetization_verdict": "GREEN",
  "edsa_context": "NONE",
  "hard_blocks": [],
  "rewrite_required": [],
  "audio_off_comprehension_gate_complete": true,
  "source_text_extraction_complete": true,
  "source_text_replacement_mode": "cover_original_with_our_korean_text",
  "hook_frontloaded_3s": true,
  "persona_our_text_only_understanding_yes": 0,
  "persona_30s_hold_yes": 0,
  "parallel_persona_gate_mode": "real_subagents",
  "parallel_persona_gate_complete": true,
  "parallel_persona_gate_size": 5,
  "parallel_persona_gate_pool": "10s_to_50s_male_female_random",
  "persona_threshold_required": "4_of_5",
  "viewer_to_keep_ko": "",
  "viewer_to_ignore_ko": "",
  "click_emotion_ko": "",
  "memory_anchor_ko": "",
  "big_open_loop_ko": "",
  "first_5_seconds_hook_ko": "",
  "title_strategy_ko": "",
  "bottom_caption_strategy_ko": "",
  "purple_overlay_strategy_ko": "",
  "final_script_package_complete": true,
  "final_script_ko": [],
  "script_lock_before_screen_timing": true,
  "writer_persona_generation_complete": true,
  "chief_editor_integration_complete": true,
  "final_persona_recheck_complete": true,
  "writer_agent_gate_status": "PASS",
  "writer_agent_gate_size": 5,
  "writer_agent_pass_count": 4,
  "writer_agent_threshold_required": "4_of_5",
  "source_to_remake_structure_report_complete": true,
  "big_screen_plan_complete": true,
  "srt_mapped_to_big_screens": true,
  "final_script_line_wrap_ko": "",
  "hook_fun_gate": "PASS",
  "hook_fun_gate_reason_ko": "",
  "upload_title_hook_ko": "",
  "hook_forward_plan_ko": "",
  "hook_forward_edit": {
    "applied": true,
    "source_start": "00:00.000",
    "source_end": "00:01.500",
    "target_start": "00:00.000",
    "target_end": "00:01.500",
    "return_to_chronological_at": "00:01.500",
    "reason_ko": ""
  }
}
```

Final script output contract:

- The writer pass must visibly output a `최종 대본` section in the chat or save the same content to `final_script_ko.txt` when production files are being created. For production folders, also mirror a concise version in `analysis.json` or `status.json` as `final_script_ko`.
- The script must be the actual Korean narration/visible-text script Codex recommends using, not Gemini's prose summary and not a placeholder.
- Always include the first 3 seconds as a separate hook line, the beat-by-beat body, the payoff/final line, and a one-line memory anchor.
- The script must be approved before the screen timeline. Do not create `onscreen_ko.srt`, `onscreen_layout.json`, optional voice text, or CapCut drafts until the five writer/persona gate is 4 of 5 PASS.
- After the script is approved, record the original-to-remake structure report and big screen plan before splitting the script into SRT cues.
- When the user asks for a line-length rule such as `한줄에 15자씩`, include a line-wrapped version that obeys it. Otherwise keep lines short enough for Shorts captions and overlays.
- The script must pass a `hook_fun_gate`: it needs an immediate curiosity trigger, a clear reversal or escalation, a payoff, and at least one line that feels human/funny/satisfying rather than a dry recap.
- If the best available script is factual but flat, mark the writer result `REWRITE_REQUIRED`, rewrite the hook/body, and do not call the script pass `PASS` until it is stronger.
- Do not imply that a Supertone/TTS voice file was generated from `final_script_ko`; voice generation remains off unless the user explicitly asks for it.

Rules for the pass:

- Do not use a plain label as the visible title. `title_candidates` may remain a short draft/profile label, but `top_title_text` must be a hook title.
- Generate 3-5 hook title candidates, then select one. Prefer a two-line emotional title when it improves retention.
- Generate the final upload title separately from `top_title_text`. It should feel like a human line before the clip starts, not like a category name.
- For `top_title_text`, use a strong readable one- or two-line hook title. If it looks crowded in CapCut, split or reword for visual fit.
- The first 5 seconds must create an open loop: what should the viewer watch for, and why is the next beat necessary?
- The first 0.5-2.0 seconds should contain the strongest visual beat when the source does not already start there. Record the hook-forward source range and target range before CapCut.
- Timed `중단` captions must explain the visible story beat by beat. Middle overlays may carry setup, reversal, payoff, verified speech, TTS-derived narration, or emotional interpretation.
- In text-only mode, keep enough text for a viewer to understand the Short with no voice. The user will delete excess text manually if needed.
- Gemini/source observations are raw material. Preserve useful details from Gemini by turning them into bottom captions, purple beats, or title strategy instead of dropping them.
- The pass should expand and organize the source, not compress it into a minimal recap.
- The pass should output the final script after the strategy, so the user can copy it without asking a second time.
- The pass must answer: "Can this be understood with the source audio muted?" If not, rewrite the visible Korean text before production.
- For 11short, run the real random 5-persona parallel gate when sub-agents are available and require each persona to judge audio-off comprehension.
- The pass must answer: "Did we extract the original source text, replace it with our Korean text, put the strongest hook in the first 3 seconds, and get 4/5 persona YES for both text-only understanding and 30-second hold?"
- If the script-writer pass is skipped, the 11short job is incomplete even if the harness passes.

## URL-Only Source And Gemini Intake Rule

The default URL-only workflow is the source-evidence factory order: download or locate the source first, generate local `source_evidence.json`, then run Gemini as evidence-based interpretation. The staged intake contract is legacy/opt-in only: accept external GPT-project handoff files only when the user explicitly chooses that old workflow. Do not request those files in ordinary URL factory mode.

Use the Gemini-first execution steps below only when the user explicitly asks Codex to run Gemini/Google AI Studio directly. For factory mode from URL alone, use source-evidence-first, not Gemini-first and not legacy staged intake.

When Gemini-first execution is actually needed, do not wait for a later script. 11short is a remake/analyze-first workflow, so the first action is:

1. Create the work folder under `${env:UTUBE_ROOT}\11short\000short-production-agent\episodes\{date-videoid-or-profile}`.
2. Download or otherwise save the real source as `{work}\source.mp4`; if direct download is blocked, still run Gemini with URL context first and record the blocker in `{work}\status.json`.
3. Open Gemini / Google AI Studio visibly and paste `${env:UTUBE_ROOT}\11short\skills_sync\11short-gemini-remake-factory\references\gemini-capcut-remake-system-prompt.md` plus the user's URL. Build `{work}\gemini_request.md` with `${env:UTUBE_ROOT}\11short\skills_sync\11short-gemini-remake-factory\scripts\build_gemini_request.py` when available. Fall back to `${env:UTUBE_ROOT}\11short\GEMINI_SHORTS_ANALYSIS_PROMPT.md` only if the synced prompt is missing.
4. Enable URL context/Grounding when available. If URL context is weak or Gemini cannot inspect the video accurately, upload `{work}\source.mp4` manually in the same AI Studio chat.
5. Save the submitted prompt to `{work}\gemini_request.md`, copy Gemini's answer as text, save it to `{work}\aistudio_clipboard.txt`, extract JSON to `{work}\analysis_raw_gemini.json`, normalize it to `{work}\analysis.json`, then run the `analysis` harness. Preserve useful Gemini raw fields, especially v2.1 source/audio/category/timeline fields, in `analysis.json` or `status.json` before production.
6. Run the master cross-check when the user needs a long-form written analysis, when the source is complex, or before producing assets/CapCut: paste `${env:UTUBE_ROOT}\11short\GEMINI_YOUTUBE_MASTER_ANALYSIS_PROMPT.md` with the same URL/source, save the submitted prompt to `{work}\gemini_master_request.md`, save the response to `{work}\aistudio_master_clipboard.md`, and save the useful output as `{work}\analysis_master_gemini.md` or `{work}\analysis_master_gemini.json`.
7. Compare the shorts analyzer result against the master result before trusting `analysis.json`. Check duration, core point, segment coverage, timecode gaps/overruns, OCR/overlay candidates, visible action order, speech/sfx, title/caption direction, safety/gatekeeper warnings, and predicted comments. Save the verdict to `{work}\analysis_crosscheck.md` with `PASS`, `FIXED`, or `BLOCKED`.
8. If the two Gemini results conflict on facts, timing, OCR, or core meaning, inspect the downloaded `source.mp4` and repair/re-run analysis before `assets`; do not proceed with TTS/SRT/CapCut from an unverified analysis.
9. Report the `[ 진행판 ]` with `URL/소스접수`, `원본다운로드`, `Gemini분석`, `분석정규화`, and `analysis_crosscheck` filled. Continue to assets/CapCut only when the user asked to make/remake the video, or when the current task clearly implies full production.

Gemini output remains raw observation. Codex still rewrites the actual spoken script, captions, overlays, voice files, SRT, and CapCut package from that analysis.

## Gemini Raw v2.1 Normalization Gate

Gemini JSON is first-pass source material. It is not final `analysis.json`, not a final script, and not timing authority.

When `analysis_raw_gemini.json` is present, preserve these fields when available:

```text
source_audio_mode
source_audio_mode_evidence_ko
youtube_category_raw
content_mode_raw
event_timeline
situation_timeline
dialogue_timeline
music_lyric_timeline
onscreen_text_timeline
sfx_timeline
emotion_timeline
visual_focus_timeline
dialogue_function_timeline
reaction_timeline
character_state_timeline
category_point_inventory
implemented_point_timeline
category_missing_or_unclear_points
edit_impact_points
wow_point_candidates_raw
viewer_confusion_risks
turning_points
uncertain_ranges
shorts_structure_raw
remake_notes_for_codex
```

Normalization rules:

- Store the raw Gemini JSON as `analysis_raw_gemini.json`; do not overwrite it with normalized production data.
- Build `analysis.json` as the factory/harness schema from raw Gemini plus watch/direct-frame verification.
- `source.mp4` plus watch/direct-frame analysis is the authority for `source_audio_mode`, scene order, OCR, speech, timing, and visual focus.
- `final_script_ko.txt` remains the text authority when a Tikitaka handoff exists.
- Preserve useful raw signals under a raw-signal field or in `status.json`, but repair production fields before SRT, layout, voice text, or CapCut.

Required verification before `analysis.json`, SRT, layout files, voice files, or CapCut are considered production-ready:

```text
[ ] source.mp4 is secured or source_url has been downloaded/located
[ ] source_audio_mode verified against source audio
[ ] scene order and duration verified
[ ] OCR/onscreen text checked against source frames
[ ] dialogue_timeline and dialogue_function_timeline checked against actual speech/subtitles
[ ] music_lyric_timeline is not treated as character speech
[ ] visual_focus_timeline checked against direct frames
[ ] raw overstatement or unsafe wording normalized before captions/script
[ ] viewer_confusion_risks reflected in bottom captions when useful
```

If Gemini conflicts with source.mp4/watch/direct-frame, repair the normalized production files and record the repair. Do not silently overwrite Tikitaka decisions; keep the selected concept unless the source disproves it.

Record verification and repairs:

```json
{
  "extended_gemini_raw_signals_present": true,
  "extended_gemini_raw_signals_preserved": true,
  "source_audio_mode_verified": true,
  "audio_hallucination_repair_complete": true,
  "gemini_raw_overstatement_repair_complete": true,
  "watch_direct_frame_verification_complete": true,
  "youtube_category_confirmed": true,
  "content_mode_confirmed": true,
  "category_point_mapping_complete": true,
  "wow_point_verified": true,
  "visual_focus_checked": true,
  "viewer_confusion_risks_checked": true
}
```

### Source Audio Verification And Repair

Allowed `source_audio_mode` values:

```text
original_scene_audio
background_music_only
mixed_scene_audio_and_music
muted_or_unknown
```

For `background_music_only`:

```text
[ ] dialogue_timeline contains no actual spoken dialogue
[ ] dialogue_function_timeline is empty
[ ] sfx_timeline contains music only
[ ] audio_evidence_ko does not mention inferred scene sounds
[ ] middle quoted speech is not invented
```

Treat these as audio hallucination unless source audio directly proves them:

```text
유추 가능
추정
듯한 소리
현장음
문소리
폐문음
진동음
타격음
발소리
충돌음
관중함성
웃음소리
울음소리
안내방송
캔 소리
```

For background-music-only videos, move visible action evidence to `visual_evidence_ko`, keep `audio_evidence_ko` empty or `배경음악만 들림`, and store song lyrics only in `music_lyric_timeline` or OCR fields.

For `mixed_scene_audio_and_music`, still verify each claimed scene sound. If the raw JSON says scene audio exists but `sfx_timeline` only proves music, downgrade or repair `source_audio_mode` before production.

## Tikitaka Decision Gate v1.2

Use this gate when the user provides a Gemini JSON, `analysis_raw_gemini.json`, `analysis.json`, or video analysis text and asks what to do with it, why it worked, where the hook is, how to reorder it, or how to rewrite/remake it.

When the user says `티키타카`, `티키타카 시작`, `티키타카 대본`, `이거 분석해줘`, `이걸로 해보자`, or asks for hook-first script collaboration, use the `00-tikitaka` skill first. If that standalone skill is unavailable in the current session, load `references/tikitaka-script-v17.md` and follow it as the fallback operating contract.

This gate absorbs only the useful parts of `grill-me`. Do not follow coding-specific `grill-me` behavior, ADR workflows, codebase-only exploration rules, or endless questioning. The user wants analysis plus a short decision conversation, not a long interrogation.

Core rule:

```text
Analyze first.
Ask only when a production decision is genuinely needed.
Ask one question at a time.
Always include Codex's recommended answer and the reason.
```

When the JSON includes `video_url`, or when the user provides a source URL, collect or request top-liked comments before deciding the final "why it worked" reason. If direct comment collection is blocked, ask the user to paste top-liked comments and continue with whatever comments are provided. JSON alone is a surface/video-content signal; comments are the viewer-reaction signal.

Save comment-related files in the same work folder when files are being created:

```text
comments_raw.info.json
comments_top_liked.json
comments_analysis.json
audience_signal_analysis.md
remake_direction.md
```

If no files are being created, still report the same sections visibly in chat.

Comment analysis must classify:

- repeated words or phrases
- specific timestamp/scene mentions
- quoted dialogue or captions viewers repeat
- laugh/shock/satisfaction/discomfort signals
- share intent such as "친구한테 보여줌"
- negative or copyright/safety concerns
- comments that are funny but not useful for remake decisions

Combine the signals like this:

```text
Gemini JSON = what is in the video
top-liked comments = what viewers reacted to
view count/retention data when provided = how strongly it worked
```

Accuracy guide:

```text
JSON only: 60-70%
JSON + top-liked comments: 80-90%
JSON + comments + view/retention/share data: 90%+
```

Decision tree order:

1. Confirm the real working reason, normally 1-3 reasons.
2. Confirm the hook anchor and source timestamp range.
3. Confirm the genre/tone, such as Japanese variety situation-explanation, reaction comedy, emotional rescue, scam warning, quote/dialogue, or mystery/sacrifice.
4. Confirm the assembly strategy. Default is `scenario_first_montage`: use the GPT/Gemini macro structure only as guidance, split the source with `watch` into small reusable beats, then assign those clips to the scenario timeline. Legacy `12345 -> 31245` order remix is used only when the user explicitly asks for simple reorder mode.
5. Confirm viewpoint, such as observer third-person, first-person anchor, victim POV, contestant POV, or narrator explanation.
6. Confirm target length and density.
7. Only then write or revise the script/captions/CapCut plan.

Ask only one decision question at a time. Each question must include:

```text
My recommendation:
Reason:
Your choice:
1. ...
2. ...
3. ...
```

Use numbered choices only for Tikitaka questions. Do not use `A/B/C` choices unless the user explicitly requests letters.

Example:

```text
My recommendation: Put 00:27-00:33 first as the hook.
Reason: Gemini marks it as payoff, and top-liked comments repeatedly mention the sports car/skirt-flip moment.
Your choice:
1. Use this payoff-first hook.
2. Keep the original setup-first order.
```

Stop asking and proceed when the user says `그만`, `됐어`, `다음`, `바로 써`, `프로젝트 만들어`, or gives a clear decision.

## Gemini Master Cross-Check Rule

`skills_sync\11short-gemini-remake-factory\references\gemini-capcut-remake-system-prompt.md` is the primary 11short CapCut JSON analyzer. `GEMINI_SHORTS_ANALYSIS_PROMPT.md` is fallback only. `GEMINI_YOUTUBE_MASTER_ANALYSIS_PROMPT.md` is the reference analyzer for long writing, factual integrity, mode detection, target persona, safety, research angles, and script direction.

Use the master analyzer whenever:

- The user gives a URL and asks for a long article, long explanation, report, research, or script idea.
- The short analyzer output looks too shallow, misses the core point, has suspicious timecodes, or omits visible OCR/speech.
- A 11short production will proceed to assets/CapCut and the source is not trivial.

Required comparison checklist before `assets`:

```text
[ ] duration and final timestamp match source.mp4
[ ] no segment gap or end time overrun
[ ] core point/video_summary match between shorts and master outputs
[ ] visible action order matches the source
[ ] OCR/onscreen text candidates are not missed
[ ] speech/sfx are not invented
[ ] reframe/focus does not crop out the key object
[ ] captions/title are standard Korean and within 11short limits
[ ] gatekeeper/safety risks are recorded
[ ] predicted_best_comments are plausible and source-grounded
```

If the checklist is not clean, write `analysis_crosscheck.md` and fix `analysis.json` before harness `analysis`. The harness pass is not enough when the cross-check shows a visible-content problem.

## Chrome Gemini / AI Studio Fallback

Use this workflow when the Gemini API is unavailable, `google.genai` is not installed, the API key is missing, or the user explicitly asks to use Chrome/Gemini manually.

1. Open Google AI Studio visibly in Chrome:

```powershell
Start-Process -FilePath "chrome.exe" -ArgumentList "https://aistudio.google.com/prompts/new_chat"
```

Wait for the user to log in if needed.

2. Paste a clean prompt. Do not reuse unreadable Korean text from old prompt files. If an existing prompt file is still unreadable after a UTF-8 re-read, rewrite the request cleanly while preserving the 11short JSON contract, layout rules, caption requirements, and user voice/profile overrides.

3. Enable relevant AI Studio tools when available:

- `Grounding with Google Search` for current URL/source context.
- `URL context` for YouTube Shorts or website URL analysis.
- Manual file upload for local downloaded media such as `{work}/source.mp4` when URL context is insufficient.

4. Prefer one source URL per Gemini request when accuracy matters. Save the submitted prompt to `{work}/gemini_request.md`.

5. After Gemini finishes answering, move or hover the mouse over the answer card itself so the answer toolbar appears. Open the answer-card `...` menu and choose `Copy as text`. If text copy fails, use `Copy as markdown`. Do not use the page/header `...`; that menu is not the answer copy menu.

6. Save the copied response to `{work}/aistudio_clipboard.txt`, then extract the latest JSON object into `{work}/analysis_raw_gemini.json`. If the local helper exists, use it:

```powershell
py -3 ${env:UTUBE_ROOT}\11short\aistudio_capture_response.py "{work}\aistudio_clipboard.txt" "{work}\analysis_raw_gemini.json"
```

7. Treat Gemini's copied output as raw observation, not as final production data. Repair and normalize it into `{work}/analysis.json` before running the harness:

- Remove code fences and fix malformed JSON.
- Fix missing/extra fields and mixed arrays, such as segment objects accidentally placed inside `onscreen_overlays`.
- Keep only harness-valid 0..1 crop and focus coordinates.
- Rewrite captions and overlays into standard Korean and 11short layout limits.
- Preserve all useful speech, OCR, explanation, advice, and dialogue content in visible captions when the user asks that viewers understand by reading only.

8. Record the manual Gemini path in `{work}/status.json`: `gemini_source="chrome_aistudio"`, `gemini_request_md`, `analysis_raw_gemini`, `gemini_analysis_used=true`, and a short note for any JSON repairs.

9. Continue normal gates: `analysis` must pass before assets, `assets` must pass before CapCut, then run `capcut` and final `all`.

If Chrome UI automation is needed, the practical order is: focus Chrome, click the prompt input, paste prompt, run, wait for the response, hover the answer card, click the answer-card `...`, click `Copy as text`, then parse the clipboard. Use full-page `Ctrl+A` copy only as a fallback, and still extract the latest relevant JSON before normalization.

## Mandatory Intent Brainstorm Gate

For any production, review, rebuild, Gemini analysis, TTS/SRT, or CapCut draft request, run this gate before editing files, generating audio, or creating a draft. This gate is the step that turns the user's rough Korean request into an executable production brief.

Do not run it for a simple factual question, folder-open request, one-off command, or status check. If the user says `브레인스톰`, `brainstorm`, `찰떡같이 이해`, or gives a messy production request, run it even if the rest of the task is not fully specified.

Report this first:

```text
Brainstorm
- 사용자 의도:
- 작업 종류:
- 입력 소스:
- 결과물:
- 보이스/모델:
- 자막 원칙:
- 금지/주의:
- 애매한 점:

Harness TODO
- [ ] analysis
- [ ] assets
- [ ] capcut
- [ ] visual check

Text/Voice/Reframe
- 작가모드 설계:
- 상단 제목:
- 하단 자막:
- 중간 강조/OCR:
- 인트로/본문 음성:
- reframe:
```

Proceed after posting the gate unless the user objects or a listed ambiguity blocks production. Simple housekeeping commands such as opening folders, moving exports, or extracting a single audio file can be done directly.

## Mandatory Start Gate

For any production, review, rebuild, or CapCut draft work, do not jump straight to JSON/audio/draft. Report this first:

```text
Brainstorm
- 상황:
- 핵심 웃음/감정:
- 프로파일명 후보:
- OCR/중간 강조 자막 필요:
- 음성 포인트:

Harness TODO
- [ ] analysis
- [ ] assets
- [ ] capcut
- [ ] visual check

Text/Voice/Reframe
- 작가모드 설계:
- 상단:
- 하단 타임라인:
- 중간 강조 자막 타임라인:
- 인트로/본문 음성:
- reframe:
```

Proceed only if the user does not object. Simple housekeeping commands such as opening folders, moving exports, or extracting a single audio file can be done directly.

## User-Provided Result JSON Means Full Production

When the user provides a structured analysis/result JSON for a YouTube Shorts remake, treat it as a production request, not a review-only request. Unless the user explicitly says `검토만`, `분석만`, `초안 만들지 마`, or `CapCut 만들지 마`, continue through the full pipeline:

1. Download or reuse the real `source.mp4` and verify the JSON against the actual video.
2. Rewrite/fix `analysis.json`, captions, overlays, voice text, and reframe data as needed for the locked 3-text layout.
3. Run `shorts_remake_harness.py "{work}" --stage analysis`; stop only on FAIL.
4. Generate required assets including source audio, intro voice, body voice, SRT, OCR/layout files, and BGM.
5. Run `shorts_remake_harness.py "{work}" --stage assets`; stop only on FAIL.
6. Create and register the visible local CapCut draft/profile with `capcut_factory_profile.py`.
7. Run `shorts_remake_harness.py "{work}" --stage capcut --draft-name "{draft_name}"`, then final `--stage all`.

Do not end with only JSON, SRT, a plan, or a summary when the user has supplied the result JSON. The required done state is a registered CapCut project under the active CapCut draft root, with the exact draft name and path reported. Upload still waits for an explicit upload request.

## Locked 3-Text Layout

Every valid 11short CapCut draft must have exactly three visible text classes:

1. Top fixed title
   - Source: `top_title_text`.
   - One title, fixed until video end.
   - Top black band only.
   - One- or two-line emotional titles are allowed.
   - If the title looks crowded in CapCut, split or reword it for visual fit; do not fail it only by character count.
   - Prefer meaningful two-line titles for story/reaction/emergency clips, e.g. `진정한 영웅\n이웃집 아저씨`.
   - CapCut UI `x=0`, `y=1498`.
   - Project normalized `x=0`, `y=0.78125`.
   - `font_size=15`, `scale=1.34`, white text, black stroke.
   - Standard Korean only.

2. Bottom yellow caption
   - Source: `segments[].caption_ko_final`.
   - One yellow rounded-box caption track.
   - Bottom black band only.
   - Max 2 lines, max 14 Korean chars per line.
   - CapCut UI `x=0`, `y=-1516`.
   - Project normalized `x=0`, `y=-0.7895833333333333`.
   - `font_size=12`, `scale=1.02`, black text, yellow rounded box `#ffdc00`, round radius `0.4`.
   - Tone: natural Korean, 10대 고등학생 여자 말투 느낌.
   - No Chungcheong dialect, no `~유`, `~슈`, `~네유`, `~했슈`, `~갑니다잉`.

3. Middle overlay
   - Source: `onscreen_overlays[]` for OCR cover, or Codex-created final script beat.
   - One middle overlay track only.
   - Middle video area only; never top or bottom black band.
   - Do not require a purple background or white text. Use the user-approved one-line middle emphasis style.
   - Middle text must have both CapCut Glow and Shadow enabled. Screenshot baseline: black Glow, opacity/intensity `30`, range `20`, X/Y offset `0`; black Shadow, opacity `80%`, blur `15%`, distance `5`.
   - If CapCut's exact Glow JSON field is not stable, copy Glow from the middle sample text in the factory/reference draft. Do not substitute the old purple box as the rule.
   - `style_hint` is optional. If recording one, use `middle_glow_shadow_text` or `middle_emphasis_text`, not `purple_box_white_text` as a required contract.
   - For OCR cover, `cover_original=true` required.
   - OCR cover must fully cover the original source text.
   - Only one middle overlay may be visible at any timestamp.

## Default Middle Situation/Voice Overlays

By default, include enough middle overlays to make the situation and voice beats understandable, even when the original video has little or no OCR.

- Add middle `script_beat` overlays for the strongest setup, reversal, and payoff beats.
- If the generated voice has an important line, add one matching middle overlay near that voice timing unless it would duplicate the bottom caption exactly.
- For most 30-70 second Shorts, target enough middle overlays to explain the full situation. 3-6 is fine for simple clips; 8-12 is acceptable for text-only, emergency, story, or Gemini-rich clips.
- Middle overlays should explain the situation or spoken hook, not merely repeat surface action.
- Do not make the middle overlay text identical to any bottom caption text. If the meaning overlaps, rewrite it with different wording so the harness does not confuse the text classes.
- Keep each middle overlay short: normally 8-18 Korean characters, max 2 lines.
- It is acceptable for a draft to have many short text segments when the user wants text-only comprehension. Do not down-rank or reject a draft only because it is text-dense.
- Keep at least 0.3 seconds of gap between middle overlays unless replacing the same visual caption continuously.
- Never show more than one middle overlay at the same timestamp, including OCR covers and script beats.
- When OCR covers are needed, OCR covers take priority. Place script beats immediately before or after OCR-covered moments rather than overlapping them.
- Record the selected middle overlay strategy in `status.json` as `middle_overlay_strategy`, including why any expected setup/reversal/payoff overlay was skipped.

Any extra visible text class, overlapping middle overlays, grouped text/stickers/shapes, shared movement, or text outside these three classes is FAIL even if the harness says PASS.

## Current Timed Middle Caption Default

Timed `중단` captions are the primary visible explanation layer for current v5 jobs. Write them as compact Korean captions that can include situation explanation, verified quoted speech, reaction text, or TTS-derived narration.

- In current Tikitaka jobs, `onscreen_ko.srt` comes from timed `중단`.
- `( ... )` is creative situation/reaction/emotion text.
- `" ... "` is source-speech truth and must be verified by source audio, subtitles, OCR, or reliable transcript.
- Plain text is allowed for narration/explanation and can be used as TTS source when marked `include_in_tts=true`.
- Assume the viewer may watch with the original audio muted. The timed `중단` sequence must explain who/what is on screen, what changed, and why the beat matters.
- Do not create a separate `하단`, `하단 원문`, `guide_ko.srt`, bottom-caption, or bottom-TTS layer for current v5 jobs.
- Avoid vague one-word or generic labels when a clearer action, cause, result, object, person, number, or reversal is supported by the source.
- If one visual beat has more than one important detail, split it into multiple shorter timed `중단` entries instead of dropping the detail.
- Default caption density should fit the video and user direction. Simple clips can use sparse captions; source-dialogue or explanation-heavy clips may use more timed `중단` entries.
- Record `subtitle_mode` in `analysis.json` or `status.json`, for example `timed_middle_captions`, `source_dialogue_middle_captions`, or `tts_derived_middle_captions`.

## Generated Voice Must Be In Timed Middle SRT

Every generated TTS line must be represented in timed `중단` / `onscreen_ko.srt` before the assets gate. Do not create an audible MP3 from text that is missing from the timed caption plan.

- Current v5 TTS source is timed `중단`, not `하단`, `하단 원문`, or `voice_body.txt`.
- If generated voice is OFF, keep `voice_status=OFF` or `WAIT_USER_TTS`; do not create placeholder MP3 files and do not require voice files.
- If voice is requested, build per-beat TTS files from all timed `중단` entries marked `include_in_tts=true`.
- There is no fixed TTS split count. Use as many or as few clips as the timed script requires.
- Each generated voice clip must have matching timing in `voice_segments.srt` or equivalent segment metadata and must align to the related `onscreen_ko.srt` beat.
- Split long spoken sentences into multiple readable cues. Preserve meaning by splitting/rewording, not by dropping source-supported story logic.
- After TTS generation, compare normalized text from TTS segment metadata and audio filenames/manifests against the timed `중단` text. Missing spoken content means the job is incomplete even if audio and CapCut draft files exist.
- Record `voice_to_srt_complete=true` in `status.json` only after this comparison passes.

## Edge TTS Free Voice Option

When the user asks for free Microsoft Edge voices, no API key voice generation, `edge-tts`, `ko-KR-SunHiNeural`, or `ko-KR-InJoonNeural`, use the local 11short wrapper:

Do not use Edge TTS as an automatic fallback when Supertone is disabled. It is still generated voice and requires an explicit user voice/TTS request.

```powershell
py -3 ${env:UTUBE_ROOT}\11short\edge_tts_11short.py --voice female --text-file "{work}\tts_lines.txt" --out "{work}\voice_segments_merged.mp3" --srt "{work}\voice_segments.srt"
py -3 ${env:UTUBE_ROOT}\11short\edge_tts_11short.py --voice male --text-file "{work}\voice_opening.txt" --out "{work}\voice_opening.mp3" --srt "{work}\voice_opening.srt"
```

- Female aliases use `ko-KR-SunHiNeural`; male aliases use `ko-KR-InJoonNeural`.
- The wrapper writes MP3 and SRT together and returns `voice_to_srt_complete=true`.
- For generated narration, pass `--voiceover-srt "{work}\voice_segments.srt"` and the matching audio files/manifest to the CapCut builder.
- Copy any intro cue into `onscreen_ko.srt` when it must be visible as timed `중단`.
- Edge TTS is a free online Microsoft voice endpoint accessed by the `edge-tts` library. It does not need an API key, but it is not a guaranteed SLA service.

## Optional Text Effect Presets

When the user explicitly asks for CapCut fire text, neon text, repeated laugh/pop text, `TXT_FIRE_*`, `TXT_NEON_*`, `TXT_POP_*`, or a meme/text-effect variant, read `references/capcut_text_effect_presets.md` before planning or editing.

The shared text-effect preset source is:

```text
${env:UTUBE_ROOT}\0shrt\assets\emotion_pack\text_effect_presets.md
```

Default 11short harness drafts must not use these presets because they add or restyle visible text beyond the locked 3-text layout. If the user still wants the effect, create or plan a separate `layout_variant=custom_text_effect` draft and state that it is an opt-in custom/test variant, not the normal harness profile. `TXT_POP_하하하증식` is especially incompatible with normal 11short because it requires multiple duplicated text layers visible in staggered overlap.

## White Background Variant

When the user says `하얀배경`, `흰배경`, `화이트 배경`, or otherwise asks for the white bar style, use this variant instead of the default black top/bottom bars:

- Top and bottom bar/background color: white.
- Top title text: black.
- Top title text effect: CapCut `텍스트 > 편집효과` style shown by the user as the second attached reference, visually the `ART` preset with black letters and colorful childlike hand-drawn background. In existing JSON this corresponds to the text effect named `Dynamic, childlike, colorful hand-drawn` with resource id `7629365132539284752` when available.
- Top title style reference/factory: `$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\260517-스핑크스목욕-bars-voice`.
- Bottom caption remains the yellow rounded box with black text unless the user explicitly changes it.
- Add/copy the lower-left sphynx cat decoration from the same reference draft. It is the visible cat image/video overlay at the lower-left of the white bottom area in `260517-스핑크스목욕-bars-voice`.
- Middle overlay rules are unchanged: user-approved emphasis style, Glow and Shadow both enabled, one visible at a time, middle video area only.
- Keep the same upload rule: generated draft waits for `TAKKTWO` upload request; do not upload automatically.
- When generating a CapCut draft for this variant, pass the reference draft through `--factory "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\260517-스핑크스목욕-bars-voice"` and verify the white bars, black top title, text effect, and lower-left sphynx cat survived generation.

Report the selected layout mode in the start gate and status file as `layout_variant=white_background` when this variant is used.

## Source-Driven Cut And Motion Defaults

When the user provides a YouTube Shorts URL or any raw video link, download `source.mp4` first and treat the actual downloaded video as the production truth.

Default YouTube download quality is FHD/1080-first: secure the full source as
`source.mp4` at `1920x1080` for landscape or `1080x1920` for vertical Shorts
when available. Use a `width<=1920 AND height<=1920` yt-dlp format cap, not a
plain `height<=1080` cap. Lower-resolution files are allowed only as
preview/proxy fallbacks, for blocked downloads, or when the user explicitly
asks; mark those as non-authoritative if they are not the production source.

- Build the remake from the given source video, not from stale JSON, placeholder summaries, or a previous project with a similar title.
- If an existing `analysis.json` conflicts with the downloaded source duration, visible content, OCR, or action order, stop before assets/CapCut and re-analyze from the actual source.
- Analyze visual changes in 1-second windows (`0-1`, `1-2`, `2-3`, ...). Use that scan to find action/composition changes, then merge adjacent seconds only when the visible action remains continuous.
- During the 1-second scan, mark the best hook-forward candidate: bite, fall, reveal, payoff, shock face, transformation, price reveal, or punchline.
- If that candidate is not already in the first 1-2 seconds, create a short front preview or equivalent CapCut duplicate segment before the chronological edit. The viewer should see the promise immediately, then the story can restart.
- If front preview would break a source-audio joke, synced dialogue, or OCR story, keep chronological order but record `hook_forward_edit.applied=false` and the exact reason.
- Cut the source video by visual-change units. Do not let old caption timing, narration beats, or a supplied JSON segment force a cut that ignores visible motion.
- Default source video scale is `1.10` (110%) on every video segment. Use a stronger zoom only when the subject is small or the segment `reframe.suggested_zoom` clearly requires it.
- Default source video speed is `1.10x` (110%) on every video segment unless the user explicitly asks for original speed or source-audio sync would break. Recalculate segment durations, SRT timings, overlay timings, and audio timing after speed is applied.
- Apply automatic zoom/pan from `focus_bbox`, `focus_center`, and `pan_direction`; keep faces, hands, readable OCR, captions, and the main action inside frame.
- Mirror only when the existing mirror rules allow it.
- Record these decisions in `status.json`: `source_driven_analysis=true`, `cut_detection_granularity_sec=1`, `default_video_scale=1.10`, `default_video_speed=1.10`, plus any per-segment exceptions.
- Also record `upload_title_hook_ko`, `hook_forward_plan_ko`, and `hook_forward_edit`.

## Core Point And Situation Explanation

Before writing final captions, voice lines, overlays, or generating a CapCut draft, identify the real core point of the YouTube video from the downloaded `source.mp4`.

Required behavior:

- Do not only restate the supplied JSON summary. Use the actual source video to determine the funniest, most surprising, most satisfying, or most important moment.
- Write a short Korean explanation of the core point in the work files and status report before assets/capcut:
  - `core_point_ko`: what the video is really about.
  - `why_funny_or_hook_ko`: why this moment is funny/interesting/satisfying.
  - `dialogue_context_ko`: what the people are saying or implying, including who sets up the situation and who causes the reversal.
  - `situation_flow_ko`: the setup, turn, reaction, and payoff in order.
- Use that explanation to design captions and voice. The bottom captions and middle overlays must make the core point understandable, not just describe surface actions.
- If the supplied analysis misses the core point, rewrite `analysis.json`, `onscreen_ko.srt`, optional TTS text, and status before continuing.
- For comedy or reaction clips, explicitly capture the reversal. Example: if a person makes a rule and immediately breaks it themselves, captions should make that rule/reversal clear.
- Keep the final visible text within the locked 3-text layout and length limits, but choose wording that explains the joke or conflict.
- Record the core point fields in `status.json`. If this explanation is missing, treat the production as incomplete even if the harness passes.

## Normalized Production analysis.json Contract

This contract is for normalized production `analysis.json`, not raw Gemini v2.1 output. Raw Gemini collection JSON may contain `source_audio_mode`, timelines, category inventories, and `remake_notes_for_codex`; preserve those signals, then convert them into this harness-ready schema after source.mp4/watch/direct-frame verification.

Required top-level fields:

```text
video_url, video_summary_ko, layout_rules, title_candidates, top_title_text,
opening_voice_line, main_subject, tone, onscreen_overlays, segments
```

Required segment fields:

```text
start, end, time_range_note, visual_ko, action_ko,
onscreen_text_en, onscreen_text_ko_natural,
speech_en, speech_ko_natural, sfx_ko,
caption_ko_final, reframe, importance
```

Required `reframe` fields:

```text
focus_bbox, focus_center, important_object_ko, suggested_zoom,
pan_direction, mirror_allowed, mirror_reason
```

Required OCR overlay fields when OCR exists:

```text
start, end, overlay_type, source_text, source_language,
ko_overlay_text, source_bbox, overlay_bbox, x, y, width, height,
cover_original, style_hint
```

All bbox coordinates are 0..1 screen ratios:

```json
{ "x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0 }
```

`x1/y1` is top-left, `x2/y2` is bottom-right. Reject pixel coordinates such as `1200`, `-1100`, `1498`, or `-1516` for OCR placement. Those UI pixel-like values are allowed only in `layout_rules.top_title.y_ui` and `layout_rules.bottom_caption.y_ui`.

## Naming And Script

- `title_candidates`: profile/draft name only. Exactly one natural Korean title, 6 Korean chars or fewer when possible. No forced suffix.
- `top_title_text`: visible top title only.
- `opening_voice_line`: voice intro only, not visible title. It must be a rumor/setup phrase such as `...라는데`, `...한다는데`, `...보여줬다는데`.
- Never paste Gemini prose directly as narration. Rewrite it into a short 11short script.
- Writer-mode analysis must finish with `final_script_ko`: a hooked, fun, production-usable Korean script. If it is only a situation summary, the analysis is incomplete unless the user explicitly requested summary only.
- Bottom captions explain the scene in detail; they are not comment-reading captions unless the user explicitly asks.

## 11short Voice Policy

- For 11short remake work, always write the recommended spoken scenario script when production text is being finalized.
- Do not use Supertone/TTS unless the user explicitly requests voice generation, asks for `음성`, `대사`, `TTS`, `보이스`, `슈퍼톤`, or asks for a completed result video that includes narration.
- Default text-only draft mode is original source audio + captions/OCR + BGM.
- If the user asks for narration or result video with voice, generate or place the voice track as part of the CapCut timeline unless they explicitly say `소리는 빼고`, `무음`, or `TTS는 내가 넣을게`.
- If Supertone is not explicitly requested, set:
  - voice_generation_mode: user_supplied
  - supertone_generation_enabled: false
- Do not check Supertone balance or run Supertone scripts unless voice generation was explicitly requested.

## Voice Rules

Current 11short source-remake default: Supertone generation is OFF unless the user explicitly asks for generated voice again.

Use this record in `status.json`:

```json
{
  "supertone_generation_enabled": false,
  "voice_generation_mode": "user_supplied",
  "voice_status": "user_will_add_voice"
}
```

Do not call the Supertone API, check Supertone balance, generate `voice_opening.mp3`, or generate `voiceover_body.mp3` while this mode is active. Prepare the visible text package and optional voice guide text only. Do not fake voice files to satisfy a draft gate.

Even when generated voice is OFF, save or record the recommended spoken lines as `tts_lines.txt` or `tts_segments.json` only when the user may later request TTS. The timed `중단` script remains the scenario spine for visible captions.

Default voices below apply only when the user re-enables generated voice:

```text
intro/opening voice_id: ca0b75f0fc2ee0ab6fa54d
main body voice_id: ca0b75f0fc2ee0ab6fa54d
```

Default Supertone settings:

```text
speed=1.2
pitch_shift=1.2
pitch_variance=1.0
model=sona_speech_2t
```

Rules:

- When generated voice is enabled, create the spoken script yourself from the Gemini/source report.
- Intro uses Daniel by default: `ca0b75f0fc2ee0ab6fa54d`.
- Body uses Daniel by default: `ca0b75f0fc2ee0ab6fa54d`.
- Do not use comment/reaction voices by default.
- Silence longer than 3 seconds is allowed.
- Do not narrate the whole video just to fill silence.
- Put body voice only on the strongest 1-3 moments unless the user asks for dense narration.
- If the body voice is long or the user may delete pieces, split it with a voiceover SRT and generate separate timeline clips.

Generate audio only after explicit voice generation is requested:

```powershell
py -3 ${env:UTUBE_ROOT}\11short\supertone_11short_tts.py --text-file "{work}\voice_opening.txt" --out "{work}\voice_opening.mp3" --voice-id ca0b75f0fc2ee0ab6fa54d --speed 1.2 --pitch-shift 1.2
py -3 ${env:UTUBE_ROOT}\11short\supertone_11short_tts.py --text-file "{work}\tts_lines.txt" --out "{work}\voice_segments_merged.mp3" --voice-id ca0b75f0fc2ee0ab6fa54d --speed 1.2 --pitch-shift 1.2
```

Supertone model selection:

- Default and first choice for Shorts factory Daniel is Supertonic 3: `sona_speech_2t`.
- Use `--model supertonic`, `--model supertonic3`, or omit `--model` in the current Daniel wrapper for Supertonic 3 (`sona_speech_2t`).
- Use `--model sona` only when the user explicitly asks for Sona Speech 2 (`sona_speech_2`).
- Use `--model flash` for `sona_speech_2_flash`.
- Use `--model supertonic1` only when the user explicitly asks for old Supertonic API 1 (`supertonic_api_1`).
- `supertonic_api_1` supports only `speed`; do not depend on pitch or advanced voice settings with it.
- After any Supertone API generation or balance check, report the remaining `credit_balance` to the user. Never print or expose `SUPERTONE_API_KEY`.

Example:

```powershell
py -3 ${env:UTUBE_ROOT}\11short\supertone_11short_tts.py --model supertonic3 --text-file "{work}\tts_lines.txt" --out "{work}\voice_segments_merged.mp3" --voice-id ca0b75f0fc2ee0ab6fa54d --speed 1.2 --pitch-shift 1.2
```

Do not print or expose `SUPERTONE_API_KEY`.

## Audio And CapCut Track Rules

Always separate audio tracks for editability:

1. Extract original source audio:

```powershell
ffmpeg -y -hide_banner -loglevel error -i "{work}\source.mp4" -map 0:a:0 -vn -c:a libmp3lame -q:a 2 "{work}\source_original_audio.mp3"
```

2. Add original source audio as its own CapCut audio track with `--source-audio` only for edit reference, unless the user asks to remove it.
3. The remake must not depend on original source audio for comprehension. If user-supplied voice mode is active, leave generated voice tracks absent and mark `voice_status=user_will_add_voice`.
4. Add intro voice as a separate audio track only when generated voice is enabled or the user provides an intro voice file.
5. Add body voice as a separate audio track only when generated voice is enabled or the user provides a body voice file. If split, keep all body pieces on one body audio track.
6. Add background music as a separate low-volume audio track on every generated 11short draft unless the user explicitly says not to. Use the shared folder `${env:UTUBE_ROOT}\11short\assets\always_bgm`; trim the active BGM segment to the final video duration. Keep all BGM source files in that folder as profile media. Vary BGM across drafts: avoid reusing any BGM used in the most recent 3 generated CapCut drafts when another file is available, then prefer the least-used file in `always_bgm`. Record the selected BGM filename in `status.json` or the work report.
7. CapCut audio materials must use native local audio schema:
   - `type="extract_music"`
   - `category_name="local"`
   - `check_flag=1`
   - nonempty `music_id` and `local_material_id`
   - segment `extra_material_refs` includes speed, placeholder, beats, sound channel mapping, and vocal separation support materials.
8. `wave_points=[]` is normal. CapCut calculates waveforms when it opens the draft.

## CapCut Draft Generation

Use the project generator, not hand-written draft JSON unless patching a specific bug:

Factory input meaning:

- `--srt "{work}\onscreen_ko.srt"` is the current visible timed `중단` caption track.
- `--ocr-srt "{work}\onscreen_ko.srt"` may be used only by older helpers that still name the middle overlay input `ocr-srt`; it must point to the same timed `중단` authority.
- `--voiceover-srt "{work}\voice_segments.srt"` is the generated/user-supplied voice sync when TTS is requested. It must match the timed `중단` entries selected for TTS.

```powershell
py -3 ${env:UTUBE_ROOT}\tools\youtube_ko_subtitles\capcut_factory_profile.py `
  --draft-name "{draft_name}" `
  --video "{work}\source.mp4" `
  --srt "{work}\onscreen_ko.srt" `
  --top-title "{top_title_text}" `
  --source-audio "{work}\source_original_audio.mp3" `
  --bgm-audio "{optional specific BGM, otherwise omitted to auto-select from assets\always_bgm}" `
  --ocr-srt "{work}\onscreen_ko.srt" `
  --ocr-layout-json "{work}\onscreen_layout.json" `
  --analysis-json "{work}\analysis.json"
```

Add `--intro-audio`, `--voiceover-audio`, and `--voiceover-srt` only when voice generation was explicitly requested or the user supplied voice files. If there is no body split SRT, omit `--voiceover-srt`.

The generator must copy text styles from the base template text materials, not guess a CapCut preset number. CapCut preset buttons are not stable JSON identifiers.

Every generated `capcut_timeline_manifest.json` must include these audit fields:

```json
{
  "timeline_content_start_sec": 0.0,
  "original_source_media": {
    "path": "source.mp4",
    "imported_to_capcut_media": true,
    "has_audio_stream": true
  },
  "audio_normalization_status": "PASS",
  "normalized_audio_assets": [],
  "three_line_text_layout_status": "PASS",
  "script_aligned_timeline_structure": [
    {
      "script_beat_id": "b01",
      "target_range": "0.000-2.000",
      "display_text_lines": [
        {"line_index": 1, "text": "후킹/대사형 문구"},
        {"line_index": 2, "text": "(감정, 상황설명)"},
        {"line_index": 3, "text": "TTS 자막"}
      ],
      "video_segment_id": "video_b01",
      "voice_audio_segment_id": "voice_b01",
      "audio_video_aligned": true,
      "tts_visual_fill_status": "PASS",
      "visual_covers_tts_audio": true
    }
  ]
}
```

For quoted source-speech beats, replace or supplement `voice_audio_segment_id` with `source_speech_audio_segment_id`. For visual-only parenthesized beats, keep the visual segment and set no voice segment unless the user explicitly asked to voice that line.

## Script File And Open Path Report

When a CapCut draft is created or rebuilt, save the script being used for editing under the project/work folder. Prefer:

```text
{work}\edit_script_view.txt
```

The file must be human-readable beside CapCut, with timed lines grouped in the same 3-row display logic:

```text
[00:00-00:02]
1. 후킹/대사형 문구
2. (감정, 상황설명)
3. TTS 자막
```

Rules:

- If `final_script_ko.txt` already exists, copy or derive `edit_script_view.txt` from it; do not invent new text.
- If source dialogue analysis changed the verified `"..."` lines, regenerate `edit_script_view.txt` from the approved final report/script package.
- The completed report must include copyable/openable absolute paths:
  - `각본 파일 열기: {work}\edit_script_view.txt`
  - `프로젝트 폴더 열기: {work}`
  - `CapCut 프로젝트: {draft_name}` or `draft_path` when registered.
- Do not report a CapCut draft as complete if the script file path is missing from the final report.

## CapCut Visual Enhancement Defaults

Apply these defaults to every source-video segment when the CapCut draft JSON supports the fields. If a reference draft has the user's chosen filters/styles, copy those effect templates and randomize from that approved set.

- Quality enhancement: use `HD` as the default, not `UHD`, unless the user explicitly requests UHD.
- Auto adjust / `smart_color_adjust`: enable per video segment.
  - front half of the video segments: random `50-65`
  - back half of the video segments: random `66-80`
- Clear / `clear` / `선명하게`: random `40-70` per split video segment.
- Sharpen / `sharpen` / `선명도`: random `40-70` per split video segment.
- Filter: apply exactly one approved filter per split video segment. Randomize from the user-selected filter set in the reference/current draft, such as `매트 파우더`, `허니 피치`, `옵티클리어` when those are the selected filters.
- Avoid duplicate adjustment effects of the same type on one segment. Each video segment should have at most one `smart_color_adjust`, one `clear`, one `sharpen`, and one `filter` effect.
- Use seeded randomness based on `{draft_name}:rule-name` so repeated rebuilds are reproducible enough to debug.
- Save the chosen values in `adjust_random_report.json` or `status.json`.
- If applying these by direct JSON patch after a draft was created, back up `draft_content.json` first.
- After export, run `render_check` / ffprobe checks for codec, resolution, FPS, bitrate, audio, and pixel stats.

Generated drafts must preserve the Source-Driven Cut And Motion Defaults. If the project generator cannot apply segment speed, 110% scale, or visual-change cuts directly, patch the generated `draft_content.json` before the capcut harness gate and record the patch in `status.json`.

## Video Option Modification Report

Every CapCut draft creation, rebuild, status reply after draft creation, blocked reply after partial draft work, and completed 11short report must include a visible video-option modification report. This report is mandatory evidence for source-similarity reduction and edit auditability.

Record the report in `status.json` and print it in the final chat report. Missing per-segment video-option reporting is `REWRITE_REQUIRED` for the report even if the CapCut harness passes.

Required `status.json` fields:

```json
{
  "video_option_modification_report_complete": true,
  "source_similarity_reduction_direction_ko": "",
  "per_segment_video_option_changes": [
    {
      "target_start": "00:00.000",
      "target_end": "00:00.000",
      "source_start": "00:00.000",
      "source_end": "00:00.000",
      "visual_role_ko": "",
      "source_visual_ko": "",
      "change_summary_ko": "",
      "cut_or_order_change_ko": "",
      "scale": 1.1,
      "speed": 1.1,
      "reframe_ko": "",
      "focus_ko": "",
      "pan_direction": "",
      "mirror": false,
      "filter_name": "",
      "smart_color_adjust": 0,
      "clear": 0,
      "sharpen": 0,
      "ocr_cover_or_middle_overlay_ko": "",
      "bottom_caption_ko": "",
      "audio_bgm_sfx_ko": "",
      "reason_ko": ""
    }
  ],
  "hook_forward_report_ko": "",
  "bgm_report_ko": "",
  "sfx_report_ko": "",
  "adjust_random_report_file": "adjust_random_report.json"
}
```

Per-segment report rules:

- Report every target segment that changes source order, speed, scale, crop, zoom, pan, mirror, filter, adjustment, OCR cover, middle overlay, bottom caption, BGM, or SFX.
- Use exact `target_start-target_end` and `source_start-source_end` times. If source and target times are the same, still report them.
- For hook-forward previews or duplicated source ranges, explicitly say which source range was pulled forward and where the chronological flow resumes.
- For unchanged chronological segments, report `cut_or_order_change_ko=원본 순서 유지` and still list scale, speed, filter, color, clear, sharpen, captions, and audio choices.
- If an option is intentionally not used, write the reason, for example `mirror=false: 로고/문자 보호`.
- If the draft generator cannot apply an option and a JSON patch is needed, report the patch file/path and rerun the `capcut` and `all` harness gates.
- Do not use vague wording such as `전체적으로 보정`. The report must say what changed in each time range.

Required visible block:

```text
영상옵션수정보고
[00:00.000-00:02.000] source 00:10.200-00:12.200
- 화면역할:
- 원본화면:
- 변경:
- 컷/순서:
- 스케일/속도:
- 리프레임/팬/미러:
- 필터/색보정/선명:
- 중단/하단 반영:
- 오디오/BGM/SFX:
- 이유:
```

CapCut draft generation is complete only when the draft is a visible local CapCut project, not merely a generated profile JSON, status file, or preview render. After the generator runs:

- Confirm the draft folder exists under the active CapCut draft root (`%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\{draft_name}` on Windows, or the configured Mac mini draft root).
- Confirm the draft is registered in CapCut's project index (`root_meta_info.json`) or by the generator's equivalent registration path, so it appears in the CapCut home/project list after refresh or restart.
- Record the exact `draft_name`, `draft_dir`, and `draft_content.json` path in `status.json` or the work report.
- Run `shorts_remake_harness.py "{work}" --stage capcut --draft-name "{draft_name}"` before calling the project ready.
- Report the exact CapCut project name and local path to the user. If CapCut UI is already open and stale, say to refresh/restart, but still complete registration on disk first.

If the user asks for a custom/test layout variant or text-effect shell, create/register it as a separate CapCut project and label it as a custom/test draft, not the normal 3-text harness profile.

## Post-Report SRT And Voice Update Loop

After a 11short CapCut draft is created and reported, the job remains editable. If the user later provides SRT, caption text, voice script, or voice audio for that same draft, treat it as a follow-up patch request for the existing 11short project instead of starting a new analysis.

- Resolve the work folder and registered `draft_name` from the last `캣컵프로젝트파일 복사용`, legacy `프로젝트검색용 이름`, `status.json`, `production_console.json`, handoff manifest, or CapCut draft folder.
- Save user-provided caption/SRT content into the matching current files such as `onscreen_ko.srt`, `voice_opening.srt`, or `voice_segments.srt`. Keep a backup copy when replacing an existing file.
- Save user-provided voice text into `tts_lines.txt`, `tts_segments.json`, or `voice_opening.txt`. If the user gives text only, do not generate TTS until they explicitly request voice generation; ask or proceed only when the request clearly says to make audio.
- If the user provides voice audio files, or explicitly asks to generate audio, add the audio to the CapCut project as native local audio tracks and pass the matching SRT with `--intro-audio`, `--voiceover-audio`, and `--voiceover-srt` as applicable.
- The updated CapCut project must open with SRT/caption text and voice audio already placed on the timeline. Do not only save loose `.srt`, `.txt`, or `.mp3` files in the work folder.
- If the just-created draft has not been manually edited, rebuilding the same draft is allowed. If the draft may contain user edits, create a suffixed copy such as `{draft_name}-srt`, `{draft_name}-voice`, or `{draft_name}-fixed` unless the user explicitly asks to overwrite the current draft.
- Re-run `shorts_remake_harness.py "{work}" --stage capcut --draft-name "{updated_draft_name}"`, then `--stage all` when applicable. Verify `draft_content.json` contains the new text/audio materials and report the updated draft name/path.
- Record the update in `status.json` with fields such as `user_srt_applied`, `user_voice_applied`, `voice_to_srt_complete`, `updated_capcut_draft_name`, and `updated_at`.

## CapCut Cloud Upload

Do not upload a generated CapCut draft automatically. Upload only when the user explicitly asks, such as `업로드해`, `올려`, or `TAKKTWO에 올려`.

Default upload destination:

```text
TAKKTWO
```

Upload is a CapCut Desktop UI operation, not a public API call. When asked to upload:

1. Open CapCut Desktop home/project list.
2. Find the generated draft by `draft_name`.
3. Right-click the draft.
4. Choose `업로드`.
5. In the upload destination dialog, choose `TAKKTWO`.
6. Click the right arrow (`>`) to enter the `TAKKTWO` space if required.
7. Click `업로드` when the button becomes enabled.
8. Keep CapCut open until upload completes.

Report:

```text
업로드 요청 수신: 예
draft 이름:
업로드 대상: TAKKTWO
업로드 상태: 완료 / 진행 중 / 실패
실패 원인:
```

If the user has not explicitly requested upload, report only that the CapCut draft is ready and upload is waiting.

## Upload Text Format

When the user asks for YouTube Shorts upload text, always write it in this exact Korean structure:

```text
제목
{curiosity title ending with exactly one lowercase #shorts}

내용
{line 1}
{line 2}

출처:{source_url}

테그
tag1,tag2,tag3,
```

Rules:

- `제목` is a real title, not just a hashtag.
- Do not reveal the result or punchline in the title.
- The title must end with exactly one lowercase plural `#shorts`.
- `내용` should be short copy-ready Korean description lines followed by the source line.
- The source line must be exactly `출처:{source_url}` with no space after `출처:`.
- Use `테그` spelling, not `태그`, unless the user explicitly asks otherwise.
- Keep tags relevant to the video subject and Shorts discovery.
- `테그` uses tag words only, without `#`. Put a comma immediately after every tag, including the final tag.

## Required Files Per Work Folder

Expected folder:

```text
${env:UTUBE_ROOT}\11short\000short-production-agent\episodes\{date-profile}
```

Required or expected files:

```text
source.mp4
source_original_audio.mp3
analysis_raw_gemini.json
analysis_master_gemini.md or analysis_master_gemini.json
analysis_crosscheck.md
analysis.json
onscreen_ko.srt
onscreen_layout.json
voice_segments.srt when generated/user-supplied voice is requested
tts_segments.json when generated/user-supplied voice is requested
render_plan_pre_capcut.json
production_gate_contract.json
production_gate_result.json
capcut_timeline_manifest.json after CapCut draft creation
post_capcut_timeline_gate_result.json after CapCut draft creation
voice_opening.txt when generated/user-supplied voice is requested
voice_opening.mp3 when generated/user-supplied voice is requested
tts_lines.txt when generated/user-supplied voice is requested
voice_segments_*.mp3 when generated/user-supplied voice is requested
status.json
shorts_remake_harness_report*.json
exports\
```

Exports from Desktop must be moved into `{work}\exports`. If a file cannot be matched to a profile, move it to:

```text
${env:UTUBE_ROOT}\11short\_desktop_exports_unmatched\exports
```

## Final Chat Report

Every completed 11short remake response must include these upload fields in Korean, even when the main work report already lists draft paths and harness results. The full required report shape is defined in `Required Final Report Blocks For 11short Output`.

```text
제목
내용
테그
```

Rules:

- `제목` is the final upload title, not only the CapCut draft/profile name.
- `제목` must end with exactly one lowercase plural `#shorts`.
- `내용` is a short YouTube description of the situation. Do not over-explain production steps.
- `내용` must end with the first source URL the user provided for the job, formatted exactly as `출처:{url}`. Use the original pasted URL, including query parameters when present. Do not add a space after `출처:`.
- Use `테그`, not `태그`, in 11short final copy reports.
- `테그` must include relevant Korean tag words only, without `#`.
- `테그` must be comma-separated without spaces. Put a comma immediately after every tag, including the final tag.
- If the draft is not fully ready, still include the best current `제목 / 내용 / 테그` package and separately state what remains blocked.
- Do not omit these three fields from the final chat report.

### Final Upload Package Override

Legacy minimum upload package fields:

```text
제목
내용
출처:
테그
```

- Always include these upload fields in the full required final report for every completed 11short job. The complete source of truth is `Required Final Report Blocks For 11short Output`.
- `출처` is a separate line formatted as `출처:{url or source axis}` with no space after `출처:`.
- `테그` uses tag words only, without `#`.
- Every tag must end with a comma, including the final tag.

### Final Middle TTS Copy And CapCut Name Order

Always put the copyable TTS/voice text immediately after the timed `중단` block. The `캣컵 복사하기` block comes after `중단 TTS 글자만 복사` and closes the copy-ready report.

Use this exact Korean label and fenced text block:

```text
중단 TTS 글자만 복사

{voice line 1}
{voice line 2}
{voice line 3}

캣컵 복사하기
{draft_name}
```

Rules:

- This block must be inside the `Current Completion Report Contract Override v3.0` copy-ready report.
- The CapCut project name appears after `중단 TTS 글자만 복사`, not above it.
- Include only timed `중단` lines that should be spoken by TTS/voice.
- Exclude visual-only parenthesized situation/effect/emotion captions such as `(퍽)`, `(가소롭군)`, and `(뭐지..??)` unless the user explicitly asks to voice them.
- If no TTS/voice lines are ready yet, write `중단 TTS 글자만 복사` and put the exact blocker line below it.
- `캣컵프로젝트파일 복사용` is a legacy alias used only for resolving older work folders or previous reports. Do not use it as the current output label.

### Required Final Report Blocks For 11short Output

Every 11short work report after CapCut draft creation must follow
`Current Completion Report Contract Override v3.0`. First print the required
`CapCut 검수` block, then print the compact copy-ready block:

```text
CapCut 검수
draft_name: {draft_name}
draft_path: {absolute local CapCut draft folder}
selected_template: {template name}
openability_gate: PASS / FAIL / WAIT
media_link_gate: PASS / FAIL / WAIT
style_preservation_gate: PASS / FAIL / WAIT
role_track_gate: PASS / FAIL / WAIT
frame_layout_QA: PASS / FAIL / WAIT
harness: analysis={PASS/FAIL/WAIT}, assets={PASS/FAIL/WAIT}, capcut={PASS/FAIL/WAIT}, all={PASS/FAIL/WAIT}

제목
{최종 업로드 제목 #shorts}

내용
{업로드 설명 1}
{업로드 설명 2}

출처:{원본 URL}

테그
tag1,tag2,tag3,

상단
{CapCut 상단 1줄}
{CapCut 상단 2줄}

중단
[00:00.000-00:02.800]
감정: ...
화자...:
대본:

중단 TTS 글자만 복사
...

캣컵 복사하기
{draft_name}
```

Rules:

- Keep the blocks separate so the user can copy each field independently.
- `CapCut 검수` is mandatory after CapCut draft creation. Extra gate/evidence
  details such as `production_gate_result.json`,
  `post_capcut_timeline_gate_result.json`,
  `shorts_remake_harness_report_*.json`, visual preview notes, source-change
  summary, or blocker notes may be reported briefly above the copy-ready block
  when needed. They are not inserted into the copy block.
- If `openability_gate`, `media_link_gate`, `style_preservation_gate`,
  `role_track_gate`, `frame_layout_QA`, or required harness state is not
  `PASS`, state the blocker and keep the status `FAIL` or `WAIT`; do not call
  the CapCut project completed.
- `제목` is the final upload title, not only the CapCut draft/profile name.
- `내용` must include the source line exactly as `출처:{url}` with no space after `출처:`.
- Use `테그`, not `쉼표테그`, in the copy-ready report.
- `상단` must be the exact CapCut top fixed title.
- `중단` must include timed middle captions only. Do not add `하단`.
- `중단 TTS 글자만 복사` must come immediately after `중단` and before `캣컵 복사하기`.
- `캣컵 복사하기` must contain the exact registered CapCut `draft_name` inside a Markdown fenced `text` code block when a draft exists; if not created yet, use the planned draft name and clearly state the blocker above the copy block.
- Do not append platform copy blocks or evidence blocks after `캣컵 복사하기` unless the user explicitly asks for them.
- `중단 TTS 글자만 복사` must include only timed `중단` lines that should be spoken by TTS/voice, without timestamps.
- Exclude visual-only parenthesized situation/effect/emotion captions such as `(퍽)` or `(뭐지..??)` unless the user explicitly asks to voice them.
- Include plain TTS/narration middle lines by default. Include quoted speaker/source lines only when that line is explicitly intended for generated TTS/voice.
- After these blocks, if the user later provides SRT or voice content for this project, apply the Post-Report SRT And Voice Update Loop instead of asking them to recreate the project manually.

## Harness Gates

Run gates in order. Do not proceed after a FAIL:

```powershell
py -3 ${env:UTUBE_ROOT}\11short\shorts_remake_harness.py "{work}" --stage analysis
py -3 ${env:UTUBE_ROOT}\11short\shorts_remake_harness.py "{work}" --stage assets
py -3 {skill_dir}\scripts\validate_production_gate.py "{work}" "{work}\production_gate_contract.json" --out "{work}\production_gate_result.json"
py -3 ${env:UTUBE_ROOT}\11short\shorts_remake_harness.py "{work}" --stage capcut --draft-name "{draft_name}"
py -3 {skill_dir}\scripts\validate_capcut_timeline_order.py "{work}" "{work}\production_gate_result.json" "{work}\capcut_timeline_manifest.json" --contract-json "{work}\production_gate_contract.json" --out "{work}\post_capcut_timeline_gate_result.json"
```

Use `--stage all` only as final confirmation and include `--draft-name` or `--draft-path` when capcut is involved.

Do not run the CapCut harness until `production_gate_result.json` is `PASS`. Do not run or report final `--stage all` as upload-ready evidence until `post_capcut_timeline_gate_result.json` is `PASS`.

## Visual Truth Rule

Harness PASS is necessary but not sufficient. If the user's screenshot or CapCut preview shows a layout problem, call it FAIL.

Review response format:

```text
판정: PASS / FAIL
기준: 3텍스트 구조 + SHORTS_REMAKE_CONTRACT.md + visual check
문제:
- ...
다음 조치:
- ...
검증:
- analysis: PASS/FAIL/not run
- assets: PASS/FAIL/not run
- capcut: PASS/FAIL/not run
```

If harness passes but visible output fails, write:

```text
하네스는 PASS지만 시각 기준에서 FAIL입니다.
```

## Reframe And Duplicate Avoidance

- Cut video by visual action beats, not only by narration or bottom-caption beats.
- First scan the source at 1-second granularity.
- Only split finer than 1 second when that 1-second window contains a sudden screen transition, source cut, composition jump, or major action change.
- For transition windows, refine by frame-difference/visual inspection to the true cut point, then split only that affected second. Example: `12.000-13.000` becomes `12.000-12.733` and `12.733-13.000`.
- Ranking/TOP-N transitions are mandatory precision windows. When a rank/title/number/item boundary appears inside a 1-second scan bucket, rescan that bucket at `0.2` to `0.4` second intervals or with frame-difference inspection, record the exact cut boundary, and use that boundary for the CapCut split.
- For ranking/TOP-N or sequence-order jobs, insert the MP4 asset `$env:UTUBE_ROOT\11short\assets\ranking_separator\랭킹순서사이효과.mp4` between rank/item sections after the order remix. `랭킹중간` is a legacy CapCut preset name only. If the visible draft has no separator asset between ranking beats, mark the ranking placement gate `FAIL`.
- Do not micro-split stable seconds. If the picture does not change, keep the 1-second unit or merge adjacent stable seconds by action.
- Record refined transition boundaries in `source_scene_transitions_precision.json` when precision splitting is required, and mark `precise_scene_transition_check_complete=true`.
- Keep only true holds, reveals, or final freeze/extension beats longer than `3` seconds.
- If source action changes inside one caption, split the caption/overlay/analysis segment too so the CapCut video track has precise cuts.
- Use `segments[].reframe.focus_bbox` for important action.
- Default every source video segment to `scale=1.10` (110%). Normal range: `1.10` to `1.25`; up to `1.35` only when the subject is small.
- Default every source video segment to `speed=1.10x` (110%) unless the user explicitly asks otherwise or source-audio sync would fail.
- Prefer automatic subtle zoom/pan based on the visible subject, not static full-frame duplication.
- Use `pan_direction` and `focus_center` to keep the subject visible.
- Mirror only when `mirror_allowed=true`.
- Never mirror readable text, logos, jersey numbers, left/right-sensitive action, or direction-sensitive motion.
- Before success, check that crop did not cut off faces, hands, captions, or the important action.

## Draft Safety

- Never overwrite a user-edited CapCut draft.
- If a draft name exists, create a new suffix or explicitly back it up first.
- Treat `failed_previous_drafts` in `status.json` as failed references.
- Do not group text, stickers, vectors, or shapes.
- Text segments and materials must have unique ids.
- If moving one text layer moves another layer, the draft fails.

Windows CapCut draft root:

```text
$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft
```

Mac mini CapCut draft root is usually:

```bash
~/Movies/CapCut/User Data/Projects/com.lveditor.draft
```

For Mac mini production, set:

```bash
export SHORT_ROOT="$HOME/Library/CloudStorage/OneDrive/22utube/11utube/11short"
export TOOLS_ROOT="$HOME/Library/CloudStorage/OneDrive/22utube/11utube/tools/youtube_ko_subtitles"
export LOCALAPPDATA="$HOME/Movies"
```

Use `python3` on Mac instead of `py -3`. Keep the OneDrive `22utube` folder local with "Always Keep on This Device" so `ffmpeg`, Python, and CapCut can read real files.

## Shared Production Console Requirement

This dedicated Shorts skill must also obey the shared `22utube-production-agent` production console and progress-board rules.

- Use `phaseMap: 11short_remake_production`; do not use the 0shrt `script/imagegen/audio/capcut/final` package checklist as this skill's gate.
- n8n board phases are URL/source intake, source download, Gemini/AI Studio analysis, normalized `analysis.json`, TTS/SRT/assets, CapCut draft, report.
- Harness phases are `analysis`, `assets`, `capcut`, then final `all` when applicable. Required evidence is remake evidence: `source.mp4`, `analysis.json`, `onscreen_ko.srt`, `onscreen_layout.json`, CapCut draft manifest/name, and the locked visible text classes. Voice segment files such as `voice_opening.*`, `tts_segments.json`, `voice_segments.srt`, and `voice_segments_*.mp3` are required only when generated/user-supplied voice was explicitly requested.
- Do not block 11short only because 0shrt-only files such as `image2_manifest.json`, `job_state.json`, `evidence_pack.json`, or `final_report.md` are missing.
- Every YouTube production status report must start with the compact `[ 진행판 ]` board: n8n execution, harness validation, current blocker, and next action.
- The visible TODO/status report must include the full `A. n8n 실행` / `B. 하네스 검증` board from `22utube-production-agent`; do not replace it with prose-only status.
- Template gate for generic 11short/쇼츠공장 production: do not ask a generic template question when the mandatory channel/template routing has already produced a default. Use the routed template unless the user explicitly overrides it. If routing is missing or ambiguous enough to change the template, ask before creating a draft: `블랙기본`, `인스타템플릿`, `일반템플릿`, or another user-named template such as `정치템플릿`.
- **DRAFT_FAST / FINAL_LOCK mode gate**: every 11short factory run is `DRAFT_FAST` by default. The user must explicitly say `FINAL_LOCK`, `최종 업로드용`, `업로드 준비`, or equivalent to switch to `FINAL_LOCK`.
  - `DRAFT_FAST` (default): CapCut 초안 생성 후 DRAFT_FAST 체크만 한다. 템플릿 복사 확인, placeholder 영상 제거, 실제 source video 연결, `랭킹중간` 또는 지정 separator 삽입(랭킹/순서형), 0.2~0.4초 정밀 컷, 하단/bottom-caption 금지, `상단 + timed 중단` 구조 준수를 검증한다. `SCRIPT_LOCK`, `production PASS`, `upload_ready`를 쓰지 않는다. 5-persona reader gate, full writer harness, YouTube policy full gate를 강제하지 않는다.
  - `FINAL_LOCK` (user must explicitly request): 전체 Writer Harness Checklist, 5-persona reader gate, YouTube policy gate, SCRIPT_LOCK, `production_gate_result.json` PASS, `post_capcut_timeline_gate_result.json` PASS, capcut/all harness PASS, upload_ready 검수를 실행한다. `SCRIPT_LOCK`, `production PASS`, `upload_ready`는 FINAL_LOCK일 때만 쓴다.
- **CapCut T-track contract**: `T1/T2/T3`는 작업 단계명이 아니라 CapCut 내부 텍스트 트랙 순서다. `T1=소제목1`, `T2=소제목2`, `T3=TTS/나레이션 자막`, `T4=화자발언1(검증된 " "만)`, `T5=화자발언2(검증된 " "만)`, `T6=(현장상황/행동/감정설명)` 순서를 유지한다.
  - `V7=템플릿 배경/랭킹중간/전환용 클립`, `V8=실제 영상 짜집은 source clip`을 기본 영상 역할로 쓴다.
  - `A9=원본음성/BGM/랭킹 기본 배경음`, `A10=TTS/효과음/나의 사전 설정 효과음`을 기본 오디오 역할로 쓴다.
  - 오디오/TTS/BGM/SFX 삽입은 A트랙에만 추가한다. 오디오 삽입 때문에 기존 `T1~T6` 텍스트 트랙 순서/역할/세그먼트를 바꾸면 `FAIL`.
  - 오디오 삽입 후 반드시 실제 `draft_content.json`에서 track order와 track type을 재검사한다. T트랙에 오디오/비디오 segment가 들어가거나 A트랙에 text segment가 들어가면 `FAIL`.
- Template routing: user-explicit wording still wins. If the user says `인스타`, `인스타용`, `인스타로 만들어`, or `릴스`, clone/use `인스타템플릿`. If the user says `블랙`, `블랙기본`, `블랙템플릿`, or black-band layout wording, clone/use `블랙기본` unless the operator has explicitly mapped the local base name to `블랙템플릿`. If the user says `일반`, `기본`, `유튜브`, or normal Shorts wording, clone/use `일반템플릿`. If the user only says `만들어`, `프로젝트까지`, `쇼츠공장 돌려`, `가자`, or similar generic wording, use the mandatory routing proposal as the default template; ask only when the routing gate cannot decide.
- CapCut draft creation means template-copy + `draft_content.json` media/text replacement. FFmpeg cannot create editable CapCut `T1~T6` tracks; FFmpeg is only allowed for `ffmpeg_render_match` final MP4 preview/render that visually matches the selected template.
- Instagram/Reels requests must read and follow `$env:UTUBE_ROOT/11short/INSTAGRAM_LAYOUT_CONTRACT.md` when that contract is explicitly selected, but the production base for current factory work is `인스타템플릿` unless the user names another actual CapCut template. Keep the selected template's saved font, color, position, animation refs, BGM, SFX, and safe-area layout by default.
- Template selection means one of the two defaults in `manifests/capcut-template-set.json`: `black` or `insta white`. Settings JSON is a replacement-value list only; never build a lookalike project from `source.mp4 + PNG + text`.
- Instagram/Reels creation must copy the `insta white` master draft folder first. Black-template creation must copy the `black` master draft folder first. Preserve `draft_content.json`, `draft_meta_info.json`, `draft_virtual_store.json`, `subdraft`, `Resources/combination`, `materials.drafts`, preset audio placeholder relationships, sticker/effect rows, 10 total tracks, 4 editable text tracks, and z-order. Then replace only current job `source.mp4`, visible text, timing, and TTS/audio values.
- The internal source in both defaults is test media only. Generated work must replace `test.mp4` or any placeholder source with the job source.
- `260625-ig-contortion-top3-urakkai-instagram-tts-fixed` is forbidden as a base. A draft with `Default`, `T1`, or `T2` visible placeholder text or a stale 98-second tail is FAIL.
- `T6` situation captions may overlap `T3`, `T4`, or `T5` when they explain the same screen moment. `T4/T5` are for verified source speech only. Invented or creative lines must go to `T3` or `T6`, never to `T4/T5`.
- The video material inside a selected template may be placeholder media. After cloning the template, replace placeholder source video/audio with real job media while preserving template structure, `subdraft`, `Resources/combination`, and `materials.drafts`.
- General/basic Shorts production must clone or derive from the CapCut preset/template `일반템플릿`. A generic draft built from the old normal fallback without the selected preset fails the template gate.
- Black-template production must clone or derive from `블랙기본`, keep the top/bottom black bands, place `T1/T2` as white bold top-band text, and keep timed body captions inside the video-safe area. If the local CapCut base is still named `블랙템플릿`, use it only after an explicit operator alias mapping and record that alias in the status/report.
- FFmpeg render-match jobs must use the same common role contract (`T1~T6`, `V7/V8`, `A9/A10`) and must output 1080x1920, 30fps, h264+aac, source audio preserved unless explicitly muted by the plan, no visible timecodes, no bottom-caption layer, and no unverified quoted speech.
- General/basic Shorts production must clone or derive from the CapCut preset/template `일반템플릿`. A generic draft built from the old normal 3-text fallback without the selected preset fails the template gate.
- The OneDrive Instagram setup folder must contain the form image, top-left cat video, and bottom-right animal image together. If another PC cannot resolve Korean asset names, use the ASCII aliases in the same folder: `instagram_form_pixel_frame.png`, `instagram_cat_top_left.mp4`, and `instagram_animals_lower_right.png`.
- Instagram-only production from a new source: if the user asks from the beginning to make only an Instagram/Reels version, still run normal 11short source intake, Gemini/source analysis when needed, `analysis.json`, SRT, OCR layout, source-original-audio extraction, BGM decision, and `analysis/assets` gates. Do not create the normal YouTube 3-text CapCut master unless the user also asks for it. Create the first visible CapCut draft directly from `인스타템플릿` as `{episode_id}-인스타` or the requested Instagram draft name unless the user explicitly asks for a legacy shell.
- For Instagram-only production, set `target=instagram_reels`, `instagram_status=created`, `youtube_master_draft_created=false`, `instagram_draft_name`, `instagram_draft_dir`, and `instagram_original_audio_track=true`. Mark normal 11short `capcut/all` harness as `N/A - instagram custom layout`, keep n8n as `WAIT - local run; n8n webhook not invoked` when not invoked, and run the Instagram-specific JSON/audio/layer/ffprobe/frame QA.
- Existing Shorts to Instagram conversion: if the user asks to make an already-created 11short draft into Instagram/Reels, do not rerun Gemini/source analysis or rebuild the YouTube master. Resolve the existing work folder and `capcut_draft_name` from the user's draft name, `status.json`, `production_console.json`, handoff manifest, or local CapCut root; then create a separate `{existing_draft_name}-인스타` draft from `인스타템플릿` unless the user explicitly asks for a legacy shell.
- Reuse existing files for conversion: `{work}\source.mp4`, `{work}\source_original_audio.mp3`, `{work}\onscreen_ko.srt`, `{work}\onscreen_layout.json`, top title, timed middle captions, optional voice segment files, and any existing BGM decision in `status.json`.
- Do not overwrite the YouTube Shorts master draft. Convert only project-specific media/text inside the Instagram shell: main source video, top title, timed middle captions/T3~T6 role text, optional reaction/punch text, source original audio A-track, and optional BGM.
- Instagram audio conversion must keep original sound as a separate native CapCut audio track. Mute the main video track if needed, add `{work}\source_original_audio.mp3`, add animal BGM only for animal jobs or when the YouTube draft already used BGM, and avoid extra BGM for music/dance/source-audio-centered clips.
- Instagram conversion verification must check `draft_content.json`, `draft_meta_info.json`, source video/audio existence, source original audio material and track presence, fixed Instagram visual layers, ffprobe duration, and at least one frame/screenshot QA. Update `status.json` with `instagram_status=created`, `instagram_target=instagram_reels`, `instagram_draft_name`, `instagram_draft_dir`, `instagram_original_audio_track=true`, and the actual `instagram_harness_state`.
- Before user review and harness PASS, file names and reports must say `REVIEW` or `DRAFT`, never `FINAL`.
- Use `$env:UTUBE_ROOT\tools\production_console` for scene-level review/editing.
- Save scene edits inside the current episode/work folder as `production_console.json`; do not create a new production root.
- If the user splits a cut or image, update `production_console.json` first, then regenerate or relink audio, SRT, prompt, image, and layout assets from that updated scene plan.
- Update `production_console.json` at every major stage: source analysis, assets, audio, CapCut, render/export, ffprobe, frame QA, and final gate. If `http://127.0.0.1:47831/api/episode` is available, use it to load/save the episode status.
- If the work is local and n8n was not invoked, mark n8n as `WAIT` with `local run; n8n webhook not invoked`. If Compound has no linked log, mark it as `WAIT - compound log not linked`.
- The console summary must include title, content summary, tags, total duration, voice mode, voice model/version and voice_id by role when voice is explicitly requested (otherwise `N/A`), target, `instagram_status`, output video path, n8n state, harness state, Compound state, blocker, and next action.
