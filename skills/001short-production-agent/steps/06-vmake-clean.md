# 06 VMake

`FINAL_DESIGN_LOCKED` 후 VMake에 원본을 올려 `clean_source.mp4`를 받는다. 클린 영상은 화면 전용이며 내장 음성은 음소거한다.

`clean_visual_manifest.json`에 source identity, design lock, 클린 영상 SHA-256과 예상 길이·해상도를 고정한다. `references/checks/clean-visual.md`에 따라 아래 검증을 실행하고 신규 `clean_visual_receipt.json`을 만든다.

```powershell
python scripts/validate_clean_visual.py --manifest clean_visual_manifest.json --source-identity source_identity.json --design-lock-evidence design_lock_evidence.json --clean-visual-evidence evidence/clean_visual_receipt.json --approved-evidence-root evidence
```

receipt가 스키마에 맞고 실제 ffprobe 결과까지 일치할 때만 `CLEAN_VISUAL_READY`다.
