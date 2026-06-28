---
name: 11short-reple-agent
description: Use when 11utube/11short work asks for 리플, 댓글, 댓글창, reply, reple, reaction comments, 몰라도됨/알면개꿀 comment-card series, or replacing the 11short bottom yellow caption with YouTube-style comment/reply images in CapCut drafts.
---

# 11short Reple Agent

This skill extends `11short-production-agent` for 11short remake videos whose visible lower caption must be a YouTube-style reply/comment image instead of the standard yellow bottom caption.

## Priority

Use this skill before the base `11short-production-agent` when the user says any of:

- `리플`, `댓글`, `댓글창`, `댓글 이미지`, `reply`, `reple`
- `하단은 댓글`, `노란 자막 말고`, `댓글 반응`, `댓글 카드`
- `몰라도됨`, `알면개꿀`, `이게왜됨`, `속이시원` as a comment-reaction format

Still follow the 11short base workflow for source download, Gemini/JSON analysis, Supertone TTS, CapCut registration, OCR/list overlays, source audio, and final verification unless this skill overrides a visual rule.

## Reple Layout Contract

Visible text classes:

1. Top fixed title
   - Same as base 11short.
   - Fixed to project end.
   - Top black band only.

2. Left/middle list or OCR overlay
   - Same as base 11short.
   - For series/list videos, show `1.` through `N.` in ascending order on the left.
   - Place it left-aligned, visually close to normalized `x=-0.82`, `y=0.22`.
   - For reple series, use the CapCut text style the user selected: left aligned, bold, black text, normal letter/line spacing, no visible purple box.
   - Do not fill `1.` first in ranked countdown series. Reveal from the highest number down.

3. Bottom reple/comment image
   - This replaces the visible yellow bottom caption.
   - Use a YouTube-comment-like card in the lower black band or the lower safe video area.
   - Dark rounded rectangle: `#181818` to `#202124`, alpha `0.88` to `0.96`.
   - Avatar circle on the left. Use varied solid colors such as pink, purple, blue, green, orange.
   - Display names must vary across cards. Use names like `아몰랑`, `몰랑`, `다몰랑`, `너몰랑`, `또몰랑`, `우리몰랑`, `개몰랑`.
   - Comment text is white, left-aligned, readable, and short.
   - Author name, blurred handle width, time text, like count, reply label, avatar color, and avatar text must come from a reusable template set, not fixed literals.
   - Use `11short/assets/reple_comment_templates.json` as the default 20-template pool.
   - Never use visible yellow rounded caption boxes in reple projects.

### Molla Format

For `몰라도됨` reple videos, use this locked bottom format:

- Add a solid white lower panel behind the reply card.
- Place the dark YouTube-style reply card on top of that white panel.
- Keep the top fixed title as the normal 11short top-title rule.
- Use this format for `몰라도됨` intros, outros, and body segments unless the user explicitly changes it.

## Caption Text Rules

The visible comment text must sound like a viewer reaction or situation explanation, not a production note.

Never show these in visible captions/comment text:

- `조회수순`
- `source`, `segment`, `draft`, `CapCut`, `Gemini`, `OCR`
- file names, ranking metadata, internal workflow terms

Good visible comment text examples:

```text
굳이 이걸 고친다고?
말은 안 되는데 되네
이걸 왜 해ㅋㅋ
결과가 더 어이없네
저게 왜 되는 거야
쓸데없는데 계속 보게 됨
그냥 새로 사면 안 됨?
```

For news, script, or narration work, rewrite the lower text as comment-style reactions while keeping the actual information. If the content is long, split it into multiple comment cards instead of making one dense card.

## Reaction Labels

Use these labels to classify the tone:

```text
와 이거 써먹겠다 -> 알면개꿀
이걸 왜 해ㅋㅋ -> 몰라도됨
말도 안 되는데 되네 -> 이게왜됨
보는 맛 좋다 -> 속이시원
```

For `몰라도됨` series voice, use short reactions aligned to clip starts:

```text
몰라도됨.
굳이?
이걸?
왜?
흠, 이건 좀.
몰라도됨.
```

## CapCut Draft Rule

Preferred implementation:

- Render bottom comment cards as image/sticker assets, or build them from CapCut shape/text layers.
- Store the card plan in `analysis.editable_comment_overlays[]`.
- Each card must include `comment_text`, `start`, `end`, `capcut_x`, `capcut_y`, `width`, `height`, and `style_hint: "youtube_reple_card"`.

If the base 11short harness still requires `segments[].caption_ko_final` to be present:

- Keep `caption_ko_final` semantically equal to the comment text.
- If a yellow caption track is required only for compatibility, make it non-visible and mark it `harness_compat_only` in notes/status.
- The final visible user-facing lower caption must be the reple/comment card, not the yellow caption.

## Series/Reple Specifics

For `3개`, `4개`, `5개`, or other grouped series:

- The left list shows only item numbers and short item names.
- The bottom comment card explains the current item or reacts to it.
- Do not put `N번조회수순...` in the bottom.
- Acceptable list text: `4. 장작순삭`.
- Acceptable bottom card: `굳이 장작을 이렇게 쪼갠다고?`

## Verification Checklist

Before calling a reple draft ready:

- [ ] Top title is fixed and readable.
- [ ] End intro is included if the user requested it.
- [ ] Left list is left-aligned and all numbers are visible.
- [ ] Left list uses black bold text in the user-selected style, not the earlier green style.
- [ ] No visible yellow caption box remains.
- [ ] Bottom comment cards are visible, readable, and aligned left inside the card.
- [ ] For `몰라도됨`, the lower panel is white behind the dark reply card.
- [ ] Comment author names are varied, not all `아몰랑`.
- [ ] Comment metadata is varied from `reple_comment_templates.json`, not fixed to `2시간 전 / 1.2천 / 답글`.
- [ ] Visible bottom text does not contain `조회수순` or internal workflow terms.
- [ ] Voice cues align to each clip.
- [ ] Source audio and voiceover are present.
- [ ] Run the base harness when possible, then do a visual check because reple visual rules override yellow-caption visuals.

## Final Reply

For completed 11short/reple work, include:

```text
제목
내용
출처
태그
```

Tags must not include `#`, and every tag must end with a comma.
