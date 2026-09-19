# -*- coding: utf-8 -*-
"""강조 모션 JS 조각. 장면당 1개, 합계 1.0초 이하. Shake 는 챕터당 1회 (Q5).

색은 강조색 2개 규칙 안에 둔다. RGB Split 은 눈이 아파 뺐다 (사용자 지시 2026-09-16).
"""
from . import fx

def snap_zoom(i, b, out):
    """29 Snap Zoom. 0.5초. 띠 사이 #safe 를 벗어나지 않게 1.04 까지만."""
    if b["type"] == "timeline":
        k = b.get("fx_at", len(b["points"]) - 1)
        sel = "#b%d_c%d" % (i, k)
    elif b["type"] in fx.TEXT_KINDS:
        sel = "#b%d" % i
    else:
        raise SystemExit("MOTION_FX_TARGET_MISSING: snap_zoom 은 title·panel·bubble·timeline 에만 붙는다")
    t = _at(b, 0.62)
    out.append("gsap.set('%s',{transformOrigin:'50%% 50%%'});" % sel)
    out.append("tl.to('%s',{keyframes:[{scale:1.04,duration:.16,ease:'power3.out'},"
               "{scale:1,duration:.34,ease:'power2.out'}],immediateRender:false},%.4f);" % (sel, t))


def glow(i, b, out):
    """25 Glow. 강조 어절 1회 attack-decay. 상시 pulse 금지."""
    t = _at(b, 0.55)
    out.append("(function(){var k=document.querySelector('#m%d .hl')||document.querySelector('#m%d .cy');"
               "if(!k){return;}gsap.set(k,{filter:'drop-shadow(0 0 0 #ffe27600)'});"
               "tl.to(k,{keyframes:[{filter:'drop-shadow(0 0 20px #ffe276cc)',duration:.18,ease:'power2.out'},"
               "{filter:'drop-shadow(0 0 0 #ffe27600)',duration:.42,ease:'power2.in'}],"
               "immediateRender:false},%.4f);})();" % (i, i, t))


def light_sweep(i, b, out):
    """36 Light Sweep 을 강조로 쓸 때. 기본과 같은 구현, 한 번만."""
    fx.light_sweep(i, b, out)


def burst(i, b, out):
    """21 Radial Burst. 0.4초. flow 우회 곡선이 갈라지는 순간 1회."""
    if b["type"] != "flow" or not b.get("bypass"):
        raise SystemExit("MOTION_FX_TARGET_MISSING: burst 는 bypass 가 있는 flow 비트에만 붙는다")
    n = max(1, len(b["nodes"]))
    step = max(0.9, (b["_sp"] - 1.4) / n)
    t = b["_s"] + 0.4 + step * n + 0.55
    out.append("(function(){var p=document.getElementById('b%d_by'),h=document.getElementById('b%d');"
               "if(!p||!h){return;}var L=p.getTotalLength(),q=p.getPointAtLength(L*.5),ds=[];"
               "for(var k=0;k<8;k++){var d=document.createElement('i');d.className='hfb';"
               "d.style.cssText='position:absolute;width:12px;height:12px;border-radius:50%%;background:#ffd24a;"
               "opacity:0;margin:-6px 0 0 -6px;left:'+q.x+'px;top:'+q.y+'px';h.appendChild(d);ds.push(d);"
               "var a=k*Math.PI/4;"
               "tl.fromTo(d,{x:0,y:0,scale:1},{x:Math.cos(a)*92,y:Math.sin(a)*92,scale:.4,duration:.4,"
               "ease:'power2.out',immediateRender:false},%.4f);}"
               "tl.set(ds,{opacity:1},%.4f);tl.to(ds,{opacity:0,duration:.34,ease:'power1.in'},%.4f);})();"
               % (i, i, t, t, t + 0.06))


def shake(i, b, out):
    """35 Camera Shake. 세기는 presets.SHAKE. 챕터당 1회. 대립·모순 장면에만."""
    from .presets import SHAKE, SHAKE_DAMP
    sel = "#b%d" % i
    t = _at(b, 0.6)
    step = SHAKE["seconds"] / len(SHAKE_DAMP)
    keys = ",".join("{x:%.1f,y:%.1f,rotation:%.2f,duration:%.3f}"
                    % (SHAKE["x"] * r, SHAKE["y"] * r * (-1) ** k, SHAKE["rot"] * r * (-1) ** k, step)
                    for k, r in enumerate(SHAKE_DAMP))
    out.append("gsap.set('%s',{transformOrigin:'50%% 50%%'});" % sel)
    out.append("tl.to('%s',{keyframes:[%s],ease:'none',immediateRender:false},%.4f);" % (sel, keys, t))


def parallax_in(i, b, out):
    """31 Parallax 를 강조로 쓸 때. 진입 1회."""
    fx.parallax_in(i, b, out)


def _at(b, frac):
    """비트 안에서 강조가 터지는 시각. 비트가 짧아도 끝을 넘지 않는다."""
    return b["_s"] + min(b["_sp"] * frac, max(0.2, b["_sp"] - 1.0))


FX = {"snap_zoom": snap_zoom, "glow": glow, "light_sweep": light_sweep, "burst": burst,
      "shake": shake, "parallax_in": parallax_in}
