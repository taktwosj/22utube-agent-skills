# -*- coding: utf-8 -*-
"""장면 유형 프리셋을 타임라인 JS 로 바꾼다.

`spec["motion"]` 이 없으면 아무것도 넣지 않는다 — 기존 회차 출력은 한 바이트도 바뀌지 않는다.
쓰는 법: spec 에 `"motion": "evidence"`, 강조를 줄 비트에 `"fx": "snap_zoom"`.
"""
from .. import core
from . import accent, fx
from .presets import FX_CHAPTER_ONCE, FX_SECONDS, PRESETS, SCENE_FX_BUDGET

_USED = {}


def emit(spec):
    kind = spec.get("motion")
    if not kind:
        return ""
    if kind not in PRESETS:
        raise SystemExit("MOTION_PRESET_UNKNOWN: %s — %s 중 하나" % (kind, ", ".join(sorted(PRESETS))))
    preset = PRESETS[kind]
    beats = spec["beats"]
    picked = [(i, b) for i, b in enumerate(beats, 1) if b.get("fx")]
    _check(spec, kind, preset, picked)

    lines, need = [], []
    for name in preset["base"]:
        for i, b in enumerate(beats, 1):
            fx.BASE[name](i, b, lines)
        if fx.NEEDS_HELPER.get(name):
            need.append(name)
    for i, b in picked:
        if fx.NEEDS_HELPER.get(b["fx"]):
            need.append(b["fx"])
        accent.FX[b["fx"]](i, b, lines)
    if not lines:
        return ""
    if need:
        lines.insert(0, fx.HELPERS)
    return core.NL.join(lines)


def _check(spec, kind, preset, picked):
    """장면당 강조 1개·합계 1.0초·챕터당 Shake 1회 (사용자 지시 2026-09-16)."""
    if len(picked) > 1:
        raise SystemExit("MOTION_ACCENT_TOO_MANY: %s 에 강조가 %d 개 — 장면당 1개"
                         % (spec["file"], len(picked)))
    total = 0.0
    for _, b in picked:
        name = b["fx"]
        if name not in FX_SECONDS:
            raise SystemExit("MOTION_FX_UNKNOWN: %s" % name)
        if name not in preset["fx"]:
            raise SystemExit("MOTION_FX_NOT_ALLOWED: %s 유형에서 %s 금지 — 허용 %s"
                             % (kind, name, ", ".join(preset["fx"]) or "없음"))
        total += FX_SECONDS[name]
        if name in FX_CHAPTER_ONCE:
            _chapter_once(spec, name)
    if total > SCENE_FX_BUDGET + 1e-9:
        raise SystemExit("MOTION_ACCENT_BUDGET: %s 강조 합계 %.2f초 > %.2f초"
                         % (spec["file"], total, SCENE_FX_BUDGET))


def _chapter_once(spec, name):
    """같은 실행 안에서만 센다. 장면 하나만 다시 만들 때는 세지 못한다 (limits.md 에 적어 둔다)."""
    key = (str(core.ROOT), spec.get("chapter", ""), name)
    prev = _USED.get(key)
    if prev is not None and prev != spec["file"]:
        raise SystemExit("MOTION_CHAPTER_LIMIT: 챕터 '%s' 에서 %s 를 %s 가 이미 썼다 — 챕터당 1회"
                         % (spec.get("chapter", ""), name, prev))
    _USED[key] = spec["file"]

# 모션 프리셋이 글자를 맡는 장면에서는 build.py 의 기본 제목·말풍선 진입을 조용하게 바꾼다.
# 덩어리가 scale·y 로 움직이는 동안 어절이 x 로 미끄러지면 흔들려 보인다 (사용자 지적 2026-09-16).
_LOUD_TITLE = (
    "tl.fromTo('#m'+b.id, {opacity:0,y:62,scale:1.05}, "
    "{opacity:1,y:0,scale:1,duration:.72,ease:'power4.out'}, s+.10);")
_QUIET_TITLE = "tl.fromTo('#m'+b.id, {opacity:0}, {opacity:1,duration:.34,ease:'power2.out'}, s+.08);"
_DRIFT = (chr(10) + "    tl.to('#m'+b.id, {y:-12, duration:Math.max(.2,b.sp-.9), ease:'none'}, s+.82);")
_LOUD_BUBBLE = ("tl.fromTo(st, {opacity:0,x:-46,scale:.96}, "
                "{opacity:1,x:0,scale:1,duration:.5,ease:'power3.out'}, s);")
_QUIET_BUBBLE = "tl.fromTo(st, {opacity:0,x:-28}, {opacity:1,x:0,duration:.5,ease:'power3.out'}, s);"


def quiet(html):
    """글자 덩어리의 배율·상시 떠오름을 뺀다. 모션 프리셋이 붙은 장면에서만 부른다."""
    for old, new in ((_LOUD_TITLE, _QUIET_TITLE), (_DRIFT, ""), (_LOUD_BUBBLE, _QUIET_BUBBLE)):
        if html.count(old) != 1:
            raise SystemExit("MOTION_QUIET_ANCHOR_MISSING: build.py 의 기본 진입 문구가 바뀌었다")
        html = html.replace(old, new)
    return html
