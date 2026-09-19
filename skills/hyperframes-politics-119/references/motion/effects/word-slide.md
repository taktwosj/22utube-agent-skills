# word-slide — 12 Per-character 한국어판 (13 Tracking 대체)

**왜 대체인가.** 13 Tracking 은 글자 간격을 늘렸다 줄인다. `letterSpacing` 트윈은 매 프레임 리플로를 일으켜 `HA/adapters/gsap-transforms-and-perf.md:62` 가 금지한다. 한글은 글자 단위로 쪼개면 낱글자가 흩어져 읽기도 나빠진다.
**대신.** 어절(띄어쓰기 단위)로 나눠 `x` 로만 민다. 간격은 그대로다. (사용자 확정 2026-09-16)

## 구현

`hf119/motion/fx.py` 의 `word_slide`. 헬퍼 `hfW` 가 텍스트 노드를 어절 `span.hfw` 로 바꾸고 `display:inline-block` 만 인라인으로 준다. CSS 파일은 건드리지 않는다.

```js
var q = hfW(document.getElementById('m1'));
tl.fromTo(q, {opacity:0, x:-20},
  {opacity:1, x:0, duration:.46, stagger:Math.min(.08, .44/q.length),
   ease:'power3.out', immediateRender:false}, S+0.16);
```

- `stagger` 는 어절 수로 나눠 **그룹 합계 0.5초**를 넘지 않게 한다(`HA/rules-index.md:13`).
- `<span class='hl'>` · `<span class='cy'>` 안쪽도 어절로 쪼개지지만 색 클래스는 부모에 남아 그대로 보인다.
- `<br>` 은 그대로 둔다. 줄바꿈이 유지된다.

## 쓰는 곳

`opening` 유형의 기본 모션. 설명·인용에는 `mask_reveal` 을 쓴다. 두 개를 같은 비트에 겹치지 않는다.

## 확인

`hyperframes check --strict` 의 Layout·Contrast 가 통과해야 한다. 어절이 `#safe` 밖으로 나가면 안 된다.
