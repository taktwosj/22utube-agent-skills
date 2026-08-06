# Stage 04: Mac Mini Urakkai Review Contract

Load only for Stage 04 and only for `URAKKAI`. Run one creator-machine review before a user decision; never turn it into automatic approval.

Load `references/mara-urakkai-review-rubric.md` together with this file. That rubric is the review criteria and output format; this file is the execution, authority, and evidence contract. A Stage 04 review that reports no rubric verdict fails with `URAKKAI_REVIEW_RUBRIC_MISSING`.

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

## Creative urakkai license (supersedes the conservative sentence above)

Urakkai is an entertaining re-story, not a documentary transcript. The user may deliberately add a playful premise, emotional framing, hook, reversal, or imagined inner thought when it makes the visible situation more engaging. For example, a father and son walking can open with a warm “remember mom” premise, then land on the father briefly looking at a passing runner. The written story may connect these beats even when the source never literally states that message.

Keep three fields separate in the blueprint:

- `SOURCE_OBSERVATION`: only what is visibly/audibly evidenced.
- `CREATIVE_URAKKAI`: the added story, narration, hook, emotional interpretation, or comic reversal.
- `FICTIONAL_RECONSTRUCTION`: relationships, motives, identities, or background the source never confirms.

Inventing a family tie, a prior promise, a job, or a purpose is allowed and must not be penalized on its own. The single failure condition is recording invented material as source fact, which fails with `URAKKAI_FACT_BOUNDARY_VIOLATION`.

Creative copy may be witty, exaggerated, or fictional, but must not present an unverified real-world identity, crime, medical/legal claim, relationship, or defamatory allegation as fact. It should make the moment fun, not pretend to report a real event. The Stage 04 reviewer evaluates whether the creative premise is clear, funny, and aligned with the user's requested tone; it must not rewrite the draft back into a sterile literal description.

## Audio policy declaration

Every reviewed draft must declare exactly one audio policy, and the reviewer must confirm it:

- `TTS_ONLY_MUTE_SOURCE`: every VIDEO muted, new A9 TTS required, A10/A11/A12 empty.
- `A10_RETAINED_SYNC`: original speaker audio retained through a verified external vocal stem, VIDEO muted, A10 synchronized with the VIDEO source/target ranges, A12 empty.

A draft that mixes original voice and new TTS without stem evidence, or that declares neither policy, fails with `URAKKAI_AUDIO_POLICY_UNDECLARED`.

## Review result

Report: `verdict`, `present_scene`, `emotional_hook`, `rewrite_or_keep`, and `approval_status=WAIT_USER_URAKKAI_APPROVAL`.

`verdict` is one of `PASS_CANDIDATE`, `REVISE_REQUIRED`, `WAIT_SOURCE_RECHECK`, `REJECTED_MARA_INSUFFICIENT`. Record it in `20_script/external-review.json` alongside the rubric item table and the P0–P4 must-fix list. `PASS_CANDIDATE` is a recommendation only; it never advances the episode by itself, and the state stays `WAIT_USER_URAKKAI_APPROVAL` under every verdict. Each user correction reuses this same stage and reports again.
