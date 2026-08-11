# Matt Auxiliary Routing

Common specialist rules live in
[1caveman Matt auxiliary routing](../../1caveman/references/matt-auxiliary-routing.md).
This file defines only 119-specific exceptions. `NONE` means no specialist beyond the workspace baseline.

## Production routing

| Observable condition | Action |
|---|---|
| Normal PRE119, direct, legacy, A/B/C/D, join, build, relink, readback, or visual work | `NONE`; execute the selected 119 stage. |
| A missing user decision blocks requirements before approval | Recommend that the user explicitly invoke `$grill-with-docs`; run it only after that invocation, then return the decision to PRE-119 or direct-script. |
| Approval SHA is locked | Planning Matt is `OFF`; preserve the approved question, thesis, script, chapter order, and editorial choices. |
| A production stage fails | Resume only the owning stage through `resume-map.md` first. |
| The same code/tool failure is reproducible after stage recovery | `$diagnosing-bugs`; establish the cause before editing. |

Matt output cannot satisfy `MEDIA_RELINK` or `VISUAL_GATE`, and Matt failure never blocks normal production.

## Research boundary

- Before approval, `$research` may support political facts or evidence inside PRE-119.
- After approval, new political facts or screen logic return to PRE-119; do not research them inside 119.
- External technical documentation may be researched inside an active code/tool defect or contract-change task.

Use the existing 119 handoff and resume contracts. Do not add a second Matt handoff flow.

## Authority boundary

Matt output is `ADVISORY_ONLY`. It cannot replace or alter `owner_skill`, PRE-119 validation,
approval evidence or SHA, the approved script, cards, root contract, stage state, validator evidence,
media relink, visual gate, or user screen approval.
