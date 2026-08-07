---
name: 001short-production-agent
description: Use for original-shorts production, or when a new-session 001 conversation handoff JSON must load env safely and resume the same lane.
---

# 001short Compact Production

## Load order

1. Read [production-orchestrator.md](references/production-orchestrator.md) first.
2. Read `workflow.json`, episode state, and `protocol.json`; select one internal stage from the orchestrator's state/lock table.
3. Load exactly one current stage MD: [original-capcut-grid.md](templates/original-capcut-grid.md), [urakkai-production-grid.md](templates/urakkai-production-grid.md), or [capcut-assembly-grid.md](templates/capcut-assembly-grid.md).
4. Load only the direct supporting references linked by that stage MD. Do not load a second stage MD or replace a stage authority with a legacy document.

## Minimal executable protocol

- `protocol.json` is the machine contract and `workflow.json` owns state transitions. Stop with `STOP_PROTOCOL_CONFLICT` on conflict.
- Start locally from the episode root. Keep one active writer and never mutate an active CapCut draft while CapCut or its background processes are open.
- Validate an approved Stage 05 production plan with `scripts/validate_executable_protocol.py --plan <path>` before a build. Static validation does not establish a user visual approval.
- Treat every `WAIT_*` and `FAIL_*` in the selected stage MD as a hard stop. Do not use conversational memory as evidence.
- This documentation router does not authorize CapCut UI actions, cloud sync, render, upload, Drive writes, VMake, or any external action. Those require a separate explicit request and their own evidence.
- Stage 02's `templates/original-capcut-grid.md` must fill every `ORIGINAL_CAPCUT_GRID_REQUIRED_ROWS`: `T1`, `T2`, `A9 TTS`, `A9_TEXT`, `A10 작가 나레이션`, `A10 화자발언 1`, `A10 화자발언 2`, `A10 화자발언 3`, `STATE 상황설명문구`. Do not leave a cell as bare `없음`, `비움`, `UNVERIFIED`; pair every absence or uncertainty with its evidence.

## New Session Handoff Bootstrap

운영자가 `/new` 뒤 001 핸드오프 대화 JSON을 제공하면 다른 제작 스킬을 추가로 로드하지 않고 이 스킬 안에서 바로 재개한다.

1. 터미널에서 `$HOME/.hermes/.env`가 있으면 **한 번만** 조용히 로드한다. 값·키 목록·파일 내용은 출력하거나 핸드오프에 저장하지 않는다.
   ```bash
   set -a; [ ! -f "$HOME/.hermes/.env" ] || . "$HOME/.hermes/.env"; set +a
   ```
2. JSON을 임시 파일로 받은 뒤 `python3 scripts/validate_conversation_handoff.py --handoff <path>`를 실행한다. `PASS` 전에는 제작을 시작하지 않는다.
3. `owner_skill=001short-production-agent`, `lane=general_shorts_production`을 유지하고 안전 요약의 `request_scope`와 `next_action`부터 진행한다.
4. `resume_requested=true`일 때만 `episode_id`와 실제 state/readback을 대조해 과거 회차를 연다. 둘 중 하나라도 없으면 `HANDOFF_EPISODE_ID_REQUIRED`로 중단한다.
5. `resume_requested=false`이면 새 회차로 취급하며 과거 프로젝트를 열거나 수정하지 않는다.

핸드오프 정본 모양은 `templates/conversation-handoff.json`, schema는 `schemas/conversation_handoff.schema.json`이다. 토큰·쿠키·API 키·비밀번호·OAuth 값·session/conversation ID가 들어 있는 JSON은 `HANDOFF_SECRET_MATERIAL_FORBIDDEN`으로 거부하며 원문을 다시 출력하지 않는다.

## Compatibility

Existing legacy references, templates, schemas, and scripts remain available only through the orchestrator or a current-stage direct link. Do not delete them, copy their prose into this router, or let them compete with the selected stage authority.
