# 시각 자산

대본 승인 뒤 C 작업자 한 명이 수행한다. 입력은 승인 대본의 `ASSEMBLY_ONLY_SEED`와 필요한 카드 목록이다. 출력은 이 회차 `Resources`의 지원 이미지·그래픽뿐이다. source, narration, root, target, CapCut draft, `episode_cards.json`을 수정하지 않는다.

## 필요한 경우만 제작

`visual_asset_ref`가 있고 실제 자산이 없을 때만 만든다. 같은 visual ID·문구·style profile·SHA의 PASS 자산이 있으면 재생성하지 않는다.

## DEMOCRATIC_BLUE_CENTER_INFO_CARD_V1

실제 파일:

```text
templates/democratic_blue_center_info_card_v1.html
templates/democratic_blue_center_info_card_v1.css
scripts/render_democratic_blue_card.py
```

입력 JSON 최소 필드:

```json
{
  "visual_id": "V001",
  "top_label": "POLICY CHECK",
  "headline_line1": "정책 방향과 실제 집행",
  "headline_line2": "무엇이 달랐나",
  "highlight_terms": ["실제 집행"],
  "info_blocks": [
    {"label": "방향", "main": "정책 목표", "sub": "확인된 설명"},
    {"label": "집행", "main": "세부 시행", "sub": "남은 쟁점"}
  ],
  "footer_text": "다음 원본에서 시행 시점을 확인합니다",
  "lower_safe_area": true
}
```

렌더:

```powershell
python scripts/render_democratic_blue_card.py `
  --input <visual.json> `
  --output <episode_dir>\Resources\V001.png `
  --manifest <episode_dir>\90_reports\V001_visual_manifest.json
```

Windows에서는 Edge/Chrome headless를 자동 탐색한다. 필요하면 `--browser <msedge.exe|chrome.exe>`를 지정한다.

검증:

```text
1920×1080 PNG
SHA-256
2~4 info blocks
하단 324px 안전영역
DOM overflow 없음
문구 길이 제한
```

HTML 자체를 CapCut에 넣지 않는다. PNG는 무음 챕터 전환이면 `CHAPTER_CARD`, 승인 나레이션과 함께 쓰면 `NARRATION_IMAGE`의 실제 조립 자산으로 사용한다. 외부 이미지 검색·AI 이미지 생성·다중 시안을 기본 실행하지 않는다.

## 화면 안전영역

하단 자막 슬롯을 쓰는 카드는 하단 30%에 핵심 문구·도형·인물·로고를 두지 않는다. 기술 PASS는 최종 `VISUAL_GATE`를 대체하지 않는다.
