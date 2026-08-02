# 06 VMake

VMake submission starts after `SOURCE_OCR_VERIFIED`; Stage 06 is the later final technical binding step. First run `scripts/validate_clean_candidate.py` when a download (including a user-supplied VMake download) appears. Its result is limited to source identity, distinct SHA, ffprobe video stream, duration, and resolution. It must record `quality_evaluated=false`, `user_visual_review_required=true`, and `final_clean_acceptance=NOT_DECIDED`.

The user alone judges whether removal quality improved. Do not perform OCR, watermark, aesthetic, or cleanliness scoring. After `FINAL_DESIGN_LOCKED`, bind the same candidate to `clean_visual_manifest.json` and run the existing final integrity receipt below. `CLEAN_VISUAL_READY` is a technical asset-state gate, not a visual-quality verdict.

VMake is nonblocking. If its job is processing, unavailable, pending download, or the user will provide a clean file later, immediately make/continue the source-video CapCut project with `VIDEO=00_input/source.mp4` muted and A10 preserved. Record `visual_asset_mode=SOURCE_VIDEO_PROVISIONAL`, report the original-video use to the user, and keep all approved timing, captions, audio, effects, and project structure ready for one later VIDEO-only swap. Never hold analysis, urakkai, audio/caption work, CapCut build, user review, a requested source-provisional preview render, or another episode for VMake. Record `CLEAN_SOURCE_SWAP_NONBLOCKING`; it prevents only a false clean/public-upload claim.

`FINAL_DESIGN_LOCKED` 후 VMake에 원본을 올려 `clean_source.mp4`를 받는다. 클린 영상은 화면 전용이며 내장 음성은 음소거한다.

`clean_visual_manifest.json`에 source identity, design lock, 클린 영상 SHA-256과 예상 길이·해상도를 고정한다. `references/checks/clean-visual.md`에 따라 아래 검증을 실행하고 신규 `clean_visual_receipt.json`을 만든다.

```powershell
python scripts/validate_clean_visual.py --manifest clean_visual_manifest.json --source-identity source_identity.json --design-lock-evidence design_lock_evidence.json --clean-visual-evidence evidence/clean_visual_receipt.json --approved-evidence-root evidence
```

receipt가 스키마에 맞고 실제 ffprobe 결과까지 일치할 때만 `CLEAN_VISUAL_READY`다.
