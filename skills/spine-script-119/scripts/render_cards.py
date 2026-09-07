# -*- coding: utf-8 -*-
"""NAR 카드 PNG 렌더. 119의 render_democratic_blue_card.py 를 카드별 --css 로 호출한다.

style_profile 은 DEMOCRATIC_BLUE_INSET_CARD_V2 그대로다. CSS 만 바뀌고 지오메트리 검증은 119 렌더러가 한다.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import CAPCUT_119, load_cards_def, resolve_root, root_parser  # noqa: E402

RENDER = CAPCUT_119 / "scripts" / "render_democratic_blue_card.py"
LIMITS = {"top_label": 32, "headline1": 28, "headline2": 28, "footer": 52,
          "block_label": 16, "block_main": 24, "block_sub": 42}


def main():
    p = root_parser("NAR 카드 PNG 렌더")
    p.add_argument("only", nargs="*", help="특정 card_id 만")
    args = p.parse_args()
    root = resolve_root(args)
    cd = load_cards_def(root)
    cards_dir, css_dir = root / "cards", root / "work" / "cardcss"
    cards_dir.mkdir(exist_ok=True)
    only = set(args.only)
    n = 0
    for card in cd.CARDS:
        cid, kind = card[0], card[1]
        if kind != "NAR" or (only and cid not in only):
            continue
        pl = card[7]
        for k, lim in LIMITS.items():
            if len(pl[k]) > lim:
                raise SystemExit(f"CARD_TEXT_OVER {cid}.{k} {len(pl[k])}>{lim}: {pl[k]!r}")
        css = css_dir / f"v_{pl['css']}.css"
        if not css.is_file():
            raise SystemExit(f"CSS_VARIANT_MISSING {cid}: {css} — make_card_css.py 먼저")
        payload = {
            "visual_id": cid, "style_profile": "DEMOCRATIC_BLUE_INSET_CARD_V2", "raster_size": "1920x1080",
            "top_label": pl["top_label"], "headline_line1": pl["headline1"], "headline_line2": pl["headline2"],
            "footer_text": pl["footer"], "lower_safe_area": True, "highlight_terms": pl.get("hl", []),
            "info_blocks": [{"label": pl["block_label"], "main": pl["block_main"], "sub": pl["block_sub"]}],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False); tmp = fh.name
        r = subprocess.run([sys.executable, str(RENDER), "--input", tmp, "--output", str(cards_dir / f"{cid}.png"),
                            "--css", str(css)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        Path(tmp).unlink(missing_ok=True)
        if r.returncode != 0:
            raise SystemExit(f"RENDER_FAIL {cid}\n{r.stdout[-500:]}\n{r.stderr[-500:]}")
        n += 1
        print(f"ok {cid:14s} {pl['css']:6s}")
    print(f"rendered {n}")


if __name__ == "__main__":
    main()
