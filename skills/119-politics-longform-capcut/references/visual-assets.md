# 시각 자산

대본 승인 뒤 C 작업자 한 명이 수행한다. 입력은 승인 대본의 `ASSEMBLY_ONLY_SEED`와 필요한 카드 목록이다. 출력은 이 회차 `Resources`의 지원 이미지·그래픽뿐이다. source, narration, root, target, CapCut draft, `episode_cards.json`을 수정하지 않는다.

## 필요한 경우만 제작

`visual_asset_ref`가 있고 실제 자산이 없을 때만 만든다. 같은 visual ID·문구·style profile·SHA의 PASS 자산이 있으면 재생성하지 않는다.

## DEMOCRATIC_BLUE_CENTER_INFO_CARD_V1

구형 전체화면 프로젝트가 `style_profile`로 명시한 경우에만 사용하는 레거시 profile이다. 새 카드의 기본값으로 선택하지 않는다.

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

## DEMOCRATIC_BLUE_INSET_CARD_V2

이 profile은 새 카드의 기본값이며, 16:9 전체 배경이 아니라 **근본 프로젝트 위에 올리는 이미지 레이어**다. `style_profile`을 생략하거나 빈 값으로 두어도 V2를 선택한다.

```text
templates/democratic_blue_inset_card_v2.html
templates/democratic_blue_inset_card_v2.css
scripts/inset_card_layout.py
scripts/render_democratic_blue_card.py
```

입력 JSON에는 다음을 추가한다.

```json
{
  "style_profile": "DEMOCRATIC_BLUE_INSET_CARD_V2",
  "raster_size": "1920x1080"
}
```

`info_blocks`는 정확히 1개만 허용한다. 주제가 둘 이상이면 각각 별도 JSON·별도 PNG로 만들고 타임라인에서 순서대로 배치한다. 한 카드의 좌우 2열로 합치지 않는다. 글자 크기는 제목 60px, 항목명 30px, 핵심문구 68px, 보조문구 40px 고정이며 긴 문구를 작은 글씨로 축소하지 않는다.

`raster_size`는 `1920x1080`만 허용한다. CapCut에서 수동 V8 근본과 같은 `scale=0.65`, 화면 `x=336, y=189, width=1248, height=702` 프레임에 놓인다. `y=891~1080`은 하단 자막 영역이다. 이미지 안에 출처·상단 챕터·하단 자막을 포함하지 않는다.

## 화면 안전영역

하단 자막 슬롯은 공백 제외 15자 이하 한 줄이다. 기술 PASS는 최종 `VISUAL_GATE`를 대체하지 않는다.
