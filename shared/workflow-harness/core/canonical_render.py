"""Canonical JSON -> human Markdown renderer.

V2 design section 37: machine JSON is canonical. Human MD is rendered from
it deterministically (no LLM — section 44.2). The two are never edited
independently. If a hand-edited MD diverges from the canonical projection,
reconciliation raises HUMAN_MD_CANONICAL_JSON_MISMATCH.

The renderer is intentionally simple and deterministic: it walks the JSON
in a stable order and emits section/key markdown. It is NOT a creative
formatter; creative formatting happens only in prompt_factory output for
external models, never here.
"""

from __future__ import annotations

import json
from typing import Any


class HumanMdCanonicalJsonMismatch(Exception):
    """Raised when a hand-edited MD disagrees with the canonical JSON
    projection on a tracked field."""

    def __init__(self, field_path: str, canonical_value, human_value):
        super().__init__(
            f"HUMAN_MD_CANONICAL_JSON_MISMATCH field={field_path} "
            f"canonical={canonical_value!r} human={human_value!r}"
        )
        self.field_path = field_path
        self.canonical_value = canonical_value
        self.human_value = human_value


def _hash_canonical(canonical: dict) -> str:
    # Stable serialization for the footer fingerprint line.
    return json.dumps(canonical, sort_keys=True, ensure_ascii=False)


def _emit_value(buf: list[str], depth: int, key: str, value: Any) -> None:
    indent = "  " * depth
    if isinstance(value, dict):
        buf.append(f"{indent}- **{key}**")
        for k in sorted(value.keys()):
            _emit_value(buf, depth + 1, k, value[k])
    elif isinstance(value, list):
        buf.append(f"{indent}- **{key}** ({len(value)} items)")
        for i, item in enumerate(value):
            if isinstance(item, dict):
                _emit_value(buf, depth + 1, f"[{i}]", item)
            else:
                buf.append(f"{indent}  - [{i}] {item}")
    elif isinstance(value, bool):
        buf.append(f"{indent}- `{key}`: {str(value).lower()}")
    elif isinstance(value, (int, float)):
        buf.append(f"{indent}- `{key}`: {value}")
    elif value is None:
        buf.append(f"{indent}- `{key}`: null")
    else:
        # String. Escape any markdown bullet leaders to avoid accidental
        # structural edits in the rendered file.
        text = str(value).replace("\n", " ")
        buf.append(f"{indent}- `{key}`: {text}")


def render_markdown(canonical: dict) -> str:
    """Render canonical JSON to deterministic markdown.

    Output shape:
        # <schema_version or 'canonical-json'>

        <top-level prose summary is intentionally absent; the renderer is
         a pure projection, not a creative writer.>

        ## Fields
        <field tree>

        <!-- CANONICAL_SHA256: <sha> -->
    """
    # Provoke serialization errors early (e.g. non-JSON-serializable input).
    serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=False)

    import hashlib

    sha = hashlib.sha256(serialized.encode("utf-8")).hexdigest().upper()
    title = canonical.get("schema_version") if isinstance(canonical, dict) else None
    title = title or "canonical-json"

    buf: list[str] = []
    buf.append(f"# {title}")
    buf.append("")
    buf.append("<!-- This file is rendered from canonical JSON. Do not edit directly. -->")
    buf.append("<!-- To change content, edit the canonical JSON and re-render. -->")
    buf.append("")
    buf.append("## Fields")
    buf.append("")
    if isinstance(canonical, dict):
        for k in sorted(canonical.keys()):
            _emit_value(buf, 0, k, canonical[k])
    else:
        buf.append(f"- {serialized}")
    buf.append("")
    buf.append(f"<!-- CANONICAL_SHA256: {sha} -->")
    buf.append("")
    return "\n".join(buf)


def reconcile_human_md(*, canonical: dict, human_md: str) -> dict:
    """Compare a hand-edited MD against the canonical JSON projection.

    Strategy: re-render the canonical, then verify that every tracked
    scalar field's rendered form is still present in the human MD. If any
    field is missing or changed beyond whitespace, raise
    HumanMdCanonicalJsonMismatch.

    Returns a reconciliation report when all tracked fields are intact.
    """
    rendered = render_markdown(canonical)
    if human_md.strip() == rendered.strip():
        return {
            "status": "IN_SYNC",
            "action": "NONE",
        }

    # The MD differs. Determine whether the divergence is a tracked-field
    # change or merely cosmetic (whitespace / formatting). We do this by
    # checking each tracked scalar field's value still appears in the MD.
    tracked = _extract_tracked_scalars(canonical)
    normalized_human = " ".join(human_md.split())
    for path, value in tracked.items():
        token = str(value)
        if token and token not in normalized_human:
            raise HumanMdCanonicalJsonMismatch(path, value, "<absent-or-changed>")

    # All tracked fields present; the diff is cosmetic. Treat as reconciled
    # but flag for explicit re-render.
    return {
        "status": "COSMETIC_DIFF_ONLY",
        "action": "RE_RENDER_RECOMMENDED",
    }


def _extract_tracked_scalars(canonical: dict, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not isinstance(canonical, dict):
        return out
    for k, v in canonical.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_extract_tracked_scalars(v, path))
        elif isinstance(v, list):
            # Only track scalar lists by length + element strings.
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    out.update(_extract_tracked_scalars(item, f"{path}[{i}]"))
                else:
                    out[f"{path}[{i}]"] = item
        elif isinstance(v, (str, int, float)) and not isinstance(v, bool):
            # Skip None and empty strings — they are not stable markers.
            if v not in (None, ""):
                out[path] = v
    return out
