# G40 — Politics Caption and SRT Lock

G40 requires the measured G30 lock. Validate cue order, text, punctuation, line
breaks, timing range, and the locked audio SHA. When a user-corrected SRT is
applicable, that exact file and SHA are final authority; generated output may
not overwrite it. Preserve `FINAL_CORRECTED_CAPTION_FIDELITY=PASS` evidence and
remove visible noise markers such as `>>`, `[웃음]`, and `[콧방귀]`.

