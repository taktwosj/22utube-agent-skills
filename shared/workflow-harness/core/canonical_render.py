"""Canonical JSON -> human Markdown renderer with structural reconciliation.

V2 design section 37: machine JSON is canonical. Human MD is rendered from
it deterministically (no LLM — section 44.2). The two are never edited
independently. If a hand-edited MD diverges from the canonical projection,
reconciliation raises HUMAN_MD_CANONICAL_JSON_MISMATCH.

RW-P04-03 round 4 (structural record comparison):
- render_markdown emits one normalized record line per tracked scalar:
  ``path:parent.parent.leaf = value``. The full parent chain and array
  index are part of the path, so two structural positions that share a
  value always render to distinct records.
- reconcile_human_md parses the canonical and the human MD into the same
  ``{(path, value)}`` set and compares them exactly. It is NOT a substring
  test. The path is bound to the record it appears on; reparenting,
  array-element moves, value edits, bool/null deletion, and container
  reshapes are all detected because the parsed record set differs.

Cosmetic whitespace, blank lines, and comment edits never affect the
parsed set, so genuine cosmetic diffs still return COSMETIC_DIFF_ONLY.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


class HumanMdCanonicalJsonMismatch(Exception):
    """Raised when a hand-edited MD disagrees with the canonical JSON
    projection."""

    def __init__(self, kind: str, detail: str):
        super().__init__(f"HUMAN_MD_CANONICAL_JSON_MISMATCH kind={kind} {detail}")
        self.kind = kind
        self.detail = detail


# Path-record line format. The "P " prefix + " = " + value uniquely
# identifies a structural record. The prefix avoids ambiguity with prose.
# Example:  P path:chapter_a.title = SAME
_PATH_RECORD_RE = re.compile(r"^P\s+path:(?P<path>\S+)\s+=\s+(?P<value>.*)$")


def _hash_canonical(canonical: dict) -> str:
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest().upper()


def _collect_path_records(
    value: Any,
    path: str = "",
) -> list[tuple[str, str]]:
    """Walk canonical recursively and return (path, normalized_value) tuples
    for every scalar leaf and every array index position.

    Containers (dict / non-empty list) produce no record of their own but
    their children carry the parent path. Empty containers are recorded
    explicitly so adding/removing them is detectable."""
    out: list[tuple[str, str]] = []
    if isinstance(value, dict):
        if not value:
            # Empty container — record explicitly so deletion is detectable.
            out.append((path or "<root>", "<empty-object>"))
            return out
        for k in sorted(value.keys()):
            child_path = f"{path}.{k}" if path else k
            out.extend(_collect_path_records(value[k], child_path))
        return out
    if isinstance(value, list):
        if not value:
            out.append((path or "<root>", "<empty-list>"))
            return out
        for i, item in enumerate(value):
            child_path = f"{path}[{i}]"
            out.extend(_collect_path_records(item, child_path))
        return out
    # Scalar leaf.
    if isinstance(value, bool):
        normalized = "true" if value else "false"
    elif value is None:
        normalized = "null"
    else:
        normalized = str(value)
    out.append((path, normalized))
    return out


def _parse_path_records_from_md(md: str) -> set[tuple[str, str]]:
    """Parse a rendered MD back into the (path, value) record set.

    The MD format is line-oriented; any line matching the path-record
    regex contributes one record. Comment lines, prose, headings, and
    whitespace are ignored."""
    records: set[tuple[str, str]] = set()
    for raw_line in md.splitlines():
        line = raw_line.strip()
        m = _PATH_RECORD_RE.match(line)
        if m:
            records.add((m.group("path"), m.group("value").strip()))
    return records


def render_markdown(canonical: dict) -> str:
    """Render canonical JSON to deterministic markdown.

    Every tracked scalar is rendered as one ``P path:<full.path> = <value>``
    record line. Containers are represented only through their children's
    paths, except empty containers which get an explicit record so
    adding/removing them is detectable.

    The render is stable: sorting the records yields the same output for
    the same canonical input. Cosmetic edits (whitespace, prose, comment
    rewording) to the MD do not change the parsed record set.
    """
    # Round-trip through json to ensure deterministic key ordering and to
    # reject non-JSON-serializable input early.
    serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    canonical_norm = json.loads(serialized)
    sha = _hash_canonical(canonical_norm)

    records = _collect_path_records(canonical_norm)
    # Sort by (path, value) for deterministic output.
    records_sorted = sorted(records, key=lambda r: (r[0], r[1]))

    title = (
        canonical_norm.get("schema_version")
        if isinstance(canonical_norm, dict)
        else None
    ) or "canonical-json"

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("<!-- Rendered from canonical JSON. Do not edit. -->")
    lines.append("<!-- To change content, edit the canonical JSON and re-render. -->")
    lines.append("<!-- Each path-record line below is parsed as (path, value) and")
    lines.append("     compared as a set against the canonical projection. -->")
    lines.append("")
    lines.append("## Records")
    lines.append("")
    for path, value in records_sorted:
        lines.append(f"P path:{path} = {value}")
    lines.append("")
    lines.append(f"<!-- CANONICAL_SHA256: {sha} -->")
    lines.append("")
    return "\n".join(lines)


def reconcile_human_md(*, canonical: dict, human_md: str) -> dict:
    """Compare a hand-edited MD against the canonical JSON projection.

    Strategy (RW-P04-03 round 4):
    - Build the canonical record set from the canonical JSON.
    - Parse the human MD's path-record lines into the same set shape.
    - Compare the two sets EXACTLY (set equality on (path, value) tuples).
      Any extra/missing/different record is a real change.

    Cosmetic edits (whitespace, prose between records, comment rewording,
    blank lines) do not produce or remove path-record lines, so genuine
    cosmetic diffs still return COSMETIC_DIFF_ONLY.
    """
    canonical_norm = json.loads(
        json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    )
    canonical_records = set(_collect_path_records(canonical_norm))
    human_records = _parse_path_records_from_md(human_md)

    if canonical_records == human_records:
        return {"status": "IN_SYNC", "action": "NONE"}

    missing = canonical_records - human_records
    extra = human_records - canonical_records
    if not missing and not extra:
        return {"status": "COSMETIC_DIFF_ONLY", "action": "RE_RENDER_RECOMMENDED"}

    # We have at least one real structural/value change. Classify for the
    # error message.
    missing_paths = sorted(p for p, _ in missing)
    extra_paths = sorted(p for p, _ in extra)
    detail = (
        f"missing_from_human={missing_paths[:5]} "
        f"extra_in_human={extra_paths[:5]} "
        f"(canonical_records={len(canonical_records)} "
        f"human_records={len(human_records)})"
    )
    raise HumanMdCanonicalJsonMismatch("STRUCTURAL_OR_VALUE_CHANGE", detail)
