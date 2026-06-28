---
name: 000brainstorm
description: Use first when the user says $000brainstorm, $brainstorm, brainstorm, 브레인스토밍, 브레인스톰, 찰떡같이 이해, or gives a messy production request that must be interpreted before execution. Forces a short Korean intent brief before file edits, media generation, API calls, n8n runs, or production work.
---

# 000brainstorm

This skill is a mandatory pre-work intent gate. It does not replace production skills. It runs first, then the selected production skill runs second.

## Current 11short Factory Override - 2026-06-13

For current 11short/쇼츠공장 work, this skill is only the intake and routing gate.
It must not override `000short-production-agent` production decisions.
The `000short-production-agent` source-verified validation contract wins over
older voice-intake text below. Do not force ElevenLabs/Scribe or user-supplied
SRT/audio/ZIP for ordinary current 11short factory jobs unless the user
explicitly chooses that external handoff route.

Current route when the user gives a YouTube URL plus an existing Gemini analysis:

```text
000brainstorm intent brief
-> 000short-production-agent owns source download/evidence/watch verification
-> Gemini is saved as raw intake and cross-checked, not treated as fact authority
-> 00-tikitaka writes 상단 + timed 중단 + 중단 TTS 글자만 복사
-> 00script-writer/writer gate; SCRIPT_LOCK only after any required source timecodes are user-confirmed
-> requested Supertone/Chunsik TTS if explicitly requested
-> SRT/layout/render_plan
-> CapCut draft
-> harness
```

## Mandatory 11short Channel/Template Proposal Gate - 2026-06-25

For every 11short/Shorts source URL, Gemini intake, Tikitaka script, SRT/layout,
TTS, CapCut, or upload-package request, the first brainstorm brief must include
a concrete upload-channel and CapCut-template proposal before any downstream
skill starts.

Routing authority:

```text
$env:UTUBE_ROOT\tools\youtube_channel_router\channel_routing_rules.json
```

If the routing file exists, read and apply it. If it is missing, use these
fallback defaults:

- `우니웃니`: `블랙기본`; shopping, life hacks, household tools, product
  experiments, mystery items, Coupang Partners. Generic `정보/지식` goes here
  only when the object is a product, tool, household problem, or product test.
- `난감동란`: `인스타템플릿`; funny scenes, overseas humor, funny 해짜, 예짜,
  variety, funny rankings, body gag, challenge/fail/comedy compilations.
- `별별지구인g9`: `인스타템플릿`; person rankings, information-led stories,
  knowledge/information, brand/craft/world stories, unusual jobs, history or
  object backstories.

The first brief must state:

```text
- 추천 업로드 채널:
- 추천 템플릿:
- 주제/카테고리 판정:
- 추천 이유:
- 제외/보류 채널:
- 라우팅 확신도:
```

Do not wait until CapCut creation to make this recommendation. State it before
`00-tikitaka`, `000short-production-agent`, source download, TTS/SRT, n8n, or
CapCut work. If the source is ambiguous, still recommend one default and mark
the uncertainty. Ask one concise question only when the ambiguity would change
the channel/template decision.

For current 11short 우라까이/script requests, the intent brief must route the
script as `기능 구조 우라까이`. Numeric `1-2-3-4-5` labels are allowed only as
temporary source-segment IDs for the user's exact timecode confirmation; they
are not the creative structure by themselves. The expected script-side sequence
is:

```text
원본 기능 구조 분석
-> 초벌대본 작성: 상단 + timed 중단 + Codex 제안 원본 분초
-> PROPOSED_SOURCE_TIMECODE: Codex가 먼저 구간별 분초를 정하되 최종 확정으로 부르지 않는다
-> USER_TIMECODE_CHECK_REQUIRED: 사용자가 초벌대본과 제안 분초가 맞는지 중간 검수
-> USER_CONFIRMED_SOURCE_TIMECODE: 사용자가 맞다고 하거나 수정값을 주면 그 값으로 확정
-> 우라까이 3가지 버전
   A. 반전 선공개형
   B. 갈등 증폭형
   C. 감동 회수형
-> 선택/잠금 버전만 000short production handoff
```

In the brief, put this under `자막/화면 규칙` or `금지/주의`:

```text
숫자 구조 X, 기능 구조 O. 1/2/3/4/5는 사용자 초구간 확인용 ID로만 쓴다.
Codex가 먼저 원본 분초를 제안하되 PROPOSED_SOURCE_TIMECODE로 표시한다.
사용자 확인 전 제안 분초로 CapCut 최종 제작을 하지 않는다.
초구간 요청은 구간표만 먼저 주는 방식이 아니라, 초벌대본과 제안 분초를 먼저 보여준 뒤 그 대본 블록 기준으로 받는다.
```

User source timecode lock:

- When the user says they will provide exact `1/2/3/4/5` source ranges after
  checking the draft, first output the rough script/report with Codex-proposed
  source ranges, then attach this check sheet derived from the rough script
  blocks:

```text
중단 초벌대본
[블록 1 | 편집 00:00-00:03 | 원본 제안 00:22-00:30 | 상태 PROPOSED_SOURCE_TIMECODE]
{초벌대본 문장}

구간 초단위 확인표
1번: {초벌대본 블록 문장/장면 설명} | Codex 제안 원본: 00:22-00:30 | 사용자 확인: USER_TIMECODE_CHECK_REQUIRED
2번: {초벌대본 블록 문장/장면 설명} | Codex 제안 원본: 00:07-00:13 | 사용자 확인: USER_TIMECODE_CHECK_REQUIRED
3번: {초벌대본 블록 문장/장면 설명} | Codex 제안 원본: 00:30-00:40 | 사용자 확인: USER_TIMECODE_CHECK_REQUIRED
```

- Accept user replies such as `1번 맞음`, `2번 00:08-00:13으로 수정`,
  `3번 빼고 4번 먼저`.
- Treat those replies as correction values for the already-written rough script,
  not as permission to reinterpret the scene order from scratch.
- After the user supplies exact ranges, Tikitaka may rewrite the selected
  sequence with `[편집 ... | 원본 ...]`.
- Do not invent exact original source times from Gemini/GPT summaries. If
  watch/frame evidence suggests a range, mark it as `PROPOSED_SOURCE_TIMECODE`
  and keep production at `USER_TIMECODE_CHECK_REQUIRED` until the user confirms
  or corrects it.

Do not ask for `1번 제미나이 분석본` when the user already provided Gemini analysis.
Do not stop at report-only or ask the user to create SRT/audio/ZIP when the user
has explicitly authorized Supertone, Chunsik, TTS, or voice generation for this job.
Do not force ElevenLabs for source-dialogue analysis unless the source contains
verified speech that must be checked and the production skill requests it.

## Trigger

Use this skill when the user says any of:

```text
$000brainstorm
$brainstorm
brainstorm
브레인스토밍
브레인스톰
찰떡같이 이해
```

Also use it when the user gives a large, messy, ambiguous, or high-risk production request and expects Codex to infer the real task.

## Output First

Before editing files, generating media, calling APIs, running n8n, or starting production, output this brief in Korean:

```text
Brainstorm
- 사용 의도:
- 작업 종류:
- 입력 소스:
- 원하는 결과물:
- 적용 스킬/프로젝트:
- 추천 채널/템플릿:
- 보이스/모델/API:
- 자막/화면 규칙:
- 파일/폴더 규칙:
- 금지/주의:
- 내가 둔 가정:
- 애매한 점:

Execution TODO
- [ ] 필요한 규칙/스킬 확인
- [ ] 입력 자료 확인
- [ ] 산출물 생성 또는 수정
- [ ] 하네스/QA 확인
- [ ] 결과 보고
```

## Behavior

- If the request is only a question, answer after the brief unless the user asked for the brief only.
- If the request asks for production or file changes, do not edit files until the brief is shown.
- If another production skill applies, name it under `적용 스킬/프로젝트`, then follow that skill.
- If a required ambiguity blocks the work, ask one concise question after the brief.
- If the ambiguity does not block work, state the assumption and proceed.
- Keep the brief short and operational.

## Source-Video Frame Gate

For source-video Shorts/remake requests, the first decision is the story frame, not the caption wording.

- If the source's core situation is obvious, state the chosen frame and proceed.
- If the source can be read as multiple genres or the reversal is uncertain, show 2-3 possible frames and recommend one before production.
- The frame brief must include:
  - `제가 본 상황:`
  - `가능한 풀이:`
  - `추천 프레임:`
  - `추천 이유:`
  - `확인 필요:`
- Do not infer sensitive conditions as fact from appearance alone. Phrase uncertain setup as `도움이 필요한 줄`, `못 움직이는 줄`, `다들 착각한 줄` unless the source explicitly states otherwise.

## 11short Voice/TTS Intake Gate

Legacy external-handoff route. Use this section only when the user explicitly
chooses user-supplied SRT/audio/ZIP or external voice handoff. For ordinary
current 11short factory jobs, `000short-production-agent` owns Whisper/OCR/VAD,
target phrase verification, segment decisions, and any explicitly authorized
Supertone/Chunsik generation.

For source-video Shorts/remake requests, do not treat TTS as an automatic generation step.

- Use this route only when the user explicitly requests external user-supplied SRT/audio/ZIP.
- In that legacy route, download/locate source first, deliver the report/script,
  then wait for the user package before CapCut.
- In ordinary current 11short factory jobs, do not set
  `voice_status=WAIT_USER_SRT_AUDIO` or
  `capcut_status=BLOCKED_UNTIL_USER_SRT_AUDIO`; route to
  `000short-production-agent` v5 instead.
- Legacy external handoff ask:

```text
TTS 만들 글자입니다. 이걸로 음성/SRT/ZIP 만들어서 주세요. 받으면 캣컵 프로젝트 만들겠습니다.
```

- Do not silently use Edge TTS, ElevenLabs, Supertone, Kokoro, browser TTS, or any fallback provider just because a key exists or because production needs audio.
- If the user already gave WAV/MP3/SRT/ZIP, treat those files as the voice authority and pass them to the production skill.
- The intent brief must include `핵심 원인/사건:` for police, rescue, hospital, accident, justice, exposure, or conflict videos. The story must answer `그래서 뭔데? / 왜 그렇게 됐는데?` before production starts.
- If the verified core event is sensitive, keep the wording restrained but clear. Do not replace the core cause with vague safe-sounding text when it makes the story incomprehensible.

## Special Rule

When the user writes `$brainstorm` together with another skill name or production request, this skill runs first, then the named production skill runs second.
