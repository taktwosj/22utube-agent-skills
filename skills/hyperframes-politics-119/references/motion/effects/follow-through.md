# follow-through — 07 늦은 정착

판이 멈춘 뒤 라벨·값이 조금 늦게 자리를 잡는다. 화면 전체가 한 번에 굳는 느낌을 없앤다.

## 대상과 시각

| 비트 | 대상 | 언제 | 간격 |
|:--|:--|:--|:--|
| `timeline` | 날짜 `.tdate` | S+1.1 | 0.06초 |
| `panel` | 값 `.row .v` | S+0.5 | 0.08초 |
| `title`·`bubble` | 부제 `#s<i>` | S+0.7 | — |

```js
tl.fromTo('#b1 .tdate', {y:-8}, {y:0, duration:.5, stagger:.06,
                                 ease:'back.out(1.2)', immediateRender:false}, 4.1000);
```

## 지키는 것

- 이동은 8px 이하, `y` 만 쓴다.
- `back.out(1.2)` 보다 센 반동을 쓰지 않는다. `elastic` · `bounce` 는 정치 다큐 톤이 아니다(index.md 03·04).
- 이미 자기 트윈이 있는 요소에는 붙이지 않는다. `timeline` 의 칩(`.tchip`)은 `diagram/timeline.py` 가 이미 `scale`·`y` 를 쓰므로 날짜만 건드린다.
- 한 번만 움직인다. 반복하면 상시 흔들림 금지에 걸린다.
