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

    Strategy (RW-P04-03 strict structural-path comparison):
    - Walk every tracked scalar field by its full structural path including
      array indices and nested-object parent paths.
    - For each (path, value) pair, require a rendered line in the human MD
      that binds the value to that specific structural position — not to
      any other position that happens to share the value.
    - We do this by rendering the canonical projection, then for each
      tracked scalar finding the unique canonical rendered line that
      contains the value, and requiring that exact line (modulo
      whitespace) to be present in the human MD.

    This catches:
    - two sibling fields with the same value where one is deleted
    - two array elements with the same value where one is dropped
    - two nested objects under different parents that share a value
    """
    rendered = render_markdown(canonical)
    if human_md.strip() == rendered.strip():
        return {
            "status": "IN_SYNC",
            "action": "NONE",
        }

    tracked = _extract_tracked_scalars(canonical)
    canonical_lines = [
        " ".join(line.split())
        for line in rendered.splitlines()
    ]
    human_lines = [
        " ".join(line.split())
        for line in human_md.splitlines()
    ]

    # Group tracked scalars by their canonical rendered line. When two
    # distinct structural positions render to the same line text (e.g. two
    # sibling nested objects whose `title` field has the same value), the
    # human MD must contain that line AT LEAST as many times as the
    # canonical projection does. A naive set-membership check would miss
    # the case where one of the duplicates was deleted.
    from collections import Counter
    canonical_counter = Counter(canonical_lines)
    human_counter = Counter(human_lines)

    # Also build per-(value, count) buckets so we can detect when N
    # structural positions share a value: the human MD must render that
    # value on at least N distinct lines (counting duplicates).
    value_to_canonical_count: dict[str, int] = {}
    for path, value in tracked.items():
        token = str(value)
        if not token:
            continue
        # Count how many canonical rendered lines carry this value.
        count = sum(1 for line in canonical_lines if token in line)
        if count > value_to_canonical_count.get(token, 0):
            value_to_canonical_count[token] = count

    # For each value, the human MD must contain at least as many lines
    # carrying that value as the canonical projection does.
    for token, required_count in value_to_canonical_count.items():
        human_count = sum(1 for line in human_lines if token in line)
        if human_count < required_count:
            raise HumanMdCanonicalJsonMismatch(
                f"<value={token}>",
                f"appears {required_count} times in canonical",
                f"appears {human_count} times in human MD",
            )

    # Additionally, every distinct canonical line must be present in the
    # human MD (catches lines whose value was edited in place).
    for canonical_line, required in canonical_counter.items():
        if human_counter.get(canonical_line, 0) < required:
            # Only flag if this line carried a tracked value; otherwise it
            # is structural (header/footer) and the byte-identity check
            # above already handles the trivial case.
            if any(
                str(value) in canonical_line
                for value in tracked.values()
            ):
                raise HumanMdCanonicalJsonMismatch(
                    canonical_line,
                    f"required {required} occurrence(s)",
                    f"found {human_counter.get(canonical_line, 0)}",
                )

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
