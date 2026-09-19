"""Dispatch the five scene diagram kinds."""
from .. import core
from . import timeline, flow, relation, move, doc

def _diagram(i, b, proj):
    """도식 비트 마크업과 타임라인 JS 조각을 돌려준다. 좌표계는 .dia (1728 x DIA_H)."""
    head = ('<div class="dhead" id="e%d"><p class="kicker">%s</p><h1 class="dtitle">%s</h1></div>'
            % (i, b.get("kicker", "&nbsp;"), b.get("title", "")))
    s_ = "b%d" % i
    kind = b["type"]
    # doc 은 문서 창 안에 제 상단 바(id e<i>)를 두므로 공용 dhead 를 넣지 않는다
    parts, js = ([] if kind == "doc" else [head]), []
    js.append("tl.fromTo('#e%d',{opacity:0,y:-16},{opacity:1,y:0,duration:.5,ease:'power3.out'},S);" % i)
    vb = "0 0 1728 %d" % core.DIA_H

    handler = {"timeline": timeline, "flow": flow, "relation": relation, "move": move, "doc": doc}.get(kind)
    if handler is not None:
        handler.render(i, b, proj, parts, js, s_, vb)
    js.append("tl.to('#%s',{scale:1.02,duration:SP,ease:'sine.inOut'},S);" % s_)
    markup = '<div class="dia" id="%s">%s</div>' % (s_, "".join(parts))
    return markup, core.NL.join(js)
