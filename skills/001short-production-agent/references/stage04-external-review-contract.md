# Stage 04: Mac Mini Urakkai Review Contract

Load only for Stage 04 and only for `URAKKAI`. Run one creator-machine review before a user decision; never turn it into automatic approval.

## Execution and authority

1. The Mac mini producer creates the candidate and calls Claude CLI with Claude Opus 5 / Low.
2. If that CLI call fails because of authentication, quota, availability, or a non-zero exit, run one same-input fallback: Codex CLI `gpt-5.6-sol` / Low.
3. A reviewer may recommend or rewrite copy. It cannot lock the design, change source ranges without evidence, or advance the episode.
4. Report the revised `20_script/URAKKAI_BLUEPRINT.md` and review summary to the user. Remain at `WAIT_USER_URAKKAI_APPROVAL` until explicit approval.

Record reviewer choice, fallback category, input/output SHA-256, findings, accepted changes, and rejected changes in `20_script/external-review.md` and `.json`. Never record credentials, tokens, cookies, private URLs, or raw session identifiers.

## Situation-caption rubric

Situation copy must make the viewer understand the current shot faster and feel its immediate emotional charge. Anchor it in a visible person, action, relationship, or reaction.

Good direction:

- "The moment she cannot speak after seeing the gift"
- "Family members watching her expression"
- "Laughter breaks the tension in the room"

Reject edit-outline copy such as "show the reaction first", "reveal the reason later", "connect to the second reaction", or "warm family ending". Those describe an edit plan or ending, not the current shot.

Create the hook through the current situation. Do not invent a twist, conclusion, or causal explanation unsupported by visible evidence. Speaker captions stay dynamic: use the actual current speaker count, do not force every video into two fixed lines, and do not create TTS merely to fill a layer. A `STATE` line is optional and must name the present scene or emotion.

## Review result

Report: `present_scene`, `emotional_hook`, `rewrite_or_keep`, and `approval_status=WAIT_USER_URAKKAI_APPROVAL`. Each user correction reuses this same stage and reports again.
