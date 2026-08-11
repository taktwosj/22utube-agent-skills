# Matt Auxiliary Routing

Common specialist rules live in
[1caveman Matt auxiliary routing](../../1caveman/references/matt-auxiliary-routing.md).
This file defines only 001-specific exceptions. `NONE` means no specialist beyond the workspace baseline.

## Episode routing

| Observable condition | Action |
|---|---|
| Normal episode | `NONE`; execute the owner stage and its validator. |
| Automatic mode | `NONE`; skip approval only and keep both full grids. |
| Original grid | `NONE`; record source order and evidence. Matt cannot change it. |
| Urakkai design is clear | Run the owner-skill hook/reversal/payoff checklist internally; this is not a Matt call. |
| A missing user decision blocks urakkai before design lock and automatic mode is off | Recommend that the user explicitly invoke `$grill-with-docs`; run it only after that invocation, then return the decision to the owner stage. |
| Download, media, state, audio, caption, builder, or readback failure | Resume the owning stage first. |
| The same code/tool failure is reproducible after owner-stage recovery | `$diagnosing-bugs`; establish the cause before editing. |

Stage 04 never uses Matt as external editorial review. Matt failure never blocks a normal or automatic episode.

## Research boundary

Use `$research` only for external technical documentation inside an active code/tool defect or
contract-change task. It never changes source observation or supplies content approval.

Use the existing 001 conversation handoff. Do not add a second Matt handoff flow.

## Authority boundary

Matt output is `ADVISORY_ONLY`. Matt cannot edit or replace the source-evidence original grid.
A decision from a user-invoked grill may be applied by the owner to the urakkai grid before lock;
the owner grid, `protocol.json`, workflow/state, source identity, validator evidence, user approval,
design lock, audio/caption locks, CapCut readback, and visual gate remain authoritative.
