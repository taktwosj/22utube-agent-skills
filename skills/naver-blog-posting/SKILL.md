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
