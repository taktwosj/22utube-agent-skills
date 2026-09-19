# -*- coding: utf-8 -*-
"""기본 모션 JS 조각. 트윈 속성은 x·y·scale·rotate·opacity·filter·clip-path 만 쓴다.

letterSpacing·width·top 은 쓰지 않는다 (hyperframes-animation/adapters/gsap-transforms-and-perf.md:62).
상시 반복 모션을 만들지 않는다 (motion-doctrine No idle wobble).
"""

# 필요한 장면에만 한 번 넣는다. 어절 분리·밑줄·스윕 레이어를 만든다.
HELPERS = r"""function hfW(el){var w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT),t=[],n;
while(n=w.nextNode()){t.push(n);}
t.forEach(function(x){var ps=x.nodeValue.split(/(\s+)/),f=document.createDocumentFragment();
ps.forEach(function(p){if(!p){return;}
if(/^\s+$/.test(p)){f.appendChild(document.createTextNode(p));return;}
var s=document.createElement('span');s.className='hfw';s.textContent=p;f.appendChild(s);});
x.parentNode.replaceChild(f,x);});
var q=el.querySelectorAll('.hfw');gsap.set(q,{display:'inline-block'});return q;}
function hfBar(k,c){gsap.set(k,{position:'relative',display:'inline-block'});
var u=document.createElement('i');
u.style.cssText='position:absolute;left:0;right:0;bottom:-.12em;height:7px;border-radius:4px;display:block;transform-origin:left;background:'+c;
k.appendChild(u);return u;}
function hfSweep(h){var s=document.createElement('i');
s.style.cssText='position:absolute;inset:0;pointer-events:none;opacity:0;background:linear-gradient(105deg,#ffffff00 42%,#ffffff3d 50%,#ffffff00 58%)';
h.appendChild(s);return s;}"""

NEEDS_HELPER = {"word_slide": "hfW", "underline": "hfBar", "light_sweep": "hfSweep"}
TEXT_KINDS = ("title", "panel", "bubble")


def word_slide(i, b, out):
    """12 Per-character 한국어 판. 어절을 나눠 x 로 민다. letterSpacing 은 건드리지 않는다 (Q2)."""
    if b["type"] not in TEXT_KINDS:
        return
    out.append("(function(){var q=hfW(document.getElementById('m%d'));"
               "tl.fromTo(q,{opacity:0,x:-20},{opacity:1,x:0,duration:.46,"
               "stagger:Math.min(.08,.44/q.length),ease:'power3.out',immediateRender:false},%.4f);})();"
               % (i, b["_s"] + 0.16))


def float_in(i, b, out):
    """글자가 아래에서 부드럽게 떠오른다. 걷어내기(clip-path)는 쓰지 않는다 (사용자 지시 2026-09-16)."""
    if b["type"] not in TEXT_KINDS:
        return
    from .presets import FLOAT_SECONDS
    out.append("tl.fromTo('#m%d',{opacity:0,y:26},{opacity:1,y:0,duration:%.2f,ease:'power2.out',"
               "immediateRender:false},%.4f);" % (i, FLOAT_SECONDS, b["_s"] + 0.12))


def underline(i, b, out):
    """15 Write-on · 19 Trim Paths. 강조 어절 밑에 선을 긋는다."""
    if b["type"] not in TEXT_KINDS:
        return
    out.append("(function(){var k=document.querySelector('#m%d .hl')||document.querySelector('#m%d .v');"
               "if(!k){return;}var u=hfBar(k,'#ffd24a');"
               "tl.fromTo(u,{scaleX:0},{scaleX:1,duration:.5,ease:'power2.out',immediateRender:false},%.4f);})();"
               % (i, i, b["_s"] + 0.5))


def light_sweep(i, b, out):
    """36 Light Sweep. 한 번만 지나간다. 반복 금지."""
    out.append("(function(){var h=document.getElementById('b%d');if(!h){return;}var s=hfSweep(h);"
               "tl.set(s,{opacity:1},%.4f);"
               "tl.fromTo(s,{xPercent:-120},{xPercent:120,duration:.9,ease:'power1.inOut',immediateRender:false},%.4f);"
               "tl.set(s,{opacity:0},%.4f);})();"
               % (i, b["_s"] + 0.7, b["_s"] + 0.7, b["_s"] + 1.6))


def follow_through(i, b, out):
    """07 Follow-through. 판이 멈춘 뒤 라벨·값이 늦게 자리를 잡는다."""
    if b["type"] == "timeline":
        sel, d, st, t = "#b%d .tdate" % i, 0.5, 0.06, b["_s"] + 1.1
    elif b["type"] == "panel":
        sel, d, st, t = "#b%d .row .v" % i, 0.44, 0.08, b["_s"] + 0.5
    elif b["type"] in TEXT_KINDS:
        sel, d, st, t = "#s%d" % i, 0.42, 0, b["_s"] + 0.7
    else:
        return
    out.append("tl.fromTo('%s',{y:-8},{y:0,duration:%.2f,stagger:%.2f,ease:'back.out(1.2)',"
               "immediateRender:false},%.4f);" % (sel, d, st, t))


def anticipation(i, b, out):
    """06 Anticipation. 움직이기 전 0.15초 뒤로 뺀다."""
    if b["type"] == "move":
        out.append("tl.fromTo('#b%d_pin',{x:0},{x:-16,duration:.15,ease:'power2.in',"
                   "immediateRender:false},%.4f);" % (i, b["_s"] + 1.05))
    elif b["type"] == "flow":
        t = _flow_first_move(b)
        # 본 트윈 시작과 정확히 맞닿게 두면 %.4f 반올림으로 수십 µs 늦어져 check --strict 의
        # overlapping_gsap_tweens 에 걸린다(2026-09-17 n=3·SP=12.7). 한 프레임 앞당겨 끝낸다.
        out.append("tl.fromTo('#b%d_pk',{x:0},{x:-14,duration:.15,ease:'power2.in',"
                   "immediateRender:false},%.4f);" % (i, t - 0.15 - 1 / 30))
    elif b["type"] == "timeline":
        out.append("tl.fromTo('#b%d_mk',{x:0},{x:-14,duration:.15,ease:'power2.in',"
                   "immediateRender:false},%.4f);" % (i, b["_s"] + 0.35))


def trail(i, b, out):
    """10 Motion Trails. 이동하는 동안만 꼬리를 남긴다."""
    if b["type"] == "move":
        sel, t, d = "#b%d_pin" % i, b["_s"] + 1.2, max(1.4, b["_sp"] * 0.45)
    elif b["type"] == "flow":
        sel, t, d = "#b%d_pk" % i, _flow_first_move(b), max(0.9, (b["_sp"] - 1.4) / max(1, len(b["nodes"]))) * (len(b["nodes"]) - 1)
    else:
        return
    out.append("tl.to('%s',{filter:'drop-shadow(-14px 0 12px #ffd24a7a)',duration:.25,ease:'power1.out',"
               "immediateRender:false},%.4f);" % (sel, t))
    out.append("tl.to('%s',{filter:'drop-shadow(0 0 0 #ffd24a00)',duration:.3,ease:'power1.in'},%.4f);"
               % (sel, t + max(0.3, d)))


def depth_in(i, b, out):
    """32 2.5D 얕게 + 33 Rack Focus. 스포크가 뒤에서 초점을 잡으며 들어온다."""
    if b["type"] != "relation":
        return
    n = max(1, len(b["spokes"]))
    step = max(0.7, (b["_sp"] - 1.6) / n)
    out.append("gsap.set('#b%d',{perspective:1400});" % i)
    out.append("tl.fromTo('#b%d .rnode',{rotateY:9,filter:'blur(4px)'},{rotateY:0,filter:'blur(0px)',"
               "duration:.6,stagger:%.3f,ease:'power2.out',immediateRender:false},%.4f);"
               % (i, step, b["_s"] + 0.9))


def parallax_in(i, b, out):
    """31 Parallax. 장면에 들어올 때 배경이 한 번만 어긋난다. 상시 drift 금지."""
    out.append("tl.fromTo('.grid',{x:0,y:0},{x:-24,y:-10,duration:1.4,ease:'power1.out',"
               "immediateRender:false},%.4f);" % b["_s"])
    out.append("tl.fromTo('.ribbon',{x:0},{x:26,duration:1.4,ease:'power1.out',"
               "immediateRender:false},%.4f);" % b["_s"])


def _flow_first_move(b):
    """flow.py 가 첫 패킷을 움직이는 시각. 그 모듈 계산식과 같게 둔다."""
    n = max(1, len(b["nodes"]))
    step = max(0.9, (b["_sp"] - 1.4) / n)
    return b["_s"] + 0.4 + step + 0.35


BASE = {"word_slide": word_slide, "float_in": float_in, "underline": underline,
        "light_sweep": light_sweep, "follow_through": follow_through, "anticipation": anticipation,
        "trail": trail, "depth_in": depth_in, "parallax_in": parallax_in}
