# -*- coding: utf-8 -*-
"""나레이션 카드 도형 CSS 변형. 설치본 템플릿은 건드리지 않고 render 시 --css 로만 갈아끼운다.

지오메트리 계약(.main-shell/.footer/.info-block 배치)은 stock V2 와 동일하게 유지하고,
장식은 .main-shell::before / ::after 절대배치 레이어로만 넣는다. 실사 이미지는 쓰지 않는다.
출력: <root>/work/cardcss/v_<variant>.css
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent))
from _common import resolve_root, root_parser  # noqa: E402

BASE = """
:root { --blue-0:#051327; --blue-1:#0a2a5d; --white:#f7fbff; --muted:#c5d5ea; --yellow:#ffd24a; }
* { box-sizing:border-box; }
html, body { width:1280px; height:720px; margin:0; overflow:hidden; font-family:"Pretendard","Noto Sans KR","Malgun Gothic",sans-serif; color:var(--white); }
body { position:relative; background:linear-gradient(135deg,#0d3979 0%,var(--blue-1) 42%,var(--blue-0) 100%); }
.main-shell { position:absolute; inset:0; padding:34px 50px 28px; display:flex; flex-direction:column; background:linear-gradient(120deg,rgba(4,22,49,.99),rgba(7,33,74,.96)); border:2px solid rgba(118,174,238,.64); border-radius:24px; box-shadow:0 18px 52px rgba(0,0,0,.36); overflow:hidden; }
.main-shell::before, .main-shell::after { content:""; position:absolute; pointer-events:none; z-index:0; background-repeat:no-repeat; }
.top-label, .headline, .info-grid, .footer { position:relative; z-index:2; }
.top-label { font-size:24px; letter-spacing:.16em; font-weight:800; color:#a8d1ff; margin-bottom:10px; }
.headline { margin:0; font-size:60px; line-height:1.08; letter-spacing:-.05em; font-weight:900; }
.headline .line { display:block; min-height:65px; }
.highlight { color:var(--yellow); }
.info-grid { display:flex; flex:1 1 auto; min-height:0; align-items:center; justify-content:center; margin:16px 0 12px; }
.info-block { position:relative; width:100%; min-height:270px; padding:30px 40px; display:flex; flex-direction:column; justify-content:center; border:2px solid rgba(111,170,239,.62); border-radius:22px; background:linear-gradient(120deg,rgba(28,74,139,.72),rgba(16,51,105,.62)); box-shadow:0 14px 34px rgba(0,0,0,.20); overflow:hidden; }
.info-block > * { position:relative; z-index:2; }
.info-label { font-size:30px; font-weight:800; color:#9fd0ff; margin-bottom:12px; }
.info-main { font-size:68px; font-weight:900; line-height:1.12; letter-spacing:-.04em; }
.info-sub { margin-top:14px; font-size:40px; font-weight:700; line-height:1.2; color:var(--muted); }
.footer { flex:0 0 46px; padding-top:12px; border-top:1px solid rgba(133,181,235,.44); font-size:24px; line-height:1.28; color:#e1ecfb; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.lower-safe-area { display:none; }
"""

S, Y, D = "#7fb4ee", "#ffd24a", "#2f6bb5"   # 선 / 강조 / 흐린 선


def svg(body: str, w: int = 460, h: int = 300) -> str:
    doc = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" fill="none">{body}</svg>'
    return 'url("data:image/svg+xml,' + quote(doc, safe="") + '")'


VARIANTS = {
    # 저울 — 비대칭·판정
    "scale": svg(
        f'<line x1="230" y1="40" x2="230" y2="250" stroke="{D}" stroke-width="6"/>'
        f'<path d="M150 250 H310" stroke="{D}" stroke-width="8" stroke-linecap="round"/>'
        f'<g transform="rotate(-13 230 70)">'
        f'<line x1="60" y1="70" x2="400" y2="70" stroke="{S}" stroke-width="7" stroke-linecap="round"/>'
        f'<line x1="90" y1="70" x2="90" y2="130" stroke="{D}" stroke-width="4"/>'
        f'<line x1="370" y1="70" x2="370" y2="130" stroke="{D}" stroke-width="4"/>'
        f'<path d="M30 130 H150 L120 196 H60 Z" stroke="{Y}" stroke-width="7" stroke-linejoin="round"/>'
        f'<path d="M310 130 H430 L406 172 H334 Z" stroke="{S}" stroke-width="6" stroke-linejoin="round"/>'
        f'</g><circle cx="230" cy="70" r="12" stroke="{Y}" stroke-width="6"/>'),
    # 비율 바 — 수치 대비
    "ratio": svg(
        f'<rect x="20" y="70" width="420" height="46" rx="10" stroke="{D}" stroke-width="4"/>'
        f'<rect x="20" y="70" width="378" height="46" rx="10" fill="{S}" fill-opacity=".55"/>'
        f'<rect x="20" y="184" width="420" height="46" rx="10" stroke="{D}" stroke-width="4"/>'
        f'<rect x="20" y="184" width="210" height="46" rx="10" fill="{Y}" fill-opacity=".7"/>'
        f'<line x1="230" y1="164" x2="230" y2="250" stroke="{Y}" stroke-width="4" stroke-dasharray="10 8"/>'),
    # 타임라인 — 시간 간격
    "time": svg(
        f'<line x1="30" y1="150" x2="430" y2="150" stroke="{D}" stroke-width="5"/>'
        f'<circle cx="70" cy="150" r="17" stroke="{S}" stroke-width="6"/>'
        f'<circle cx="230" cy="150" r="17" stroke="{S}" stroke-width="6"/>'
        f'<circle cx="390" cy="150" r="24" stroke="{Y}" stroke-width="8"/>'
        f'<circle cx="390" cy="150" r="9" fill="{Y}" fill-opacity=".8"/>'
        f'<path d="M70 150 V96" stroke="{D}" stroke-width="4"/><path d="M230 150 V96" stroke="{D}" stroke-width="4"/>'
        f'<path d="M390 150 V80" stroke="{Y}" stroke-width="4"/>'),
    # 숫자 블록 — 사람 수·건수
    "num": svg(
        ''.join(f'<rect x="{40+i*52}" y="{110 if i%2 else 96}" width="34" height="{78 if i%2 else 106}" rx="6" '
                f'stroke="{Y if i < 3 else D}" stroke-width="5"/>' for i in range(8))
        + f'<line x1="30" y1="228" x2="430" y2="228" stroke="{S}" stroke-width="5"/>'),
    # 흐름 — 인과·구조
    "flow": svg(
        ''.join(f'<path d="M{40+i*130} 90 L{130+i*130} 150 L{40+i*130} 210" stroke="{Y if i==2 else S}" '
                f'stroke-width="{9 if i==2 else 7}" stroke-linecap="round" stroke-linejoin="round" '
                f'opacity="{0.35 + i*0.28}"/>' for i in range(3))),
    # 인용 — 원본 발화
    "quote": svg(
        f'<path d="M150 92 C96 92 60 128 60 178 C60 214 86 238 118 238 C148 238 170 216 170 188 '
        f'C170 160 150 140 124 140 C120 140 116 141 112 142 C120 118 138 104 158 98 Z" stroke="{S}" stroke-width="7" stroke-linejoin="round"/>'
        f'<path d="M330 92 C276 92 240 128 240 178 C240 214 266 238 298 238 C328 238 350 216 350 188 '
        f'C350 160 330 140 304 140 C300 140 296 141 292 142 C300 118 318 104 338 98 Z" stroke="{Y}" stroke-width="7" stroke-linejoin="round"/>'),
    # 경고 — 사선 해칭 (data URI 안에서 <pattern> 참조가 안 잡혀 명시 사선으로)
    "warn": svg(
        f'<rect x="20" y="60" width="420" height="180" rx="16" stroke="{Y}" stroke-width="5"/>'
        + ''.join(f'<line x1="{-160+i*34}" y1="240" x2="{40+i*34}" y2="60" stroke="{D}" stroke-width="9" '
                  f'opacity=".55" clip-path="inset(60px 0px 60px 20px)"/>' for i in range(18))),
    # 격자 — 기본
    "grid": svg(
        ''.join(f'<line x1="{30+i*50}" y1="60" x2="{30+i*50}" y2="240" stroke="{D}" stroke-width="3" opacity=".55"/>' for i in range(9))
        + ''.join(f'<line x1="30" y1="{60+i*45}" x2="430" y2="{60+i*45}" stroke="{D}" stroke-width="3" opacity=".35"/>' for i in range(5))),
    # 갈라짐 — 분열·역전
    "split": svg(
        f'<path d="M230 40 V130" stroke="{S}" stroke-width="8" stroke-linecap="round"/>'
        f'<path d="M230 130 L110 250" stroke="{Y}" stroke-width="8" stroke-linecap="round"/>'
        f'<path d="M230 130 L350 250" stroke="{Y}" stroke-width="8" stroke-linecap="round"/>'
        f'<circle cx="230" cy="130" r="14" stroke="{Y}" stroke-width="6"/>'
        f'<circle cx="110" cy="250" r="10" fill="{S}" fill-opacity=".7"/><circle cx="350" cy="250" r="10" fill="{S}" fill-opacity=".7"/>'),
    # 한 방향 — 군집·쥐떼
    "herd": svg(
        ''.join(f'<path d="M{50+(i%5)*88} {80+(i//5)*70} l30 20 -30 20" stroke="{Y if i==7 else S}" stroke-width="6" '
                f'stroke-linecap="round" stroke-linejoin="round" opacity="{0.85 if i==7 else 0.4}"/>' for i in range(10))),
}

DECOR = """
.main-shell::before {{ right:44px; top:58px; width:392px; height:246px; opacity:.46; background-image:{img}; background-size:392px 246px; }}
.main-shell::after {{ left:0; right:0; top:0; height:6px; background:linear-gradient(90deg,rgba(255,210,74,.9) 0%,rgba(127,180,238,.55) 38%,rgba(127,180,238,0) 100%); }}
.info-block::before {{ content:""; position:absolute; inset:0; z-index:0; pointer-events:none; background:radial-gradient(120% 140% at 88% 50%,rgba(10,42,93,.0) 40%,rgba(4,20,45,.55) 100%); }}
"""


def main():
    args = root_parser("카드 도형 CSS 변형 생성").parse_args()
    root = resolve_root(args)
    out = root / "work" / "cardcss"
    out.mkdir(parents=True, exist_ok=True)
    for name, img in VARIANTS.items():
        (out / f"v_{name}.css").write_text(BASE + DECOR.format(img=img), encoding="utf-8")
    print(f"css variants: {', '.join(VARIANTS)} -> {out}")


if __name__ == "__main__":
    main()
