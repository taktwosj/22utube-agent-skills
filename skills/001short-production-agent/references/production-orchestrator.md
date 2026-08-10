# 001short Production Orchestrator

`protocol.json` is the machine contract and `workflow.json` owns stage transitions. Resolve one internal stage and load exactly its direct stage document. Conflicting instructions stop at `STOP_PROTOCOL_CONFLICT`.

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

After assembly, report current validator/readback evidence, then separate code
blocks for the 프로젝트 파일명 and 프로젝트 전체 경로. Missing readback is
`NOT RUN`, never `PASS`.

## VMake Direct-Insert Contract

Use only the validated `clean_video` asset for normal VIDEO placements. A source-video provisional build is review-only and never clears clean, render, or upload gates.

An exact file that the user explicitly selects may instead use
`USER_APPROVED_NONMATCHING_CLEAN_SOURCE`. Bind the local file, SHA-256, and the
user's exact approval text in `user_clean_override.json`. Duration or resolution
may differ from the source in this mode; that difference is recorded, not used as
a rejection gate. This mode is not VMake evidence, is not
`CLEAN_VISUAL_READY`, and remains `upload_ready=false` until manual CapCut review.

The canonical physical layout stays at 15 tracks. Only `STATE_LASER` is
routable for STATE cues (`LASER_CUT`); `STATE_FLICKER` and `STATE_GLITCH` stay
physically present and empty. Retained-speaker captions use the two
`A10_TEXT_WHITE` and `A10_TEXT_YELLOW` lanes while A10 remains one audio stem.

## Urakkai Editorial Authority

Urakkai always requires the source-time original table and target-time urakkai
table. Do not call an external AI reviewer. Manual mode waits for user approval;
when the user requests automatic mode, preserve both tables and continue without
asking for approval. Its final duration is allowed to differ from source
duration; clean-only remains full-length passthrough.

## Handoff

For a new session, validate `templates/conversation-handoff.json` with `scripts/validate_conversation_handoff.py --handoff <path>`. Load the environment once without output. Never include a token, cookie, key, password, OAuth value, or session identifier; reject it as `HANDOFF_SECRET_MATERIAL_FORBIDDEN`. Resume an old episode only with `resume_requested=true`, an episode ID, and current artifact readback.
