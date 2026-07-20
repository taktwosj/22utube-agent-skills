"""Prompt Factory + analysis cache contracts.

V2 design sections 30-34, 44.3:

- External AI prompts are built from versioned templates (never hand-assembled).
- Gemini / external analysis is OPTIONAL input. Local source is primary
  evidence. If external analysis conflicts with local, raise
  EXTERNAL_ANALYSIS_MISMATCH and do NOT silently adopt the external result.
- Analysis cache: same source is not re-analyzed. Cache key is
  content-addressed (source SHA + duration + resolution + selected range +
  profile version + tool versions + sampling policy). Only the affected
  layer invalidates on partial input change.
- Prompt manifest records template path/SHA, input paths/SHAs, included
  segment IDs, excluded fields, packet SHA. The same content-addressed key
  reuses the same packet.
- The shared language quality contract + shared external authority contract
  are appended to every external prompt packet.

The factory performs NO external calls and uses NO LLM (deterministic only,
section 44.2).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


PROMPT_MANIFEST_SCHEMA_VERSION = "prompt-packet-manifest-v1"
ANALYSIS_CACHE_SCHEMA_VERSION = "analysis-cache-manifest-v1"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


# ---------------------------------------------------------------------------
# Prompt Factory
# ---------------------------------------------------------------------------


def _content_address_key(
    *,
    template_sha256: str,
    input_artifacts: list[dict],
    included_segment_ids: list[str],
    excluded_fields: list[str],
    language_quality_contract_sha: str,
    external_authority_contract_sha: str,
) -> str:
    """Stable content-addressed key for prompt-packet reuse."""
    payload = json.dumps(
        {
            "template_sha256": template_sha256,
            "input_artifacts": [
                {"path": a["path"], "sha256": a["sha256"]} for a in input_artifacts
            ],
            "included_segment_ids": list(included_segment_ids),
            "excluded_fields": sorted(excluded_fields),
            "language_quality_contract_sha256": language_quality_contract_sha,
            "external_authority_contract_sha256": external_authority_contract_sha,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return _sha256_text(payload)


def build_prompt(
    *,
    template_path: str,
    template_text: str,
    inputs: list[dict],
    included_segment_ids: list[str],
    excluded_fields: list[str],
    language_quality_contract: str,
    external_authority_contract: str,
) -> dict:
    """Build an external prompt packet + manifest.

    inputs: list of {path, content} dicts. Content may be str or bytes.
    The packet body is deterministic: template, then inputs in given order,
    then the shared contracts appended.

    The manifest records the content-addressed packet SHA so callers can
    reuse the same packet when the key matches.
    """
    if not isinstance(template_text, str):
        raise TypeError("template_text must be str")
    template_sha = _sha256_text(template_text)

    input_artifacts: list[dict] = []
    input_bodies: list[str] = []
    for inp in inputs:
        path = inp["path"]
        content = inp["content"]
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        elif isinstance(content, (bytes, bytearray)):
            content_bytes = bytes(content)
        else:
            raise TypeError(f"input content must be str or bytes: {path}")
        sha = _sha256_bytes(content_bytes)
        input_artifacts.append({"path": path, "sha256": sha})
        input_bodies.append(
            f"--- INPUT: {path} (sha256={sha}) ---\n{content_bytes.decode('utf-8', errors='replace')}"
        )

    lq_text = ""
    lq_sha = ""
    if language_quality_contract:
        try:
            from pathlib import Path

            lq_text = Path(language_quality_contract).read_text(encoding="utf-8")
            lq_sha = _sha256_text(lq_text)
        except OSError:
            lq_text = ""
            lq_sha = ""

    ea_text = ""
    ea_sha = ""
    if external_authority_contract:
        try:
            from pathlib import Path

            ea_text = Path(external_authority_contract).read_text(encoding="utf-8")
            ea_sha = _sha256_text(ea_text)
        except OSError:
            ea_text = ""
            ea_sha = ""

    # Compose the packet in a fixed order.
    parts: list[str] = []
    parts.append("# External Prompt Packet")
    parts.append("")
    parts.append(f"<!-- template_path: {template_path} -->")
    parts.append(f"<!-- template_sha256: {template_sha} -->")
    parts.append("")
    parts.append("## Template")
    parts.append("")
    parts.append(template_text.strip())
    parts.append("")
    if included_segment_ids:
        parts.append("## Included Segment IDs")
        parts.append("")
        for sid in included_segment_ids:
            parts.append(f"- {sid}")
        parts.append("")
    if excluded_fields:
        parts.append("## Excluded Fields (do not surface to external model)")
        parts.append("")
        for f in excluded_fields:
            parts.append(f"- {f}")
        parts.append("")
    parts.append("## Inputs")
    parts.append("")
    parts.extend(input_bodies)
    parts.append("")
    if lq_text:
        parts.append("## Shared Language Quality Contract")
        parts.append("")
        parts.append(lq_text.strip())
        parts.append("")
    if ea_text:
        parts.append("## Shared External Authority Contract")
        parts.append("")
        parts.append(ea_text.strip())
        parts.append("")

    packet_text = "\n".join(parts)
    packet_sha = _sha256_text(packet_text)

    content_key = _content_address_key(
        template_sha256=template_sha,
        input_artifacts=input_artifacts,
        included_segment_ids=included_segment_ids,
        excluded_fields=excluded_fields,
        language_quality_contract_sha=lq_sha,
        external_authority_contract_sha=ea_sha,
    )

    manifest = {
        "schema_version": PROMPT_MANIFEST_SCHEMA_VERSION,
        "template_path": template_path,
        "template_sha256": template_sha,
        "language_quality_contract_path": language_quality_contract or None,
        "language_quality_contract_sha256": lq_sha or None,
        "external_authority_contract_path": external_authority_contract or None,
        "external_authority_contract_sha256": ea_sha or None,
        "input_artifacts": input_artifacts,
        "included_segment_ids": list(included_segment_ids),
        "excluded_fields": list(excluded_fields),
        "content_addressed_key": content_key,
        "packet_sha256": packet_sha,
        "packet_text": packet_text,
    }
    return {"packet_text": packet_text, "manifest": manifest}


# ---------------------------------------------------------------------------
# Analysis cache
# ---------------------------------------------------------------------------


@dataclass
class _LayerInputs:
    """Which upstream inputs each cache layer depends on. Used by the
    invalidation planner to invalidate only the affected layer."""

    transcript_segments: tuple[str, ...] = ("source_sha256",)
    ocr_segments: tuple[str, ...] = ("source_sha256", "tool_versions.ocr")
    scene_segments: tuple[str, ...] = (
        "source_sha256",
        "tool_versions.scene",
        "sampling_policy.frame_sample_fps",
    )
    motion_segments: tuple[str, ...] = (
        "source_sha256",
        "tool_versions.scene",
        "sampling_policy.frame_sample_fps",
    )
    speaker_segments: tuple[str, ...] = ("source_sha256",)
    audio_event_segments: tuple[str, ...] = ("source_sha256",)


_LAYER_DEPS = _LayerInputs()


def _layer_depends_on(layer_name: str) -> tuple[str, ...]:
    return getattr(_LAYER_DEPS, layer_name, ("source_sha256",))


def _cache_key_payload(
    *,
    source_sha256: str,
    duration_us: int,
    resolution: str,
    selected_range: dict,
    profile_version: str,
    tool_versions: dict,
    sampling_policy: dict,
) -> str:
    return json.dumps(
        {
            "source_sha256": source_sha256,
            "duration_us": duration_us,
            "resolution": resolution,
            "selected_range": selected_range,
            "profile_version": profile_version,
            "tool_versions": tool_versions,
            "sampling_policy": sampling_policy,
        },
        sort_keys=True,
        ensure_ascii=False,
    )


def build_analysis_cache_manifest(
    *,
    source_sha256: str,
    duration_us: int,
    resolution: str,
    selected_range: dict,
    profile_version: str,
    tool_versions: dict,
    sampling_policy: dict,
    layers: dict,
    external_analysis: dict | None = None,
) -> dict:
    """Build an analysis-cache manifest.

    external_analysis, when provided, is treated as optional supplementary
    input. If it disagrees with local primary evidence on a tracked hash
    (e.g. transcript_sha256), the manifest records
    external_analysis_status=EXTERNAL_ANALYSIS_MISMATCH and does NOT adopt
    the external result.
    """
    if not isinstance(layers, dict) or not layers:
        raise ValueError("ANALYSIS_CACHE_EMPTY_LAYERS")
    for layer_name, layer in layers.items():
        if "sha256" not in layer:
            raise ValueError(f"ANALYSIS_CACHE_LAYER_MISSING_SHA: {layer_name}")

    key = _sha256_text(
        _cache_key_payload(
            source_sha256=source_sha256,
            duration_us=duration_us,
            resolution=resolution,
            selected_range=selected_range,
            profile_version=profile_version,
            tool_versions=tool_versions,
            sampling_policy=sampling_policy,
        )
    )

    external_status = "NOT_PROVIDED"
    if external_analysis is not None:
        # Compare any tracked hash the external result claims against the
        # local layer hash of the same name.
        external_status = "ACCEPTED_SUPPLEMENTARY"
        for ext_key, local_layer in (
            ("transcript_sha256", "transcript_segments"),
            ("ocr_sha256", "ocr_segments"),
            ("scene_sha256", "scene_segments"),
        ):
            if ext_key in external_analysis and local_layer in layers:
                if external_analysis[ext_key] != layers[local_layer]["sha256"]:
                    external_status = "EXTERNAL_ANALYSIS_MISMATCH"
                    break

    return {
        "schema_version": ANALYSIS_CACHE_SCHEMA_VERSION,
        "cache_key_sha256": key,
        "source_sha256": source_sha256,
        "duration_us": duration_us,
        "resolution": resolution,
        "selected_range": selected_range,
        "profile_version": profile_version,
        "tool_versions": dict(tool_versions),
        "sampling_policy": dict(sampling_policy),
        "layers": dict(layers),
        "external_analysis": external_analysis,
        "external_analysis_status": external_status,
    }


def plan_cache_invalidation(
    *,
    current_manifest: dict,
    new_inputs: dict,
) -> dict:
    """Decide which layers to invalidate when inputs change.

    Rule:
    - source_sha256 change => invalidate every layer (full rebuild).
    - tool_versions.<x> change => invalidate layers depending on tool <x>.
    - sampling_policy change => invalidate layers depending on sampling.
    """
    current_source = current_manifest.get("source_sha256")
    new_source = new_inputs.get("source_sha256")
    if current_source != new_source:
        return {
            "invalidate": sorted(current_manifest.get("layers", {}).keys()),
            "reason": "SOURCE_SHA256_CHANGED",
        }

    invalidate: set[str] = set()
    current_tools = current_manifest.get("tool_versions", {})
    new_tools = new_inputs.get("tool_versions", {})
    current_sampling = current_manifest.get("sampling_policy", {})
    new_sampling = new_inputs.get("sampling_policy", {})

    sampling_changed = current_sampling != new_sampling

    for layer_name in current_manifest.get("layers", {}).keys():
        deps = _layer_depends_on(layer_name)
        for dep in deps:
            if dep == "source_sha256":
                continue
            if dep.startswith("tool_versions."):
                tool_key = dep.split(".", 1)[1]
                if current_tools.get(tool_key) != new_tools.get(tool_key):
                    invalidate.add(layer_name)
                    break
            elif dep.startswith("sampling_policy."):
                if sampling_changed:
                    invalidate.add(layer_name)
                    break

    return {
        "invalidate": sorted(invalidate),
        "reason": "PARTIAL_INVALIDATION",
    }
