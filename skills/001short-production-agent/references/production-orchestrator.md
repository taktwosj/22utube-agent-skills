# 001short Production Orchestrator

`protocol.json` is the machine contract and `workflow.json` owns stage transitions. Resolve one internal stage and load exactly its direct stage document. Conflicting instructions stop at `STOP_PROTOCOL_CONFLICT`.

## Intake and root

The final 001 episode root is `{factory_root}/0000shrt/<YYMMDD_short-title_source-id>`. Use `scripts/resolve_episode_root.py`; source media, source identity, and receipt live in `00_input/`.

Accepted intake declarations are `GOOGLE_DRIVE`, `URL`, and `DESKTOP`. Do not perform a network or UI action merely because the declaration exists. Before Stage 01, create the local source identity and validate the local receipt with `scripts/validate_source_intake.py --receipt <receipt>`. The receipt must bind its local media and source identity SHA-256, episode ID, and source ID.

## Audio anchors

Normal production semantics are A9=TTS, A10=original speaker/source audio, A11=SFX, A12=BGM. A11/A12 are optional, not globally forbidden. The explicit clean-only and `TTS_ONLY_MUTE_SOURCE` branches declare their empty anchors in the plan and retain their tighter rules.

## VMake Direct-Insert Contract

Use only the validated `clean_video` asset for normal VIDEO placements. A source-video provisional build is review-only and never clears clean, render, or upload gates.

## Urakkai Editorial Authority

Urakkai requires the declared structural reorder and user approval. Its final duration is allowed to differ from source duration; clean-only remains full-length passthrough.

## Handoff

For a new session, validate `templates/conversation-handoff.json` with `scripts/validate_conversation_handoff.py`. Load the environment once without output. Never include a token, cookie, key, password, OAuth value, or session identifier; reject it as `HANDOFF_SECRET_MATERIAL_FORBIDDEN`. Resume an old episode only with `resume_requested=true`, an episode ID, and current artifact readback.
