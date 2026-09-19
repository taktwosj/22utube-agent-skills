# -*- coding: utf-8 -*-
"""장면 유형 11종 → 기본 모션·허용 강조·강조 길이. 표 정본은 references/motion/scene-presets.md."""

# base : 유형마다 항상 붙는 기본 모션 (1~2개)
# fx   : 그 유형에서만 허용하는 강조. 장면당 최대 1개 (limits.md)
PRESETS = {
    "opening":  {"base": ("word_slide", "parallax_in"), "fx": ("snap_zoom",)},
    "explain":  {"base": ("float_in",),              "fx": ()},
    "quote":    {"base": ("float_in",),              "fx": ("glow",)},
    "evidence": {"base": ("underline",),                "fx": ("snap_zoom", "light_sweep")},
    "timeline": {"base": ("anticipation", "follow_through"), "fx": ("snap_zoom",)},
    "flow":     {"base": ("anticipation", "trail"),     "fx": ("burst",)},
    "relation": {"base": ("depth_in",),                 "fx": ("parallax_in",)},
    "move":     {"base": ("anticipation", "trail"),     "fx": ()},
    "contrast": {"base": ("float_in", "follow_through"), "fx": ("shake",)},
    "closing":  {"base": ("follow_through",),           "fx": ()},
    "document": {"base": (),                            "fx": ("light_sweep",)},  # doc 도식: 줄 순차·밑줄이 곧 모션
}

# 강조 1개가 쓰는 시간(초). 장면 합계 1.0 초 이하 (사용자 지시 2026-09-16 Q5)
FX_SECONDS = {
    "snap_zoom": 0.50,
    "glow": 0.60,
    "light_sweep": 0.90,
    "burst": 0.40,
    "shake": 0.28,
    "parallax_in": 0.30,
}

# 흔들림 세기. 감쇠 비율은 고정, 진폭만 바꾼다.
SHAKE = {"x": 18, "y": 6, "rot": 0.5, "seconds": 0.28}
SHAKE_DAMP = (1.0, -0.72, 0.46, -0.26, 0.0)

# 챕터당 1회 이하 (사용자 지시 2026-09-16 Q5)
FX_CHAPTER_ONCE = ("shake",)

SCENE_FX_BUDGET = 1.0

# 글자가 떠오르는 시간(초). 값 하나로 전 장면이 같이 바뀐다.
FLOAT_SECONDS = 0.50
