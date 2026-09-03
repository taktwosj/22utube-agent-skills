"""Canonical 001 assembly-type contract.

An assembly type selects an execution strategy and the logical layers that must
be populated, may be populated, or must be cleared.  Audio routing remains
owned by ``audio_policy_matrix``; this module only declares which existing
mode/policy routes are compatible with each type.

New types are data-only when they can be expressed with the existing logical
roles and existing audio routes.  A new physical track or new audio behavior is
an engine change and intentionally fails this contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from audio_policy_matrix import CANONICAL_MODE_MATRIX
from track_template_matrix import CANONICAL_TRACKS, LOGICAL_ROLE_BY_TRACK


ALWAYS_CLEARED = ("A11", "A12", "A12_RESERVED_EMPTY", "STATE_GLITCH")
LEGACY_EXECUTION_STRATEGY_ALIASES = {
    "2": frozenset({"tts_only"}),
}
_ENGINE_PLACEMENT_ROLES = frozenset(
    role for role in LOGICAL_ROLE_BY_TRACK if role is not None
)
_ENGINE_CLEARABLE_ROLES = frozenset(CANONICAL_TRACKS) | _ENGINE_PLACEMENT_ROLES
_CANONICAL_MODE_POLICIES = frozenset(
    (mode, policy) for mode, policy, _source in CANONICAL_MODE_MATRIX
)
_PLACEMENT_RULES = frozenset({
    "A9_FIRST_VIDEO_ONLY",
    "A10_TEXT_AFTER_FIRST_VIDEO",
    "A9_AFTER_FIRST_VIDEO_REQUIRED",
})


@dataclass(frozen=True)
class AssemblyTypeDefinition:
    type_id: str
    execution_strategy: str
    required_roles: frozenset[str]
    optional_roles: frozenset[str]
    cleared_roles: tuple[str, ...]
    allowed_mode_policies: frozenset[tuple[str, str]]
    placement_rules: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.type_id, str) or not self.type_id.strip():
            raise ValueError("ASSEMBLY_TYPE_ID_INVALID")
        if (
            not isinstance(self.execution_strategy, str)
            or not self.execution_strategy.strip()
        ):
            raise ValueError("ASSEMBLY_TYPE_STRATEGY_INVALID")
        required = frozenset(self.required_roles)
        optional = frozenset(self.optional_roles)
        cleared = tuple(self.cleared_roles)
        cleared_set = set(cleared)
        if len(cleared) != len(cleared_set):
            raise ValueError("ASSEMBLY_TYPE_CLEARED_ROLE_DUPLICATE")
        if (
            required & optional
            or required & cleared_set
            or optional & cleared_set
        ):
            raise ValueError("ASSEMBLY_TYPE_ROLE_OVERLAP")
        if not (required | optional) <= _ENGINE_PLACEMENT_ROLES:
            raise ValueError("ASSEMBLY_TYPE_PLACEMENT_ROLE_UNKNOWN")
        if not cleared_set <= _ENGINE_CLEARABLE_ROLES:
            raise ValueError("ASSEMBLY_TYPE_CLEAR_ROLE_UNKNOWN")
        routes = frozenset(tuple(route) for route in self.allowed_mode_policies)
        if not routes or not routes <= _CANONICAL_MODE_POLICIES:
            raise ValueError("ASSEMBLY_TYPE_AUDIO_ROUTE_INVALID")
        placement_rules = frozenset(self.placement_rules)
        if not placement_rules <= _PLACEMENT_RULES:
            raise ValueError("ASSEMBLY_TYPE_PLACEMENT_RULE_UNKNOWN")
        object.__setattr__(self, "required_roles", required)
        object.__setattr__(self, "optional_roles", optional)
        object.__setattr__(self, "cleared_roles", cleared)
        object.__setattr__(self, "allowed_mode_policies", routes)
        object.__setattr__(self, "placement_rules", placement_rules)


ASSEMBLY_TYPE_DEFINITIONS: dict[str, AssemblyTypeDefinition] = {
    "1": AssemblyTypeDefinition(
        type_id="1",
        execution_strategy="caption_only",
        required_roles=frozenset({"STATE"}),
        optional_roles=frozenset(),
        cleared_roles=("A9", "A9_TEXT", "A10", "A10_TEXT"),
        allowed_mode_policies=frozenset({
            ("URAKKAI", "CAPTION_ONLY_MUTE_SOURCE"),
        }),
    ),
    "2": AssemblyTypeDefinition(
        type_id="2",
        execution_strategy="full_tts",
        required_roles=frozenset({"A9", "A9_TEXT"}),
        optional_roles=frozenset({"STATE"}),
        cleared_roles=("A10", "A10_TEXT", "STATE_LASER"),
        allowed_mode_policies=frozenset({
            ("URAKKAI", "TTS_ONLY_MUTE_SOURCE"),
        }),
    ),
    "3": AssemblyTypeDefinition(
        type_id="3",
        execution_strategy="original_audio_caption",
        required_roles=frozenset({"A10", "A10_TEXT"}),
        optional_roles=frozenset({"STATE"}),
        cleared_roles=("A9", "A9_TEXT"),
        allowed_mode_policies=frozenset({
            ("SOURCE_ORDER_UNCHANGED_CLEAN_ONLY", "SOURCE_ORDER_CLEAN_AUDIO"),
            ("SOURCE_ORDER_UNCHANGED_A10_RETAINED", "A10_RETAINED_SYNC"),
            ("URAKKAI", "A10_REASSEMBLED_SYNC"),
            ("URAKKAI", "SOURCE_ORDER_CLEAN_AUDIO"),
        }),
    ),
    "4": AssemblyTypeDefinition(
        type_id="4",
        execution_strategy="tts_intro_original_body",
        required_roles=frozenset({"A9", "A9_TEXT", "A10", "A10_TEXT"}),
        optional_roles=frozenset({"STATE"}),
        cleared_roles=(),
        allowed_mode_policies=frozenset({
            ("URAKKAI", "A9_TTS_PLUS_A10_REASSEMBLED"),
            ("URAKKAI", "A9_TTS_PLUS_A10_SOURCE_CLIP"),
        }),
        placement_rules=frozenset({
            "A9_FIRST_VIDEO_ONLY",
            "A10_TEXT_AFTER_FIRST_VIDEO",
        }),
    ),
    "5": AssemblyTypeDefinition(
        type_id="5",
        execution_strategy="narration_plus_speaker",
        required_roles=frozenset({"A9", "A9_TEXT", "A10", "A10_TEXT"}),
        optional_roles=frozenset({"STATE"}),
        cleared_roles=(),
        allowed_mode_policies=frozenset({
            ("URAKKAI", "A9_TTS_PLUS_A10_REASSEMBLED"),
            ("URAKKAI", "A9_TTS_PLUS_A10_SOURCE_CLIP"),
        }),
        placement_rules=frozenset({"A9_AFTER_FIRST_VIDEO_REQUIRED"}),
    ),
}


def validate_assembly_placement_rules(
    definition: AssemblyTypeDefinition,
    role_ranges: Mapping[str, Sequence[tuple[int, int]]],
    video_ranges: Sequence[tuple[int, int]],
) -> list[str]:
    if not definition.placement_rules:
        return []
    videos = sorted(video_ranges)
    if not videos:
        return ["ASSEMBLY_TYPE_VIDEO_REQUIRED"]
    intro = videos[0]
    errors: list[str] = []

    if "A9_FIRST_VIDEO_ONLY" in definition.placement_rules:
        narration_ranges = tuple(role_ranges.get("A9", ())) + tuple(
            role_ranges.get("A9_TEXT", ())
        )
        if any(target != intro for target in narration_ranges):
            errors.append("ASSEMBLY_TYPE_A9_INTRO_ONLY")

    if "A10_TEXT_AFTER_FIRST_VIDEO" in definition.placement_rules:
        if any(
            target[0] < intro[1] and intro[0] < target[1]
            for target in role_ranges.get("A10_TEXT", ())
        ):
            errors.append("ASSEMBLY_TYPE_A10_TEXT_AFTER_INTRO_REQUIRED")

    if "A9_AFTER_FIRST_VIDEO_REQUIRED" in definition.placement_rules:
        if not any(
            target[0] >= intro[1]
            for target in role_ranges.get("A9", ())
        ):
            errors.append("ASSEMBLY_TYPE_A9_BODY_REQUIRED")

    return errors


def assembly_type_definition(type_id: str) -> AssemblyTypeDefinition:
    try:
        return ASSEMBLY_TYPE_DEFINITIONS[type_id]
    except KeyError as exc:
        raise ValueError(f"ASSEMBLY_TYPE_UNKNOWN:{type_id}") from exc
