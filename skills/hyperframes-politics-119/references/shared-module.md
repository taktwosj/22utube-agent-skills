# 공용 모듈 — 상세

> 원문: `hyperframes-politics-119/SKILL.md` 에서 줄 단위로 옮김. 내용 수정 없음.

## 공용 모듈

CSS 와 헬퍼는 `scripts/politics119_style.py` 에 있다. 회차 스크립트가 CSS 를 처음부터
다시 쓰지 않는다. 다시 쓰면 회차마다 색과 크롬이 조금씩 달라지고 결국 재현이 안 된다.

```python
import sys
sys.path.insert(0, r"<skills>/hyperframes-politics-119/scripts")
from politics119_style import BASE_CSS, GRAMMAR_CSS, chrome, foot, anim, spans, page

css = BASE_CSS + GRAMMAR_CSS["balance"]
beats, total = spans(["rebuttal_1", "rebuttal_2", "rebuttal_3"], timing)
markup = chrome("06 / 처분 경위", "한동훈 공개 자료") + ... + foot("한국경제", 1, 3)
page(dest, "han-rebuttal", "처분 경위", total, css, markup, tweens, audios, assertions,
     asset_source=<이전 회차 assets 폴더>)
```

들어 있는 문법은 `balance`(06) `rails`(07) `stepper`(08) `ledger`(09) `notice`(10) 다.
01~05 는 기준 회차 `PL_20260911_한동훈_척추후보/work/design_five_hyperframes_v2.py` 에 있다.
그 문법을 다시 쓰는 회차에서 이 모듈로 옮긴다. 새로 만든 문법도 재사용 가치가 있으면 올린다.

`spans()` 는 길이를 프레임 정수로 맞춘다. 119 조립이 그룹 안 오프셋을 프레임으로 누적하므로
여기서 어긋나면 카드가 밀린다. 직접 계산하지 말고 이 함수를 쓴다.
