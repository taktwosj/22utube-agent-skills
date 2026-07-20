"""Canonical JSON -> human Markdown renderer with lossless record codec.

V2 design section 37: machine JSON is canonical. Human MD is rendered from
it deterministically (no LLM — section 44.2). The two are never edited
independently. If a hand-edited MD diverges from the canonical projection,
reconciliation raises HUMAN_MD_CANONICAL_JSON_MISMATCH.

RW-P04-03 round 5 (lossless typed record codec):
- Each tracked scalar is encoded as a single JSON array record of two
  elements: ``[path_segments, value]`` where ``path_segments`` is itself a
  JSON array of escaped segment strings (so a key like ``"a.b"`` never
  collides with a nested path ``a → b``), and ``value`` is the original
  JSON scalar (bool/number/string/null with full type, newline, and
  whitespace fidelity).
- Records are emitted one per line, prefixed with ``R ``. The MD therefore
  round-trips losslessly: parsing the record lines yields exactly the
  canonical scalars.
- reconcile_human_md compares the canonical record list against the
  human-MD-parsed record list as a SORTED MULTIPLICITY-PRESERVING list
  (NOT a set). Duplicate record lines and dot-bearing keys can no longer
  hide changes.

IN_SYNC vs COSMETIC_DIFF_ONLY:
- IN_SYNC: the rendered MD is byte-identical to a fresh canonical render.
- COSMETIC_DIFF_ONLY: the record lists are identical (same scalars) but
  the surrounding MD text differs (whitespace, comments, prose).
- Otherwise: HUMAN_MD_CANONICAL_JSONMismatch.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


class HumanMdCanonicalJsonMismatch(Exception):
    def __init__(self, kind: str, detail: str):
        super().__init__(f"HUMAN_MD_CANONICAL_JSON_MISMATCH kind={kind} {detail}")
        self.kind = kind
        self.detail = detail


RECORD_PREFIX = "R "


def _hash_canonical(canonical: Any) -> str:
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest().upper()


def _collect_records(
    value: Any,
    segments: list[str] | None = None,
) -> list[tuple[list[str], Any]]:
    """Walk canonical recursively and return [(segments, value)] for every
    scalar leaf plus explicit markers for empty containers.

    Containers (dict / non-empty list) produce no record of their own but
    their children carry the parent segments. Empty containers emit a
    synthetic record so adding/removing them is detectable.

    ``segments`` is a list of string segment names. Dict keys are appended
    verbatim (a key may contain dots; that's fine because we never split
    on dots — we transport the whole array). List indices are appended as
    ``[i]`` strings to mirror the source structure.
    """
    if segments is None:
        segments = []
    out: list[tuple[list[str], Any]] = []
    if isinstance(value, dict):
        if not value:
            out.append((list(segments), {"__empty__": "object"}))
            return out
        for k in sorted(value.keys()):
            child = list(segments)
            child.append(str(k))
            out.extend(_collect_records(value[k], child))
        return out
    if isinstance(value, list):
        if not value:
            out.append((list(segments), {"__empty__": "list"}))
            return out
        for i, item in enumerate(value):
            child = list(segments)
            child.append(f"[{i}]")
            out.extend(_collect_records(item, child))
        return out
    # Scalar leaf — keep the original Python value so json.dumps preserves
    # the JSON type exactly (bool vs number vs string).
    out.append((list(segments), value))
    return out


def _serialize_record(segments: list[str], value: Any) -> str:
    """Encode one record as a single JSON array line."""
    return RECORD_PREFIX + json.dumps([segments, value], ensure_ascii=False)


def _parse_record_line(line: str) -> tuple[list[str], Any] | None:
    """Parse a single record line. Returns (segments, value) or None if
    the line is not a record line."""
    s = line.strip()
    if not s.startswith(RECORD_PREFIX):
        return None
    payload = s[len(RECORD_PREFIX):]
    try:
        rec = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(rec, list) or len(rec) != 2:
        return None
    segments, value = rec
    if not isinstance(segments, list) or not all(
        isinstance(x, str) for x in segments
    ):
        return None
    return segments, value


def _parse_records_from_md(md: str) -> list[tuple[list[str], Any]]:
    """Parse every record line in the MD, preserving multiplicity and order."""
    out: list[tuple[list[str], Any]] = []
    for raw in md.splitlines():
        rec = _parse_record_line(raw)
        if rec is not None:
            out.append(rec)
    return out


def render_markdown(canonical: Any) -> str:
    """Render canonical JSON to deterministic markdown with lossless record
    encoding."""
    # Round-trip through json for deterministic key ordering and to reject
    # non-JSON-serializable input early.
    serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    canonical_norm = json.loads(serialized)
    sha = _hash_canonical(canonical_norm)

    records = _collect_records(canonical_norm)
    # Sort records by (segments, json(value)) for deterministic output that
    # is independent of insertion order.
    records.sort(key=lambda r: (r[0], json.dumps(r[1], sort_keys=True, ensure_ascii=False)))

    title = (
        canonical_norm.get("schema_version")
        if isinstance(canonical_norm, dict)
        else None
    ) or "canonical-json"

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("<!-- Rendered from canonical JSON. Do not edit. -->")
    lines.append("<!-- Each 'R ' line below is one JSON record [segments, value].")
    lines.append("     Reconciliation parses those records and compares them")
    lines.append("     losslessly as a sorted, multiplicity-preserving list. -->")
    lines.append("")
    lines.append("## Records")
    lines.append("")
    for segments, value in records:
        lines.append(_serialize_record(segments, value))
    lines.append("")
    lines.append(f"<!-- CANONICAL_SHA256: {sha} -->")
    lines.append("")
    return "\n".join(lines)


def reconcile_human_md(*, canonical: Any, human_md: str) -> dict:
    """Compare a hand-edited MD against the canonical JSON projection.

    Strategy (RW-P04-03 round 5, lossless codec):
    - Build the canonical record list (segments, value) preserving type
      and multiplicity.
    - Parse the human MD's R-lines into the same shape.
    - Sort both lists (canonical key for sorted order) and compare element
      by element. Set semantics are explicitly forbidden: duplicate lines
      and structural collisions must be caught.

    Outcomes:
    - IN_SYNC: the human MD is byte-identical to a fresh canonical render.
    - COSMETIC_DIFF_ONLY: the record lists are identical (same scalars,
      same multiplicity) but the surrounding MD text differs.
    - HumanMdCanonicalJsonMismatch: the record lists differ.
    """
    canonical_norm = json.loads(
        json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    )
    canonical_records = _collect_records(canonical_norm)
    human_records = _parse_records_from_md(human_md)

    # Sort key: deterministic ordering independent of source order. Segments
    # are converted to tuples so the key is hashable for the Counter step.
    def _key(rec: tuple[list[str], Any]) -> tuple:
        segments, value = rec
        return (tuple(segments), json.dumps(value, sort_keys=True, ensure_ascii=False))

    canonical_sorted = sorted(canonical_records, key=_key)
    human_sorted = sorted(human_records, key=_key)

    if canonical_sorted == human_sorted:
        # Record lists identical. Now decide IN_SYNC vs COSMETIC_DIFF_ONLY
        # by comparing the surrounding MD text against a fresh render.
        fresh = render_markdown(canonical)
        if human_md.strip() == fresh.strip():
            return {"status": "IN_SYNC", "action": "NONE"}
        return {"status": "COSMETIC_DIFF_ONLY", "action": "RE_RENDER_RECOMMENDED"}

    # Record lists differ. Classify the difference for the error message.
    canonical_count: dict[tuple, int] = {}
    for rec in canonical_sorted:
        k = _key(rec)
        canonical_count[k] = canonical_count.get(k, 0) + 1
    human_count: dict[tuple, int] = {}
    for rec in human_sorted:
        k = _key(rec)
        human_count[k] = human_count.get(k, 0) + 1

    missing = [
        k for k, n in canonical_count.items() if human_count.get(k, 0) < n
    ]
    extra = [
        k for k, n in human_count.items() if canonical_count.get(k, 0) < n
    ]
    # Render a short readable preview of the first few diffs.
    def _preview(key_tuple: tuple) -> str:
        segments_tuple, value_json = key_tuple
        path = "/".join(segments_tuple) if segments_tuple else "<root>"
        return f"{path}={value_json}"

    detail = (
        f"missing_or_underrepresented={[ _preview(k) for k in missing[:5] ]} "
        f"extra_or_overrepresented={[ _preview(k) for k in extra[:5] ]} "
        f"(canonical_records={len(canonical_sorted)} "
        f"human_records={len(human_sorted)})"
    )
    raise HumanMdCanonicalJsonMismatch("STRUCTURAL_OR_VALUE_CHANGE", detail)
