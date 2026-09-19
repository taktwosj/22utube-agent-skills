"""doc diagram: an edited news article shown like an open markdown file.

나레이션이 기사 내용을 설명하는 동안 문서 창이 열리고 줄이 차례로 뜬다.
원문 이미지가 아니라 편집한 요지이므로 고지 라벨(note)을 항상 보인다.
트윈은 opacity·y·scale·scaleX 만 쓰고 전부 tl 에 절대 시각(S+…)으로 등록한다.
"""
from .. import core  # noqa: F401  (다른 도식과 같은 서명·좌표계 유지)

DEFAULT_NOTE = "보도 요지 · 원문 이미지 아님"
DEFAULT_FNAME = "기사.md"
MAX_LINES = 6
BAR_COLOR = {"hl": "#ffd24a", "cy": "#8ef0ee"}
# 줄 사이 간격(초). (SP-1.2)/줄수 를 이 범위로 자른다
STEP_MIN, STEP_MAX = 0.6, 1.4
# 밑줄 헬퍼. fx.hfBar 와 같은 모양이지만 motion.emit 흐름과 섞이지 않게 도식 IIFE 안에 따로 둔다
_BAR = ("function dBar(k,c){gsap.set(k,{position:'relative',display:'inline-block'});"
        "var u=document.createElement('i');"
        "u.style.cssText='position:absolute;left:0;right:0;bottom:-.08em;height:6px;border-radius:3px;"
        "display:block;transform-origin:left;background:'+c;k.appendChild(u);return u;}")


def render(i, b, proj, parts, js, s_, vb):
    lines = list(b["lines"])              # [(text, "hl"|"cy"|"")]
    n = len(lines)
    if not 1 <= n <= MAX_LINES:
        raise SystemExit("DOC_LINES_COUNT: %s 의 doc 줄이 %d 개 — 1~%d 줄 (3~5 권장)" % (s_, n, MAX_LINES))
    for k, (_, ac) in enumerate(lines):
        if ac not in ("", "hl", "cy"):
            raise SystemExit("DOC_LINE_ACCENT: %s 줄 %d 강조 %r — 'hl'|'cy'|'' 만" % (s_, k, ac))
    reveal = b.get("reveal", "line")
    if reveal not in ("line", "all"):
        raise SystemExit("DOC_REVEAL_UNKNOWN: %r — 'line'|'all'" % reveal)
    note = b.get("note", DEFAULT_NOTE)

    parts.append('<div class="doc" id="%s_w">' % s_)
    parts.append('<div class="bar" id="e%d"><span class="src">%s</span><span class="fname">%s</span></div>'
                 % (i, b.get("kicker", ""), b.get("fname", DEFAULT_FNAME)))
    parts.append('<h2 class="ttl" id="%s_t">%s</h2>' % (s_, b.get("title", "")))
    for k, (text, ac) in enumerate(lines):
        parts.append('<div class="ln %s" id="%s_l%d"><span class="tx">%s</span></div>' % (ac, s_, k, text))
    parts.append('<div class="notice" id="%s_n">%s</div>' % (s_, note))
    parts.append('</div>')

    js.append(_BAR)
    if reveal == "line":
        js.append("var st=Math.min(%.1f,Math.max(%.1f,(SP-1.2)/%d));" % (STEP_MAX, STEP_MIN, n))
    else:
        js.append("var st=.08;")
    js.append("tl.fromTo('#%s_w',{opacity:0,scale:.98},{opacity:1,scale:1,duration:.45,ease:'power2.out'},S);" % s_)
    js.append("tl.fromTo('#%s_t',{opacity:0,y:14},{opacity:1,y:0,duration:.45,ease:'power3.out'},S+.25);" % s_)
    for k, (_, ac) in enumerate(lines):
        t = "S+.7+st*%d" % k
        js.append("tl.fromTo('#%s_l%d',{opacity:0,y:20},{opacity:1,y:0,duration:.45,ease:'power3.out'},%s);" % (s_, k, t))
        if ac:
            js.append("(function(){var k=document.querySelector('#%s_l%d .hl,#%s_l%d .cy')"
                      "||document.querySelector('#%s_l%d .tx');var u=dBar(k,'%s');"
                      "tl.fromTo(u,{scaleX:0},{scaleX:1,duration:.4,ease:'power2.out'},%s+.3);})();"
                      % (s_, k, s_, k, s_, k, BAR_COLOR[ac], t))
    js.append("tl.fromTo('#%s_n',{opacity:0},{opacity:1,duration:.4},Math.min(S+SP-.4,S+.7+st*%d+.5));" % (s_, n - 1))
