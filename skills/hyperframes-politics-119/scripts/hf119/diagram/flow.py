"""flow diagram markup and animation."""
import math
import shutil
from .. import core
from ..icons import svg_icon


def render(i, b, proj, parts, js, s_, vb):
    nodes = b["nodes"]                    # [(icon, label, small, colorclass)]
    n = len(nodes)
    w, h, y = 300, 250, 300
    gap = (1728 - n * w) / (n + 1)
    xs = [gap + k * (w + gap) for k in range(n)]
    svg = ['<svg class="dsvg" viewBox="%s">' % vb]
    for k in range(n - 1):
        ax, bx = xs[k] + w, xs[k + 1]
        svg.append('<path id="%s_l%d" class="conn" d="M%d %d L%d %d" stroke="#7fb0dd" stroke-width="6" pathLength="1"/>'
                   % (s_, k, ax, y + h / 2, bx, y + h / 2))
    if b.get("bypass"):
        a, c = b["bypass"]
        ax, cx = xs[a] + w / 2, xs[c] + w / 2
        svg.append('<path id="%s_by" class="conn" d="M%d %d C%d %d %d %d %d %d" stroke="#ffd24a" stroke-width="7" pathLength="1"/>'
                   % (s_, ax, y, ax, y - 150, cx, y - 150, cx, y))
    svg.append('</svg>')
    parts.append("".join(svg))
    for k, (ic, label, small, color) in enumerate(nodes):
        parts.append('<div class="fcard %s" id="%s_f%d" style="left:%dpx;top:%dpx"><div class="badge">%s</div><b>%s</b>%s</div>'
                     % (color, s_, k, xs[k], y, svg_icon(ic), label, ("<small>%s</small>" % small) if small else ""))
    parts.append('<div class="packet" id="%s_pk" style="left:%dpx;top:%dpx"></div>' % (s_, xs[0] + w, y + h / 2))
    js.append("gsap.set('#%s .fcard',{opacity:0});gsap.set('#%s_pk',{opacity:0});" % (s_, s_))
    js.append("gsap.set('#%s .conn',{strokeDasharray:1,strokeDashoffset:1});" % s_)
    step = "Math.max(.9,(SP-1.4)/%d)" % max(1, n)
    js.append("gsap.set('#%s .conn',{opacity:0});" % s_)
    for k in range(n):
        t = "S+.4+%s*%d" % (step, k)
        js.append("tl.fromTo('#%s_f%d',{opacity:0,y:30,scale:.94},{opacity:1,y:0,scale:1,duration:.5,ease:'back.out(1.4)'},%s);" % (s_, k, t))
        if k > 0:
            js.append("tl.set('#%s_l%d',{opacity:1},%s+.35);" % (s_, k - 1, t))
            js.append("tl.to('#%s_l%d',{strokeDashoffset:0,duration:.55,ease:'power2.out'},%s+.35);" % (s_, k - 1, t))
            js.append("tl.fromTo('#%s_pk',{opacity:1,x:%d},{opacity:1,x:%d,duration:.55,ease:'power1.inOut',immediateRender:false},%s+.35);"
                      % (s_, xs[k - 1] + w - (xs[0] + w), xs[k] - (xs[0] + w), t))
    js.append("tl.to('#%s_pk',{opacity:0,duration:.2},S+.4+%s*%d);" % (s_, step, n))
    if b.get("bypass"):
        a, c = b["bypass"]
        js.append("tl.to('#%s_f%d',{opacity:.35,filter:'grayscale(.8)',duration:.5},S+.4+%s*%d);"
                  % (s_, (a + c) // 2, step, n))
        js.append("tl.set('#%s_by',{opacity:1},S+.4+%s*%d);" % (s_, step, n))
        js.append("tl.to('#%s_by',{strokeDashoffset:0,duration:1.1,ease:'power2.inOut'},S+.4+%s*%d);" % (s_, step, n))
