# G90 — Final QC and Release Gate

G90 requires valid G80 evidence. `FINAL_QC_PASS` by the validator must precede
`UPLOAD_APPROVED` by the user. Without upload approval, return
`WAIT_UPLOAD_APPROVAL`. Release permission never performs the upload and the
runner may not auto-advance it.

