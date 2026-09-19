"""timeline diagram markup and animation."""
import math
import shutil
from .. import core
from ..icons import svg_icon


def render(i, b, proj, parts, js, s_, vb):
    pts = b["points"]                     # [(date, chip, accent)]
    x0, x1, y = 60, 1668, 350
    parts.append('<div class="rail" id="%s_rail" style="left:%dpx;top:%dpx;width:%dpx"></div>' % (s_, x0, y, x1 - x0))
    n = len(pts)
    xs = [x0 + 120 + (x1 - x0 - 240) * k / max(1, n - 1) for k in range(n)]
    for k, (date, chip, ac) in enumerate(pts):
        parts.append('<div class="tnode %s" id="%s_n%d" style="left:%dpx;top:%dpx"></div>' % (ac, s_, k, xs[k], y))
        parts.append('<div class="tdate" id="%s_d%d" style="left:%dpx;top:%dpx">%s</div>' % (s_, k, xs[k], y + 40, date))
        parts.append('<div class="tchip %s" id="%s_c%d" style="left:%dpx;top:%dpx">%s</div>'
                     % (ac, s_, k, xs[k], y - 120 - (46 if k % 2 else 0), chip))
    parts.append('<div class="marker" id="%s_mk" style="left:%dpx;top:%dpx"></div>' % (s_, xs[0], y))
    js.append("tl.fromTo('#%s_rail',{scaleX:0},{scaleX:1,duration:Math.min(2.2,SP*.35),ease:'power2.inOut'},S+.3);" % s_)
    js.append("gsap.set('#%s .tnode,#%s .tdate,#%s .tchip',{opacity:0});gsap.set('#%s .tdate,#%s .tchip',{xPercent:-50});" % (s_, s_, s_, s_, s_))
    js.append("gsap.set('#%s_mk',{opacity:0});" % s_)
    js.append("tl.to('#%s_mk',{opacity:1,duration:.2},S+.5);" % s_)
    for k in range(n):
        t = "S+.6+(SP-1.6)*%.4f" % (k / max(1, n - 1) if n > 1 else 0)
        js.append("tl.to('#%s_mk',{x:%d,duration:.7,ease:'power2.inOut'},Math.max(S+.5,%s-.7));" % (s_, xs[k] - xs[0], t))
        js.append("tl.fromTo('#%s_n%d',{opacity:0,scale:.2},{opacity:1,scale:1,duration:.35,ease:'back.out(2)'},%s);" % (s_, k, t))
        js.append("tl.set('#%s_d%d',{opacity:1},%s);" % (s_, k, t))
        js.append("tl.set('#%s_c%d',{opacity:1},%s+.15);" % (s_, k, t))
        js.append("tl.fromTo('#%s_c%d',{scale:.6,y:14},{scale:1,y:0,duration:.45,ease:'back.out(1.6)',immediateRender:false},%s+.15);" % (s_, k, t))
