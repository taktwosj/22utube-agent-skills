"""Single data authority for 001 CapCut track and template capabilities.

Physical coordinates and styles remain owned by the immutable layout contract
bound to each template archive.  This module owns only the engine-facing facts
needed before that contract is loaded: role routing, seed capabilities, base
track clearing, text budgets, and pinned portable assets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


V2_TRACK_LAYOUT = "shrt_white_base_v2_15"
V3_TRACK_LAYOUT = "shrt_white_base_v3_15"
TRACK_LAYOUT = V3_TRACK_LAYOUT

V2_TEMPLATE_PROFILE = "shrt_white_base_v2"
V3_TEMPLATE_PROFILE = "shrt_white_base_v3"
BLACK_TOP_TEMPLATE_PROFILE = "shrt_black_top_v1"
FOREIGN_VIRAL_DIALOGUE_TEMPLATE_PROFILE = "shrt_black_headline_dialogue_v1"
TEMPLATE_PROFILE = V3_TEMPLATE_PROFILE

SPEAKER_BLUE_DIALOGUE_WHITE_TWO_LINE = "speaker_blue_dialogue_white_two_line"
YELLOW_RED_YELLOW_EMPHASIS = "yellow_red_yellow_emphasis"

CANONICAL_TRACKS = (
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "SOURCE_CREDIT", "STATE_GLITCH",
    "STATE_LASER", "A10_TEXT_WHITE", "A10_TEXT_YELLOW", "A9_TEXT", "T2", "T1",
    "A9", "A10", "A11", "A12_RESERVED_EMPTY",
)
VISUAL_TRACK_COUNT = 11
HUMAN_GRID_ROWS = (
    tuple(reversed(CANONICAL_TRACKS[:VISUAL_TRACK_COUNT]))
    + CANONICAL_TRACKS[VISUAL_TRACK_COUNT:]
)

LOGICAL_ROLE_BY_TRACK = (
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "SOURCE_CREDIT", "STATE", "STATE",
    "A10_TEXT", "A10_TEXT", "A9_TEXT", "T2", "T1", "A9", "A10", "A11",
    "A12_RESERVED_EMPTY",
)
CANONICAL_TRACK_TYPES = (
    "video", "effect", "video", "text", "text", "text", "text", "text",
    "text", "text", "text", "audio", "audio", "audio", "audio",
)
V2_LAYOUT_CONTRACT_ROLES = (
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "STATE_EFFECT_3", "STATE_EFFECT_2",
    "STATE_EFFECT_1", "A10_TEXT_WHITE", "A10_TEXT_YELLOW", "A9_TEXT", "T2",
    "T1", "A9", "A10", "A11_SFX", "A12",
)
V3_LAYOUT_CONTRACT_ROLES = (
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "SOURCE_CREDIT", "STATE_EFFECT_2",
    "STATE_EFFECT_1", "A10_TEXT_WHITE", "A10_TEXT_YELLOW", "A9_TEXT", "T2",
    "T1", "A9", "A10", "A11_SFX", "A12",
)
LAYOUT_CONTRACT_ROLES = MappingProxyType({
    V2_TRACK_LAYOUT: V2_LAYOUT_CONTRACT_ROLES,
    V3_TRACK_LAYOUT: V3_LAYOUT_CONTRACT_ROLES,
})
TRACK_TYPES_BY_LAYOUT = MappingProxyType({
    V2_TRACK_LAYOUT: CANONICAL_TRACK_TYPES,
    V3_TRACK_LAYOUT: CANONICAL_TRACK_TYPES,
})
V2_LOGICAL_ROLE_BY_TRACK = (
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", None, "STATE", "STATE",
    "A10_TEXT", "A10_TEXT", "A9_TEXT", "T2", "T1", "A9", "A10", "A11",
    "A12_RESERVED_EMPTY",
)

A12_INDEX = 14
TRACK_INDEX = {name: index for index, name in enumerate(CANONICAL_TRACKS)}
STATE_TRACK_BY_EFFECT = {"LASER_CUT": TRACK_INDEX["STATE_LASER"]}
A10_TEXT_TRACK_BY_COLOR = {
    "WHITE": TRACK_INDEX["A10_TEXT_WHITE"],
    "YELLOW": TRACK_INDEX["A10_TEXT_YELLOW"],
}


@dataclass(frozen=True)
class LineBudget:
    max_lines: int | None
    max_chars: int

    def __post_init__(self) -> None:
        if self.max_lines is not None and self.max_lines < 1:
            raise ValueError("TEMPLATE_LINE_BUDGET_LINES_INVALID")
        if self.max_chars < 1:
            raise ValueError("TEMPLATE_LINE_BUDGET_CHARS_INVALID")


@dataclass(frozen=True)
class TrackTemplateProfile:
    name: str
    track_layout: str
    physical_tracks: tuple[str, ...]
    logical_role_by_track: tuple[str | None, ...]
    visual_track_count: int
    required_seed_roles: tuple[str, ...]
    seed_preserved_roles: frozenset[str]
    full_span_roles: tuple[str, ...]
    optional_full_span_roles: tuple[str, ...]
    role_line_budgets: Mapping[str, LineBudget]
    grid_line_budgets: Mapping[tuple[str, str], LineBudget]
    pinned_assets: Mapping[str, str]
    state_track_by_effect: Mapping[str, int] = field(
        default_factory=lambda: dict(STATE_TRACK_BY_EFFECT)
    )
    dialogue_text_style_policy: str | None = None
    headline_text_style_policy: str | None = None

    def __post_init__(self) -> None:
        physical_tracks = tuple(self.physical_tracks)
        logical_roles = tuple(self.logical_role_by_track)
        if not self.name or not self.track_layout:
            raise ValueError("TRACK_TEMPLATE_PROFILE_ID_INVALID")
        if (
            not physical_tracks
            or len(physical_tracks) != len(logical_roles)
            or len(set(physical_tracks)) != len(physical_tracks)
        ):
            raise ValueError("TRACK_TEMPLATE_PROFILE_TRACKS_INVALID")
        if physical_tracks != CANONICAL_TRACKS:
            raise ValueError("TRACK_TEMPLATE_PROFILE_PHYSICAL_ORDER_UNSUPPORTED")
        if not 0 < self.visual_track_count < len(physical_tracks):
            raise ValueError("TRACK_TEMPLATE_PROFILE_VISUAL_COUNT_INVALID")
        physical_roles = set(physical_tracks)
        logical_role_set = {role for role in logical_roles if role is not None}
        allowed_roles = physical_roles | logical_role_set
        for roles in (
            self.required_seed_roles,
            self.seed_preserved_roles,
            self.full_span_roles,
            self.optional_full_span_roles,
        ):
            if any(role not in allowed_roles for role in roles):
                raise ValueError("TRACK_TEMPLATE_PROFILE_ROLE_UNKNOWN")
        if set(self.full_span_roles) & set(self.optional_full_span_roles):
            raise ValueError("TRACK_TEMPLATE_PROFILE_FULL_SPAN_OVERLAP")
        if physical_tracks[-1] != "A12_RESERVED_EMPTY":
            raise ValueError("TRACK_TEMPLATE_PROFILE_RESERVED_TRACK_INVALID")
        role_line_budgets = dict(self.role_line_budgets)
        grid_line_budgets = dict(self.grid_line_budgets)
        pinned_assets = dict(self.pinned_assets)
        state_tracks = dict(self.state_track_by_effect)
        if any(not isinstance(budget, LineBudget) for budget in role_line_budgets.values()):
            raise ValueError("TRACK_TEMPLATE_PROFILE_ROLE_BUDGET_INVALID")
        if any(not isinstance(budget, LineBudget) for budget in grid_line_budgets.values()):
            raise ValueError("TRACK_TEMPLATE_PROFILE_GRID_BUDGET_INVALID")
        if any(role not in allowed_roles for role in role_line_budgets):
            raise ValueError("TRACK_TEMPLATE_PROFILE_BUDGET_ROLE_UNKNOWN")
        if any(role not in physical_roles for role in pinned_assets):
            raise ValueError("TRACK_TEMPLATE_PROFILE_ASSET_ROLE_UNKNOWN")
        if any(not isinstance(path, str) or not path for path in pinned_assets.values()):
            raise ValueError("TRACK_TEMPLATE_PROFILE_ASSET_INVALID")
        if any(
            not isinstance(effect, str) or not effect
            or not isinstance(index, int) or isinstance(index, bool)
            or index < 0 or index >= len(logical_roles)
            or logical_roles[index] != "STATE"
            for effect, index in state_tracks.items()
        ):
            raise ValueError("TRACK_TEMPLATE_PROFILE_STATE_ROUTE_INVALID")
        if self.dialogue_text_style_policy not in {
            None, SPEAKER_BLUE_DIALOGUE_WHITE_TWO_LINE,
        }:
            raise ValueError("TRACK_TEMPLATE_PROFILE_DIALOGUE_POLICY_INVALID")
        if self.headline_text_style_policy not in {
            None, YELLOW_RED_YELLOW_EMPHASIS,
        }:
            raise ValueError("TRACK_TEMPLATE_PROFILE_HEADLINE_POLICY_INVALID")
        object.__setattr__(self, "physical_tracks", physical_tracks)
        object.__setattr__(self, "logical_role_by_track", logical_roles)
        object.__setattr__(self, "required_seed_roles", tuple(self.required_seed_roles))
        object.__setattr__(self, "seed_preserved_roles", frozenset(self.seed_preserved_roles))
        object.__setattr__(self, "full_span_roles", tuple(self.full_span_roles))
        object.__setattr__(self, "optional_full_span_roles", tuple(self.optional_full_span_roles))
        object.__setattr__(self, "role_line_budgets", MappingProxyType(role_line_budgets))
        object.__setattr__(self, "grid_line_budgets", MappingProxyType(grid_line_budgets))
        object.__setattr__(self, "pinned_assets", MappingProxyType(pinned_assets))
        object.__setattr__(self, "state_track_by_effect", MappingProxyType(state_tracks))

    @property
    def clear_track_indices(self) -> tuple[int, ...]:
        return tuple(
            index for index, role in enumerate(self.physical_tracks)
            if role not in self.seed_preserved_roles
        )

    def supports_role(self, role: str) -> bool:
        return role in self.logical_role_by_track


# The white v2/v3 seeds have no width or wrap settings. These are the measured
# per-line budgets before text leaves the frame. SOURCE_CREDIT remains the
# conservative scaled estimate; a future template must supply its own measured
# layout contract instead of inheriting these values silently.
_COMMON_ROLE_LINE_BUDGETS = {
    "T1": LineBudget(None, 12),
    "T2": LineBudget(None, 12),
    "A10_TEXT": LineBudget(None, 15),
    "A9_TEXT": LineBudget(2, 10),
    "STATE": LineBudget(2, 15),
}
_GRID_LINE_BUDGETS = {
    ("original", "A9_TEXT"): LineBudget(2, 15),
    ("urakkai", "A9_TEXT"): LineBudget(2, 10),
    ("original", "STATE_LASER"): LineBudget(2, 15),
    ("urakkai", "STATE_LASER"): LineBudget(2, 15),
    ("original", "STATE_GLITCH"): LineBudget(2, 18),
    ("urakkai", "STATE_GLITCH"): LineBudget(2, 18),
}
_SEED_PRESERVED_ROLES = frozenset({
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "T2", "T1",
})
_FULL_SPAN_ROLES = ("T1", "T2", "SCREEN_WHITE", "SCREEN_EFFECT")
_PINNED_ASSETS = {"SCREEN_WHITE": "transparent_center_white_1080x1920.png"}

TRACK_TEMPLATE_PROFILES: dict[str, TrackTemplateProfile] = {
    V2_TEMPLATE_PROFILE: TrackTemplateProfile(
        name=V2_TEMPLATE_PROFILE,
        track_layout=V2_TRACK_LAYOUT,
        physical_tracks=CANONICAL_TRACKS,
        logical_role_by_track=V2_LOGICAL_ROLE_BY_TRACK,
        visual_track_count=VISUAL_TRACK_COUNT,
        required_seed_roles=("VIDEO", "A9", "A10"),
        seed_preserved_roles=_SEED_PRESERVED_ROLES,
        full_span_roles=_FULL_SPAN_ROLES,
        optional_full_span_roles=(),
        role_line_budgets=_COMMON_ROLE_LINE_BUDGETS,
        grid_line_budgets=_GRID_LINE_BUDGETS,
        pinned_assets=_PINNED_ASSETS,
        state_track_by_effect=STATE_TRACK_BY_EFFECT,
        dialogue_text_style_policy=None,
        headline_text_style_policy=None,
    ),
    V3_TEMPLATE_PROFILE: TrackTemplateProfile(
        name=V3_TEMPLATE_PROFILE,
        track_layout=V3_TRACK_LAYOUT,
        physical_tracks=CANONICAL_TRACKS,
        logical_role_by_track=LOGICAL_ROLE_BY_TRACK,
        visual_track_count=VISUAL_TRACK_COUNT,
        required_seed_roles=("VIDEO", "A9", "A10", "SOURCE_CREDIT"),
        seed_preserved_roles=_SEED_PRESERVED_ROLES,
        full_span_roles=_FULL_SPAN_ROLES,
        optional_full_span_roles=("SOURCE_CREDIT",),
        role_line_budgets={
            **_COMMON_ROLE_LINE_BUDGETS,
            "SOURCE_CREDIT": LineBudget(1, 16),
        },
        grid_line_budgets=_GRID_LINE_BUDGETS,
        pinned_assets=_PINNED_ASSETS,
        state_track_by_effect=STATE_TRACK_BY_EFFECT,
        dialogue_text_style_policy=None,
        headline_text_style_policy=None,
    ),
    BLACK_TOP_TEMPLATE_PROFILE: TrackTemplateProfile(
        name=BLACK_TOP_TEMPLATE_PROFILE,
        track_layout=V3_TRACK_LAYOUT,
        physical_tracks=CANONICAL_TRACKS,
        logical_role_by_track=LOGICAL_ROLE_BY_TRACK,
        visual_track_count=VISUAL_TRACK_COUNT,
        required_seed_roles=("VIDEO", "A9", "A10", "SOURCE_CREDIT"),
        seed_preserved_roles=_SEED_PRESERVED_ROLES,
        full_span_roles=_FULL_SPAN_ROLES + ("SOURCE_CREDIT",),
        optional_full_span_roles=(),
        role_line_budgets={
            **_COMMON_ROLE_LINE_BUDGETS,
            "SOURCE_CREDIT": LineBudget(1, 16),
        },
        grid_line_budgets=_GRID_LINE_BUDGETS,
        # Compatibility filename inside the black-top archive.  The pixels,
        # archive SHA, and layout binding differ; the builder path does not.
        pinned_assets=_PINNED_ASSETS,
        state_track_by_effect=STATE_TRACK_BY_EFFECT,
        dialogue_text_style_policy=None,
        headline_text_style_policy=None,
    ),
    FOREIGN_VIRAL_DIALOGUE_TEMPLATE_PROFILE: TrackTemplateProfile(
        name=FOREIGN_VIRAL_DIALOGUE_TEMPLATE_PROFILE,
        track_layout=V3_TRACK_LAYOUT,
        physical_tracks=CANONICAL_TRACKS,
        logical_role_by_track=LOGICAL_ROLE_BY_TRACK,
        visual_track_count=VISUAL_TRACK_COUNT,
        required_seed_roles=("VIDEO", "A9", "A10", "SOURCE_CREDIT"),
        seed_preserved_roles=_SEED_PRESERVED_ROLES,
        full_span_roles=_FULL_SPAN_ROLES + ("SOURCE_CREDIT",),
        optional_full_span_roles=(),
        role_line_budgets={
            **_COMMON_ROLE_LINE_BUDGETS,
            "A10_TEXT": LineBudget(2, 18),
            "STATE": LineBudget(2, 18),
            "SOURCE_CREDIT": LineBudget(1, 16),
        },
        grid_line_budgets=_GRID_LINE_BUDGETS,
        pinned_assets={"SCREEN_WHITE": "black_frame_local_1080x1920.png"},
        state_track_by_effect={"GLITCH_SHAKE": TRACK_INDEX["STATE_GLITCH"]},
        dialogue_text_style_policy=SPEAKER_BLUE_DIALOGUE_WHITE_TWO_LINE,
        headline_text_style_policy=YELLOW_RED_YELLOW_EMPHASIS,
    ),
}


def track_template_profile(name: str) -> TrackTemplateProfile:
    try:
        return TRACK_TEMPLATE_PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"TEMPLATE_PROFILE_UNKNOWN:{name}") from exc


def template_profiles_for_layout(layout: str) -> tuple[str, ...]:
    names = tuple(
        name for name, profile in TRACK_TEMPLATE_PROFILES.items()
        if profile.track_layout == layout
    )
    if not names:
        raise ValueError(f"TRACK_LAYOUT_UNKNOWN:{layout}")
    return names


def profile_supports_role(profile_name: str, role: str) -> bool:
    return track_template_profile(profile_name).supports_role(role)


def state_track_by_effect(profile_name: str) -> Mapping[str, int]:
    return track_template_profile(profile_name).state_track_by_effect


def layout_contract_roles(layout: str) -> tuple[str, ...]:
    try:
        return LAYOUT_CONTRACT_ROLES[layout]
    except KeyError as exc:
        raise ValueError(f"TRACK_LAYOUT_CONTRACT_ROLES_UNKNOWN:{layout}") from exc


def track_types_for_layout(layout: str) -> tuple[str, ...]:
    try:
        return TRACK_TYPES_BY_LAYOUT[layout]
    except KeyError as exc:
        raise ValueError(f"TRACK_LAYOUT_TYPES_UNKNOWN:{layout}") from exc


TRACK_LAYOUT_BY_TEMPLATE_PROFILE = {
    name: profile.track_layout for name, profile in TRACK_TEMPLATE_PROFILES.items()
}
TEMPLATE_PROFILE_BY_TRACK_LAYOUT = {
    layout: names[0]
    for layout in {profile.track_layout for profile in TRACK_TEMPLATE_PROFILES.values()}
    for names in (template_profiles_for_layout(layout),)
}
LOGICAL_ROLE_BY_LAYOUT: dict[str, tuple[str | None, ...]] = {}
for _profile in TRACK_TEMPLATE_PROFILES.values():
    _existing_roles = LOGICAL_ROLE_BY_LAYOUT.setdefault(
        _profile.track_layout, _profile.logical_role_by_track,
    )
    if _existing_roles != _profile.logical_role_by_track:
        raise ValueError(
            f"TRACK_LAYOUT_LOGICAL_ROLE_CONFLICT:{_profile.track_layout}"
        )

DEFAULT_TRACK_TEMPLATE = track_template_profile(TEMPLATE_PROFILE)
FULL_SPAN_ROLES = DEFAULT_TRACK_TEMPLATE.full_span_roles
OPTIONAL_FULL_SPAN_ROLES = DEFAULT_TRACK_TEMPLATE.optional_full_span_roles
ROLE_LINE_BUDGETS = DEFAULT_TRACK_TEMPLATE.role_line_budgets
GRID_LINE_BUDGETS = DEFAULT_TRACK_TEMPLATE.grid_line_budgets
PINNED_ASSETS = DEFAULT_TRACK_TEMPLATE.pinned_assets
MAX_LINE_LENGTH_BY_ROLE = MappingProxyType({
    role: budget.max_chars for role, budget in ROLE_LINE_BUDGETS.items()
})
MAX_LINE_COUNT_BY_ROLE = MappingProxyType({
    role: budget.max_lines
    for role, budget in ROLE_LINE_BUDGETS.items()
    if budget.max_lines is not None
})
LINE_LIMITS = MappingProxyType({
    key: (budget.max_lines, budget.max_chars)
    for key, budget in GRID_LINE_BUDGETS.items()
})
