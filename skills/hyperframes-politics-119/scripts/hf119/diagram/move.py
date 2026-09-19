"""move diagram markup and animation."""
import math
import shutil
from .. import core
from ..icons import svg_icon


def render(i, b, proj, parts, js, s_, vb):
    (fa, fs), (ta, ts) = b["from"], b["to"]
    ax, bx, y = 360, 1368, 430
    parts.append('<svg class="dsvg" viewBox="%s"><path id="%s_arc" class="conn" d="M%d %d C%d %d %d %d %d %d" '
                 'stroke="#ffd24a" stroke-width="6" stroke-dasharray="14 14" pathLength="1"/></svg>'
                 % (vb, s_, ax, y - 60, ax + 250, y - 260, bx - 250, y - 260, bx, y - 60))
    parts.append('<div class="place" id="%s_pa" style="left:%dpx;top:%dpx">%s<small>%s</small></div>' % (s_, ax, y, fa, fs))
    parts.append('<div class="place to" id="%s_pb" style="left:%dpx;top:%dpx">%s<small>%s</small></div>' % (s_, bx, y, ta, ts))
    parts.append('<div class="pin" id="%s_pin" style="left:%dpx;top:%dpx">%s</div>' % (s_, ax, y - 60, svg_icon("pin")))
    if b.get("note"):
        # 진행선(띠 바닥 위 56px)과 겹치지 않게 칩 아래 95px 에 둔다
        parts.append('<div class="movenote" id="%s_note" style="left:864px;top:%dpx">%s</div>' % (s_, y + 95, b["note"]))
    js.append("gsap.set('#%s_pb,#%s_pin',{opacity:0});gsap.set('#%s_pa,#%s_pb',{xPercent:-50,yPercent:-50});" % (s_, s_, s_, s_))
    js.append("gsap.set('#%s_arc',{strokeDashoffset:1,opacity:0});tl.set('#%s_arc',{opacity:1},S+1.2);" % (s_, s_))
    js.append("tl.fromTo('#%s_pa',{opacity:0,y:20},{opacity:1,y:0,duration:.5,ease:'power3.out'},S+.3);" % s_)
    js.append("tl.to('#%s_pin',{opacity:1,duration:.25},S+.8);" % s_)
    js.append("tl.fromTo('#%s_pb',{opacity:0,y:20},{opacity:1,y:0,duration:.5,ease:'power3.out'},S+.9);" % s_)
    js.append("(function(){const p=document.getElementById('%s_arc');const L=p.getTotalLength();"
              "const o={t:0};tl.to(o,{t:1,duration:Math.max(1.4,SP*.45),ease:'power1.inOut',"
              "onUpdate:function(){const q=p.getPointAtLength(L*o.t);gsap.set('#%s_pin',{x:q.x-%d,y:q.y-%d});}},S+1.2);"
              "tl.to('#%s_arc',{strokeDashoffset:0,duration:Math.max(1.4,SP*.45),ease:'power1.inOut'},S+1.2);})();"
              % (s_, s_, ax, y - 60, s_))
    if b.get("note"):
        js.append("gsap.set('#%s_note',{opacity:0,xPercent:-50});tl.to('#%s_note',{opacity:1,duration:.5},S+1.2+Math.max(1.4,SP*.45));" % (s_, s_))
