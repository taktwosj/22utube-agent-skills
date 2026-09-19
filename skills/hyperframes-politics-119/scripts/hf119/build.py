"""Build one scene project without changing generated HTML."""
import json
import shutil
from . import core, css, motion
from .beats import span, first_nl, last_nl
from .diagram import _diagram

def build(spec):
    if core.HF is None:
        raise SystemExit("HF_LIB_NOT_INITIALIZED: hf_lib.init(root) 를 먼저 부른다")
    name = spec["file"]
    proj = core.HF / name
    if proj.exists():
        shutil.rmtree(proj)
    (proj / "assets").mkdir(parents=True)
    for f in ("gsap.min.js", "PretendardVariable.woff2"):
        shutil.copy(core.ASSETS / f, proj / "assets" / f)
    (proj / "hyperframes.json").write_text(json.dumps(
        {"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
         "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}},
        indent=2), encoding="utf-8")

    body, extra_js = [], []
    photo = spec.get("photo")                 # (person, name, side)
    scene_cls = ""
    if photo:
        img = core._photo_src(photo[0])
        shutil.copy(img, proj / "assets" / ("photo" + img.suffix))
        side = photo[2]
        scene_cls = "with" + side
        cls = "cyC" if side == "L" else "ylC"
        body.append('<div class="frame %s" id="ph" data-layout-ignore><img src="assets/photo%s" alt=""></div>' % (side, img.suffix))
        body.append('<div class="nameplate %s %s" id="phn">%s</div>' % (side, cls, photo[1]))

    t = 0.0
    for b in spec["beats"]:
        b["_s"] = t
        b["_sp"] = span(b["nl"])
        t += b["_sp"]
    total = round(t, 4)

    for i, b in enumerate(spec["beats"], 1):
        if b["type"] in core.DIAGRAM_KINDS:
            mk, js = _diagram(i, b, proj)
            body.append(mk)
            extra_js.append("(function(){const S=%.4f,SP=%.4f;%s%s})();" % (b["_s"], b["_sp"], core.NL, js))
        elif b["type"] == "bubble":
            body.append('<div class="bubble" id="b%d"><p class="who %s" id="e%d">%s</p><p class="q" id="m%d">%s</p>'
                        '<p class="note" id="s%d">%s</p></div>'
                        % (i, "ylC" if b.get("accent") == "yl" else "cyC", i, b["who"], i, b["q"], i, b.get("note", "")))
        elif b["type"] == "panel":
            rows = "".join('<div class="row"><span class="k">%s</span><span class="v %s">%s</span></div>'
                           % (k, c, v) for k, v, c in b["rows"])
            body.append('<div class="panel" id="b%d"><p class="who cyC" id="e%d" style="display:inline-block;margin:0 0 22px;'
                        'padding:6px 18px;font-size:28px;font-weight:800;background:#0d2c4c;border-left:5px solid">%s</p>'
                        '<div id="m%d">%s</div><div id="s%d"></div></div>' % (i, i, b.get("who", "&nbsp;"), i, rows, i))
        else:
            body.append('<div class="stage" id="b%d"><p class="eyebrow" id="e%d">%s</p><h1 class="mega" id="m%d">%s</h1>'
                        '<div class="rule" id="r%d"></div><p class="sub" id="s%d">%s</p></div>'
                        % (i, i, b.get("eyebrow", "&nbsp;"), i, b["mega"], i, i, b.get("sub", "")))

    mjs = motion.emit(spec)
    if mjs:
        extra_js.append(mjs)

    js_beats = ("," + core.NL + "  ").join(
        "{id:'%d', s:%.4f, sp:%.4f, kind:'%s'}" % (i, b["_s"], b["_sp"],
                                                   "diagram" if b["type"] in core.DIAGRAM_KINDS else b["type"])
        for i, b in enumerate(spec["beats"], 1))
    photo_js = ("tl.fromTo('#ph',{opacity:0,x:%d},{opacity:1,x:0,duration:.8,ease:'power3.out'},0);"
                "tl.fromTo('#phn',{opacity:0},{opacity:1,duration:.4},.6);"
                "tl.to('#ph img',{scale:1.06,duration:%s,ease:'none'},0);" % (-60 if photo[2] == "L" else 60, total)) if photo else ""
    src_div = ('<div class="source">%s</div>' % spec["source"]) if spec.get("source") else ""

    html = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=1920,height=1080">
<title>%s</title>
<script src="assets/gsap.min.js"></script>
<style>%s</style></head><body>
<div id="scene" class="%s" data-composition-id="%s" data-start="0" data-duration="%s" data-width="1920" data-height="1080">
<div class="background" data-layout-ignore></div><div class="grid" data-layout-ignore></div><div class="ribbon" data-layout-ignore></div>
<div id="safe">
<div class="brand">__BRAND__</div>
<div class="chapter">%s</div>
%s
%s
<div class="progress" data-layout-ignore><i id="bar"></i></div>
</div>
</div>
<script>
const tl = gsap.timeline({paused:true});
const B = [
  %s
];
gsap.set(B.map(function(b){return '#b'+b.id;}).join(','), {opacity:0});
gsap.set('#bar', {scaleX:0});
tl.to('#bar', {scaleX:1, duration:%s, ease:'none'}, 0);
%s
%s
B.forEach(function(b){
  const s=b.s, e=b.s+b.sp, st='#b'+b.id;
  tl.set(st, {opacity:1}, s);
  if (b.kind === 'title') {
    tl.fromTo('#e'+b.id, {opacity:0,y:-18}, {opacity:1,y:0,duration:.42,ease:'power3.out'}, s);
    tl.fromTo('#m'+b.id, {opacity:0,y:62,scale:1.05}, {opacity:1,y:0,scale:1,duration:.72,ease:'power4.out'}, s+.10);
    tl.fromTo('#r'+b.id, {scaleX:0}, {scaleX:1,duration:.58,ease:'power3.inOut'}, s+.32);
    tl.fromTo('#s'+b.id, {opacity:0,y:24}, {opacity:1,y:0,duration:.52,ease:'power3.out'}, s+.44);
    tl.to('#m'+b.id, {y:-12, duration:Math.max(.2,b.sp-.9), ease:'none'}, s+.82);
  } else if (b.kind === 'panel') {
    tl.fromTo(st, {opacity:0,y:34}, {opacity:1,y:0,duration:.5,ease:'power3.out'}, s);
    tl.fromTo('#e'+b.id, {opacity:0,x:-14}, {opacity:1,x:0,duration:.38,ease:'power2.out'}, s+.14);
    tl.fromTo('#m'+b.id+' .row', {opacity:0,x:-26}, {opacity:1,x:0,duration:.42,stagger:.12,ease:'power2.out'}, s+.26);
  } else if (b.kind === 'bubble') {
    tl.fromTo(st, {opacity:0,x:-46,scale:.96}, {opacity:1,x:0,scale:1,duration:.5,ease:'power3.out'}, s);
    tl.fromTo('#e'+b.id, {opacity:0,x:-14}, {opacity:1,x:0,duration:.38,ease:'power2.out'}, s+.16);
    tl.fromTo('#m'+b.id, {opacity:0,y:26}, {opacity:1,y:0,duration:.52,ease:'power3.out'}, s+.24);
    tl.fromTo('#s'+b.id, {opacity:0,y:16}, {opacity:1,y:0,duration:.44,ease:'power2.out'}, s+.46);
  }
  tl.set(st, {opacity:0}, e);
});
window.__timelines = {'%s': tl};
</script></body></html>""" % (
        spec.get("title", name), css.render(doc=any(x["type"] == "doc" for x in spec["beats"])), scene_cls, name.lower(), total, spec["chapter"], src_div,
        core.NL.join(body), js_beats, total, photo_js, core.NL.join(extra_js), name.lower())

    html = html.replace("__BRAND__", core.BRAND, 1)
    if mjs:
        html = motion.quiet(html)
    (proj / "index.html").write_text(html, encoding="utf-8")
    return proj, total
