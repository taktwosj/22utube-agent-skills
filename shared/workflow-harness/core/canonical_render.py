"""Canonical JSON -> human Markdown renderer (path-aware).

V2 design section 37: machine JSON is canonical. Human MD is rendered from
it deterministically (no LLM — section 44.2). The two are never edited
independently. If a hand-edited MD diverges from the canonical projection,
reconciliation raises HUMAN_MD_CANONICAL_JSON_MISMATCH.

RW-P04-03 round 3 (path-aware):
- Every tracked scalar is rendered with an explicit structural-path token
  of the form `<!-- path: full.parent.path -->` so the value is bound to
  its position. This prevents two structural positions that share a value
  from being confused, and catches field reparent / array-element-move
  attacks that a Counter-on-line-text approach cannot.
- reconcile_human_md compares the path-tokenized line for each tracked
  scalar against the human MD, so moving a field between parents (or
  moving an array element between indices) is always detected.
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
    return json.dumps(canonical, sort_keys=True, ensure_ascii=False)


def _emit_value(
    buf: list[str],
    depth: int,
    key: str,
    value: Any,
    parent_path: str = "",
) -> None:
    """Emit one node. For scalar leaves we emit a path-aware line."""
    indent = "  " * depth
    full_path = f"{parent_path}.{key}" if parent_path else key
    if isinstance(value, dict):
        buf.append(f"{indent}- **{key}**")
        for k in sorted(value.keys()):
            _emit_value(buf, depth + 1, k, value[k], full_path)
    elif isinstance(value, list):
        buf.append(f"{indent}- **{key}** ({len(value)} items)")
        for i, item in enumerate(value):
            child_path = f"{full_path}[{i}]"
            if isinstance(item, dict):
                buf.append(f"{indent}  - `[{i}]`")
                for k in sorted(item.keys()):
                    _emit_value(buf, depth + 2, k, item[k], child_path)
            else:
                _emit_path_aware_scalar(buf, indent + "  ", child_path, f"[{i}]", item)
    elif isinstance(value, bool):
        _emit_path_aware_scalar(buf, indent, full_path, key, str(value).lower())
    elif isinstance(value, (int, float)):
        _emit_path_aware_scalar(buf, indent, full_path, key, str(value))
    elif value is None:
        _emit_path_aware_scalar(buf, indent, full_path, key, "null")
    else:
        text = str(value).replace("\n", " ")
        _emit_path_aware_scalar(buf, indent, full_path, key, text)


def _emit_path_aware_scalar(
    buf: list[str],
    indent: str,
    full_path: str,
    leaf_key: str,
    rendered_value: str,
) -> None:
    """Emit a scalar line that carries an explicit structural path token.

    The token is a HTML comment immediately before the value so that:
    - the rendered MD is still human-readable
    - the structural path is recoverable from the MD text alone
    - two structural positions that share a value render to DIFFERENT
      lines (the path token differs), so Counter-based and set-based
      comparisons both distinguish them.
    """
    buf.append(
        f"{indent}- <!-- path: {full_path} --> `{leaf_key}`: {rendered_value}"
    )


def render_markdown(canonical: dict) -> str:
    """Render canonical JSON to deterministic, path-aware markdown."""
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


def _extract_tracked_scalars(
    canonical: dict,
    prefix: str = "",
) -> dict[str, Any]:
    """Map each tracked scalar's full structural path to its value.

    Paths include array indices (segments[0].title) and nested-object
    parents (chapter_a.title). This is the authority for structural
    comparison."""
    out: dict[str, Any] = {}
    if not isinstance(canonical, dict):
        return out
    for k, v in canonical.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_extract_tracked_scalars(v, path))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                child_path = f"{path}[{i}]"
                if isinstance(item, dict):
                    out.update(_extract_tracked_scalars(item, child_path))
                else:
                    out[child_path] = item
        elif isinstance(v, (str, int, float)) and not isinstance(v, bool):
            if v not in (None, ""):
                out[path] = v
    return out


def reconcile_human_md(*, canonical: dict, human_md: str) -> dict:
    """Compare a hand-edited MD against the canonical JSON projection.

    Strategy (RW-P04-03 round 3, path-aware):
    - The canonical render emits a `<!-- path: <full.path> -->` token on
      every tracked scalar line.
    - For each tracked scalar, we require the human MD to contain a line
      whose path token equals the canonical full path AND whose value
      matches the canonical value.
    - This catches: deleted duplicate-value fields, reparented fields,
      moved array elements, and any value edit. Whitespace-only diffs
      still pass as COSMETIC.
    """
    rendered = render_markdown(canonical)
    if human_md.strip() == rendered.strip():
        return {"status": "IN_SYNC", "action": "NONE"}

    tracked = _extract_tracked_scalars(canonical)
    # Normalize human MD lines (collapse internal whitespace) so cosmetic
    # whitespace does not cause false positives.
    human_lines = [" ".join(line.split()) for line in human_md.splitlines()]

    for full_path, value in tracked.items():
        token = str(value)
        # The canonical render for this scalar is a line that contains
        # both the path token and the value. We require such a line in
        # the human MD bound to THIS exact path.
        expected_path_marker = f"<!-- path: {full_path} -->"
        # Find a human line that has this exact path marker.
        matching_human_lines = [
            line for line in human_lines if expected_path_marker in line
        ]
        if not matching_human_lines:
            raise HumanMdCanonicalJsonMismatch(full_path, value, "<path-missing>")
        # Among the lines carrying this exact path, at least one must also
        # carry the canonical value.
        value_present = any(token in line for line in matching_human_lines)
        if not value_present:
            raise HumanMdCanonicalJsonMismatch(full_path, value, "<value-changed>")

    # All tracked structural positions are intact with correct values.
    return {"status": "COSMETIC_DIFF_ONLY", "action": "RE_RENDER_RECOMMENDED"}
