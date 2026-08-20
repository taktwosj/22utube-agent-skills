# 06 VMake

VMake submission starts immediately at episode intake by uploading the verified source file through Aside (URL submission is the fallback and yields a lower-resolution result); Stage 06 is the later final technical binding step. First run `scripts/validate_clean_candidate.py` when a download (including a user-supplied VMake download) appears. Its result is limited to source identity, distinct SHA, ffprobe video stream, duration, and resolution. It must record `quality_evaluated=false`, `user_visual_review_required=true`, and `final_clean_acceptance=NOT_DECIDED`.

The user alone judges whether removal quality improved. Do not perform OCR, watermark, aesthetic, or cleanliness scoring. After `FINAL_DESIGN_LOCKED`, bind the same candidate to `clean_visual_manifest.json` and run the existing final integrity receipt below. `CLEAN_VISUAL_READY` is a technical asset-state gate, not a visual-quality verdict.

VMake is nonblocking. `AGENT_PRIMARY_CLEAN_SOURCE` means submit VMake first after source identity, then obtain and validate its completed clean source. While it is pending, immediately make/continue the source-video CapCut project with `VIDEO=00_input/source.mp4` muted and A10 preserved; do not wait. Record `visual_asset_mode=SOURCE_VIDEO_PROVISIONAL` and `CLEAN_SOURCE_SWAP_NONBLOCKING`. Once the verified VMake asset exists, the agent performs the VIDEO-only swap/reassembly using the existing project contract. `USER_FALLBACK_CLEAN_SOURCE` requires exactly one explicit reason: `VMAKE_CURRENT_WORK_WINDOW_INCOMPLETE`, `VMAKE_ACQUISITION_ISSUE`, or `VMAKE_VERIFICATION_ISSUE`; it never carries a fake VMake final receipt. The agent verifies its SHA and clean-visual receipt, then performs the same VIDEO-only swap/reassembly. Neither path authorizes a false clean/public-upload claim.

`FINAL_DESIGN_LOCKED` 후 VMake에 원본을 올려 `clean_source.mp4`를 받는다. 클린 영상은 화면 전용이며 내장 음성은 음소거한다.

`clean_visual_manifest.json`에 source identity, design lock, 클린 영상 SHA-256과 예상 길이·해상도를 고정한다. `references/checks/clean-visual.md`에 따라 아래 검증을 실행하고 신규 `clean_visual_receipt.json`을 만든다.

```powershell
python scripts/validate_clean_visual.py --manifest clean_visual_manifest.json --source-identity source_identity.json --design-lock-evidence design_lock_evidence.json --clean-visual-evidence evidence/clean_visual_receipt.json --approved-evidence-root evidence
```

receipt가 스키마에 맞고 실제 ffprobe 결과까지 일치할 때만 `CLEAN_VISUAL_READY`다.
