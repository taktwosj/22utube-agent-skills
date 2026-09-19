# -*- coding: utf-8 -*-
"""쇼츠 앞·뒤 세로 하이퍼프레임 삽화 (1080x1416) — cards_def.SHORTS 를 읽어 head·tail mp4 를 만든다.

0918 회차 전용 shorts_hf.py 를 스킬로 올린 것(2026-09-19). 회차 폴더에 제작 코드를 두지 않는다.

    python gen_short_hf.py --root <root>            # 전부
    python gen_short_hf.py --root <root> --only 01_백일회견
    python gen_short_hf.py --root <root> --check-only

쇼츠 한 편 = head(앞 나레이션 동안) + tail(뒤 나레이션 + 구독 안내 카드). 결과는
    <root>/hyperframes_shorts/<slug>_head.mp4 · <slug>_tail.mp4
    SHORTS_ART/<art>  ·  SHORTS_ART/<art 의 _head→_tail>       ← build_short.py 가 이 이름으로 찾는다

cards_def.SHORTS 항목에 화면 비트를 적는다 (없으면 claim/counter 로 기본 비트를 만든다):
    hf_head=[(["NL115"], "킥커", "큰 글씨<br><span class='g'>강조</span>", "부제"), ...]
    hf_tail=[...]          # 마지막에 붙는 안내·구독 두 줄(N_SHORTS)은 자동으로 CTA 카드가 된다
비트의 nl 목록 합이 그 구간 나레이션 길이가 된다. head 비트의 nl 은 head_narration 안에서, tail 은 tail_narration 안에서 고른다.
톤: 딥 네이비 + 보라·시안 글로우, 유리 카드, 어절 슬라이드. 글자·로고만 쓰고 실존 인물 얼굴은 넣지 않는다.
"""
from __future__ import annotations

import json
import math
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import SHORTS_ART, SKILL_ROOT, load_cards_def_raw, resolve_root, root_parser  # noqa: E402
from render_scenes import npx, run_logged  # noqa: E402
from runtime_paths import configured_path  # noqa: E402

W, H = 1080, 1416
PAD = 1.0
CTA_MARKS = ("더 자세한 내용은", "구독과 좋아요")
ASSET_SOURCE = configured_path(
    "HF_ASSET_SOURCE",
    SKILL_ROOT.parent / "hyperframes-news-graphics" / "assets" / "news-institutional-flow" / "assets")


def G(t: str) -> str:
    return f"<span class='g'>{t}</span>"


CSS = """
@font-face{font-family:P;src:url(assets/PretendardVariable.woff2);font-weight:100 900}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1416px;overflow:hidden;background:#050816}
#scene{position:relative;width:1080px;height:1416px;overflow:hidden;font-family:P,sans-serif;color:#fff}
.bg{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 0%,#101a45 0%,#070b20 55%,#04050f 100%)}
.blob{position:absolute;border-radius:50%;filter:blur(90px);opacity:.75}
.b1{width:760px;height:760px;left:-240px;top:-120px;background:radial-gradient(circle,#7c3aed 0%,rgba(124,58,237,0) 70%)}
.b2{width:820px;height:820px;right:-300px;bottom:-160px;background:radial-gradient(circle,#06b6d4 0%,rgba(6,182,212,0) 70%)}
.b3{width:520px;height:520px;right:40px;top:260px;background:radial-gradient(circle,#ec4899 0%,rgba(236,72,153,0) 70%);opacity:.45}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:72px 72px;
  -webkit-mask-image:radial-gradient(70% 60% at 50% 50%,#000 30%,transparent 80%)}
.streak{position:absolute;left:-40%;top:0;width:40%;height:100%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.10),transparent);transform:skewX(-18deg)}
.stage{position:absolute;left:80px;right:80px;top:300px;height:820px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;opacity:0}
.chip{display:inline-flex;align-items:center;gap:14px;padding:14px 30px;border-radius:999px;background:rgba(255,255,255,.08);border:1.5px solid rgba(255,255,255,.22);
  font-size:38px;font-weight:700;color:#a5f3fc;letter-spacing:-.5px;backdrop-filter:blur(8px)}
.chip:before{content:"";width:14px;height:14px;border-radius:50%;background:#22d3ee;box-shadow:0 0 18px #22d3ee}
.mega{margin-top:44px;font-size:128px;line-height:1.08;font-weight:900;letter-spacing:-5px;text-shadow:0 10px 40px rgba(0,0,0,.45)}
.mega .w{display:inline-block;opacity:0}
.g{background:linear-gradient(90deg,#67e8f9 0%,#a78bfa 50%,#f472b6 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.bar{margin-top:46px;width:320px;height:10px;border-radius:10px;background:linear-gradient(90deg,#22d3ee,#a78bfa,#f472b6);transform-origin:left;box-shadow:0 0 30px rgba(167,139,250,.7)}
.sub{margin-top:34px;font-size:50px;font-weight:600;color:rgba(255,255,255,.78);letter-spacing:-1px}
.card{position:absolute;left:90px;right:90px;top:420px;padding:70px 60px;border-radius:44px;background:rgba(255,255,255,.07);border:1.5px solid rgba(255,255,255,.2);
  backdrop-filter:blur(14px);box-shadow:0 40px 120px rgba(0,0,0,.45);opacity:0;text-align:center}
.card .t{font-size:96px;font-weight:900;letter-spacing:-4px;line-height:1.12}
.btns{display:flex;gap:30px;justify-content:center;margin-top:60px}
.btn{display:flex;align-items:center;gap:18px;padding:30px 50px;border-radius:999px;font-size:52px;font-weight:800}
.sub1{background:#ef4444;box-shadow:0 0 50px rgba(239,68,68,.6)}
.like{background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.35)}
.btn svg{width:56px;height:56px}
.dots{position:absolute;inset:0}
"""


def words(html: str) -> str:
    out = []
    for part in html.split("<br>"):
        tokens, buf = [], part
        while buf:
            if buf.startswith("<span"):
                end = buf.index("</span>") + 7
                tokens.append(buf[:end]); buf = buf[end:].lstrip()
            else:
                nxt = buf.find("<span")
                chunk = buf if nxt < 0 else buf[:nxt]
                tokens += chunk.split()
                buf = "" if nxt < 0 else buf[nxt:]
        out.append(" ".join(f"<span class='w'>{t}</span>" for t in tokens))
    return "<br>".join(out)


def page(out_dir: Path, name: str, beats: list, cta: list | None, dur: dict) -> float:
    """beats = [(nl list, kicker, mega html, sub)] · cta = [nl, nl] 또는 None. 총 길이(초)를 돌려준다."""
    span = lambda nls: sum(dur[n] for n in nls)  # noqa: E731
    for nls, *_ in beats:
        for n in nls:
            if n not in dur:
                raise SystemExit(f"SHORT_HF_UNKNOWN_LINE: {name} {n} — work/narration_lines.json 에 없다")
    t, body, js = 0.0, [], []
    for i, (nls, kicker, mega, sub) in enumerate(beats, 1):
        sp = span(nls) + (PAD if (i == len(beats) and not cta) else 0)
        body.append(f"<div class='stage' id='s{i}'>" + (f"<div class='chip' id='c{i}'>{kicker}</div>" if kicker else "")
                    + f"<div class='mega' id='m{i}'>{words(mega)}</div><div class='bar' id='r{i}'></div>"
                    + (f"<div class='sub' id='u{i}'>{sub}</div>" if sub else "") + "</div>")
        js.append(f"tl.set('#s{i}',{{opacity:1}},{t:.3f});")
        if kicker:
            js.append(f"tl.fromTo('#c{i}',{{opacity:0,y:-30}},{{opacity:1,y:0,duration:.5,ease:'power3.out'}},{t:.3f});")
        if sub:
            js.append(f"tl.fromTo('#u{i}',{{opacity:0,y:30}},{{opacity:1,y:0,duration:.5,ease:'power3.out'}},{t+.6:.3f});")
        js.append(f"""
tl.fromTo('#m{i} .w',{{opacity:0,y:90,filter:'blur(14px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.7,stagger:.09,ease:'power4.out'}},{t+.12:.3f});
tl.fromTo('#r{i}',{{scaleX:0}},{{scaleX:1,duration:.7,ease:'power3.inOut'}},{t+.45:.3f});
tl.to('#m{i}',{{scale:1.035,duration:{max(sp-.8,.3):.3f},ease:'none',transformOrigin:'left center'}},{t+.8:.3f});""")
        if i < len(beats) or cta:
            js.append(f"tl.to('#s{i}',{{opacity:0,y:-40,duration:.35,ease:'power2.in'}},{t+sp-.35:.3f});")
        t += sp
    if cta:
        sp = span(cta) + PAD
        body.append("<div class='card' id='cta'><div class='t'>전체 영상은<br><span class='g'>아래 링크</span>에서</div>"
                    "<div class='btns'><div class='btn sub1' id='k1'><svg viewBox='0 0 24 24' fill='#fff'><path d='M10 15l5.2-3L10 9v6zm11.6-7.8c.4 1.4.4 4.8.4 4.8s0 3.4-.4 4.8a2.5 2.5 0 0 1-1.8 1.8C18.4 19 12 19 12 19s-6.4 0-7.8-.4a2.5 2.5 0 0 1-1.8-1.8C2 15.4 2 12 2 12s0-3.4.4-4.8a2.5 2.5 0 0 1 1.8-1.8C5.6 5 12 5 12 5s6.4 0 7.8.4a2.5 2.5 0 0 1 1.8 1.8z'/></svg>구독</div>"
                    "<div class='btn like' id='k2'><svg viewBox='0 0 24 24' fill='#fff'><path d='M2 21h4V9H2v12zm20-11a2 2 0 0 0-2-2h-6.3l1-4.6v-.3c0-.4-.2-.8-.4-1.1L13.2 1 6.6 7.6C6.2 8 6 8.5 6 9v10a2 2 0 0 0 2 2h9c.8 0 1.5-.5 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7v-2z'/></svg>좋아요</div></div></div>")
        d0 = dur[cta[0]]
        js.append(f"""tl.fromTo('#cta',{{opacity:0,y:80,scale:.94}},{{opacity:1,y:0,scale:1,duration:.7,ease:'power4.out'}},{t:.3f});
tl.fromTo('#k1',{{scale:.6,opacity:0}},{{scale:1,opacity:1,duration:.5,ease:'back.out(2)'}},{t+d0:.3f});
tl.fromTo('#k2',{{scale:.6,opacity:0}},{{scale:1,opacity:1,duration:.5,ease:'back.out(2)'}},{t+d0+.15:.3f});
tl.to('#k1',{{scale:1.06,duration:.45,yoyo:true,repeat:3,ease:'sine.inOut'}},{t+d0+.6:.3f});""")
        t += sp
    total = round(math.ceil(t * 10) / 10 + .5, 1)
    dots = "".join(f"<i style='position:absolute;left:{(k*137)%W}px;top:{(k*263)%H}px;width:{2+k%3}px;height:{2+k%3}px;border-radius:50%;background:rgba(255,255,255,{.15+(k%5)*.08:.2f})' class='p'></i>" for k in range(60))
    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width={W},height={H}">
<title>{name}</title><script src="assets/gsap.min.js"></script><style>{CSS}</style></head><body>
<div id="scene" data-composition-id="{name.lower()}" data-start="0" data-duration="{total}" data-width="{W}" data-height="{H}">
<div class="bg" data-layout-ignore></div><div class="blob b1" id="b1" data-layout-ignore></div><div class="blob b2" id="b2" data-layout-ignore></div><div class="blob b3" id="b3" data-layout-ignore></div>
<div class="grid" data-layout-ignore></div><div class="dots" data-layout-ignore>{dots}</div><div class="streak" id="st" data-layout-ignore></div>
{''.join(body)}
</div>
<script>
const tl=gsap.timeline({{paused:true}});
tl.to('#b1',{{x:120,y:80,duration:{total},ease:'sine.inOut'}},0);
tl.to('#b2',{{x:-140,y:-90,duration:{total},ease:'sine.inOut'}},0);
tl.to('#b3',{{x:-60,y:120,scale:1.2,duration:{total},ease:'sine.inOut'}},0);
tl.to('.p',{{y:-120,duration:{total},ease:'none'}},0);
tl.fromTo('#st',{{xPercent:0}},{{xPercent:360,duration:1.6,ease:'power2.inOut'}},.2);
{chr(10).join(js)}
window.__timelines={{'{name.lower()}':tl}};
</script></body></html>"""
    proj = out_dir / name
    if proj.exists():
        shutil.rmtree(proj)
    (proj / "assets").mkdir(parents=True)
    for f in ("gsap.min.js", "PretendardVariable.woff2"):
        src = ASSET_SOURCE / f
        if not src.is_file():
            raise SystemExit(f"HF_ASSETS_MISSING: {src}")
        shutil.copy(src, proj / "assets" / f)
    (proj / "hyperframes.json").write_text(json.dumps({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}, indent=2), encoding="utf-8")
    (proj / "index.html").write_text(html, encoding="utf-8")
    return total


def default_beats(entry: dict, lines: dict) -> tuple[list, list, list | None]:
    """hf_head/hf_tail 이 없을 때: claim 을 head, counter 를 tail 큰 글씨로. N_SHORTS 안내 두 줄은 CTA."""
    head_nl = list(entry["head_narration"])
    tail_all = list(entry["tail_narration"])
    cta = [n for n in tail_all if lines[n]["text"].startswith(CTA_MARKS)]
    tail_nl = [n for n in tail_all if n not in cta]
    head = entry.get("hf_head") or [(head_nl, entry.get("t1", ""), entry["claim"], "")]
    tail = entry.get("hf_tail") or ([(tail_nl, entry.get("t2", ""), entry["counter"], "")] if tail_nl else [])
    return head, tail, (cta if len(cta) == 2 else None)


def main() -> int:
    p = root_parser("쇼츠 앞·뒤 세로 하이퍼프레임 삽화")
    p.add_argument("--only", help="이 슬러그만")
    p.add_argument("--check-only", action="store_true")
    args = p.parse_args()
    root = resolve_root(args)
    cd = load_cards_def_raw(root)
    lines_path = root / "work" / "narration_lines.json"
    if not lines_path.is_file():
        raise SystemExit(f"NARRATION_LINES_MISSING: {lines_path}")
    rows = json.loads(lines_path.read_text(encoding="utf-8"))
    dur = {r["name"]: r["duration"] for r in rows}
    lines = {r["name"]: {"text": (root / "narration" / f"{r['name']}.txt").read_text(encoding="utf-8").strip()
                          if (root / "narration" / f"{r['name']}.txt").is_file() else ""} for r in rows}
    out_dir = root / "hyperframes_shorts"
    logs = out_dir / "_logs"
    logs.mkdir(parents=True, exist_ok=True)
    exe = npx()
    SHORTS_ART.mkdir(parents=True, exist_ok=True)
    failed = 0
    for entry in getattr(cd, "SHORTS", []):
        slug = entry["slug"]
        if args.only and slug != args.only:
            continue
        head, tail, cta = default_beats(entry, lines)
        art = Path(entry["art"])
        if "_head" not in art.stem:
            raise SystemExit(f"SHORT_ART_NAME: {art.name} — art 이름에 _head 가 있어야 _tail 을 짝지을 수 있다")
        for kind, beats, use_cta in (("head", head, None), ("tail", tail, cta)):
            if not beats and not use_cta:
                continue
            name = f"{slug}_{kind}"
            total = page(out_dir, name, beats, use_cta, dur)
            proj, mp4 = out_dir / name, out_dir / f"{name}.mp4"
            chk = run_logged([exe, "--yes", "hyperframes", "check", str(proj), "--strict"], logs / f"{name}.check.log")
            ren = None
            if chk == 0 and not args.check_only:
                ren = run_logged([exe, "--yes", "hyperframes", "render", str(proj), "-q", "high", "-f", "30",
                                  "-o", str(mp4), "--quiet"], logs / f"{name}.render.log")
                if ren == 0 and mp4.is_file():
                    dest = SHORTS_ART / (art.name if kind == "head" else art.name.replace("_head", "_tail"))
                    shutil.copy2(mp4, dest)
            print(f"{name:24s} {total:5.1f}s check={chk} render={ren}", flush=True)
            if chk != 0 or (ren not in (None, 0)):
                failed += 1
    if failed:
        print(f"SHORT_HF_FAILED: {failed} — hyperframes_shorts/_logs/ 를 본다")
        return 2
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
