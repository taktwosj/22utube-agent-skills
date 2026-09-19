# -*- coding: utf-8 -*-
"""119 정치롱폼 하이퍼프레임 공용 문법 — CSS 토큰과 페이지 생성 헬퍼.

회차 스크립트가 CSS 를 처음부터 다시 쓰지 않게 한다. 회차마다 새로 쓰면 색과 크롬이
조금씩 달라지고, 결국 회차 폴더를 벗어나면 재현이 안 된다.

사용:

    import sys
    sys.path.insert(0, r"<skills>/hyperframes-politics-119/scripts")
    from politics119_style import BASE_CSS, GRAMMAR_CSS, chrome, foot, anim, spans, page

    css = BASE_CSS + GRAMMAR_CSS["balance"] + GRAMMAR_CSS["ledger"]
    markup = chrome("06 / 처분 경위") + ...
    page(dest, "han-rebuttal", "처분 경위", total, css, markup, tweens, audios, assertions)

문법 이름은 SKILL.md 의 10종 목록과 같다. 없는 문법은 회차에서 새로 쓰고, 재사용할
가치가 있으면 여기로 올린다.
"""
from __future__ import annotations

import html
import json
import math
import shutil
from pathlib import Path

# 폰트·모션은 로컬만 쓴다. CDN 을 쓰면 렌더 머신이 바뀔 때 조용히 깨진다.
ASSET_FILES = ("PretendardVariable.woff2", "gsap.min.js",
               "PRETENDARD-LICENSE.txt", "PHOSPHOR-LICENSE.txt")

TOKENS = {
    "ground": "radial-gradient(ellipse at 60% 20%,#164577,#06172f 70%)",
    "grid": "#5486af12",
    "text": "#f1f7ff",
    "cyan": "#63e2ef",
    "cyan_soft": "#8ef0ee",
    "cyan_rail": "#72e3eb",
    "yellow": "#ffe276",
    "panel_dark": "#0d2c4c",
    "panel_deep": "#0b2947",
    "panel_blue": "#123a63",
    "panel_light": "#eaf2f7",
    "on_light": "#112d46",
    "muted": "#adc8df",
    "eyebrow": "#99d9ed",
}

BASE_CSS = r'''
@font-face{font-family:News;src:url(assets/PretendardVariable.woff2);font-weight:100 900}
*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;overflow:hidden}
body{font-family:News,sans-serif;color:#f1f7ff}p,h1,h2,h3{margin:0}
#main{width:1920px;height:1080px;position:relative;overflow:hidden}
.bg{position:absolute;inset:0;background:radial-gradient(ellipse at 60% 20%,#164577,#06172f 70%)}
.grid{position:absolute;inset:0;background-image:linear-gradient(#5486af12 1px,transparent 1px),linear-gradient(90deg,#5486af12 1px,transparent 1px);background-size:80px 80px}
.chrome{position:absolute;left:96px;right:96px;top:54px;display:flex;justify-content:space-between;align-items:center;font-size:28px;font-weight:750;color:#a3dbf4;letter-spacing:2px}
.chrome b{border-left:5px solid #63e2ef;padding-left:22px;color:#f1f7ff}
.footer{position:absolute;left:96px;right:96px;bottom:40px;display:flex;justify-content:space-between;font-size:26px;color:#adc8df}
.beat{position:absolute;inset:0;opacity:0}
.eyebrow{font-size:34px;font-weight:700;color:#99d9ed;letter-spacing:1px}
.headline{font-size:100px;line-height:1.08;letter-spacing:-4px;font-weight:900}
.accent{color:#ffe276}.mint{color:#8ef0ee}
.caveat{display:inline-flex;align-items:center;gap:14px;padding:14px 26px;border:2px solid #ffe276;border-radius:10px;background:#3a2f0d;color:#ffe276;font-size:30px;font-weight:800}
'''

# 06 기울어지는 저울 — 주장 슬래브 대 기록 슬래브. 대립을 보여줄 때
BALANCE_CSS = r'''
.rb-head{position:absolute;left:96px;top:150px;max-width:1720px}.rb-head .headline{margin-top:22px}
.beam{position:absolute;left:300px;top:640px;width:1320px;height:10px;background:#5fa8c9;border-radius:10px;transform-origin:center}
.fulcrum{position:absolute;left:930px;top:650px;width:0;height:0;border-left:60px solid transparent;border-right:60px solid transparent;border-top:120px solid #1d5183}
.slab{position:absolute;top:410px;width:640px;height:215px;border-radius:18px;padding:28px 34px;box-shadow:0 22px 40px #0005}
.slab .tag{font-size:29px;font-weight:750;letter-spacing:1px}
.slab .big{font-size:58px;font-weight:900;letter-spacing:-2px;margin-top:18px;line-height:1.16}
.slab.claim{left:230px;background:#123a63;border:2px solid #4f8fb8}.slab.claim .tag{color:#9fd2ea}
.slab.record{left:1050px;background:#eaf2f7;color:#112d46;border:2px solid #ffe276}.slab.record .tag{color:#4a6a82}
.rb-note{position:absolute;left:96px;top:830px;width:1728px;border-left:7px solid #ffe276;padding:22px 32px;background:#0c2845;font-size:42px;font-weight:800;line-height:1.3}
'''

# 07 이중 레일 — 두 갈래가 한 표적으로 수렴. 인용 분리판과 등급 셀을 같이 쓴다
RAILS_CSS = r'''
.tg-head{position:absolute;left:96px;top:148px}.tg-head .headline{margin-top:22px;font-size:94px}
.rail{position:absolute;height:12px;border-radius:12px;background:#2c6088;transform-origin:left}
.rail.one{left:150px;top:600px;width:980px}.rail.two{left:150px;top:730px;width:980px}
.rail-fill{position:absolute;height:12px;border-radius:12px;background:#72e3eb;transform-origin:left}
.rail-fill.one{left:150px;top:600px;width:980px}
.rail-fill.two{left:150px;top:730px;width:980px;background:#ffe276}
.rail-label{position:absolute;left:150px;font-size:36px;font-weight:800;color:#cfe8f6}
.rail-label.one{top:538px}.rail-label.two{top:786px}
.target-node{position:absolute;left:1210px;top:552px;width:560px;height:240px;border-radius:24px;border:3px dashed #ffe276;background:#112c47;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px}
.target-node .who{font-size:66px;font-weight:900;color:#ffe276;letter-spacing:-2px}
.target-node .sub{font-size:29px;color:#c6e2ee}
.quote-two{position:absolute;top:420px;width:800px;border-radius:16px;padding:32px 36px;background:#0b2947;border-left:7px solid #5de2ec}
.quote-two.b{border-left-color:#ffe276;background:#102f4f}
.quote-two .src{font-size:28px;color:#a9cde2;font-weight:750}
.quote-two .say{font-size:54px;font-weight:880;margin-top:18px;letter-spacing:-2px;line-height:1.22}
.quote-two.a{left:110px}.quote-two.b{left:1010px}
.diffbar{position:absolute;left:110px;top:790px;width:1700px;border:2px solid #ffe276;border-radius:12px;background:#3a2f0d;color:#ffe276;padding:22px 30px;font-size:40px;font-weight:850}
.grade{position:absolute;top:420px;left:110px;width:1700px;display:flex;gap:26px}
.grade .cell{flex:1;border-radius:18px;background:#0d2c4c;border:2px solid #3d7ba4;padding:30px 28px}
.grade .cell .n{font-size:34px;color:#84e6ed;font-weight:850}
.grade .cell .t{font-size:44px;font-weight:880;margin-top:18px;line-height:1.28;letter-spacing:-1px}
.grade-note{position:absolute;left:110px;top:800px;width:1700px;border-left:7px solid #ffe276;background:#0c2845;padding:24px 32px;font-size:44px;font-weight:820}
'''

# 08 단계 스테퍼 — 고발 → 배당 → 진행. 절차가 어디까지 갔는지
STEPPER_CSS = r'''
.pb-head{position:absolute;left:96px;top:152px}.pb-head .headline{margin-top:22px;font-size:96px}
.steps{position:absolute;left:130px;top:470px;width:1660px;display:flex;justify-content:space-between;align-items:flex-start}
.step{width:520px}
.step .dot{width:44px;height:44px;border-radius:50%;border:8px solid #72e3eb;background:#14496f}
.step .when{font-size:40px;font-weight:880;color:#8cf0ec;margin-top:24px;letter-spacing:-1px}
.step .what{font-size:50px;font-weight:880;margin-top:14px;letter-spacing:-2px;line-height:1.2}
.step .sub{font-size:29px;color:#b8d4e6;margin-top:16px;line-height:1.4}
.steprail{position:absolute;left:152px;top:492px;width:1560px;height:8px;background:#25537a;border-radius:8px}
.steprail-fill{position:absolute;left:152px;top:492px;width:1560px;height:8px;background:#72e3eb;border-radius:8px;transform-origin:left}
.pb-note{position:absolute;left:130px;top:840px;width:1660px;border-left:7px solid #ffe276;background:#0c2845;padding:24px 34px;font-size:42px;font-weight:820;line-height:1.3}
'''

# 09 정산 원장 — 행이 쌓이며 상태 칩이 붙는다. 마무리 전용
LEDGER_CSS = r'''
.wp-head{position:absolute;left:96px;top:150px}.wp-head .headline{margin-top:22px;font-size:98px}
.ledger{position:absolute;left:110px;top:420px;width:1700px}
.row{display:flex;align-items:center;gap:32px;height:112px;border-bottom:1px solid #35618a}
.row .what{flex:1;font-size:50px;font-weight:850;letter-spacing:-2px}
.row .chip{padding:12px 26px;border-radius:999px;font-size:31px;font-weight:850;white-space:nowrap}
.chip.fact{background:#123f63;color:#8ef0ee;border:2px solid #4f97bd}
.chip.claim{background:#3a2f0d;color:#ffe276;border:2px solid #ffe276}
.chip.open{background:#33234a;color:#d7b9ff;border:2px solid #a882e0}
.wp-close{position:absolute;left:110px;top:880px;width:1700px;border-left:7px solid #ffe276;background:#0c2845;padding:24px 34px;font-size:44px;font-weight:850}
'''

# 10 안내 — 중앙 정렬 2판. CTA 전용
NOTICE_CSS = r'''
.cta-head{position:absolute;left:0;right:0;top:210px;text-align:center}
.cta-head .headline{margin-top:24px}
.plates{position:absolute;left:210px;right:210px;top:520px;display:flex;gap:40px}
.plate{flex:1;border-radius:20px;padding:40px 44px;background:#0d2c4c;border:2px solid #3d7ba4;text-align:center}
.plate .n{font-size:32px;color:#84e6ed;font-weight:850;letter-spacing:1px}
.plate .t{font-size:56px;font-weight:900;margin-top:20px;letter-spacing:-2px;line-height:1.2}
.plate.warm{background:#3a2f0d;border-color:#ffe276}
.plate.warm .n{color:#ffe276}.plate.warm .t{color:#ffe276}
.cta-note{position:absolute;left:210px;right:210px;top:800px;text-align:center;font-size:44px;font-weight:820;color:#dcecf8}
'''

GRAMMAR_CSS = {
    "balance": BALANCE_CSS,   # 06
    "rails": RAILS_CSS,       # 07
    "stepper": STEPPER_CSS,   # 08
    "ledger": LEDGER_CSS,     # 09
    "notice": NOTICE_CSS,     # 10
}

# 01~05(키네틱 타이포·카드 스택·녹취 대조·경로 연결·타임라인)은 기준 회차
# PL_20260911_한동훈_척추후보/work/design_five_hyperframes_v2.py 에 있다.
# 그 회차에서 다시 쓸 때 여기로 옮긴다. 옮기기 전까지는 그 파일을 원본으로 본다.
PENDING_GRAMMARS = ("kinetic", "paperstack", "transcript", "route", "timeline")


def e(text: str) -> str:
    return html.escape(text)


def chrome(label: str, brand: str) -> str:
    """좌상단 브랜드 + 우상단 NN / 챕터명. 회차 내내 brand 는 같은 문구를 쓴다."""
    return ('<div class="bg" data-layout-ignore></div><div class="grid" data-layout-ignore></div>'
            f'<header class="chrome"><b>{e(brand)}</b><span>{e(label)}</span></header>')


def foot(source: str, idx: int, total: int) -> str:
    """좌하단 출처 : 채널명 + 우하단 NN / 총개수. 플랫폼명·영문 병기를 넣지 않는다."""
    left = e("출처 : " + source) if source else ""
    return f'<div class="footer"><span>{left}</span><span>{idx:02} / {total:02}</span></div>'


def anim(selector: str, start: dict, end: dict, at: float) -> str:
    end = dict(end)
    end["immediateRender"] = False
    return f"tl.fromTo({json.dumps(selector)},{json.dumps(start)},{json.dumps(end)},{at:.6f});"


def spans(ids, timing):
    """비트별 (id, 시작, 길이, 음성길이). 길이는 프레임 정수로 맞춘다.

    119 조립이 그룹 안 오프셋을 프레임 단위로 누적하므로 여기서 어긋나면 카드가 밀린다.
    """
    out, cursor = [], 0.0
    for i in ids:
        duration = math.ceil(timing[i]["voice_duration"] * 30) / 30
        out.append((i, cursor, duration, timing[i]["voice_duration"]))
        cursor += duration
    return out, cursor


def page(dest: Path, name: str, title: str, duration: float, css: str,
         markup: str, tweens: str, audios, assertions, asset_source: Path) -> dict:
    """프로젝트 폴더 하나를 쓴다. audios 는 (wav 경로, 시작초, 길이초) 목록이다."""
    project = Path(dest) / name
    assets = project / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for f in ASSET_FILES:
        src = Path(asset_source) / f
        if src.is_file() and not (assets / f).exists():
            shutil.copy2(src, assets / f)
    tags = []
    for i, (wav, start, length) in enumerate(audios):
        wav = Path(wav)
        if not (assets / wav.name).exists():
            shutil.copy2(wav, assets / wav.name)
        tags.append(f'<audio id="voice{i}" src="assets/{wav.name}" data-start="{start:.6f}" '
                    f'data-duration="{length:.6f}" data-track-index="10" data-volume="1"></audio>')
    source = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{e(title)}</title>'
              f'<style>{css}</style></head><body>'
              f'<div id="main" data-composition-id="{name}" data-width="1920" data-height="1080" '
              f'data-duration="{duration:.6f}">{markup}{"".join(tags)}</div>'
              f'<script src="assets/gsap.min.js"></script>'
              f'<script>const tl=gsap.timeline({{paused:true}});{tweens}'
              f'window.__timelines={{"{name}":tl}};</script></body></html>')
    (project / "index.html").write_text(source, encoding="utf-8")
    (project / "index.motion.json").write_text(
        json.dumps({"duration": duration, "assertions": assertions}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return {"project": name, "title": title, "duration": duration,
            "source": str(project / "index.html")}
