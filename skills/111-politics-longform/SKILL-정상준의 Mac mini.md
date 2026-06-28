---
name: 111-politics-longform
description: Use when the user says 111정치롱폼, 정치롱폼, 민주진영 유튜브, 매불쇼 롱폼, 유시민 롱폼, or asks to make/update a Korean political longform CapCut draft, T1 chapter text, YouTube upload package, channel profile, keywords, or thumbnail hooks for a 민주진영 political commentary channel.
---

# 111 Politics Longform

## Core Rule

Use the user's locked political longform setup as the base:

```text
CapCut project: YM007_maebulshow_yusimin_20m_rcut
Route: keep the setup, replace only the source video/media unless the user says otherwise.
Source label: 출처 매불쇼
```

Do not rebuild the style from scratch. Preserve the template feel: top source label, top subscribe line, lower T1 explanation lane, 1280x720 political commentary layout, and source-audio longform flow.

## Workflow

1. Resolve the episode and CapCut draft.
   - CapCut root usually lives under `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft`.
   - For source evidence, prefer the episode folder under `22utube\11utube\yellow\episodes\...`.
   - Read `edit\roughcut_edl.json`, `edit\segment_markers_hq.srt`, `source\M1\source.ko.srt`, `analysis\srt_items.json`, `upload_description.md`, and `report.md` when present.

2. Keep CapCut visible text roles separate.
   - Top source: `출처 매불쇼`.
   - Top subscribe line: keep as-is unless asked.
   - Lower T1: chapter-by-chapter explanatory commentary.
   - Never show internal ids such as `M1-1`, `M1-2`, `roughcut`, `edl`, or `진입`.

3. Write lower T1 from the actual speech.
   - Start at `00:00`; do not leave the opening empty.
   - Maintain continuous flow through the full roughcut unless the user asks for sparse notes.
   - For a 20:30 cut, target about 40-50 lower T1 segments, not 8-18.
   - Use `챕터1_`, `챕터2_`, `챕터3_` labels that match viewer-facing topic sections.
   - Each item should be 1-2 lines: first line summarizes what the speaker is saying, second line adds concise interpretation/opinion.
   - Be concrete: name the actor, claim, issue, or consequence. Avoid abstract filler such as `민심을 챙겨야 합니다`, `정치가 중요합니다`, or generic advice.
   - Positive opinion is allowed, but keep it tied to the exact claim: `이 분석은 구조를 보게 만든다`, `이 지점은 민주당이 아프게 들어야 한다`.

4. Chapter mapping for the saved 매불쇼 유시민 example.
   - `00:00` chapter 1: 유시민 등장, 사전투표, 선거 토론의 판 세팅.
   - `02:20` chapter 2: 선거 의미, 내란 청산, 이재명 정부 동력, 보수/극우 제도화 분석.
   - `07:46` chapter 3: 민주당, 조국혁신당, 범민주 진보 진영, 포용력과 대선 후보군.
   - `14:16` chapter 4: 내부 경쟁의 폭력성, 당원 압박, 투표 전략과 민주당 지도부 책임.

5. CapCut JSON update rules.
   - Back up `draft_content.json` and `template-2.tmp` before edits.
   - Patch both project root files and matching `Timelines/*/draft_content.json`, `Timelines/*/template-2.tmp` cache files.
   - Use UTF-8 Python IO. Avoid PowerShell inline Korean strings for JSON writes; store Korean text in UTF-8 JSON or patch via `apply_patch`.
   - After writing, verify segment count, first start time, last end time, gap count, and forbidden terms.

Verification pattern:

```text
lower T1 segment count: 40-50 for 20m
first_start: 0.00
last_end: roughcut end
gap_count: 0 unless intentionally sparse
forbidden visible terms: M1-, roughcut, edl, 진입
mojibake scan: use the project's Korean Encoding Constitution patterns, including common CP949 mojibake and Unicode replacement character U+FFFD
```

If CapCut is open or background processes remain, tell the user to fully close CapCut before reopening the draft.

## Upload Package

For longform upload text, do not apply Shorts `#shorts` title rules.

Use this structure:

```text
제목
{person/source issue hook}｜{viewer reason to click}

내용
출처 매불쇼

{one-paragraph summary of what this edit explains}

00:00 {topic line with a logical one-sentence explanation}
02:20 {topic line with a logical one-sentence explanation}
07:46 {topic line with a logical one-sentence explanation}
14:16 {topic line with a logical one-sentence explanation}

출처
- 원본 채널:
- 원본 영상:
- 원본 URL:
- 원본 업로드일:

{3-5 hashtags}
```

Timestamp lines must not be bare labels. Write what the section argues and why it matters.

## Channel Setup

If the user asks to convert a channel to 민주진영 political YouTube, use this baseline:

```text
채널 이름: 민주 디코더
핸들: @minju_decoder_kr
설명 첫 줄: 정치 뉴스 뒤에 숨은 흐름을 민주진영의 시선으로 정리하는 채널입니다.
```

Keyword baseline:

```text
민주당, 이재명, 유시민, 매불쇼, 민주진영, 정치해설, 시사해설, 검찰개혁, 언론개혁, 내란청산, 국민의힘, 조국혁신당, 범민주, 진보진영, 정치뉴스, 한국정치, 선거분석, 여론분석, 국회, 대통령, 윤석열, 김어준, 뉴스공장, 정치비평, 진보유튜브, 민주당유튜브, 정치유튜브, 시사유튜브
```

## Thumbnail Package

When asked for a thumbnail prompt, provide:

```text
강한훅 1줄
{urgent political hook}

다음훅 2줄
{specific person or issue}
{specific conflict or warning}

이미지 프롬프트
1280x720 YouTube political commentary thumbnail...
```

Rules:
- Hook must be concrete, not generic.
- Use the actual person/issue: `유시민`, `이재명`, `민주당`, `내란 청산`, `폭력적 방식`, `적신호`.
- Avoid fake claims, caricature, flames, or distorted faces.
- If source is a real show frame, keep the thumbnail as political commentary, not impersonation.

## Policy

Political content is allowed as commentary, but keep source attribution visible and description-level EDSA context clear. Do not claim upload-ready/final if source reuse rights or fair-use judgment has not been checked.
