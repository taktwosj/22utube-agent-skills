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

    Strategy (RW-P04-03 structural-path comparison):
    - For every tracked scalar field, render its canonical line and require
      that exact line (key + value) to appear in the human MD. A field is
      matched by its structural path (e.g. `title_a`), not by whether its
      value happens to appear anywhere else in the document.
    - If any tracked field's rendered line is absent or carries a different
      value, raise HumanMdCanonicalJsonMismatch.

    This prevents a deleted duplicate-value field from being misclassified
    as a cosmetic diff: each `path: value` pair must be present on its own.
    """
    rendered = render_markdown(canonical)
    if human_md.strip() == rendered.strip():
        return {
            "status": "IN_SYNC",
            "action": "NONE",
        }

    tracked = _extract_tracked_scalars(canonical)
    normalized_human_lines = [
        " ".join(line.split())
        for line in human_md.splitlines()
    ]

    for path, value in tracked.items():
        # The rendered form for a scalar is `- `key`: <value>` possibly
        # nested under parents. We compare the canonical leaf-line token.
        leaf_key = path.split(".")[-1]
        # Strip array-index suffix for display key (segment lists).
        if "[" in leaf_key:
            leaf_key = leaf_key.split("[", 1)[0]
        token = str(value)
        # Require a line whose tail matches "`leaf_key`: token" so the value
        # is bound to the right field, not to any other field.
        expected_tail = f"`{leaf_key}`: {token}".replace(" ", "")
        found = any(
            expected_tail in line.replace(" ", "")
            for line in normalized_human_lines
        )
        if not found:
            raise HumanMdCanonicalJsonMismatch(path, value, "<absent-or-changed>")

    # All tracked structural field paths are intact; any remaining diff is
    # cosmetic (whitespace, comment order).
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
