# 장면 유형별 모션 조합표

`work/scenes.py` 의 장면에 `"motion": "<유형>"` 을 적으면 기본 모션이 붙는다. 강조는 비트에 `"fx": "<이름>"` 을 적을 때만 붙는다.
유형을 안 적으면 아무 모션도 붙지 않는다(옛 회차와 같은 화면).

| 유형 | 비트 | 기본 (자동) | 허용 강조 (최대 1개) | 금지 |
|:--|:--|:--|:--|:--|
| `opening` 제목·챕터 | `T` | word_slide · parallax_in | snap_zoom | 글자 해독 |
| `explain` 일반 설명 | `T`·`P` | float_in | 없음 | shake, glow |
| `quote` 발언 인용 | `Q` | float_in | glow | 글자 단위 과다 |
| `evidence` 숫자·문서 | `P`·`T` | underline | snap_zoom 또는 light_sweep | 흔들림 |
| `timeline` 시간 흐름 | `timeline` | anticipation · follow_through | snap_zoom | 2.5D |
| `flow` 인과·절차 | `flow` | anticipation · trail | burst | shake |
| `relation` 인물 관계 | `relation` | depth_in | parallax_in | 왜곡 효과 |
| `move` 장소·상태 | `move` | anticipation · trail | 없음 | 휩 팬 |
| `contrast` 대립·모순 | `T`·`P` | float_in · follow_through | shake | 강조 두 개 |
| `closing` 마무리 | `P`·`T` | follow_through | 없음 | 모든 강조 |
| `document` 문서·기사 | `doc` | 없음 (도식 자체가 줄 순차·밑줄) | light_sweep | shake |

## 쓰는 법

```python
{"file": "NL42-NL44", "chapter": C3, "motion": "evidence", "beats": [
   dict(P("NL42", "국회 회의록", [("발언 일자", "1990-01-22", ""), ("표결", "찬성 128", "cy")]),
        fx="light_sweep"),
   T("NL43", "기록은 <span class='hl'>남아 있다</span>")]},
```

- `dict(T(...), fx="glow")` 처럼 비트에 `fx` 를 얹는다. 강조를 안 줄 장면은 `motion` 만 적는다.
- `timeline` 에서 `fx="snap_zoom"` 은 `fx_at=<칩 번호>` 로 어느 시점을 키울지 고른다. 안 적으면 마지막 칩.
- `burst` 는 `bypass` 가 있는 `flow` 비트에만 붙는다.

## 기본 모션이 하는 일

| 이름 | 효과 | 대상 |
|:--|:--|:--|
| word_slide | 12 Per-character 한국어판. 어절이 차례로 들어온다 | `T`·`P`·`Q` 본문 |
| float_in | 글자가 아래에서 부드럽게 떠오른다 (0.50초, `presets.FLOAT_SECONDS`) | `T`·`P`·`Q` 본문 |
| underline | 15 Write-on · 19 Trim Paths. 강조 어절 밑에 선 | `.hl` 어절 |
| light_sweep | 36 Light Sweep. 카드 위를 한 번 지나간다 | 비트 상자 |
| follow_through | 07 Follow-through. 라벨·값이 늦게 정착 | 날짜 · 표 값 · 부제 |
| anticipation | 06 Anticipation. 출발 전 0.15초 후퇴 | 핀 · 패킷 · 표식 |
| trail | 10 Motion Trails. 이동 중에만 꼬리 | 핀 · 패킷 |
| depth_in | 32 2.5D 얕게 + 33 Rack Focus | 관계도 노드 |
| parallax_in | 31 Parallax. 진입 때 배경이 한 번 어긋난다 | 격자 · 리본 |

상한과 금지는 [limits.md](limits.md). 40개 대조는 [index.md](index.md).
