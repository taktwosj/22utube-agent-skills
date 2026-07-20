"""Context manifest writer.

Every model call must write a context manifest recording:
- loaded files (path + sha)
- excluded files / categories (negative context)
- estimated_input_tokens (always) and provider_input_tokens (when available)
- unrelated_lane_reads (must be 0)
- legacy_reads (0 unless contract_mode=LEGACY_COMPAT)
- full_srt_injected (False by default)
- status

NORM-007: provider_input_tokens is recorded when available; when not, it is
null and estimated_input_tokens + estimator_version are recorded instead.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


SCHEMA_VERSION = "context-manifest-v1"

DEFAULT_ESTIMATOR_VERSION = "chars_div_4_v1"


@dataclass
class ContextManifest:
    lane: str
    gate: str
    subgate: str | None
    run_id: str
    loaded_files: list[dict] = field(default_factory=list)
    excluded_by_policy: list[str] = field(default_factory=list)
    provider_input_tokens: int | None = None
    estimated_input_tokens: int | None = None
    estimator_version: str = DEFAULT_ESTIMATOR_VERSION
    unrelated_lane_reads: int = 0
    legacy_reads: int = 0
    full_srt_injected: bool = False
    contract_mode: str = "V2_CANONICAL"
    status: str = "PASS"

    def add_loaded_file(self, path: str, content: bytes | str | None = None) -> None:
        entry = {"path": path}
        if content is not None:
            if isinstance(content, str):
                content = content.encode("utf-8")
            entry["sha256"] = hashlib.sha256(content).hexdigest().upper()
            entry["chars"] = len(content)
        self.loaded_files.append(entry)

    def add_excluded(self, category: str) -> None:
        if category not in self.excluded_by_policy:
            self.excluded_by_policy.append(category)

    def set_estimated_tokens_from_chars(self, total_chars: int) -> None:
        # Simple deterministic estimator; production may override.
        self.estimated_input_tokens = max(0, total_chars // 4)
        self.estimator_version = DEFAULT_ESTIMATOR_VERSION

    def to_dict(self) -> dict:
        if self.provider_input_tokens is None and self.estimated_input_tokens is None:
            raise ValueError(
                "CONTEXT_MANIFEST_MISSING_TOKENS: set provider_input_tokens "
                "or estimated_input_tokens"
            )
        return {
            "schema_version": SCHEMA_VERSION,
            "lane": self.lane,
            "gate": self.gate,
            "subgate": self.subgate,
            "run_id": self.run_id,
            "loaded_files": list(self.loaded_files),
            "excluded_by_policy": list(self.excluded_by_policy),
            "provider_input_tokens": self.provider_input_tokens,
            "estimated_input_tokens": self.estimated_input_tokens,
            "estimator_version": self.estimator_version
            if self.provider_input_tokens is None
            else None,
            "unrelated_lane_reads": self.unrelated_lane_reads,
            "legacy_reads": self.legacy_reads,
            "full_srt_injected": self.full_srt_injected,
            "contract_mode": self.contract_mode,
            "status": self.status,
        }
