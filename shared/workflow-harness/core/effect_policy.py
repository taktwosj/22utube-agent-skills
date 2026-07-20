"""Versioned lane-local deterministic effect selection."""

from __future__ import annotations

import hashlib


class EffectPolicyError(Exception):
    pass


def _approved_presets(pool: dict) -> list[dict]:
    presets = pool.get("presets")
    if not isinstance(presets, list):
        raise EffectPolicyError("EFFECT_POOL_PRESETS_REQUIRED")
    approved = [
        preset
        for preset in presets
        if isinstance(preset, dict)
        and preset.get("approved") is True
        and isinstance(preset.get("preset_id"), str)
        and preset["preset_id"]
    ]
    if len({preset["preset_id"] for preset in approved}) != len(approved):
        raise EffectPolicyError("DUPLICATE_EFFECT_PRESET_ID")
    return approved


def select_effect(*, pool: dict, episode_id: str, segment_id: str) -> dict:
    if pool.get("schema_version") != "effect-pool-v1":
        raise EffectPolicyError("EFFECT_POOL_SCHEMA")
    version = pool.get("preset_pool_version")
    lane = pool.get("lane")
    policy = pool.get("policy")
    if not all(isinstance(value, str) and value for value in (version, lane, policy)):
        raise EffectPolicyError("EFFECT_POOL_IDENTITY_REQUIRED")
    if policy == "NONE":
        return {
            "status": "NONE",
            "preset_id": None,
            "preset_pool_version": version,
        }
    if policy == "EXPLICIT_ONLY":
        return {
            "status": "WAIT_EXPLICIT_EFFECT_SELECTION",
            "preset_id": None,
            "preset_pool_version": version,
        }
    if (
        lane == "politics_longform"
        and policy == "SELECT_FROM_POOL"
        and pool.get("conservative") is not True
    ):
        raise EffectPolicyError("POLITICS_EFFECT_POOL_MUST_BE_CONSERVATIVE")
    approved = _approved_presets(pool)
    if policy == "LOCKED":
        locked_id = pool.get("locked_preset_id")
        if locked_id not in {preset["preset_id"] for preset in approved}:
            raise EffectPolicyError("LOCKED_EFFECT_NOT_APPROVED")
        selected = next(preset for preset in approved if preset["preset_id"] == locked_id)
    elif policy == "SELECT_FROM_POOL":
        if not approved:
            raise EffectPolicyError("NO_APPROVED_EFFECT_PRESETS")
        seed_material = f"{episode_id}{segment_id}{version}"
        digest = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
        selected = approved[int(digest, 16) % len(approved)]
    else:
        raise EffectPolicyError("UNKNOWN_EFFECT_POLICY")
    seed_material = f"{episode_id}{segment_id}{version}"
    return {
        "status": "SELECTED",
        "preset_id": selected["preset_id"],
        "preset_pool_version": version,
        "lane": lane,
        "seed_material": seed_material,
        "seed_sha256": hashlib.sha256(seed_material.encode("utf-8")).hexdigest().upper(),
    }
