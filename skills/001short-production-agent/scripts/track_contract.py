"""Single executable authority for the versioned 15-track CapCut layouts."""

V2_TRACK_LAYOUT = "shrt_white_base_v2_15"
V3_TRACK_LAYOUT = "shrt_white_base_v3_15"
TRACK_LAYOUT = V3_TRACK_LAYOUT

V2_TEMPLATE_PROFILE = "shrt_white_base_v2"
V3_TEMPLATE_PROFILE = "shrt_white_base_v3"
TEMPLATE_PROFILE = V3_TEMPLATE_PROFILE
TRACK_LAYOUT_BY_TEMPLATE_PROFILE = {
    V2_TEMPLATE_PROFILE: V2_TRACK_LAYOUT,
    V3_TEMPLATE_PROFILE: V3_TRACK_LAYOUT,
}
TEMPLATE_PROFILE_BY_TRACK_LAYOUT = {
    layout: profile for profile, layout in TRACK_LAYOUT_BY_TEMPLATE_PROFILE.items()
}

CANONICAL_TRACKS = (
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "SOURCE_CREDIT", "STATE_GLITCH",
    "STATE_LASER", "A10_TEXT_WHITE", "A10_TEXT_YELLOW", "A9_TEXT", "T2", "T1",
    "A9", "A10", "A11", "A12_RESERVED_EMPTY",
)

VISUAL_TRACK_COUNT = 11
# Human-facing grid rows read top-down: the visual tracks reversed (T1 first)
# followed by the audio tracks in physical order.
HUMAN_GRID_ROWS = (
    tuple(reversed(CANONICAL_TRACKS[:VISUAL_TRACK_COUNT]))
    + CANONICAL_TRACKS[VISUAL_TRACK_COUNT:]
)

LOGICAL_ROLE_BY_TRACK = (
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "SOURCE_CREDIT", "STATE", "STATE",
    "A10_TEXT", "A10_TEXT", "A9_TEXT", "T2", "T1", "A9", "A10", "A11",
    "A12_RESERVED_EMPTY",
)

# v2 has no routable role at physical track 3. Keeping that slot explicitly
# empty lets old contracts validate without granting them the v3-only credit.
V2_LOGICAL_ROLE_BY_TRACK = (
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", None, "STATE", "STATE",
    "A10_TEXT", "A10_TEXT", "A9_TEXT", "T2", "T1", "A9", "A10", "A11",
    "A12_RESERVED_EMPTY",
)
LOGICAL_ROLE_BY_LAYOUT = {
    V2_TRACK_LAYOUT: V2_LOGICAL_ROLE_BY_TRACK,
    V3_TRACK_LAYOUT: LOGICAL_ROLE_BY_TRACK,
}

A12_INDEX = 14
TRACK_INDEX = {name: index for index, name in enumerate(CANONICAL_TRACKS)}
STATE_TRACK_BY_EFFECT = {
    "LASER_CUT": TRACK_INDEX["STATE_LASER"],
}
A10_TEXT_TRACK_BY_COLOR = {
    "WHITE": TRACK_INDEX["A10_TEXT_WHITE"],
    "YELLOW": TRACK_INDEX["A10_TEXT_YELLOW"],
}
