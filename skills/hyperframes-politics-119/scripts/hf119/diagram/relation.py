"""relation diagram markup and animation."""
import math
import shutil
from .. import core
from ..icons import svg_icon


def render(i, b, proj, parts, js, s_, vb):
    hub = b["hub"]                        # (person, name)
    spokes = b["spokes"]                  # [(label, small)]
    cx, cy = 864, 360
    img = core._photo_src(hub[0])
    shutil.copy(img, proj / "assets" / ("hub_%d%s" % (i, img.suffix)))
    n = len(spokes)
    rx, ry = 620, 140
    # 허브 둘레 반타원(왼쪽 아래 → 위 → 오른쪽 아래)에 고르게 놓는다
    angs = [math.radians(200 - 220 * k / max(1, n - 1)) for k in range(n)] if n > 1 else [math.radians(90)]
    pts = [(cx + rx * math.cos(a), cy - ry * math.sin(a)) for a in angs]
    svg = ['<svg class="dsvg" viewBox="%s">' % vb]
    for k, (x, y) in enumerate(pts):
        svg.append('<path id="%s_s%d" class="conn" d="M%d %d L%d %d" stroke="#8ef0ee" stroke-width="5" pathLength="1"/>'
                   % (s_, k, cx, cy, x, y))
    svg.append('</svg>')
    parts.append("".join(svg))
    parts.append('<div class="hub" id="%s_h" style="left:%dpx;top:%dpx"><img src="assets/hub_%d%s" alt=""></div>'
                 % (s_, cx - 130, cy - 130, i, img.suffix))
    parts.append('<div class="hubname ylC" id="%s_hn" style="left:%dpx;top:%dpx">%s</div>' % (s_, cx, cy + 140, hub[1]))
    for k, ((x, y), (label, small)) in enumerate(zip(pts, spokes)):
        parts.append('<div class="rnode" id="%s_r%d" style="left:%dpx;top:%dpx"><b>%s</b><small>%s</small></div>'
                     % (s_, k, x, y, label, small))
    js.append("gsap.set('#%s .rnode',{opacity:0});gsap.set('#%s .conn',{strokeDasharray:1,strokeDashoffset:1,opacity:0});gsap.set('#%s .rnode',{xPercent:-50,yPercent:-50});" % (s_, s_, s_))
    js.append("tl.fromTo('#%s_h',{opacity:0,scale:.6},{opacity:1,scale:1,duration:.6,ease:'back.out(1.6)'},S+.3);" % s_)
    js.append("gsap.set('#%s_hn',{xPercent:-50,opacity:0});tl.set('#%s_hn',{opacity:1},S+.7);" % (s_, s_))
    step = "Math.max(.7,(SP-1.6)/%d)" % max(1, n)
    for k in range(n):
        t = "S+.9+%s*%d" % (step, k)
        js.append("tl.set('#%s_r%d',{opacity:1},%s);" % (s_, k, t))
        js.append("tl.fromTo('#%s_r%d',{scale:.7},{scale:1,duration:.45,ease:'back.out(1.6)',immediateRender:false},%s);" % (s_, k, t))
        js.append("tl.set('#%s_s%d',{opacity:1},%s+.3);" % (s_, k, t))
        js.append("tl.to('#%s_s%d',{strokeDashoffset:0,duration:.5,ease:'power2.out'},%s+.3);" % (s_, k, t))
