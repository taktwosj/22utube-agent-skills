# Clean visual check

Stage 06은 `clean_visual_manifest.json`이 고정한 source identity, design lock, `clean_source.mp4`를 실제 SHA-256과 ffprobe 결과로 다시 확인한다.

필수 확인:

- 모든 문서의 `episode_id`와 source fingerprint가 같다.
- source identity, design lock, 원본 영상, 클린 영상의 SHA-256이 선언값과 같다.
- 클린 영상에 video stream이 있고 길이와 해상도가 manifest와 일치한다.
- `clean_visual_receipt.json`은 승인된 증거 루트 아래의 존재하지 않는 신규 경로에만 쓴다.

검증기: `scripts/validate_clean_visual.py`
