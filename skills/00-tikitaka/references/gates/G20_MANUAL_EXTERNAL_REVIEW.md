# G20 — Manual External Return Integration and Design/Editorial Lock

> Lane: `general_shorts_design`
> Owner skill: `00-tikitaka`
> Schema version: `shared-gates-separated-lanes-v2`

## Purpose

Integrate manually-returned external review, record Codex's evidence-based
decisions, and lock the final design. The result is the canonical
`20_script/design_handoff.json` that 000short-production-agent consumes at
G30.

**NORM-005**: external review transport is USER manual. Browser automation,
API calls, and automatic retry are FORBIDDEN. The browser-assisted
two-pass review that prior versions required as MANDATORY is **superseded**
— packets are generated locally, the user transports them.

## Subgate sequence (V2 design section 6.1)

```text
G20.REVIEW_R1_WAIT
→ G20.REVIEW_R1_RETURNED
→ G20.CODEX_DECISIONS_LOCKED
→ G20.REVIEW_R2_WAIT
→ G20.REVIEW_R2_RETURNED
→ G20.FINAL_AUDIT
→ G20.DESIGN_LOCKED
```

## Manual events (input events, NOT approvals)

```text
RETURN_EXTERNAL_REVIEW_R1
RETURN_EXTERNAL_REVIEW_R2
```

These are input events. They do NOT auto-advance to PASS. PASS is emitted
only by the deterministic validator at `G20.DESIGN_LOCKED`.

## External packet policy

Packets are generated locally via `scripts/build_external_prompt.py`:

```text
Round 1 packet  ← shorts_review_r1_prompt.md + design_blueprint
Round 2 packet  ← shorts_review_r2_prompt.md + delta only
```

Round 2 is a **delta packet** (V2 design section 38). It carries:
```text
Round 1 issue list
Codex decision table (ADOPTED / PARTIALLY_ADOPTED / REJECTED / PENDING_EVIDENCE)
changed sentences
unchanged-region SHA values
remaining evidence issues
current completed draft
```

Round 2 uses the **same external review conversation** as Round 1 when
continuity is required. The receipt metadata records the conversation
reference. The external reviewer is never asked to generate internal
hashes or manifests.

## Codex decision rule

For each external suggestion, Codex records exactly one adoption
decision:

```text
ADOPTED
PARTIALLY_ADOPTED
REJECTED
PENDING_EVIDENCE
```

`PENDING_EVIDENCE` blocks the final audit until evidence is supplied or
the suggestion is rejected.

## External authority restrictions

External returns may use only:
```text
PASS_RECOMMENDED
REVISE_REQUIRED
EVIDENCE_REQUIRED
```

External returns must NOT claim:
```text
FINAL
PASS
ADOPTED
SCRIPT_LOCK
DESIGN_LOCK
USER_APPROVED
PRODUCTION_PASS
```

If an external return carries a forbidden claim, the receipt records it
as `EXTERNAL_AUTHORITY_OVERREACH` and the claim is ignored.

## Codex editorial lock boundary (V2 design section 2.3)

Codex may lock G20 without another user approval token only when all of:

```text
user brief is already locked
requested_target allows work beyond design_only
source identity and selected ranges did not materially change
governing thesis did not materially change
production mode did not change
no new high-risk allegation was added
Round 2 recommendation is PASS_RECOMMENDED
deterministic review gate passes
remaining blockers are empty
```

Codex must stop with `WAIT_USER_EDITORIAL_CONFIRMATION` if any of:

```text
new source added
selected source range changes beyond allowed context expansion
governing thesis changes
content profile changes
source_led ↔ narrated mode changes
new legal/defamation-sensitive allegation appears
Round 2 returns REVISE_REQUIRED or EVIDENCE_REQUIRED
user-marked protected text must change
```

## Final artifacts

```text
20_script/design_handoff.json          (canonical handoff authority)
20_script/external_review_receipt.json
20_script/owner_transfer_receipt.json  (only if requested_target != design_only)
20_script/script_handoff_gate.json     (compatibility pointer manifest)
20_script/report1_handoff.json         (compatibility pointer manifest)
```

Compatibility pointers (V2 design section 14.3, 20.1) are
`handoff-compat-v1` manifests pointing at the canonical handoff SHA. They
do NOT duplicate the full payload across three files.

## Owner transfer conditions (to 000short-production-agent G30)

```text
requested_target != design_only
design_handoff.status == PASS
source_fingerprint matches
design_blueprint SHA matches
timeline SHA matches
external review receipt valid
owner_transfer_receipt exists
```

If all conditions are met and G00 pre-authorized the requested target, the
runner may transfer ownership without another routine user question.

## Stop conditions

```text
WAIT_EXTERNAL_RETURN           packet waiting for user transport
WAIT_USER_EDITORIAL_CONFIRMATION material change required
EXTERNAL_AUTHORITY_OVERREACH   external return claimed final authority
SAME_CONVERSATION_REQUIRED     Round 2 broke conversation continuity
PENDING_EVIDENCE               unresolved evidence request
STOP_SOURCE_OF_TRUTH_CONFLICT
```

## Forbidden in this lane

```text
TTS audio generation
final SRT
CapCut assembly
render
upload package
```

These belong to 000short-production-agent (G30-G90). Tikitaka stops at G20.
