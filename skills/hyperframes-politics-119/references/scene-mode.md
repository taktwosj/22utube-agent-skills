# 장면 모드

## 장면 제작 — 상세


아래 명령은 `spine-script-119/scripts` 디렉터리에서 실행한다. 생성 구현의 정본은 이 스킬의 `scripts/hf119/`다.

```bash
python plan_hyperframes.py --root <root> --missing     # 만들 장면 이름
# work/scenes.py 의 SPECS 작성 (templates/scenes.template.py)
python render_scenes.py --root <root>                  # 생성 → check --strict → render
python render_scenes.py --root <root> NL02-NL05        # 하나만 다시
```

`hyperframes-politics-119/scripts/hf119` 가 장면을 만든다. spine `hf_lib.py` 는 호환 연결 파일이다. 기본은 큰 글씨 비트(`T` 제목 · `P` 패널 · `Q` 말풍선)이고, 네다섯 장면에 하나꼴로 도식 비트를 섞는다.

```text
timeline   레일이 그려지고 점이 차례로 켜지며 표식이 레일을 따라 이동      시간 흐름
flow       아이콘 카드가 차례로 뜨고 연결선이 그려지며 패킷이 이동        인과·절차. bypass 로 우회 곡선
relation   가운데 인물 사진에서 주변 노드로 선이 뻗는다                  인물 관계
move       출발지·도착지 사이 곡선 위로 핀이 이동                        장소·상태 변화
doc        기사 요지가 md 문서처럼 열리고 줄이 차례로 뜨며 강조 줄에 밑줄   언론 기사 설명. 원문 이미지 아님 고지 항상 표시
```

장면 유형별 모션 조합·상한은 [motion/scene-presets.md](motion/scene-presets.md) 를 읽고 `SPECS` 에 `motion` 을 적는다.

순서도·관계도를 정지 박스 나열로 끝내지 않는다. 선이 그려지며 이어지고 아이콘이 경로를 따라 움직여야 한다(2026-09-14 사용자 지시). 인물 원본 사진은 `PEOPLE_ART/_src/<이름>.jpg|png` 에서 읽고 없으면 `PEOPLE_PHOTO_MISSING` 으로 멈춘다. 사진 정본·복사 절차·최욱 두 장 규칙은 [people-photos.md](people-photos.md). 폰트·GSAP 는 `hyperframes-news-graphics` 승인 템플릿 assets 에서 복사한다. 좌상단 브랜드 문구는 `cards_def.HF_BRAND`(없으면 `민주 디코더`).

**화면 자리.** 렌더는 1920×1080 이지만 119 조립이 위 0~189·아래 891~1080 띠를 잘라내고 좌우 끝까지 1920×702(y 189~891)로 놓는다(2026-09-15 사용자 지시 "위아래 띠만 빼고 좌우는 쓴다"). `hf119` 는 글자·도식·크롬을 전부 그 띠 사이 `#safe` 상자에 두고 배경·격자·리본만 화면 전체에 깐다. 띠 값은 119 `inset_card_layout.NARRATION_VIDEO_STRIP` 을 읽는다. 장면 스냅샷을 볼 때 위아래 띠 부분은 화면에 안 나간다고 보고 판단한다.

`render_scenes.py` 는 check 가 실패한 장면을 렌더하지 않는다. 결과는 `work/render_scenes.json`, 로그는 `hyperframes/_logs/`. 실패가 하나라도 있으면 `HYPERFRAME_RENDER_FAILED` 로 exit 2. 스냅샷은 사람이 눈으로 본다.

```
<root>/hyperframes/NL88-NL90.mp4    NL88 부터 NL90 까지 한 장면으로 덮는다
<root>/hyperframes/NL06.mp4         그 한 줄만 덮는다
```

