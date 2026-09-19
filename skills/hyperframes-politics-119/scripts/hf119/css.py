"""Scene CSS; geometry follows the configured 119 strip."""
from . import core

CSS = """@font-face{font-family:EditorialKR;src:url('assets/PretendardVariable.woff2') format('woff2');font-weight:100 900;font-display:block}
*{box-sizing:border-box}
html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#06172f}
body{font-family:EditorialKR,sans-serif;color:#f1f7ff}
#scene{position:relative;width:1920px;height:1080px;overflow:hidden}
.background{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 16%,#164577 0%,#0b2947 46%,#06172f 88%)}
.grid{position:absolute;inset:0;background-image:linear-gradient(#5486af12 1px,transparent 1px),linear-gradient(90deg,#5486af12 1px,transparent 1px);background-size:80px 80px}
.ribbon{position:absolute;width:1500px;height:360px;left:-300px;top:250px;transform:rotate(-12deg);background:linear-gradient(90deg,#63e2ef00,#63e2ef12 38%,#63e2ef00);border-top:1px solid #63e2ef2b;border-bottom:1px solid #63e2ef2b}
#safe{position:absolute;left:0;top:__STRIP_TOP__px;width:1920px;height:__STRIP_H__px}
.brand{position:absolute;left:96px;top:22px;padding:8px 22px;border-left:5px solid #63e2ef;background:#0d2c4c;font-size:31px;font-weight:750}
.chapter{position:absolute;right:96px;top:24px;font-size:34px;font-weight:700;color:#a9c9e6;letter-spacing:.04em}
.source{position:absolute;left:96px;bottom:10px;padding:5px 16px;background:#091f38;font-size:31px;font-weight:700;color:#cfe2f5;z-index:6}
.frame{position:absolute;bottom:70px;width:380px;height:470px;border-radius:18px;overflow:hidden;border:3px solid #8ef0ee;box-shadow:0 18px 46px #0009,inset 0 0 0 1px #ffffff33;background:#0b2947}
.frame img{width:100%;height:100%;object-fit:cover;object-position:50% 18%;display:block}
.frame.L{left:96px}.frame.R{right:96px;border-color:#ffe276}
.nameplate{position:absolute;bottom:14px;padding:7px 20px;background:#0d2c4c;font-size:38px;font-weight:800;z-index:5}
.nameplate.L{left:96px;border-left:5px solid}.nameplate.R{right:96px;border-right:5px solid;text-align:right}
.cyC{color:#8ef0ee;border-color:#8ef0ee}.ylC{color:#ffe276;border-color:#ffe276}
.stage{position:absolute;left:0;right:0;top:120px;height:420px;text-align:center}
.withL .stage{left:520px;right:60px}.withR .stage{left:60px;right:520px}
.eyebrow{font-size:34px;font-weight:750;color:#8ef0ee;letter-spacing:.04em;margin:0 0 22px}
.mega{font-size:124px;font-weight:900;letter-spacing:-.05em;line-height:1.08;text-shadow:0 6px 0 #041427,0 18px 40px #0008;margin:0}
.withL .mega,.withR .mega{font-size:104px}
.mega .hl{color:#ffe276}.mega .cy{color:#8ef0ee}
.rule{width:520px;height:4px;margin:28px auto 0;background:linear-gradient(90deg,#63e2ef00,#63e2ef,#63e2ef00);transform-origin:center}
.sub{font-size:48px;font-weight:700;color:#d7e8f9;letter-spacing:-.02em;margin:24px 0 0}
.bubble{position:absolute;top:120px;left:560px;width:820px;padding:34px 40px 38px;background:linear-gradient(180deg,#123a63,#0b2947);border:1px solid #3b6e9e;box-shadow:0 18px 46px #0009}
.bubble .who{display:inline-block;margin:0 0 18px;padding:6px 18px;font-size:34px;font-weight:800;background:#0d2c4c;border-left:5px solid}
.bubble .q{margin:0;font-size:72px;font-weight:900;letter-spacing:-.045em;line-height:1.16;color:#f4faff;text-shadow:0 4px 0 #04142a}
.bubble .q .hl{color:#ffe276}.bubble .q .cy{color:#8ef0ee}
.bubble .note{margin:24px 0 0;font-size:46px;font-weight:750;color:#dceaf8}
.panel{position:absolute;left:300px;right:300px;top:130px;padding:36px 44px;background:linear-gradient(180deg,#123a63,#0b2947);border:1px solid #3b6e9e;box-shadow:0 18px 46px #0009}
.panel .row{display:flex;align-items:baseline;justify-content:space-between;padding:16px 0;border-bottom:1px solid #2d5b86}
.panel .row:last-child{border-bottom:0}
.panel .k{font-size:44px;font-weight:750;color:#cfe2f5}
.panel .v{font-size:66px;font-weight:900;letter-spacing:-.03em;color:#ffe276}.panel .v.cy{color:#8ef0ee}
.dia{position:absolute;left:96px;right:96px;top:84px;height:__DIA_H__px}
.dhead{position:absolute;left:0;top:0}
.kicker{display:inline-block;padding:8px 20px;background:#1764b5;color:#fff;font-weight:750;font-size:31px;margin:0 0 16px;border-left:5px solid #8eddeb}
.dtitle{font-size:84px;font-weight:880;letter-spacing:-.045em;line-height:1.1;margin:0;text-shadow:0 4px 0 #03152d,0 12px 30px #0005}
.dtitle .hl{color:#ffe276}.dtitle .cy{color:#8ef0ee}
.dsvg{position:absolute;left:0;top:0;width:1728px;height:__DIA_H__px;overflow:visible;pointer-events:none}
.conn{fill:none;stroke-linecap:round;stroke-linejoin:round}
.rail{position:absolute;height:5px;background:#7fb0dd;transform-origin:left;border-radius:3px}
.tnode{position:absolute;width:30px;height:30px;border-radius:50%;background:#8ef0ee;box-shadow:0 0 0 8px #8ef0ee33;margin:-12px 0 0 -15px}
.tnode.yl{background:#ffd24a;box-shadow:0 0 0 8px #ffd24a33}
.tdate{position:absolute;font-size:36px;font-weight:700;color:#b9cee6;white-space:nowrap}
.tchip{position:absolute;border-radius:6px;border:2px solid #547b9e;background:#061c38;padding:12px 22px;font-size:36px;font-weight:800;color:#fff;white-space:nowrap}
.tchip.yl{border-color:#ffeeaa;background:linear-gradient(115deg,#ffe596,#ffd24a);color:#17293f}
.tchip.cy{border-color:#8ef0ee}
.marker{position:absolute;width:22px;height:22px;border-radius:50%;background:#fff;box-shadow:0 0 18px 6px #8ef0ee88;margin:-9px 0 0 -11px}
.fcard{position:absolute;width:300px;height:250px;border:2px solid #648ab5;border-radius:10px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;box-shadow:0 12px 0 #031126,0 26px 32px #0006,inset 0 2px 0 #ffffff66}
.fcard .badge{width:118px;height:118px;border-radius:22px;padding:16px;background:linear-gradient(145deg,#ffffffce,#ffffff24);border:1px solid #ffffffbb;color:#133c65}
.fcard .badge .ico{width:100%;height:100%;display:block}
.fcard b{font-size:48px;font-weight:850;letter-spacing:-.03em}
.fcard small{font-size:31px;font-weight:700;opacity:.85;margin-top:-10px}
.cobalt{background:linear-gradient(125deg,#2279cd,#144d8d 62%,#103866);border-color:#82beef;color:#f7fbff}
.pale{background:linear-gradient(125deg,#f0f7ff,#b9d4ee);color:#102c50;border-color:#eaf5ff}
.teal{background:linear-gradient(125deg,#c4f0f5,#70bccf);color:#123b4f;border-color:#bff2f4}
.slate{background:linear-gradient(125deg,#2b4a72,#1b3556);border-color:#5d81ab;color:#e8f2ff}
.amber{background:linear-gradient(125deg,#ffe596,#ffc321);border-color:#ffeeaa;color:#17293f}
.packet{position:absolute;width:26px;height:26px;border-radius:50%;background:#ffd24a;box-shadow:0 0 16px 5px #ffd24a88;margin:-13px 0 0 -13px}
.hub{position:absolute;width:260px;height:260px;border-radius:50%;overflow:hidden;border:5px solid #ffe276;box-shadow:0 0 0 14px #ffe27622,0 20px 40px #0009;background:#0b2947}
.hub img{width:100%;height:100%;object-fit:cover;object-position:50% 20%}
.hubname{position:absolute;font-size:40px;font-weight:850;white-space:nowrap}
.rnode{position:absolute;min-width:250px;padding:18px 26px;border-radius:10px;border:2px solid #82beef;background:linear-gradient(125deg,#2279cd,#144d8d);text-align:center;box-shadow:0 10px 0 #031126,0 20px 28px #0006}
.rnode b{display:block;font-size:44px;font-weight:850;color:#fff}
.rnode small{display:block;font-size:31px;font-weight:700;color:#cfe8ff;margin-top:4px}
.place{position:absolute;padding:18px 30px;border-radius:10px;border:2px solid #82beef;background:#0d2c4c;font-size:52px;font-weight:880;white-space:nowrap}
.place.to{border-color:#ffeeaa;color:#ffe276}
.place small{display:block;font-size:28px;font-weight:700;color:#b9cee6;text-align:center}
.pin{position:absolute;width:76px;height:76px;color:#ffe276;margin:-70px 0 0 -38px;filter:drop-shadow(0 8px 10px #0009)}
.pin .ico{width:100%;height:100%}
.movenote{position:absolute;font-size:40px;font-weight:800;color:#dceaf8;white-space:nowrap}
.progress{position:absolute;left:96px;bottom:56px;width:1728px;height:3px;background:#5486af44;z-index:6}
.progress i{display:block;height:3px;background:linear-gradient(90deg,#63e2ef,#8ef0ee);transform-origin:left}"""

# doc 도식 전용. doc 비트가 있는 장면에만 붙여 다른 장면의 index.html 은 한 바이트도 바뀌지 않는다.
DOC_CSS = """.doc{position:absolute;left:0;top:0;width:1728px;bottom:30px;padding:0 44px 16px;border-radius:12px;overflow:hidden;background:linear-gradient(180deg,#0f3358,#0a2643);border:1px solid #3b6e9e;box-shadow:0 18px 46px #0009;transform-origin:50% 50%}
.doc .bar{display:flex;align-items:center;justify-content:space-between;height:52px;margin:0 -44px 18px;padding:0 30px;background:#0d2c4c;border-bottom:1px solid #3b6e9e;font-size:28px;font-weight:750}
.doc .src{color:#8ef0ee;letter-spacing:.02em}
.doc .fname{padding:2px 12px;border:1px solid #3b6e9e;border-radius:6px;font-size:24px;font-weight:700;color:#a9c9e6}
.doc .ttl{font-size:64px;font-weight:880;letter-spacing:-.04em;line-height:1.12;margin:0 0 16px;text-shadow:0 4px 0 #03152d,0 12px 30px #0005}
.doc .ttl .hl{color:#ffe276}.doc .ttl .cy{color:#8ef0ee}
.doc .ln{position:relative;margin:0 0 10px;padding:0 0 0 40px;font-size:44px;font-weight:700;line-height:1.25;color:#d7e8f9;letter-spacing:-.02em}
.doc .ln::before{content:'–';position:absolute;left:4px;top:0;color:#7fa3c7}
.doc .ln.hl{color:#ffe276}.doc .ln.cy{color:#8ef0ee}.doc .ln .hl{color:#ffe276}.doc .ln .cy{color:#8ef0ee}
.doc .notice{position:absolute;right:30px;bottom:12px;padding:3px 14px;border-radius:6px;border:1px solid #3b6e9e;background:#122f4d;font-size:24px;font-weight:700;color:#8fa9c4}"""


def render(doc=False):
    css = CSS + ("\n" + DOC_CSS if doc else "")
    return css.replace("__STRIP_TOP__", str(core.STRIP_TOP)).replace("__STRIP_H__", str(core.STRIP_H)).replace("__DIA_H__", str(core.DIA_H))
