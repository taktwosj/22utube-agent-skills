# 001short Production Orchestrator

`protocol.json` is the machine contract and `workflow.json` owns stage transitions. Resolve one internal stage and load exactly its direct stage document. Conflicting instructions stop at `STOP_PROTOCOL_CONFLICT`.

## NORMAL_FAST execution

`NORMAL_FAST` is the default profile. One task-owner performs Stage 01 through Stage 04 sequentially and owns their canonical writes. Stage 01, Stage 03, post-design, and postbuild worker fanout are inactive. Candidate promotion, coordinator revalidation, and duplicate evidence barriers are inactive. Run the validator owned by each stage once per current artifact revision and rerun it only after a proven relevant artifact change.

The same task-owner may submit the VMake job after source identity verification and continue Stage 02 through Stage 04 while the remote job runs. This is one-owner background work, not worker fanout.

## Source authority and divergence gate

Source authority: `C:\Users\arajun\agent-skills\skills\001short-production-agent`

Worktree source repository: `C:\Users\arajun\agent-skills`

Modify the skill only in an isolated Git worktree derived from that repository. The installed entrypoints and active runtime releases are immutable, read-only entrypoints:

```text
Codex: C:\Users\arajun\.codex\skills\001short-production-agent
Claude: C:\Users\arajun\.claude\skills\001short-production-agent
Hermes: C:\Users\arajun\AppData\Local\hermes\skills\22utube\001short-production-agent
```

Never edit those entrypoints or active runtime release contents. Release only in this order after the required user approvals:

1. Isolated worktree derived from `C:\Users\arajun\agent-skills`
2. Tests
3. Independent review
4. Approved revision on GitHub `main`
5. `python -B scripts/skill_release.py publish`
6. `python -B scripts/skill_release.py activate --target all`
7. `python -B scripts/skill_release.py verify --target all --self-check`

If the plan, contract, validator, or proposed action diverges, stop before any skill source, runtime, or episode draft mutation. Report `mismatch`, `expected`, `actual`, `impact`, and `safe options`, then ask exactly:

```text
1. 별도 승인 — 이번 작업만
2. 일단 정지 — 어떤 문제인지 보고만
3. 스킬 수정하기 — 스킬 수정 폴더에서
```

Never self-select. Option 1 records an episode-only override and changes no skill. Option 2 is evidence-only and makes no mutation. Option 3 opens a separate canonical worktree change; production waits through independent review, GitHub `main`, publish, activation, and verification.

User-provided audio, images, and TTS are declared episode-only overlay exceptions. Keep the root template, canonical base 15 tracks, and default audio policy unchanged. Never promote an exception into the global contract. No option bypasses safety: never mutate a draft while CapCut or its background processes are open.

## Intake and root

The final 001 episode root is `{factory_root}/0000shrt/<YYMMDD_short-title_source-id>`. Use `scripts/resolve_episode_root.py`; source media, source identity, and receipt live in `00_input/`.

Accepted intake declarations are `GOOGLE_DRIVE`, `URL`, and `DESKTOP`. Do not perform a network or UI action merely because the declaration exists. Before Stage 01, create the local source identity and validate the local receipt with `scripts/validate_source_intake.py --receipt <receipt>`. The receipt must bind its local media and source identity SHA-256, episode ID, and source ID.

## Audio anchors

Normal production semantics are A9=TTS, A10=validated Demucs source vocal stem, A11=SFX, A12=EMPTY. A11 is optional; A12 is reserved empty in the canonical v2 contract. The explicit clean-only and `TTS_ONLY_MUTE_SOURCE` branches declare their empty anchors in the plan and retain their tighter rules.

## User-facing three phases

Always expose production as `원본표 → 우라까이표 → CapCut 조립`.
Both tables use the fixed 15-row order declared by `protocol.json`, contain no
implicit empty cells, and are emitted to the 대화창 by
`scripts/validate_capcut_grids.py --emit-report`. Automatic mode does not skip
the complete-table report. The CapCut builder validates both files before any
work-root or local-draft write.

After assembly, the first item in the result report is the exact CapCut 프로젝트명 in its own copyable code block. Then report current validator/readback evidence and use separate code blocks for the 프로젝트 전체 경로. Missing readback is `NOT RUN`, never `PASS`.

## Build and audio contract

`scripts/build_episode_capcut.py` validates both tables before work-root or draft writes. It validates the canonical root ZIP against the root contract, extracts it into immutable `source_authority`, clones that tree to `working_project`, assigns new project, draft, and timeline IDs, and injects episode assets only into that clone. Validate the assembled clone; never mutate the root ZIP or extracted source.

The builder binds normalized text, cue/layer/color/effect, and path/SHA locks for the timeline, manifest, design, audio, and captions. Require timeline/caption cue bijection, source-time evidence, audio-material registration, project-ID mirrors, and Timeline mirrors. Zero captions require empty timeline cues, lock cues, and `final.srt`. Keep VIDEO embedded audio muted.

A9/A9_TEXT require narration audio. STATE_LASER is silent situation text; never request TTS for STATE-only screens. Select one explicit audio matrix without fallback:

- `SOURCE_ORDER_UNCHANGED_CLEAN_ONLY` + `SOURCE_ORDER_CLEAN_AUDIO`: full source-identity-bound raw A10; no Demucs.
- `SOURCE_ORDER_UNCHANGED_A10_RETAINED` + `A10_RETAINED_SYNC`: validated full Demucs stem.
- `URAKKAI` + `A10_REASSEMBLED_SYNC`: mapped reassembly derived from that full stem.

Run Demucs once per explicit stem mode and reuse its manifest. For mixed generated A9, use `source_audio[].mode=duck` under narration and `source_audio[].mode=on` elsewhere; partial overlap is `MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED`. Validated file/SHA/duration/range-bound user audio keeps A10 on at 1.0 with no auto-duck, mute, or split and stops at `WAIT_USER_CAPCUT_AUDIO_ADJUSTMENT`.

## VMake Direct-Insert Contract

Use only the validated `clean_video` asset for normal VIDEO placements. A source-video provisional build is review-only and never clears clean, render, or upload gates.

An exact file that the user explicitly selects may instead use
`USER_APPROVED_NONMATCHING_CLEAN_SOURCE`. Bind the local file, SHA-256, and the
user's exact approval text in `user_clean_override.json`. Duration or resolution
may differ from the source in this mode; that difference is recorded, not used as
a rejection gate. This mode is not VMake evidence, is not
`CLEAN_VISUAL_READY`, and remains `upload_ready=false` until manual CapCut review.

The canonical base layout stays at 15 tracks. Only an evidence-bound
`001short-user-provided-media-overlay-layout-v1` may append declared overlays
after index 14; every undeclared extra track fails. Only `STATE_LASER` is
routable for STATE cues (`LASER_CUT`); `STATE_FLICKER` and `STATE_GLITCH` stay
physically present and empty. File/SHA/duration-bound overlapping user audio keeps
A10 on at volume 1.0 for manual volume adjustment and is never auto-ducked.
Retained-speaker captions use the two
`A10_TEXT_WHITE` and `A10_TEXT_YELLOW` lanes while A10 remains one audio stem.

## Urakkai Editorial Authority

Urakkai always requires the source-time original table and target-time urakkai
table. One task-owner writes one independent Stage 03 recommendation from the locked Stage 02 artifacts and does not mutate the original grid. Manual mode waits for user approval;
when the user requests automatic mode, preserve both tables and continue without
asking for approval. Its final duration is allowed to differ from source
duration; clean-only remains full-length passthrough.

## Handoff

For a new session, validate `templates/conversation-handoff.json` with `scripts/validate_conversation_handoff.py --handoff <path>`. Load the environment once without output. Never include a token, cookie, key, password, OAuth value, or session identifier; reject it as `HANDOFF_SECRET_MATERIAL_FORBIDDEN`. Resume an old episode only with `resume_requested=true`, an episode ID, and current artifact readback.
