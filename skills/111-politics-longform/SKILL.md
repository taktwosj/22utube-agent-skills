---
name: 111-politics-longform
description: Use when the user says 111정치롱폼, 정치롱폼, 정치롱폼1단계, 정치롱폼2단계, 정치롱폼 대화형, Claude 초벌, 캣컵전단계, 민주진영 유튜브, 매불쇼 롱폼, 유시민 롱폼, or asks to make/update a Korean political longform source-download package, CapCut draft, T1 chapter text, YouTube upload package, channel profile, keywords, or thumbnail hooks for a 민주진영 political commentary channel.
---

# 111 Politics Longform

## Load Order

Always read [00_CORE_RULES.md](00_CORE_RULES.md) first.

Then load only the files required by the current request:

- Stage 1 / Claude rough package / 자료조사 / source intake:
  - [10_STAGE1_RESEARCH_SOURCE.md](10_STAGE1_RESEARCH_SOURCE.md)
  - [11_STAGE1_OUTPUT_CONTRACT.md](11_STAGE1_OUTPUT_CONTRACT.md)
- Stage 2 / Codex finalization / CapCut / 캣컷 / 출력 / 제작:
  - [20_STAGE2_CAPCUT_BUILD.md](20_STAGE2_CAPCUT_BUILD.md)
  - [21_STAGE2_BASE_JUNGCHILONG.md](21_STAGE2_BASE_JUNGCHILONG.md)
  - [22_STAGE2_PATCH_RULES.md](22_STAGE2_PATCH_RULES.md)
  - [23_STAGE2_VALIDATION_HARNESS.md](23_STAGE2_VALIDATION_HARNESS.md)
- T1 / flow strap / lower commentary writing:
  - [30_TEXT_T1_AND_FLOW.md](30_TEXT_T1_AND_FLOW.md)
- Upload text:
  - [40_UPLOAD_PACKAGE.md](40_UPLOAD_PACKAGE.md)
- Thumbnail or channel setup:
  - [50_THUMBNAIL_AND_CHANNEL.md](50_THUMBNAIL_AND_CHANNEL.md)
- TTS / narration / generated voice:
  - [60_TTS_OPTIONAL.md](60_TTS_OPTIONAL.md)
- Old YP007/YP005/YM007/YSM notes only when explicitly needed:
  - [90_LEGACY_REFERENCE.md](90_LEGACY_REFERENCE.md)

Hook and validator guardrails:

- Public validators live in [scripts/](scripts/). Stage 2 must run them manually before claiming PASS.
- Claude hook wrappers live in [hooks/](hooks/) and enforce the same guardrails where Claude hooks are available.
- Hooks are a guardrail only. They do not replace the final harness or the required frame evidence.

## Routing Rules

Stage 1 is source research and handoff only. It must not create, edit, inspect,
or claim any CapCut draft. If download fails, it must say so explicitly with
`WAIT_DOWNLOAD`.

Stage 2 owns speech lock, locked clips, `jungchilong` copy, CapCut JSON patch,
visual/frame validation, final harness, upload package, and thumbnail hooks.

Do not claim `PASS`, `FINAL`, `upload_ready`, or `검증 통과` unless the matching
stage contract and validation file say PASS with evidence.
