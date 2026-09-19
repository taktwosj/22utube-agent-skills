"""Narration beat constructors and frame-rounded duration helpers."""
import math
from . import core

def T(nl, mega, eyebrow="&nbsp;", sub=""):
    """큰 글씨 비트. mega 안에서 <span class='hl'>옐로</span> <span class='cy'>시안</span>."""
    return {"nl": nl, "type": "title", "eyebrow": eyebrow, "mega": mega, "sub": sub}

def P(nl, who, rows):
    """패널 비트. rows = [(키, 값, "cy"|"")]."""
    return {"nl": nl, "type": "panel", "who": who, "rows": rows}

def Q(nl, who, q, note="", accent="cy"):
    """말풍선 비트. 발화자를 who 에 세운다."""
    return {"nl": nl, "type": "bubble", "who": who, "q": q, "note": note, "accent": accent}

def span(nl):
    nls = nl if isinstance(nl, (list, tuple)) else [nl]
    return sum(math.ceil(core.LINES[x]["duration"] * 30) / 30 for x in nls)

def first_nl(b):
    return b["nl"][0] if isinstance(b["nl"], (list, tuple)) else b["nl"]

def last_nl(b):
    return b["nl"][-1] if isinstance(b["nl"], (list, tuple)) else b["nl"]
