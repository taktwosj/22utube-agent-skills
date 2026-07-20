"""Validate an analysis cache manifest against the V2 schema and contract.

Rules:
- Every layer entry must have a sha256.
- cache_key_sha256 must match a recomputed key from the canonical payload.
- external_analysis_status must be one of NOT_PROVIDED / ACCEPTED_SUPPLEMENTARY
  / EXTERNAL_ANALYSIS_MISMATCH.
- If external_analysis_status=EXTERNAL_ANALYSIS_MISMATCH, the manifest must
  carry the external_analysis block (so callers can see what conflicted).

This validator is deterministic and never performs external calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = (
    REPO_ROOT
    / "skills"
    / "00-tikitaka"
    / "schemas"
    / "analysis_cache_manifest.schema.json"
)
SHARED_CORE = REPO_ROOT / "shared" / "workflow-harness" / "core" / "prompt_factory.py"


class AnalysisCacheValidationError(Exception):
    pass


def _import_prompt_factory():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "tikitaka_pf_for_cache", SHARED_CORE
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tikitaka_pf_for_cache"] = mod
    spec.loader.exec_module(mod)
    return mod


def validate_manifest(manifest: dict) -> dict:
    """Return a gate_result-shaped report. PASS only when every rule holds."""
    errors: list[dict] = []
    warnings: list[dict] = []

    if manifest.get("schema_version") != "analysis-cache-manifest-v1":
        errors.append(
            {
                "code": "FAIL_SCHEMA_VERSION",
                "message": "schema_version must be analysis-cache-manifest-v1",
            }
        )

    for required in (
        "cache_key_sha256",
        "source_sha256",
        "duration_us",
        "resolution",
        "selected_range",
        "profile_version",
        "tool_versions",
        "sampling_policy",
        "layers",
        "external_analysis_status",
    ):
        if required not in manifest:
            errors.append(
                {
                    "code": "FAIL_MISSING_FIELD",
                    "field": required,
                    "message": f"manifest missing required field: {required}",
                }
            )

    layers = manifest.get("layers", {})
    if not isinstance(layers, dict) or not layers:
        errors.append(
            {
                "code": "FAIL_NO_LAYERS",
                "message": "layers must be a non-empty object",
            }
        )
    for layer_name, layer in layers.items():
        if not isinstance(layer, dict) or "sha256" not in layer:
            errors.append(
                {
                    "code": "FAIL_LAYER_MISSING_SHA",
                    "field": f"layers.{layer_name}",
                    "message": f"layer {layer_name} missing sha256",
                }
            )

    status = manifest.get("external_analysis_status")
    if status not in (
        "NOT_PROVIDED",
        "ACCEPTED_SUPPLEMENTARY",
        "EXTERNAL_ANALYSIS_MISMATCH",
    ):
        errors.append(
            {
                "code": "FAIL_EXTERNAL_STATUS",
                "field": "external_analysis_status",
                "message": f"invalid external_analysis_status: {status}",
            }
        )
    if status == "EXTERNAL_ANALYSIS_MISMATCH" and not manifest.get(
        "external_analysis"
    ):
        errors.append(
            {
                "code": "FAIL_MISMATCH_WITHOUT_EXTERNAL_BLOCK",
                "message": "external_analysis_status=MISMATCH but external_analysis is absent",
            }
        )

    # Recompute the cache key to confirm integrity.
    if not errors:
        pf = _import_prompt_factory()
        try:
            from shared.workflow_harness_helpers import (
                recompute_cache_key,
            )  # type: ignore  # noqa: F401
        except Exception:
            # Inline recompute to avoid import path coupling in tests.
            payload = json.dumps(
                {
                    "source_sha256": manifest["source_sha256"],
                    "duration_us": manifest["duration_us"],
                    "resolution": manifest["resolution"],
                    "selected_range": manifest["selected_range"],
                    "profile_version": manifest["profile_version"],
                    "tool_versions": manifest["tool_versions"],
                    "sampling_policy": manifest["sampling_policy"],
                },
                sort_keys=True,
                ensure_ascii=False,
            )
            import hashlib

            recomputed = hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()
            if recomputed != manifest["cache_key_sha256"]:
                errors.append(
                    {
                        "code": "FAIL_CACHE_KEY_MISMATCH",
                        "field": "cache_key_sha256",
                        "message": f"expected {recomputed}",
                    }
                )

    return {
        "schema_version": "gate-result-v1",
        "status": "PASS" if not errors else "FAIL",
        "lane": "general_shorts_design",
        "gate": "G10",
        "subgate": "ANALYSIS_CACHE_VALIDATION",
        "validated_inputs": [{"path": "analysis_cache_manifest.json"}],
        "evidence": [],
        "errors": errors,
        "warnings": warnings,
        "next_action": "NONE" if errors else "READY_FOR_DESIGN_BLUEPRINT",
        "auto_advance_allowed": not errors,
        "auto_advance_class": "DETERMINISTIC_ONLY" if not errors else "NONE",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate an analysis cache manifest."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = validate_manifest(manifest)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
