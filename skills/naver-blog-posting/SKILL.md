---
name: naver-blog-posting
description: Use when the user asks to write, draft, publish, or report a Naver blog post with triggers such as 글작성하자, 블로그 글쓰자, 메인키워드, 어디블로그, 승인후 작성, 작성후 링크보고, 11the, hauzee1, blog_a, or blog_b.
---

# Naver Blog Posting

## Overview

Run the user's Naver blog posting flow as a gated workflow: gather the keyword and account, prepare the post and images, get approval before live publishing, then report the final URL and work log in the chat.

## Portable Workspace Root

Resolve `{BLOG_ROOT}` before reading files, writing drafts, or running commands. Never construct a path from a guessed Windows username and never hardcode a machine-specific OneDrive root.

Use this precedence:

1. Use `NAVER_BLOG_ROOT` when it is set and valid.
2. Walk from the current directory through its parents and select the first valid `22blog` repository root.
3. Append `22blog` to each distinct non-empty Windows OneDrive root from `$env:OneDrive`, `$env:OneDriveConsumer`, and `$env:OneDriveCommercial`.
4. Append `22blog` to each `UserFolder` found under `HKCU:\Software\Microsoft\OneDrive\Accounts`.
5. Try `$HOME/OneDrive/22blog` only as a final compatibility candidate.

A candidate is valid only when both sentinels exist:

```text
{BLOG_ROOT}/scripts/naver_auto_queue.py
{BLOG_ROOT}/assets/naver_images
```

After selecting one valid root, change the working directory to `{BLOG_ROOT}` and interpret every relative path in this skill from there. If no candidate is valid, stop with `BLOG_ROOT_NOT_FOUND` and report the candidates checked. If multiple candidates remain valid after the precedence rules, stop with `BLOG_ROOT_AMBIGUOUS`, list them, and ask the user which repository to use.

## Input Contract

When the user says `글작성하자`, collect or infer:

```text
메인키워드:
어디블로그:
대략적인 내용요약:
```

Resolve blog names:

| User says | Account | Blog ID |
|---|---|---|
| `11the`, `11theleader` | `blog_b` | `11theleader` |
| `hauzee`, `hauzee1` | `blog_a` | `hauzee1` |

If the account is unclear, ask one short question. Do not publish to a guessed account.

## Workflow

1. Resolve and enter `{BLOG_ROOT}` using the portable workspace-root contract.
2. State goal, scope, assumptions, risks, validation, rollback in Korean.
3. Check same-day publish count for the account; stop if it would exceed 3 posts that day.
4. Check `{BLOG_ROOT}/drafts` and `{BLOG_ROOT}/out/naver_publish_queue_log.json` for the same title or same URL before publishing.
5. Draft the article in the existing Naver blog style: title, intro, numbered sections, FAQ, final paragraph, image prompts, hashtags.
6. Use the existing image channel under `{BLOG_ROOT}/assets/naver_images/임대아파트대출` unless a more specific channel exists.
7. Generate/validate the Naver payload before browser upload. Stop if body image count is 0.
8. Ask for approval before live publishing when the user has not already clearly authorized publish.
9. Publish only after approval; use draft mode only when the user asks for draft.
10. Keep Chrome open after publishing.
11. Report the published URL and a concise work report in the same chat.

## Image Rules

Representative image selection:

| Main keyword contains | Use representative image folder |
|---|---|
| `부영` | `{BLOG_ROOT}/assets/naver_images/임대아파트대출/main_templates/부영아파트` |
| `민간` | `{BLOG_ROOT}/assets/naver_images/임대아파트대출/main_templates/민간임대아파트` |
| other rental apartment keywords | `{BLOG_ROOT}/assets/naver_images/임대아파트대출/main_templates` |

### 메인 템플릿 시각 계약

단지별 대표 이미지를 새로 만들 때는 먼저 선택된 `main_templates` 폴더의 이미지 3장 이상을 직접 열어 비교한다. 대표 이미지는 그 폴더와 같은 **파스텔 카드형**이며 아래 구성을 그대로 따른다.

- 1:1 정사각형, 파스텔색 둥근 외곽 프레임, 흰색 또는 아이보리 중앙 면, 얇은 점선 안쪽 테두리
- 중앙 상단부터 화면의 약 68~72%를 차지하는 굵은 한글 3줄
- ExtraBlack 수준의 둥근 고딕, 1024px 기준 10~14px 검정 외곽선, 회색 또는 연분홍 그림자
- 첫째·셋째 줄은 아이보리 또는 흰색, 둘째 줄은 분홍·보라·연두 등 파스텔 강조색
- 하단에는 단순한 아파트 일러스트와 계약서·계산기·열쇠 중 주제에 맞는 금융 아이콘
- 대표 이미지는 일러스트형 카드로 완성하고, GPT 실사 아파트·상담 사진은 본문 이미지에 사용

3줄 문구는 긴 제목을 그대로 축소하지 말고 모바일에서 읽히도록 다음처럼 짧게 나눈다.

| 주제 | 1행 | 2행 | 3행 |
|---|---|---|---|
| e편한세상 도화 | `e편한세상` | `도화민간` | `임대대출` |
| 사송 롯데캐슬 | `사송롯데` | `캐슬민간` | `임대대출` |
| 힐스테이트 호매실 | `힐스테이트` | `호매실민간` | `임대대출` |

다른 단지도 같은 규칙으로 3줄을 짧게 만든다. 대표 이미지는 **빈 배경을 생성한 뒤 글자를 별도 합성하지 않는다.** GPT 이미지 프롬프트 안에 세 줄 한글을 그대로 넣고, 완성 이미지 중앙에 직접 크게 디자인하도록 지시한다. 한글이 누락·오탈자·잘림·저대비이면 그 결과는 폐기하고 같은 프롬프트로 재생성한다. 최종 이미지에 오탈자, 얇은 글자, 빈 텍스트 영역, 사진형 배경, 지나치게 긴 문장이 남으면 대표 이미지로 사용하지 않는다.

### 고정 메인 이미지 프롬프트

새 대표 이미지는 아래 프롬프트를 기본값으로 사용하고 `<1행>`, `<2행>`, `<3행>`, `<강조색>`, `<금융아이콘>`만 바꾼다.

```text
Use case: ads-marketing
Asset type: 네이버 블로그 1:1 정사각형 대표 이미지
Primary request: 기존 임대아파트대출 메인 템플릿과 같은 파스텔 카드형 대표 이미지. 아래 한글 3줄을 빈 칸 없이 최종 이미지 중앙에 직접 크게 디자인한다.
Scene/backdrop: 둥근 파스텔 외곽 프레임, 아이보리 중앙 면, 얇은 점선 안쪽 테두리, 작은 구름·별 장식
Composition: 중앙에 한글 3줄이 화면의 68~72%, 사용 가능 너비의 약 88%를 차지하고, 하단 약 18%에만 아파트 일러스트와 <금융아이콘>을 배치. 빈 중앙 카드나 글자 자리만 남긴 배경은 금지.
Typography: 매우 굵고 둥근 ExtraBlack 한글, 글자 속을 단색으로 꽉 채움, 1024px 기준 12~14px의 균일한 검정 외곽선, 오른쪽 아래 짧은 회색 그림자, 모바일 썸네일에서도 즉시 읽히는 크기
Color: 1행과 3행은 아이보리 또는 흰색, 2행은 <강조색> 파스텔 채움, 모든 글자는 검정 외곽선
Directly render these exact Korean headline lines in the finished image. Never omit, paraphrase, crop, or replace them with placeholders:
Text line 1 (verbatim): "<1행>"
Text line 2 (verbatim): "<2행>"
Text line 3 (verbatim): "<3행>"
Constraints: 기존 main_templates/민간임대아파트 이미지와 같은 정보 밀도와 여백, 정확한 한글, 깨끗한 벡터풍 일러스트, 워터마크 없음, 파란 정보 박스 없음, 초록 대표 배지 없음, 빈 텍스트 영역 없음. 한글이 정확하지 않으면 재생성.
```

생성 후 `main_templates/민간임대아파트` 이미지와 나란히 비교하여 글자 굵기, 검정 외곽선, 3줄 배치, 하단 아이콘이 같은 수준인지 확인한다. 대표 이미지는 본문의 첫 번째 이미지로 넣는다.

Body image shape:

- 1 representative image first.
- 1 image each from required body folders `01_`, `02_`, `03_`.
- 3 images from `normal`.
- 2 CTA images from `{BLOG_ROOT}/assets/naver_images/common_cta` at the very bottom: phone first, Kakao second.

Stop if stdout or payload says `image files = 0`.

## Editor Formatting

Apply Naver `소제목` formatting to every numbered section title:

- `1. ...`
- `2. ...`
- Continue through the final numbered section such as `7. 마무리`.

CTA placement is strict:

1. Move the caret to the exact end of the final body sentence.
2. Press Enter twice.
3. Insert phone CTA image.
4. Link it to `tel:010-4233-7455`.
5. Insert Kakao CTA image.
6. Link it to `https://open.kakao.com/o/sH54dQti`.

If the CTA appears above the final paragraph, do not claim completion. Fix the editor or report the issue clearly.

## Approval Gate

If the user requests `승인후 작성`, do not publish immediately. Provide:

- proposed title
- target account
- content outline
- image folder plan
- publish mode

Then wait for explicit approval such as `진행해`, `발행해`, or `승인`.

If the user already says `발행해`, `블로그 포스팅까지`, or clearly asks to publish, approval is already given.

## Final Report

After writing or publishing, always leave a report in the chat:

```text
블로그 작업 보고
- 계정:
- 제목:
- 상태:
- URL:
- 대표이미지:
- 본문 이미지:
- 소제목:
- CTA:
- 중복 점검:
- 발행 수 점검:
- 문제/조치:
```

If URL cannot be confirmed, say `URL 미확인` and explain why. Do not pretend a URL was copied.

## Failure Branches

If `{BLOG_ROOT}` cannot be resolved or is ambiguous, stop before opening a browser. Report `BLOG_ROOT_NOT_FOUND` or `BLOG_ROOT_AMBIGUOUS` with the checked candidates; do not guess a username or OneDrive location.

If the Naver session expired, profile is missing, or the profile is locked, report the exact error. For session/profile expiration say:

```text
py -3 scripts\naver_login.py --account <account>
```

needs to be run once manually from `{BLOG_ROOT}`.

If Chrome automation succeeds but the visible editor shows a layout issue, distinguish:

- stdout success
- visual issue
- code fix applied for future runs
- manual correction needed for current editor
