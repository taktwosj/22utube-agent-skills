"""Resolve a thin production preset against the shared 001 matrices."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from assembly_type_matrix import ALWAYS_CLEARED, assembly_type_definition
from audio_policy_matrix import CANONICAL_MODE_MATRIX
from schema_runtime import validate_schema
from track_template_matrix import track_template_profile


_PROFILE_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / "schemas" / "production_profile.schema.json")
    .read_text(encoding="utf-8")
)
SELECTOR_FIELDS = tuple(_PROFILE_SCHEMA["required"])
SCHEMA_VERSION = _PROFILE_SCHEMA["properties"]["schema_version"]["const"]


@dataclass(frozen=True)
class ResolvedProductionProfile:
    selector: Mapping[str, str]
    execution_strategy: str
    audio_source: str
    track_layout: str
    required_roles: frozenset[str]
    optional_roles: frozenset[str]
    cleared_roles: tuple[str, ...]


def audio_source_for_route(production_mode: str, audio_policy: str) -> str:
    sources = {
        source
        for mode, policy, source in CANONICAL_MODE_MATRIX
        if (mode, policy) == (production_mode, audio_policy)
    }
    if len(sources) != 1:
        raise ValueError("PRODUCTION_PROFILE_AUDIO_ROUTE_INCOMPATIBLE")
    return next(iter(sources))


def resolve_production_profile(payload: Mapping[str, object]) -> ResolvedProductionProfile:
    if not isinstance(payload, Mapping) or set(payload) != set(SELECTOR_FIELDS):
        raise ValueError("PRODUCTION_PROFILE_FIELDS_INVALID")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("PRODUCTION_PROFILE_SCHEMA_UNSUPPORTED")
    if validate_schema(dict(payload), _PROFILE_SCHEMA):
        raise ValueError("PRODUCTION_PROFILE_FIELDS_INVALID")

    selector = {field: str(payload[field]) for field in SELECTOR_FIELDS}
    definition = assembly_type_definition(selector["assembly_type"])
    route = (selector["production_mode"], selector["audio_policy"])
    if route not in definition.allowed_mode_policies:
        raise ValueError("PRODUCTION_PROFILE_AUDIO_ROUTE_INCOMPATIBLE")
    audio_source = audio_source_for_route(*route)
    template = track_template_profile(selector["template_profile"])
    active_state_tracks = {
        template.physical_tracks[index]
        for index in template.state_track_by_effect.values()
    }
    profile_always_cleared = tuple(
        role for role in ALWAYS_CLEARED if role not in active_state_tracks
    )
    placement_roles = {
        role for role in template.logical_role_by_track if role is not None
    }
    clearable_roles = set(template.physical_tracks) | placement_roles
    # A12 is the legacy contract anchor; the physical lane is named
    # A12_RESERVED_EMPTY and both names remain cleared for v1/v2 plans.
    clearable_roles.add("A12")
    if not (
        set(definition.required_roles) | set(definition.optional_roles)
    ) <= placement_roles:
        raise ValueError("PRODUCTION_PROFILE_TEMPLATE_ROLE_UNSUPPORTED")
    if not (
        set(definition.cleared_roles) | set(ALWAYS_CLEARED)
    ) <= clearable_roles:
        raise ValueError("PRODUCTION_PROFILE_TEMPLATE_ROLE_UNSUPPORTED")

    return ResolvedProductionProfile(
        selector=MappingProxyType(selector),
        execution_strategy=definition.execution_strategy,
        audio_source=audio_source,
        track_layout=template.track_layout,
        required_roles=definition.required_roles,
        optional_roles=definition.optional_roles,
        cleared_roles=profile_always_cleared + definition.cleared_roles,
    )
